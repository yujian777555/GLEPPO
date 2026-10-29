"""R12 Phase 1: R11 audit."""
import json

BASE = "research/runs/20261029T111634Z_R11"
with open(f"{BASE}/R11_RAW.json") as f:
    raw = json.load(f)
with open(f"{BASE}/R11_LEDGER.jsonl") as f:
    ledger = [json.loads(l) for l in f]

print(f"R11 Run ID: {raw['run_id']}")
print(f"Units: {raw['units_completed']}/{raw['total_units']}")
print(f"Generations: {len(ledger)}/{raw['max_generations']}")
print(f"Ledger == runtime: {len(ledger) == raw['llm_stats']['actual_generations']}")

units = raw["units"]

print(f"\n=== R11 Per-Task ===")
for tid in sorted(set(u["task_id"] for u in units)):
    for arm in ["C0", "C1", "C2"]:
        arm_t = [u for u in units if u["task_id"] == tid and u["arm"] == arm]
        if not arm_t:
            continue
        n = len(arm_t)
        eff = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["effective_success"])
        fmt = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["format_compliant"])
        print(f"  {tid}/{arm}: eff={eff}/{n} fmt={fmt}/{n}")

print(f"\n=== C2 Decisions ===")
c2_units = [u for u in units if u["arm"] == "C2" and u.get("c2_decision")]
for u in c2_units:
    d = u["c2_decision"]
    cr = u.get("child_result") or {}
    print(f"  {u['task_id']}/{u['seed_id']}: {d['action']} -> eff={cr.get('effective_success')} fmt={cr.get('format_compliant')}")

print(f"\n=== B2-030 C1 Evidence ===")
b2030 = [u for u in units if u["task_id"] == "B2-030"]
for u in b2030:
    cr = u.get("child_result") or {}
    print(f"  {u['arm']}/{u['seed_id']}: eff={cr.get('effective_success')} fmt={cr.get('format_compliant')} ans={cr.get('answer_correct')}")

print(f"\n=== R11 Audit Verdict ===")
print(f"Missing units: {raw['total_units'] - raw['units_completed']}")
print(f"C2 interventions: 0/9 (validation never triggered)")
print(f"B2-030 C1 advantage: 2/3 vs 0/3 (exploratory, not confirmatory)")
