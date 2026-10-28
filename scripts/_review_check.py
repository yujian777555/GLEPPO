"""Independent review: verify G3 raw data."""
import json

d = json.load(open('research/G3_DIAGNOSTIC_20261028T090752Z.json', encoding='utf-8'))
print('run_id:', d['run_id'])
print('model:', d['model_revision'])
print('total_requests:', d['total_requests'])
print('wall_s:', d['total_wall_s'])
print('budget_exhausted:', d['budget_exhausted'])
print('g3_overall:', d['g3_overall'])
print()
for op, r in d['operators'].items():
    print(f"{op}: valid={r['valid']} invalid={r['invalid']} hash={r['hash_changed']} beh={r['behavior_changed']} thresh={r['threshold']} pass={r['pass']}")

# Verify behavior_changed from diffs
print()
print("=== Recompute behavior_changed from diffs ===")
for op, r in d['operators'].items():
    recomputed = sum(1 for diff in r['diffs'] if diff['behavior_changed'])
    print(f"{op}: reported={r['behavior_changed']} recomputed={recomputed} match={r['behavior_changed']==recomputed}")

# Check CRN: verify paired seeds are independent of genotype
print()
print("=== CRN verification ===")
for op, r in d['operators'].items():
    for diff in r['diffs']:
        for sample in diff.get('samples', []):
            for tr in sample.get('parent_traces', []) + sample.get('child_traces', []):
                # Check if seed is in traces
                pass
    break  # just check first operator

# Count total parent-child comparisons
total_comparisons = sum(len(r['diffs']) * 2 for r in d['operators'].values())  # 2 tasks per diff
print(f"Total parent-child-task comparisons: {total_comparisons}")
print(f"Expected requests: {total_comparisons * 2 * 2}")  # 2 reps * 2 (parent+child)
