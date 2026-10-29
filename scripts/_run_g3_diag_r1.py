"""G3-DIAG-v2-R1: Stage B bounded diagnostic.

Hard cap: 30 actual model.generate calls (enforced at generation boundary).
Wall clock: 300 seconds.
Baseline tool-path validation on B2-001/002/003 first, then operator comparison.
Fresh run ID, R1 artifact suffix. Never overwrites v2 artifacts.
"""
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, '.')

from gleppo.llm import ProductionLLM, BudgetExceededError
from gleppo.interpreter import Interpreter
from gleppo.genotype import make_valid_genotype, behavior_hash
from gleppo.operators import apply_operator
from gleppo.tasks import attach_checker
from gleppo.tool_path import verify_tool_path_for_task

RUN_ID = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "_R1"
PROTOCOL = "G3-DIAG-v2-R1"
MAX_GENERATIONS = 30   # hard cap at model.generate boundary
MAX_WALL_S = 300

EXPECTED_MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"


def load_b2_tasks():
    """Load only B2 diagnostic tasks."""
    tasks = []
    with open('data/diagnostic_B2.jsonl', encoding='utf-8') as f:
        for line in f:
            t = json.loads(line)
            tasks.append(attach_checker(t))
    return tasks


def run_genotype_on_task(g, task, interp, llm, n_rep=1, paired_base=None,
                         genotype_role="parent", operator=""):
    """Run genotype on task, return behavior signature + tool path results."""
    succ = 0
    tools = 0
    turns = 0
    traces = []
    tool_path_results = []

    for r in range(n_rep):
        seed = (paired_base, task['task_id'], r, 0, 0) if paired_base else (task['task_id'], r, 0, 0)

        # Inject provenance for the ledger
        provenance = {
            "task_id": task['task_id'],
            "operator": operator,
            "genotype_role": genotype_role,
            "replicate": r,
            "turn": 0,
        }

        res = interp.run(g, task, seed_parts=seed, provenance=provenance)
        succ += int(res.success)
        tools += res.tool_calls
        turns += res.turns

        # Verify tool path
        tp_result = verify_tool_path_for_task(
            task['task_id'], res.trace, task.get('required_tools', [])
        )
        tool_path_results.append(tp_result)

        traces.append({
            'rep': r,
            'success': res.success,
            'failure': res.failure_category,
            'turns': res.turns,
            'tool_calls': res.tool_calls,
            'answer': res.answer[:300],
            'tool_path_passed': tp_result['passed'],
            'tool_path_details': tp_result,
            'trace': [
                {'type': e.get('type'), 'ok': e.get('ok'),
                 'detail': e.get('detail', ''),
                 'output': str(e.get('output', ''))[:150]}
                for e in res.trace
            ],
        })

    return {
        'success_rate': succ / n_rep,
        'mean_tool_calls': tools / n_rep,
        'mean_turns': turns / n_rep,
        'traces': traces,
        'tool_path_passed': all(tp['passed'] for tp in tool_path_results),
        'tool_path_results': tool_path_results,
    }


def _beh_differs(bp, bc):
    """Check if parent and child behavior differs."""
    if bp['success_rate'] != bc['success_rate']:
        return True
    if bp['mean_tool_calls'] != bc['mean_tool_calls'] or bp['mean_turns'] != bc['mean_turns']:
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


