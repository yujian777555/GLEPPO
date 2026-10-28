"""Extract experiment summary from remote results."""
import json

with open('/tmp/gleppo_prod/research/G3_DIAG_V2_RAW.json') as f:
    d = json.load(f)

print('Run ID:', d['run_id'])
print('Total requests:', d['total_requests'])
print('Wall time:', d['total_wall_s'])
print('Budget exhausted:', d['budget_exhausted'])
print()

for op, r in d['operators'].items():
    print(f'{op}:')
    print(f'  valid={r["valid"]} invalid={r["invalid"]}')
    print(f'  hash_changed={r["hash_changed"]}')
    print(f'  behavior_changed={r["behavior_changed"]}')
    print(f'  threshold={r["threshold"]}')
    print(f'  pass={r["pass"]}')

print()
print('LLM stats:', d['llm_stats'])
print()
print('Ledger summary:', d['ledger_summary'])
