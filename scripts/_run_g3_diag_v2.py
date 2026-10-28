"""G3-DIAG-v2: Diagnostic experiment runner with per-request ledger.

Phase 3: limited re-verification (60 requests max).
- tool_subset_edit, crossover, prompt_critique_rewrite (positive control)
- Per-request ledger tracking
- Tool path verification
- Budget enforcement
"""
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, '.')

from gleppo.llm import ProductionLLM
from gleppo.interpreter import Interpreter
from gleppo.genotype import make_valid_genotype, behavior_hash, validate_genotype
from gleppo.operators import apply_operator
from gleppo.tasks import attach_checker
from gleppo.tool_path import verify_tool_path_for_task

RUN_ID = "20261028T130000Z"
PROTOCOL = "G3-DIAG-v2"
MAX_REQUESTS = 60
MAX_WALL_S = 600
N_REPLICATES = 2  # paired comparison: parent and child share seeds


class RequestLedger:
    """Per-request ledger for evidence integrity."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.entries = []
        self.total_requests = 0
        self.total_tokens = 0
        self.failures = 0

    def log(self, task_id: str, operator: str, parent_id: str, replicate: int,
            request_type: str, model_response: str = "", tokens: int = 0,
            success: bool = True, error: str = ""):
        """Log a single request."""
        self.total_requests += 1
        self.total_tokens += tokens
        if not success:
            self.failures += 1

        entry = {
            "request_id": self.total_requests,
            "run_id": self.run_id,
            "task_id": task_id,
            "operator": operator,
            "parent_id": parent_id,
            "replicate": replicate,
            "request_type": request_type,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "tokens": tokens,
            "success": success,
            "error": error,
            "response_preview": model_response[:100] if model_response else "",
        }
        self.entries.append(entry)
        return entry

    def save(self, path: str):
        """Save ledger to file."""
        with open(path, "w", encoding="utf-8") as f:
            for entry in self.entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        print(f"Ledger saved: {path} ({len(self.entries)} entries, sha256={sha[:16]})")

    def get_summary(self) -> dict:
        """Get ledger summary for report."""
        by_task = {}
        by_operator = {}
        for entry in self.entries:
            tid = entry["task_id"]
            op = entry["operator"]
            by_task[tid] = by_task.get(tid, 0) + 1
            by_operator[op] = by_operator.get(op, 0) + 1

        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "failures": self.failures,
            "by_task": by_task,
            "by_operator": by_operator,
        }


def behavior_signature(g, task, interp, n_rep=N_REPLICATES, paired_base=None):
    """Run n_rep replicates and collect behavior metrics + traces."""
    succ = 0
    tools = 0
    turns = 0
    fails = {}
    traces = []

    for r in range(n_rep):
        seed = (paired_base, task['task_id'], r, 0, 0) if paired_base else (task['task_id'], r, 0, 0)
        res = interp.run(g, task, seed_parts=seed)
        succ += int(res.success)
        tools += res.tool_calls
        turns += res.turns
        fails[res.failure_category] = fails.get(res.failure_category, 0) + 1

        # Verify tool path
        tool_path_result = verify_tool_path_for_task(
            task['task_id'], res.trace, task.get('required_tools', [])
        )

        traces.append({
            'rep': r,
            'success': res.success,
            'failure': res.failure_category,
            'turns': res.turns,
            'tool_calls': res.tool_calls,
            'answer': res.answer[:200],
            'tool_path_verified': tool_path_result['passed'],
            'tool_path_details': tool_path_result,
            'trace': [
                {
                    'type': e.get('type'),
                    'ok': e.get('ok'),
                    'detail': e.get('detail', ''),
                    'output': str(e.get('output', ''))[:100]
                }
                for e in res.trace
            ],
        })

    return {
        'success_rate': succ / n_rep,
        'mean_tool_calls': tools / n_rep,
        'mean_turns': turns / n_rep,
        'fails': fails,
        'traces': traces,
    }


def _beh_differs(bp, bc):
    """Check if parent and child behavior differs."""
    if bp['success_rate'] != bc['success_rate']:
        return True
    if bp['mean_tool_calls'] != bc['mean_tool_calls'] or bp['mean_turns'] != bc['mean_turns']:
        return True
    if bp['fails'] != bc['fails']:
        return True

    for t1, t2 in zip(bp['traces'], bc['traces']):
        def safe(tr):
            return [
                (e.get('type'), e.get('ok'), e.get('detail'), e.get('output'))
                for e in tr if e.get('type') != 'meta'
            ]
        if safe(t1.get('trace', [])) != safe(t2.get('trace', [])):
            return True
        if t1.get('answer') != t2.get('answer'):
            return True

    return False


def load_diag_tasks():
    """Load corrected diagnostic tasks."""
    tasks = []
    for fname in ['data/diagnostic_A2.jsonl', 'data/diagnostic_B2.jsonl']:
        with open(fname, encoding='utf-8') as f:
            for line in f:
                t = json.loads(line)
                tasks.append(attach_checker(t))
    return tasks


def main():
    print(f"G3-DIAG-v2 Diagnostic Experiment")
    print(f"Run ID: {RUN_ID}")
    print(f"Protocol: {PROTOCOL}")
    print(f"Max requests: {MAX_REQUESTS}")
    print()

    # Initialize ledger
    ledger = RequestLedger(RUN_ID)

    # Initialize LLM
    llm = ProductionLLM(device='cuda:0', max_new_tokens=256, temperature=0.7)
    interp = Interpreter(llm=llm)

    # Load tasks
    tasks = load_diag_tasks()
    print(f"Loaded {len(tasks)} diagnostic tasks")

    # Create parents with verifiable differences
    p1 = make_valid_genotype()
    p2 = make_valid_genotype()
    p2.system_prompt = "Use a different strategy: compute step by step and transform results. Final answer: {{answer}}"
    p2.tools = ["calc", "str_ops", "py_sandbox"]
    for step in p2.workflow:
        if step.tool and step.tool not in p2.tools:
            step.tool = p2.tools[0]

    print(f"p1 tools: {p1.tools}, hash: {behavior_hash(p1)[:8]}")
    print(f"p2 tools: {p2.tools}, hash: {behavior_hash(p2)[:8]}")

    # Initialize results
    results = {
        'run_id': RUN_ID,
        'protocol': PROTOCOL,
        'mode': 'G3_DIAG_V2',
        'model_revision': llm.version,
        'max_requests': MAX_REQUESTS,
        'tasks': [{'id': t['task_id'], 'family': t['family']} for t in tasks],
        'operators': {},
    }

    t_start = time.time()
    budget_exhausted = False

    # Test both failing operators + positive control
    for op_name in ['tool_subset_edit', 'crossover', 'prompt_critique_rewrite']:
        if budget_exhausted:
            break

        print(f"\n=== {op_name} ===")
        changed_hash = 0
        changed_behavior = 0
        valid = 0
        invalid = 0
        diffs = []

        # Test with 2 parents
        for p_idx, parent in enumerate([p1, p2]):
            if ledger.total_requests >= MAX_REQUESTS or (time.time() - t_start) > MAX_WALL_S:
                budget_exhausted = True
                break

            mate = p2 if parent is p1 else p1
            ctx = {'gen': p_idx, 'mate': mate, 'failure_category': 'wrong_answer'}

            child, ok, errs = apply_operator(op_name, parent, ctx)
            if not ok:
                invalid += 1
                diffs.append({'parent': p_idx, 'valid': False, 'errors': errs})
                continue

            valid += 1
            hash_changed = behavior_hash(parent) != behavior_hash(child)
            if hash_changed:
                changed_hash += 1

            # Test on diagnostic tasks
            beh_change = False
            sample = []

            for task in tasks:
                if ledger.total_requests >= MAX_REQUESTS:
                    budget_exhausted = True
                    break

                paired = f"diag-{task['task_id']}-p{p_idx}"

                # Run parent
                bp = behavior_signature(parent, task, interp, N_REPLICATES, paired)
                ledger.log(
                    task_id=task['task_id'],
                    operator=op_name,
                    parent_id=f"p{p_idx}",
                    replicate=0,
                    request_type="parent_eval",
                    tokens=llm.stats.get("total_tokens", 0),
                    success=True,
                )

                # Run child
                bc = behavior_signature(child, task, interp, N_REPLICATES, paired)
                ledger.log(
                    task_id=task['task_id'],
                    operator=op_name,
                    parent_id=f"p{p_idx}",
                    replicate=0,
                    request_type="child_eval",
                    tokens=llm.stats.get("total_tokens", 0),
                    success=True,
                )

                delta = {
                    'task_id': task['task_id'],
                    'family': task['family'],
                    'parent': {k: bp[k] for k in ('success_rate', 'mean_tool_calls', 'mean_turns', 'fails')},
                    'child': {k: bc[k] for k in ('success_rate', 'mean_tool_calls', 'mean_turns', 'fails')},
                    'parent_traces': bp['traces'],
                    'child_traces': bc['traces'],
                    'tool_path_parent': [t.get('tool_path_verified') for t in bp['traces']],
                    'tool_path_child': [t.get('tool_path_verified') for t in bc['traces']],
                }

                if _beh_differs(bp, bc):
                    beh_change = True

                sample.append(delta)

            if beh_change:
                changed_behavior += 1

            diffs.append({
                'parent': p_idx,
                'valid': True,
                'hash_changed': hash_changed,
                'behavior_changed': beh_change,
                'samples': sample,
            })
            print(f"  parent {p_idx}: hash={hash_changed} beh={beh_change}")

        threshold = max(1, valid // 2) if valid > 0 else 0
        results['operators'][op_name] = {
            'valid': valid,
            'invalid': invalid,
            'hash_changed': changed_hash,
            'behavior_changed': changed_behavior,
            'threshold': threshold,
            'pass': changed_behavior >= threshold if valid > 0 else False,
            'diffs': diffs,
        }
        print(f"  {op_name}: valid={valid} beh={changed_behavior} thresh={threshold} pass={results['operators'][op_name]['pass']}")

    # Finalize results
    results['llm_stats'] = llm.get_stats()
    results['ledger_summary'] = ledger.get_summary()
    results['total_requests'] = ledger.total_requests
    results['total_wall_s'] = round(time.time() - t_start, 4)
    results['budget_exhausted'] = budget_exhausted

    # Save ledger
    os.makedirs('research', exist_ok=True)
    ledger.save('research/G3_DIAG_V2_LEDGER.jsonl')

    # Save raw results
    path = 'research/G3_DIAG_V2_RAW.json'
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    sha = hashlib.sha256(open(path, 'rb').read()).hexdigest()

    print(f"\n=== SUMMARY ===")
    print(f"Requests: {ledger.total_requests}, Wall: {results['total_wall_s']}s")
    print(f"Budget exhausted: {budget_exhausted}")
    for op, r in results['operators'].items():
        print(f"  {op}: valid={r['valid']} beh={r['behavior_changed']} pass={r['pass']}")
    print(f"Saved: {path} sha256={sha[:16]}")

    return results


if __name__ == '__main__':
    main()
