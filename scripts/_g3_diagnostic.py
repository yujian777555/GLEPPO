"""G3 diagnostic: five operators, budget-protected, full evidence."""
import json, os, sys, time, hashlib
sys.path.insert(0, '.')
from gleppo.llm import ProductionLLM
from gleppo.interpreter import Interpreter
from gleppo.genotype import make_valid_genotype, behavior_hash, validate_genotype
from gleppo.operators import OPERATOR_NAMES, apply_operator
from gleppo.tasks import build_task, attach_checker

RUN_ID = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
MAX_REQUESTS = 200
MAX_WALL_S = 1200

class InstrumentedInterpreter(Interpreter):
    def __init__(self, llm=None):
        super().__init__(llm=llm)
        self.seed_log = []
    def run(self, g, task, seed_parts=None):
        self.seed_log.append(tuple(seed_parts))
        return super().run(g, task, seed_parts=seed_parts)

def behavior_signature(g, task, interp, n_rep=2, paired_base=None):
    succ = 0; tools = 0; turns = 0; fails = {}; traces = []
    for r in range(n_rep):
        seed = (paired_base, task['task_id'], r, 0, 0) if paired_base else (task['task_id'], r, 0, 0)
        res = interp.run(g, task, seed_parts=seed)
        succ += int(res.success); tools += res.tool_calls; turns += res.turns
        fails[res.failure_category] = fails.get(res.failure_category, 0) + 1
        traces.append({
            'rep': r, 'success': res.success, 'failure': res.failure_category,
            'turns': res.turns, 'tool_calls': res.tool_calls,
            'answer': res.answer[:200],
            'trace': [{'type': e.get('type'), 'ok': e.get('ok'), 'detail': e.get('detail',''), 'output': str(e.get('output',''))[:100]} for e in res.trace],
        })
    return {'success_rate': succ/n_rep, 'mean_tool_calls': tools/n_rep, 'mean_turns': turns/n_rep, 'fails': fails, 'traces': traces}

def _beh_differs(bp, bc):
    if bp['success_rate'] != bc['success_rate']: return True
    if bp['mean_tool_calls'] != bc['mean_tool_calls'] or bp['mean_turns'] != bc['mean_turns']: return True
    if bp['fails'] != bc['fails']: return True
    for t1, t2 in zip(bp['traces'], bc['traces']):
        def safe(tr): return [(e.get('type'), e.get('ok'), e.get('detail'), e.get('output')) for e in tr if e.get('type') != 'meta']
        if safe(t1.get('trace',[])) != safe(t2.get('trace',[])): return True
        if t1.get('answer') != t2.get('answer'): return True
    return False

def main():
    print(f"Run ID: {RUN_ID}")
    llm = ProductionLLM(device='cuda:0', max_new_tokens=256, temperature=0.7)
    interp = InstrumentedInterpreter(llm=llm)
    tasks = [attach_checker(build_task('A-g3-prod-00', 'A', 100, 'TA1')), attach_checker(build_task('B-g3-prod-00', 'B', 200, 'TB1'))]
    parents = []
    for i in range(4):
        g = make_valid_genotype(); g.system_prompt += f" Variant {i}."; g.meta = {'parent_id': f'p{i}'}; parents.append(g)

    report = {'run_id': RUN_ID, 'mode': 'G3_PRODUCTION_DIAGNOSTIC', 'model_revision': llm.version,
              'tasks': [{'id': t['task_id'], 'family': t['family']} for t in tasks], 'operators': {}}
    requests = 0; t_start = time.time(); budget_exhausted = False

    for op in OPERATOR_NAMES:
        if budget_exhausted: break
        changed_hash = 0; changed_behavior = 0; valid = 0; invalid = 0; diffs = []
        for p_idx, parent in enumerate(parents):
            if requests >= MAX_REQUESTS or (time.time()-t_start) > MAX_WALL_S:
                budget_exhausted = True; break
            ctx = {'gen': p_idx, 'failure_category': ['tool_error','wrong_answer','format_error','timeout'][p_idx%4], 'failure_detail': 'sample', 'mate': parents[(p_idx+1)%4]}
            child, ok, errs = apply_operator(op, parent, ctx)
            if not ok: invalid += 1; continue
            valid += 1
            if behavior_hash(parent) != behavior_hash(child): changed_hash += 1
            beh_change = False; sample = []
            for task in tasks:
                paired = f"paired-{task['task_id']}-p{p_idx}"
                bp = behavior_signature(parent, task, interp, 2, paired)
                bc = behavior_signature(child, task, interp, 2, paired)
                requests += 4
                delta = {'task_id': task['task_id'], 'family': task['family'],
                         'parent': {k: bp[k] for k in ('success_rate','mean_tool_calls','mean_turns','fails')},
                         'child': {k: bc[k] for k in ('success_rate','mean_tool_calls','mean_turns','fails')},
                         'parent_traces': bp['traces'], 'child_traces': bc['traces']}
                if _beh_differs(bp, bc):
                    beh_change = True
                sample.append(delta)
            if beh_change: changed_behavior += 1
            diffs.append({'parent': p_idx, 'hash_changed': behavior_hash(parent)!=behavior_hash(child),
                          'behavior_changed': beh_change, 'samples': sample})
        threshold = max(1, valid // 2) if valid > 0 else 0
        report['operators'][op] = {'valid': valid, 'invalid': invalid, 'hash_changed': changed_hash,
                                    'behavior_changed': changed_behavior, 'threshold': threshold,
                                    'pass': changed_behavior >= threshold if valid > 0 else False, 'diffs': diffs}
        print(f"  {op}: valid={valid} invalid={invalid} hash={changed_hash} beh={changed_behavior} thresh={threshold} pass={report['operators'][op]['pass']}")

    report['llm_stats'] = llm.get_stats()
    report['total_requests'] = requests
    report['total_wall_s'] = round(time.time()-t_start, 4)
    report['budget_exhausted'] = budget_exhausted
    all_pass = all(r['pass'] for r in report['operators'].values())
    if budget_exhausted:
        report['g3_overall'] = 'INCONCLUSIVE_BUDGET'
    else:
        report['g3_overall'] = 'PASS' if all_pass else 'FAIL'

    os.makedirs('research', exist_ok=True)
    path = f'research/G3_DIAGNOSTIC_{RUN_ID}.json'
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    sha = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    print(f"\nG3_OVERALL: {report['g3_overall']}")
    print(f"Requests: {requests}, Wall: {report['total_wall_s']}s, Budget exhausted: {budget_exhausted}")
    print(f"Saved: {path} sha256={sha[:16]}")

if __name__ == '__main__':
    main()
