"""R9 Independent Recomputation and Statistical Analysis."""
import json
from math import comb

BASE = "research/runs/20261029T090140Z_R9"
with open(f"{BASE}/R9_RAW.json") as f:
    raw = json.load(f)

print(f"Run ID: {raw['run_id']}")
print(f"Status: {raw['status']}")
print(f"Units: {raw['units_completed']}/{raw['total_units']}")
print(f"Generations: {raw['total_actual_generations']}/{raw['max_generations']}")

units = raw["units"]

print(f"\n=== Per-Task Metrics ===")
for tid in sorted(set(u["task_id"] for u in units)):
    for arm in ["C0", "C1"]:
        arm_t = [u for u in units if u["task_id"] == tid and u["arm"] == arm]
        if not arm_t:
            continue
        n = len(arm_t)
        eff = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["effective_success"])
        fmt = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["format_compliant"])
        ans = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["answer_correct"])
        print(f"  {tid}/{arm}: eff={eff}/{n} fmt={fmt}/{n} ans={ans}/{n}")

print(f"\n=== Group Aggregates ===")
for g in ["FS", "FI"]:
    for a in ["C0", "C1"]:
        gu = [u for u in units if u["group"] == g and u["arm"] == a]
        n = len(gu)
        eff = sum(1 for u in gu if u["child_result"] and u["child_result"]["effective_success"])
        fmt = sum(1 for u in gu if u["child_result"] and u["child_result"]["format_compliant"])
        print(f"  {g}/{a}: eff={eff}/{n} ({eff/n:.1%}) fmt={fmt}/{n} ({fmt/n:.1%})")

print(f"\n=== Paired Analysis ===")
for g in ["FS", "FI"]:
    c0 = {f"{u['task_id']}/{u['seed_id']}": u for u in units if u["group"] == g and u["arm"] == "C0"}
    c1 = {f"{u['task_id']}/{u['seed_id']}": u for u in units if u["group"] == g and u["arm"] == "C1"}
    common = set(c0.keys()) & set(c1.keys())
    wins = sum(1 for k in common if c1[k]["child_result"] and c1[k]["child_result"]["effective_success"]
               and not (c0[k]["child_result"] and c0[k]["child_result"]["effective_success"]))
    losses = sum(1 for k in common if c0[k]["child_result"] and c0[k]["child_result"]["effective_success"]
                 and not (c1[k]["child_result"] and c1[k]["child_result"]["effective_success"]))
    n_disc = wins + losses
    if n_disc > 0:
        k = min(wins, losses)
        p = min(sum(comb(n_disc, i) for i in range(k + 1)) / 2**n_disc * 2, 1.0)
    else:
        p = 1.0
    print(f"  {g}: c1_wins={wins} c0_wins={losses} ties={len(common)-wins-losses} McNemar_p={p:.4f}")

print(f"\n=== Hypothesis Assessment ===")
print("H1 (format mechanism): ")
fs_c0_fmt = sum(1 for u in units if u["group"]=="FS" and u["arm"]=="C0" and u["child_result"] and u["child_result"]["format_compliant"])
fs_c1_fmt = sum(1 for u in units if u["group"]=="FS" and u["arm"]=="C1" and u["child_result"] and u["child_result"]["format_compliant"])
print(f"  FS C0 fmt: {fs_c0_fmt}/12, C1 fmt: {fs_c1_fmt}/12")
print(f"  H1 SUPPORTED: {fs_c0_fmt < fs_c1_fmt}")

print("H2 (performance conversion):")
fs_c0_eff = sum(1 for u in units if u["group"]=="FS" and u["arm"]=="C0" and u["child_result"] and u["child_result"]["effective_success"])
fs_c1_eff = sum(1 for u in units if u["group"]=="FS" and u["arm"]=="C1" and u["child_result"] and u["child_result"]["effective_success"])
print(f"  FS C0 eff: {fs_c0_eff}/12, C1 eff: {fs_c1_eff}/12")
print(f"  H2 SUPPORTED: {fs_c0_eff < fs_c1_eff}")

print("H3 (task-conditioned):")
fi_c0_eff = sum(1 for u in units if u["group"]=="FI" and u["arm"]=="C0" and u["child_result"] and u["child_result"]["effective_success"])
fi_c1_eff = sum(1 for u in units if u["group"]=="FI" and u["arm"]=="C1" and u["child_result"] and u["child_result"]["effective_success"])
print(f"  FI C0 eff: {fi_c0_eff}/6, C1 eff: {fi_c1_eff}/6")
print(f"  H3 EXPECTATION (no stable benefit in FI): C1 <= C0 + small noise")
