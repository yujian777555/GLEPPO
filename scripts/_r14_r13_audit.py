"""R14 Phase 1: R13 audit."""
import json

BASE = "research/runs/20261029T120036Z_R13"
with open(f"{BASE}/R13_RAW.json") as f:
    raw = json.load(f)

print(f"R13 Run ID: {raw['run_id']}")
print(f"Units: {raw['units_completed']}/{raw['total_units']}")
print(f"Generations: {raw['total_actual_generations']}/{raw['max_generations']}")
print(f"Status: {raw['status']}")

units = raw["units"]
print(f"\n=== R13 Per-Task ===")
for tid in sorted(set(u["task_id"] for u in units)):
    for arm in ["C0", "C1", "C2"]:
        arm_t = [u for u in units if u["task_id"] == tid and u["arm"] == arm]
        if not arm_t:
            continue
        n = len(arm_t)
        eff = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["effective_success"])
        fmt = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["format_compliant"])
        print(f"  {tid}/{arm}: eff={eff}/{n} fmt={fmt}/{n}")

# Check C2 decisions
c2_units = [u for u in units if u["arm"] == "C2" and u.get("c2_decision")]
use_c1 = sum(1 for u in c2_units if u["c2_decision"]["action"] == "use_C1")
print(f"\nC2 interventions: {use_c1}/{len(c2_units)}")
print(f"Missing units: {raw['total_units'] - raw['units_completed']}")
print(f"\nR12 erratum documented: R12_STATISTICAL_ERRATUM.md")
print(f"R13 verdict: INCONCLUSIVE (C2 never triggered)")
