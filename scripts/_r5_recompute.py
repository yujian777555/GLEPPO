"""R5 Independent Recomputation."""
import json

BASE = "research/runs/20261029T063026Z_R5"
with open(f"{BASE}/R5_RAW.json") as f:
    raw = json.load(f)

print(f"Run ID: {raw['run_id']}")
print(f"Status: {raw['status']}")
print(f"Units: {raw['units_completed']}/{raw['total_units']}")
print(f"Generations: {raw['total_actual_generations']}/{raw['max_generations']}")

units = raw["units"]

print(f"\n=== Arm Aggregates (Independent) ===")
arms = {}
for u in units:
    key = f"{u['arm']}/{u['operator']}"
    if key not in arms:
        arms[key] = []
    arms[key].append(u)

for key in sorted(arms.keys()):
    arm_units = arms[key]
    n = len(arm_units)
    parent_eff = sum(1 for u in arm_units if u["parent_result"] and u["parent_result"]["effective_success"])
    child_eff = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["effective_success"])
    improved = sum(1 for u in arm_units if u["child_result"] and u["parent_result"]
                   and u["child_result"]["effective_success"] and not u["parent_result"]["effective_success"])
    degraded = sum(1 for u in arm_units if u["child_result"] and u["parent_result"]
                   and not u["child_result"]["effective_success"] and u["parent_result"]["effective_success"])
    path_ok = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["tool_path_valid"])
    fmt_ok = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["format_compliant"])
    answer_ok = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["answer_correct"])
    
    print(f"\n  {key} (n={n}):")
    print(f"    parent_eff: {parent_eff}/{n} = {parent_eff/n:.3f}")
    print(f"    child_eff:  {child_eff}/{n} = {child_eff/n:.3f}")
    print(f"    improved={improved} degraded={degraded} same={n-improved-degraded}")
    print(f"    child_answer: {answer_ok}/{n} = {answer_ok/n:.3f}")
    print(f"    child_path:   {path_ok}/{n} = {path_ok/n:.3f}")
    print(f"    child_fmt:    {fmt_ok}/{n} = {fmt_ok/n:.3f}")

# Cross-check with reported
print(f"\n=== Cross-check ===")
for key, agg in raw["arm_aggregates"].items():
    print(f"  {key}: reported_child={agg['child_effective_success']}/{agg['n']}")

# Selection mechanisms
print(f"\n=== Selection Summary ===")
print(json.dumps(raw.get("selection_summary", {}), indent=2))
