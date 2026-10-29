"""G3-DIAG-v2-R2: Baseline tool-path diagnostic with task-compatible references.

Hard cap: 30 actual model.generate calls (enforced at generation boundary).
Wall clock: 300 seconds.
Baseline tool-path validation on B2-001/002/003 first, then operator comparison.
Fresh run ID, R2 artifact suffix. Never overwrites v2/R1 artifacts.
"""
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, '.')

from gleppo.llm import ProductionLLM, BudgetExceededError
from gleppo.interpreter import Interpreter
from gleppo.genotype import make_task_compatible_reference, behavior_hash
from gleppo.operators import apply_operator
from gleppo.tasks import attach_checker
from gleppo.tool_path import verify_tool_path_for_task

RUN_ID = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "_R2"
PROTOCOL = "G3-DIAG-v2-R2"
MAX_GENERATIONS = 30
MAX_WALL_S = 300
EXPECTED_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"


def load_b2_tasks():
    tasks = []
    with open('data/diagnostic_B2.jsonl', encoding='utf-8') as f:
        for line in f:
            tasks.append(attach_checker(json.loads(line)))
    return tasks


def run_genotype(g, task, interp, llm, n_rep=1, paired_base=None,
                 genotype_role="reference", operator=""):
    succ = 0
    traces = []
    tp_results = []
    for r in range(n_rep):
        seed = (paired_base, task['task_id'], r, 0, 0) if paired_base else (task['task_id'], r, 0, 0)
        prov = {"task_id": task['task_id'], "operator": operator,
                "genotype_role": genotype_role, "replicate": r, "turn": 0}
        res = interp.run(g, task, seed_parts=seed, provenance=prov)
        succ += int(res.success)
        tp = verify_tool_path_for_task(task['task_id'], res.trace, task.get('required_tools', []))
        tp_results.append(tp)
        traces.append({
            'rep': r, 'success': res.success, 'failure': res.failure_category,
            'turns': res.turns, 'tool_calls': res.tool_calls,
            'answer': res.answer[:300],
            'tool_path_passed': tp['passed'],
            'tool_path_details': tp,
            'trace': [{'type': e.get('type'), 'ok': e.get('ok'),
                       'detail': e.get('detail', ''),
                       'output': str(e.get('output', ''))[:150]}
                      for e in res.trace],
        })
    return {
        'success_rate': succ / n_rep, 'traces': traces,
        'tool_path_passed': all(tp['passed'] for tp in tp_results),
    }


def _beh_differs(bp, bc):
    if bp['success_rate'] != bc['success_rate']:
        return True
    for t1, t2 in zip(bp['traces'], bc['traces']):
        def safe(tr):
            return [(e.get('type'), e.get('ok'), e.get('detail'), e.get('output'))
                    for e in tr if e.get('type') != 'meta']
        if safe(t1.get('trace', [])) != safe(t2.get('trace', [])):
            return True
        if t1.get('answer') != t2.get('answer'):
            return True
    return False


