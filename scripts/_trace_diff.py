"""Check actual trace differences for failing operators."""
import json

d = json.load(open('research/G3_DIAGNOSTIC_20261028T090752Z.json', encoding='utf-8'))

for op_name in ['tool_subset_edit', 'crossover']:
    print(f"\n=== {op_name}: detailed trace comparison ===")
    r = d['operators'][op_name]
    for diff in r['diffs'][:2]:  # first 2 parents
        for sample in diff['samples'][:1]:  # first task
            print(f"\nParent {diff['parent']}, Task {sample['task_id']}:")
            for pt, ct in zip(sample['parent_traces'], sample['child_traces']):
                # Compare answers
                same_answer = pt.get('answer') == ct.get('answer')
                # Compare trace events (excluding meta)
                pt_events = [(e.get('type'), e.get('ok'), e.get('detail'), e.get('output')) for e in pt.get('trace', []) if e.get('type') != 'meta']
                ct_events = [(e.get('type'), e.get('ok'), e.get('detail'), e.get('output')) for e in ct.get('trace', []) if e.get('type') != 'meta']
                same_trace = pt_events == ct_events
                print(f"  rep={pt['rep']}: same_answer={same_answer}, same_trace={same_trace}")
                if not same_answer:
                    print(f"    parent answer: {pt.get('answer','')[:80]}")
                    print(f"    child  answer: {ct.get('answer','')[:80]}")
                if not same_trace:
                    print(f"    parent trace: {pt_events}")
                    print(f"    child  trace: {ct_events}")
