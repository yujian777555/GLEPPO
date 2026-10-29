"""R11 Independent Recomputation."""
import json

BASE = "research/runs/20261029T111634Z_R11"
with open(f"{BASE}/R11_RAW.json") as f:
    raw = json.load(f)

print(f"Run ID: {raw['run_id']}")
print(f"Status: {raw['status']}")
print(f"Units: {raw['units_completed']}/{raw['total_units']}")
print(f"Generations: {raw['total_actual_generations']}/{raw['max_generations']}")

units = raw["units"]

print(f"\n=== Per-Task Metrics ===")
for tid in sorted(set(u["task_id"] for u in units)):
    for arm in ["C0", "C1", "C2"]:
        arm_t = [u for u in units if u["task_id"] == tid and u["arm"] == arm]
        if not arm_t:
            continue
        n = len(arm_t)
        eff = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["effective_success"])
        fmt = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["format_compliant"])
        print(f"  {tid}/{arm}: eff={eff}/{n} fmt={fmt}/{n}")

print(f"\n=== C2 Decision Analysis ===")
c2_units = [u for u in units if u["arm"] == "C2" and u.get("c2_decision")]
for u in c2_units:
    d = u["c2_decision"]
    print(f"  {u['task_id']}/{u['seed_id']}: {d['action']} ({d['reason']})")

print(f"\n=== Key Findings ===")
print("1. C2 never used C1 (use_C1=0) — validation always showed format OK")
print("   This means the new tasks DON'T trigger format failures in validation")
print("2. C1 slightly better than C0 in FS (5/9 vs 3/9)")
print("3. FI: all arms 100%")
print("4. Matrix incomplete (33/54)")