def main():
    print(f"G3-DIAG-v2-R2 Baseline Diagnostic")
    print(f"Run ID: {RUN_ID}")
    print(f"Hard cap: {MAX_GENERATIONS} model.generate calls")
    print(f"Wall clock: {MAX_WALL_S}s")
    t_start = time.time()

    llm = ProductionLLM(device='cuda:0', max_new_tokens=256, temperature=0.7,
                        max_generations=MAX_GENERATIONS)
    interp = Interpreter(llm=llm)

    print(f"Revision match: {llm.version == EXPECTED_REVISION}")
    tasks = load_b2_tasks()
    print(f"Loaded {len(tasks)} B2 tasks")

    results = {
        'run_id': RUN_ID, 'protocol': PROTOCOL,
        'model_revision': llm.version,
        'revision_match': llm.version == EXPECTED_REVISION,
        'max_generations': MAX_GENERATIONS, 'max_wall_s': MAX_WALL_S,
        'baseline': {}, 'operators': {},
    }

    budget_exhausted = False

    # Phase 1: Baseline tool-path validation with task-compatible references
    print("\n=== Phase 1: Baseline tool-path validation ===")
    baseline_all_pass = True
    for task in tasks:
        if llm._call_id >= MAX_GENERATIONS or (time.time() - t_start) > MAX_WALL_S:
            budget_exhausted = True
            print(f"BUDGET EXHAUSTED before baseline {task['task_id']}")
            break
        try:
            ref = make_task_compatible_reference(task['task_id'])
            sig = run_genotype(ref, task, interp, llm,
                               n_rep=1, paired_base=f"r2-baseline-{task['task_id']}",
                               genotype_role="task_compatible_reference", operator="baseline")
        except BudgetExceededError:
            budget_exhausted = True
            break

        tp_pass = sig['tool_path_passed']
        baseline_all_pass = baseline_all_pass and tp_pass
        results['baseline'][task['task_id']] = {
            'tool_path_passed': tp_pass, 'success_rate': sig['success_rate'],
            'traces': sig['traces'],
        }
        print(f"  {task['task_id']}: tool_path={'PASS' if tp_pass else 'FAIL'}, success={sig['success_rate']}")

    print(f"\nBaseline all pass: {baseline_all_pass}")

    if not baseline_all_pass:
        print("STOP: baseline tool-path failure. Not spending budget on operator comparison.")
        results['stopped_reason'] = 'baseline_tool_path_failure'
    elif budget_exhausted:
        results['stopped_reason'] = 'budget_exhausted'
    else:
        # Phase 2: Operator comparison
        print("\n=== Phase 2: Operator comparison ===")
        for op_name in ['tool_subset_edit', 'crossover']:
            if budget_exhausted:
                break
            print(f"\n  --- {op_name} ---")
            valid = 0
            behavior_changed = 0
            diffs = []
            for task in tasks:
                if llm._call_id >= MAX_GENERATIONS or (time.time() - t_start) > MAX_WALL_S:
                    budget_exhausted = True
                    break
                try:
                    parent = make_task_compatible_reference(task['task_id'])
                    mate = make_task_compatible_reference(task['task_id'])
                    mate.system_prompt = mate.system_prompt + " Alternative strategy: compute intermediates first."

                    if op_name == 'crossover':
                        ctx = {'gen': 0, 'mate': mate, 'failure_category': 'wrong_answer'}
                    else:
                        ctx = {'gen': 0, 'mate': mate, 'failure_category': 'wrong_answer'}

                    child, ok, errs = apply_operator(op_name, parent, ctx)
                    if not ok:
                        diffs.append({'task': task['task_id'], 'valid': False, 'errors': errs})
                        continue
                    valid += 1
                    paired = f"r2-{task['task_id']}"
                    bp = run_genotype(parent, task, interp, llm,
                                      n_rep=1, paired_base=paired,
                                      genotype_role="reference", operator=op_name)
                    bc = run_genotype(child, task, interp, llm,
                                      n_rep=1, paired_base=paired,
                                      genotype_role="child", operator=op_name)
                    beh_change = _beh_differs(bp, bc)
                    if beh_change:
                        behavior_changed += 1
                    diffs.append({
                        'task': task['task_id'], 'valid': True,
                        'behavior_changed': beh_change,
                        'parent': {'success_rate': bp['success_rate'],
                                   'tool_path_passed': bp['tool_path_passed']},
                        'child': {'success_rate': bc['success_rate'],
                                  'tool_path_passed': bc['tool_path_passed']},
                        'parent_traces': bp['traces'], 'child_traces': bc['traces'],
                    })
                    print(f"    {task['task_id']}: beh={beh_change}")
                except BudgetExceededError:
                    budget_exhausted = True
                    break

            threshold = max(1, valid // 2) if valid > 0 else 0
            results['operators'][op_name] = {
                'valid': valid, 'behavior_changed': behavior_changed,
                'threshold': threshold,
                'pass': behavior_changed >= threshold if valid > 0 else False,
                'diffs': diffs,
            }
            print(f"    {op_name}: valid={valid} beh={behavior_changed} pass={results['operators'][op_name]['pass']}")

    # Finalize
    elapsed = time.time() - t_start
    ledger = llm.get_generation_ledger()
    stats = llm.get_stats()
    results['generation_ledger'] = ledger
    results['llm_stats'] = stats
    results['total_actual_generations'] = len(ledger)
    results['total_wall_s'] = round(elapsed, 4)
    results['budget_exhausted'] = budget_exhausted
    results['ledger_counter_match'] = (len(ledger) == stats.get('actual_generations', -1))
    token_delta_sum = sum(r['output_tokens'] for r in ledger)
    results['token_delta_sum'] = token_delta_sum
    results['token_sum_match'] = (token_delta_sum == stats.get('total_tokens', -1))

    os.makedirs('research', exist_ok=True)
    ledger_path = 'research/G3_DIAG_R2_LEDGER.jsonl'
    with open(ledger_path, 'w', encoding='utf-8') as f:
        for row in ledger:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    ledger_sha = hashlib.sha256(open(ledger_path, 'rb').read()).hexdigest()

    raw_path = 'research/G3_DIAG_R2_RAW.json'
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
