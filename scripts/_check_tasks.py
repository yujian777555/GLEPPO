"""Check current diagnostic tasks."""
import json
for f in ['data/diagnostic_A2.jsonl', 'data/diagnostic_B2.jsonl']:
    print(f'=== {f} ===')
    with open(f) as fh:
        for line in fh:
            t = json.loads(line)
            print(f"  {t['task_id']}: gold={t['gold']} input={t['input'][:80]}")