def main():
    print(f"G3-DIAG-v2-R1 Stage B Diagnostic")
    print(f"Run ID: {RUN_ID}")
    print(f"Hard cap: {MAX_GENERATIONS} model.generate calls")
    print(f"Wall clock: {MAX_WALL_S}s")
    print()

    t_start = time.time()

    # Initialize LLM with hard cap
    llm = ProductionLLM(
        device='cuda:0', max_new_tokens=256, temperature=0.7,
        max_generations=MAX_GENERATIONS,
    )
    interp = Interpreter(llm=llm)

    # Verify loaded revision
    loaded_revision = llm.version
    revision_match = loaded_revision == EXPECTED_MODEL_REVISION
    print(f"Expected revision: {EXPECTED_MODEL_REVISION}")
    print(f"Loaded revision:   {loaded_revision}")
    print(f"Revision match: {revision_match}")
    if not revision_match:
        print("WARNING: revision mismatch!")

    # Load B2 tasks
    tasks = load_b2_tasks()
    print(f"Loaded {len(tasks)} B2 diagnostic tasks")

    results = {
        'run_id': RUN_ID,
        'protocol': PROTOCOL,
        'model_revision': loaded_revision,
        'revision_match': revision_match,
        'max_generations': MAX_GENERATIONS,
        'max_wall_s': MAX_WALL_S,
        'baseline': {},
        'operators': {},
    }

    budget_exhausted = False

    # ================================================================
    # PHASE 1: Baseline tool-path validation on B2-001/002/003
    # ================================================================
    print("\n=== Phase 1: Baseline tool-path validation ===")
    baseline = make_valid_genotype()
    baseline_all_pass = True

    for task in tasks:
        if llm._call_id >= MAX_GENERATIONS or (time.time() - t_start) > MAX_WALL_S:
            budget_exhausted = True
            print(f"BUDGET EXHAUSTED before baseline {task['task_id']}")
            break

        try:
            sig = run_genotype_on_task(
                baseline, task, interp, llm,
                n_rep=1, paired_base=f"r1-baseline-{task['task_id']}",
                genotype_role="baseline", operator="baseline",
            )
        except BudgetExceededError:
            budget_exhausted = True
            print(f"BUDGET EXHAUSTED during baseline {task['task_id']}")
            break

        tp_pass = sig['tool_path_passed']
        baseline_all_pass = baseline_all_pass and tp_pass
        results['baseline'][task['task_id']] = {
            'tool_path_passed': tp_pass,
            'success_rate': sig['success_rate'],
            'traces': sig['traces'],
        }
        status = "PASS" if tp_pass else "FAIL"
        print(f"  {task['task_id']}: tool_path={status}, success={sig['success_rate']}")

    print(f"\nBaseline all pass: {baseline_all_pass}")

    if not baseline_all_pass and not budget_exhausted:
        print("STOP: baseline tool-path failure. Not spending budget on operator comparison.")
        results['stopped_reason'] = 'baseline_tool_path_failure'
    elif budget_exhausted and not baseline_all_pass:
        print("STOP: budget exhausted during baseline.")
        results['stopped_reason'] = 'budget_exhausted_during_baseline'
    else:
        # ================================================================
        # PHASE 2: Operator comparison (if baseline passes)
        # ================================================================
        print("\n=== Phase 2: Operator comparison ===")

        p1 = make_valid_genotype()
        p2 = make_valid_genotype()
        p2.system_prompt = "Use a different strategy: compute step by step and transform results. Final answer: {{answer}}"
        p2.tools = ["calc", "str_ops", "py_sandbox"]
        for step in p2.workflow:
            if step.tool and step.tool not in p2.tools:
                step.tool = p2.tools[0]

        for op_name in ['tool_subset_edit', 'crossover']:
            if budget_exhausted:
                break

            print(f"\n  --- {op_name} ---")
            valid = 0
            behavior_changed = 0
            diffs = []

            for p_idx, parent in enumerate([p1, p2]):
                if llm._call_id >= MAX_GENERATIONS or (time.time() - t_start) > MAX_WALL_S:
                    budget_exhausted = True
                    break

                mate = p2 if parent is p1 else p1
                ctx = {'gen': p_idx, 'mate': mate, 'failure_category': 'wrong_answer'}
                child, ok, errs = apply_operator(op_name, parent, ctx)
                if not ok:
                    diffs.append({'parent': p_idx, 'valid': False, 'errors': errs})
                    continue

                valid += 1
                beh_change = False
                sample = []

                for task in tasks:
                    if llm._call_id >= MAX_GENERATIONS or (time.time() - t_start) > MAX_WALL_S:
                        budget_exhausted = True
                        break

                    paired = f"r1-{task['task_id']}-p{p_idx}"

                    try:
                        bp = run_genotype_on_task(
                            parent, task, interp, llm,
                            n_rep=1, paired_base=paired,
                            genotype_role="parent", operator=op_name,
                        )
                        bc = run_genotype_on_task(
                            child, task, interp, llm,
                            n_rep=1, paired_base=paired,
                            genotype_role="child", operator=op_name,
                        )
                    except BudgetExceededError:
                        budget_exhausted = True
                        break

                    delta = {
                        'task_id': task['task_id'],
                        'parent': {
                            'success_rate': bp['success_rate'],
                            'tool_path_passed': bp['tool_path_passed'],
                        },
                        'child': {
                            'success_rate': bc['success_rate'],
                            'tool_path_passed': bc['tool_path_passed'],
                        },
                        'parent_traces': bp['traces'],
                        'child_traces': bc['traces'],
                    }

                    if _beh_differs(bp, bc):
                        beh_change = True

                    sample.append(delta)

                if beh_change:
                    behavior_changed += 1

                diffs.append({
                    'parent': p_idx, 'valid': True,
                    'behavior_changed': beh_change,
                    'samples': sample,
                })
                print(f"    parent {p_idx}: beh={beh_change}")

            threshold = max(1, valid // 2) if valid > 0 else 0
            results['operators'][op_name] = {
                'valid': valid,
                'behavior_changed': behavior_changed,
                'threshold': threshold,
                'pass': behavior_changed >= threshold if valid > 0 else False,
                'diffs': diffs,
            }
            print(f"    {op_name}: valid={valid} beh={behavior_changed} pass={results['operators'][op_name]['pass']}")

    # ================================================================
    # Finalize
    # ================================================================
    elapsed = time.time() - t_start
    ledger = llm.get_generation_ledger()
    stats = llm.get_stats()

    results['generation_ledger'] = ledger
    results['llm_stats'] = stats
    results['total_actual_generations'] = len(ledger)
    results['total_wall_s'] = round(elapsed, 4)
    results['budget_exhausted'] = budget_exhausted

    # Cross-check: ledger rows == runtime counter
    results['ledger_counter_match'] = (len(ledger) == stats.get('actual_generations', -1))

    # Cross-check: per-call output token deltas sum to runtime total
    token_delta_sum = sum(r['output_tokens'] for r in ledger)
    results['token_delta_sum'] = token_delta_sum
    results['token_sum_match'] = (token_delta_sum == stats.get('total_tokens', -1))

    # Save artifacts with R1 suffix
    os.makedirs('research', exist_ok=True)

    ledger_path = 'research/G3_DIAG_R1_LEDGER.jsonl'
    with open(ledger_path, 'w', encoding='utf-8') as f:
        for row in ledger:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    ledger_sha = hashlib.sha256(open(ledger_path, 'rb').read()).hexdigest()

    raw_path = 'research/G3_DIAG_R1_RAW.json'
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    raw_sha = hashlib.sha256(open(raw_path, 'rb').read()).hexdigest()

    print(f"\n=== SUMMARY ===")
    print(f"Run ID: {RUN_ID}")
    print(f"Actual generations: {len(ledger)} / {MAX_GENERATIONS}")
    print(f"Wall clock: {results['total_wall_s']}s / {MAX_WALL_S}s")
    print(f"Budget exhausted: {budget_exhausted}")
    print(f"Ledger counter match: {results['ledger_counter_match']}")
    print(f"Token sum match: {results['token_sum_match']}")
    print(f"Baseline all pass: {baseline_all_pass}")
    for op, r in results['operators'].items():
        print(f"  {op}: valid={r['valid']} beh={r['behavior_changed']} pass={r['pass']}")
    print(f"\nLedger: {ledger_path} sha256={ledger_sha[:16]}")
    print(f"Raw: {raw_path} sha256={raw_sha[:16]}")

    return results


if __name__ == '__main__':
    main()
