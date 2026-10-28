"""Diagnose tool_subset_edit and crossover failures."""
import json

d = json.load(open('research/G3_DIAGNOSTIC_20261028T090752Z.json', encoding='utf-8'))

# tool_subset_edit
print("=== tool_subset_edit diagnosis ===")
r = d['operators']['tool_subset_edit']
for diff in r['diffs']:
    print(f"\nParent {diff['parent']}: hash_changed={diff['hash_changed']} beh_changed={diff['behavior_changed']}")
    for sample in diff['samples']:
        print(f"  Task {sample['task_id']}:")
        print(f"    parent success={sample['parent']['success_rate']}, tools={sample['parent']['mean_tool_calls']}")
        print(f"    child  success={sample['child']['success_rate']}, tools={sample['child']['mean_tool_calls']}")
        # Check trace differences
        for pt, ct in zip(sample['parent_traces'], sample['child_traces']):
            pt_types = [e['type'] for e in pt.get('trace', []) if e.get('type') != 'meta']
            ct_types = [e['type'] for e in ct.get('trace', []) if e.get('type') != 'meta']
            if pt_types != ct_types:
                print(f"    TRACE DIFF: parent={pt_types} child={ct_types}")
            if pt.get('answer') != ct.get('answer'):
                print(f"    ANSWER DIFF: parent={pt.get('answer','')[:50]} vs child={ct.get('answer','')[:50]}")

# crossover
print("\n=== crossover diagnosis ===")
r = d['operators']['crossover']
for diff in r['diffs']:
    print(f"\nParent {diff['parent']}: hash_changed={diff['hash_changed']} beh_changed={diff['behavior_changed']}")
    for sample in diff['samples']:
        print(f"  Task {sample['task_id']}:")
        print(f"    parent success={sample['parent']['success_rate']}, tools={sample['parent']['mean_tool_calls']}")
        print(f"    child  success={sample['child']['success_rate']}, tools={sample['child']['mean_tool_calls']}")
        for pt, ct in zip(sample['parent_traces'], sample['child_traces']):
            pt_types = [e['type'] for e in pt.get('trace', []) if e.get('type') != 'meta']
            ct_types = [e['type'] for e in ct.get('trace', []) if e.get('type') != 'meta']
            if pt_types != ct_types:
                print(f"    TRACE DIFF: parent={pt_types} child={ct_types}")
            if pt.get('answer') != ct.get('answer'):
                print(f"    ANSWER DIFF: parent={pt.get('answer','')[:50]} vs child={ct.get('answer','')[:50]}")
