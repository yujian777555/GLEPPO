"""G3 diagnostic Canary: Family A/B, budget-protected, full evidence."""
import json, os, sys, time, hashlib
sys.path.insert(0, '.')
from gleppo.llm import ProductionLLM
from gleppo.interpreter import Interpreter
from gleppo.genotype import make_valid_genotype
from gleppo.tasks import build_task, attach_checker

RUN_ID = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
MAX_REQUESTS = 30
MAX_WALL_S = 300

def main():
    print(f"Run ID: {RUN_ID}")
    llm = ProductionLLM(device='cuda:0', max_new_tokens=256, temperature=0.7)
    print(f"Model: {llm.name} rev={llm.version}")
    interp = Interpreter(llm=llm)
    g = make_valid_genotype()

    tasks = [
        attach_checker(build_task('A-g3-prod-00', 'A', 100, 'TA1')),
        attach_checker(build_task('B-g3-prod-00', 'B', 200, 'TB1')),
    ]

    results = []
    requests = 0
    t_start = time.time()

    for task in tasks:
        for rep in range(3):
            if requests >= MAX_REQUESTS or (time.time() - t_start) > MAX_WALL_S:
                print(f"BUDGET LIMIT: requests={requests}, wall={time.time()-t_start:.1f}s")
                break
            seed = ('canary', task['task_id'], rep, 0, 0)
            res = interp.run(g, task, seed_parts=seed)
            requests += 1
            # Full evidence
            tool_events = []
            for e in res.trace:
                tool_events.append({
                    'type': e.get('type'), 'ok': e.get('ok'),
                    'detail': e.get('detail', ''), 'output': str(e.get('output', ''))[:200],
                })
            results.append({
                'task_id': task['task_id'], 'family': task['family'], 'replicate': rep,
                'seed': list(seed), 'success': res.success,
                'failure': res.failure_category, 'answer': res.answer[:300],
                'turns': res.turns, 'tool_calls': res.tool_calls,
                'trace': tool_events,
            })
            print(f"{task['task_id']} rep={rep}: success={res.success} fail={res.failure_category}")

    total_wall = time.time() - t_start
    llm_stats = llm.get_stats()

    # Save evidence
    raw = {
        'run_id': RUN_ID, 'mode': 'CANARY_PRODUCTION',
        'model_revision': llm.version,
        'budget': {'max_requests': MAX_REQUESTS, 'max_wall_s': MAX_WALL_S},
        'actual_requests': requests, 'actual_wall_s': round(total_wall, 4),
        'tasks': results, 'llm_stats': llm_stats,
        'family_c_accessed': False,
    }
    os.makedirs('research', exist_ok=True)
    path = f'research/CANARY_{RUN_ID}.json'
    with open(path, 'w') as f:
        json.dump(raw, f, indent=2)
    sha = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    print(f"Saved: {path} sha256={sha[:16]}")

    # Check pass condition
    for fam in ['A', 'B']:
        fam_results = [r for r in results if r['family'] == fam]
        successes = sum(1 for r in fam_results if r['success'])
        print(f"Family {fam}: {successes}/{len(fam_results)} success")
    print(f"Total: {requests} requests, {total_wall:.1f}s wall")
    print(f"LLM stats: {llm_stats}")

if __name__ == '__main__':
    main()
