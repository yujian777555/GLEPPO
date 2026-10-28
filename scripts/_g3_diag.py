"""G3-DIAG-v1: diagnostic experiment for failing operators."""
import json, os, sys, time, hashlib
sys.path.insert(0, '.')
from gleppo.llm import ProductionLLM
from gleppo.interpreter import Interpreter
from gleppo.genotype import make_valid_genotype, behavior_hash, validate_genotype
from gleppo.operators import apply_operator
from gleppo.tasks import attach_checker

RUN_ID = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
MAX_REQUESTS = 100
MAX_WALL_S = 600

class InstrumentedInterpreter(Interpreter):
    def __init__(self, llm=None):
        super().__init__(llm=llm)
    def run(self, g, task, seed_parts=None):
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

def load_diag_tasks():
    tasks = []
    for fname in ['data/diagnostic_A2.jsonl', 'data/diagnostic_B2.jsonl']:
        with open(fname) as f:
            for line in f:
                t = json.loads(line)
                tasks.append(attach_checker(t))
    return tasks

def main():
    print(f"Run ID: {RUN_ID}")
    llm = ProductionLLM(device='cuda:0', max_new_tokens=256, temperature=0.7)
    interp = InstrumentedInterpreter(llm=llm)
    
    # Load diagnostic tasks
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
    
    results = {'run_id': RUN_ID, 'mode': 'G3_DIAG_V1', 'model_revision': llm.version,
               'tasks': [{'id': t['task_id'], 'family': t['family']} for t in tasks],
               'operators': {}}
    requests = 0; t_start = time.time(); budget_exhausted = False
    
    # Test both failing operators + positive control (prompt_critique_rewrite)
    for op_name in ['tool_subset_edit', 'crossover', 'prompt_critique_rewrite']:
        if budget_exhausted: break
        print(f"\n=== {op_name} ===")
        changed_hash = 0; changed_behavior = 0; valid = 0; invalid = 0; diffs = []
        
        # Test with 2 parents (p1 and p2)
        for p_idx, parent in enumerate([p1, p2]):
            if requests >= MAX_REQUESTS or (time.time()-t_start) > MAX_WALL_S:
                budget_exhausted = True; break
            
            if op_name == 'crossover':
                mate = p2 if parent is p1 else p1
                ctx = {'gen': p_idx, 'mate': mate, 'failure_category': 'wrong_answer'}
            else:
                mate = p2 if parent is p1 else p1
                ctx = {'gen': p_idx, 'mate': mate, 'failure_category': 'wrong_answer'}
            
            child, ok, errs = apply_operator(op_name, parent, ctx)
            if not ok:
                invalid += 1
                diffs.append({'parent': p_idx, 'valid': False, 'errors': errs})
                continue
            valid += 1
            hash_changed = behavior_hash(parent) != behavior_hash(child)
            if hash_changed: changed_hash += 1
            
            # Test on diagnostic tasks
            beh_change = False; sample = []
            for task in tasks:
                if requests >= MAX_REQUESTS: budget_exhausted = True; break
                paired = f"diag-{task['task_id']}-p{p_idx}"
                bp = behavior_signature(parent, task, interp, 2, paired)
                bc = behavior_signature(child, task, interp, 2, paired)
                requests += 4
                delta = {
                    'task_id': task['task_id'], 'family': task['family'],
                    'parent': {k: bp[k] for k in ('success_rate','mean_tool_calls','mean_turns','fails')},
                    'child': {k: bc[k] for k in ('success_rate','mean_tool_calls','mean_turns','fails')},
                    'parent_traces': bp['traces'], 'child_traces': bc['traces'],
                }
                if _beh_differs(bp, bc):
                    beh_change = True
                sample.append(delta)
            
            if beh_change: changed_behavior += 1
            diffs.append({
                'parent': p_idx, 'valid': True, 'hash_changed': hash_changed,
                'behavior_changed': beh_change, 'samples': sample,
            })
            print(f"  parent {p_idx}: hash={hash_changed} beh={beh_change}")
        
        threshold = max(1, valid // 2) if valid > 0 else 0
        results['operators'][op_name] = {
            'valid': valid, 'invalid': invalid, 'hash_changed': changed_hash,
            'behavior_changed': changed_behavior, 'threshold': threshold,
            'pass': changed_behavior >= threshold if valid > 0 else False,
            'diffs': diffs,
        }
        print(f"  {op_name}: valid={valid} beh={changed_behavior} thresh={threshold} pass={results['operators'][op_name]['pass']}")
    
    results['llm_stats'] = llm.get_stats()
    results['total_requests'] = requests
    results['total_wall_s'] = round(time.time()-t_start, 4)
    results['budget_exhausted'] = budget_exhausted
    
    # Save
    os.makedirs('research', exist_ok=True)
    path = f'research/G3_DIAG_V1_RAW.json'
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    sha = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    
    print(f"\n=== SUMMARY ===")
    print(f"Requests: {requests}, Wall: {results['total_wall_s']}s, Budget exhausted: {budget_exhausted}")
    for op, r in results['operators'].items():
        print(f"  {op}: valid={r['valid']} beh={r['behavior_changed']} pass={r['pass']}")
    print(f"Saved: {path} sha256={sha[:16]}")

if __name__ == '__main__':
    main()
