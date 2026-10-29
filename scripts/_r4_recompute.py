"""R4 Independent Recomputation from raw data."""
import json

BASE = "research/runs/20261029T060743Z_R4"
with open(f"{BASE}/R4_RAW.json") as f:
    raw = json.load(f)

print(f"Run ID: {raw['run_id']}")
print(f"Status: {raw['status']}")
print(f"Units: {raw['units_completed']}/{raw['total_units']}")
print(f"Generations: {raw['total_actual_generations']}/{raw['max_generations']}")
print(f"Wall: {raw['total_wall_s']}s")
print(f"Budget exhausted: {raw['budget_exhausted']}")

# Independent recomputation from units
units = raw["units"]
n = len(units)

parent_eff = sum(1 for u in units if u["parent_result"] and u["parent_result"]["effective_success"])
child_eff = sum(1 for u in units if u["child_result"] and u["child_result"]["effective_success"])
print(f"\n=== Independent Recomputation (n={n}) ===")
print(f"Parent effective_success: {parent_eff}/{n} = {parent_eff/n:.3f}")
print(f"Child  effective_success: {child_eff}/{n} = {child_eff/n:.3f}")

# Paired outcomes
improved = sum(1 for u in units if u["child_result"] and u["parent_result"]
               and u["child_result"]["effective_success"] and not u["parent_result"]["effective_success"])
degraded = sum(1 for u in units if u["child_result"] and u["parent_result"]
               and not u["child_result"]["effective_success"] and u["parent_result"]["effective_success"])
same = sum(1 for u in units if u["child_result"] and u["parent_result"]
           and u["child_result"]["effective_success"] == u["parent_result"]["effective_success"])
print(f"Paired: improved={improved} degraded={degraded} same={same}")

# Per-operator breakdown
print(f"\n=== Per-Operator ===")
for op in ["tool_subset_edit", "crossover"]:
    op_units = [u for u in units if u["operator"] == op]
    op_n = len(op_units)
    op_parent_eff = sum(1 for u in op_units if u["parent_result"] and u["parent_result"]["effective_success"])
    op_child_eff = sum(1 for u in op_units if u["child_result"] and u["child_result"]["effective_success"])
    op_deg = sum(1 for u in op_units if u["child_result"] and u["parent_result"]
                 and not u["child_result"]["effective_success"] and u["parent_result"]["effective_success"])
    print(f"  {op}: n={op_n} parent={op_parent_eff}/{op_n} child={op_child_eff}/{op_n} degraded={op_deg}")

# Per-task breakdown
print(f"\n=== Per-Task ===")
for tid in sorted(set(u["task_id"] for u in units)):
    t_units = [u for u in units if u["task_id"] == tid]
    t_n = len(t_units)
    t_parent_eff = sum(1 for u in t_units if u["parent_result"] and u["parent_result"]["effective_success"])
    t_child_eff = sum(1 for u in t_units if u["child_result"] and u["child_result"]["effective_success"])
    print(f"  {tid}: n={t_n} parent={t_parent_eff}/{t_n} child={t_child_eff}/{t_n}")

# Selection mechanisms
print(f"\n=== Selection Mechanisms ===")
for mech, r in raw["selection_results"].items():
    print(f"  {mech}:")
    print(f"    accepted={r['accepted']}/{r['total_candidates']} ({r['acceptance_rate']:.3f})")
    print(f"    harmful_accepted={r['harmful_accepted']}")
    print(f"    harmful_rate={r['harmful_rate']:.3f}")
    print(f"    effective_success_among_accepted={r['effective_success_among_accepted']}")

# S1 static filter analysis
print(f"\n=== S1 Static Filter Analysis ===")
s1_pass = sum(1 for u in units if u.get("s1_static_pass", False))
s1_fail = n - s1_pass
print(f"S1 pass: {s1_pass}/{n}  S1 fail: {s1_fail}/{n}")

# Among S1-pass, what's harmful rate?
s1_pass_units = [u for u in units if u.get("s1_static_pass", False)]
s1_harmful = sum(1 for u in s1_pass_units if u["child_result"] and not u["child_result"]["effective_success"])
print(f"Among S1-pass: harmful={s1_harmful}/{len(s1_pass_units)}")

# Cross-check
print(f"\n=== Cross-check ===")
print(f"Reported parent rate: {raw['parent_effective_success_rate']:.3f}")
print(f"Recomputed parent rate: {parent_eff/n:.3f}")
print(f"Match: {abs(raw['parent_effective_success_rate'] - parent_eff/n) < 0.001}")
print(f"Reported child rate: {raw['child_effective_success_rate']:.3f}")
print(f"Recomputed child rate: {child_eff/n:.3f}")
print(f"Match: {abs(raw['child_effective_success_rate'] - child_eff/n) < 0.001}")
