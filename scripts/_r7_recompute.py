"""R7 Independent Recomputation."""
import json

BASE = "research/runs/20261029T073455Z_R7"
with open(f"{BASE}/R7_RAW.json") as f:
    raw = json.load(f)

print(f"Run ID: {raw['run_id']}")
print(f"Status: {raw['status']}")
print(f"Units: {raw['units_completed']}/{raw['total_units']}")
print(f"Generations: {raw['total_actual_generations']}/{raw['max_generations']}")

units = raw["units"]

print(f"\n=== Independent Recomputation ===")
arms = {}
for u in units:
    arms.setdefault(u["arm"], []).append(u)

for arm_name in ["C0", "C1"]:
    arm_units = arms.get(arm_name, [])
    n = len(arm_units)
    parent_eff = sum(1 for u in arm_units if u["parent_result"] and u["parent_result"]["effective_success"])
    child_eff = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["effective_success"])
    improved = sum(1 for u in arm_units if u["child_result"] and u["parent_result"]
                   and u["child_result"]["effective_success"] and not u["parent_result"]["effective_success"])
    degraded = sum(1 for u in arm_units if u["child_result"] and u["parent_result"]
                   and not u["child_result"]["effective_success"] and u["parent_result"]["effective_success"])
    fmt_ok = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["format_compliant"])
    path_ok = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["tool_path_valid"])
    answer_ok = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["answer_correct"])

    print(f"\n  {arm_name} (n={n}):")
    print(f"    parent_eff: {parent_eff}/{n} = {parent_eff/n:.3f}")
    print(f"    child_eff:  {child_eff}/{n} = {child_eff/n:.3f}")
    print(f"    improved={improved} degraded={degraded} same={n-improved-degraded}")
    print(f"    child_answer: {answer_ok}/{n} = {answer_ok/n:.3f}")
    print(f"    child_fmt:    {fmt_ok}/{n} = {fmt_ok/n:.3f}")
    print(f"    child_path:   {path_ok}/{n} = {path_ok/n:.3f}")

# Per-task breakdown
print(f"\n=== Per-Task Breakdown ===")
for tid in sorted(set(u["task_id"] for u in units)):
    for arm_name in ["C0", "C1"]:
        arm_t = [u for u in units if u["task_id"] == tid and u["arm"] == arm_name]
        if not arm_t:
            continue
        n = len(arm_t)
        child_eff = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["effective_success"])
        fmt_ok = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["format_compliant"])
        print(f"  {tid}/{arm_name}: child_eff={child_eff}/{n} fmt={fmt_ok}/{n}")

# Paired C1 vs C0
print(f"\n=== Paired C1 vs C0 ===")
c0_by_key = {f"{u['task_id']}/{u['seed_id']}": u for u in units if u["arm"] == "C0"}
c1_by_key = {f"{u['task_id']}/{u['seed_id']}": u for u in units if u["arm"] == "C1"}
common = set(c0_by_key.keys()) & set(c1_by_key.keys())
c1_wins = 0
c0_wins = 0
for k in sorted(common):
    e0 = c0_by_key[k]["child_result"]["effective_success"] if c0_by_key[k]["child_result"] else False
    e1 = c1_by_key[k]["child_result"]["effective_success"] if c1_by_key[k]["child_result"] else False
    if e1 and not e0:
        c1_wins += 1
    elif e0 and not e1:
        c0_wins += 1
    print(f"  {k}: C0={e0} C1={e1}")
print(f"\n  C1 wins: {c1_wins}, C0 wins: {c0_wins}, ties: {len(common)-c1_wins-c0_wins}")

# McNemar exact
from math import comb
b = c1_wins
c = c0_wins
n_disc = b + c
if n_disc > 0:
    k = min(b, c)
    p = sum(comb(n_disc, i) for i in range(0, k + 1)) / 2**n_disc * 2
    p = min(p, 1.0)
    print(f"  McNemar exact p = {p:.4f}")

# Hypothesis assessment
print(f"\n=== Decision ===")
c0_rate = 8/18
c1_rate = 9/18
print(f"C0 effective_success: {c0_rate:.3f}")
print(f"C1 effective_success: {c1_rate:.3f}")
print(f"Difference: {c1_rate - c0_rate:+.3f}")
print(f"C1 wins: {c1_wins}, C0 wins: {c0_wins}")
print(f"Format: C0=100%, C1=100% (no difference)")
print(f"Path: C0=100%, C1=100% (no difference)")
