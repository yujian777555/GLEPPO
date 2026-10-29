"""R6 Independent Recomputation and Analysis."""
import json

BASE = "research/runs/20261029T064914Z_R6"
with open(f"{BASE}/R6_RAW.json") as f:
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

for arm_name in ["C0", "C1", "C2"]:
    arm_units = arms.get(arm_name, [])
    n = len(arm_units)
    if n == 0:
        continue
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
    t_units = [u for u in units if u["task_id"] == tid]
    for arm_name in ["C0", "C1", "C2"]:
        arm_t = [u for u in t_units if u["arm"] == arm_name]
        if not arm_t:
            continue
        n = len(arm_t)
        child_eff = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["effective_success"])
        fmt_ok = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["format_compliant"])
        print(f"  {tid}/{arm_name}: child_eff={child_eff}/{n} fmt={fmt_ok}/{n}")

# Paired C0 vs C2 comparison
print(f"\n=== Paired C0 vs C2 Comparison ===")
c0_by_key = {f"{u['task_id']}/{u['seed_id']}": u for u in units if u["arm"] == "C0"}
c2_by_key = {f"{u['task_id']}/{u['seed_id']}": u for u in units if u["arm"] == "C2"}
common = set(c0_by_key.keys()) & set(c2_by_key.keys())
c2_wins = 0
c0_wins = 0
ties = 0
for k in sorted(common):
    e0 = c0_by_key[k]["child_result"]["effective_success"] if c0_by_key[k]["child_result"] else False
    e2 = c2_by_key[k]["child_result"]["effective_success"] if c2_by_key[k]["child_result"] else False
    if e2 and not e0:
        c2_wins += 1
    elif e0 and not e2:
        c0_wins += 1
    else:
        ties += 1
    print(f"  {k}: C0={e0} C2={e2}")
print(f"\n  C2 wins: {c2_wins}, C0 wins: {c0_wins}, ties: {ties}")

# Hypothesis assessment
print(f"\n=== Hypothesis Assessment ===")
print(f"""
H1 (crossover_fixed > crossover on NEW tasks):
  C0 child_eff: 8/15 (53.3%)
  C2 child_eff: 7/15 (46.7%)
  C2 NOT better than C0 on new tasks!
  VERDICT: NOT SUPPORTED on R6 tasks

H2 (format constraint reduces format failures):
  C0 fmt: 13/15 (86.7%)
  C1 fmt: 5/5 (100%)
  C2 fmt: 15/15 (100%)
  Format constraint DOES reduce format failures
  VERDICT: SUPPORTED

H3 (not just task difficulty/seed):
  Same tasks, seeds, parents for C0 and C2
  But C2 did NOT outperform C0
  VERDICT: H1 failure cannot be explained by H3

H4 (no tool_path sacrifice):
  C0 path: 15/15 (100%)
  C2 path: 15/15 (100%)
  VERDICT: SUPPORTED
""")

# C1 analysis
print(f"=== C1 Ablation Analysis ===")
c1_units = arms.get("C1", [])
c1_eff = sum(1 for u in c1_units if u["child_result"] and u["child_result"]["effective_success"])
c1_fmt = sum(1 for u in c1_units if u["child_result"] and u["child_result"]["format_compliant"])
print(f"C1 (format only): eff={c1_eff}/{len(c1_units)} fmt={c1_fmt}/{len(c1_units)}")
print(f"C1 vs C0: format improvement {'YES' if c1_fmt/len(c1_units) > 13/15 else 'NO'}")
print(f"C1 vs C2: effective success {'SAME' if c1_eff/len(c1_units) == 7/15 else 'DIFFERENT'}")
