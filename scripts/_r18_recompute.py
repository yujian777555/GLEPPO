"""R18 Independent Recomputation."""
import json

BASE = "research/runs/20261029T132950Z_R18"
with open(f"{BASE}/R18_RAW.json") as f:
    raw = json.load(f)

print(f"Run ID: {raw['run_id']}")
print(f"Status: {raw['status']}")
print(f"Units: {raw['units_completed']}/{raw['total_units']}")
print(f"Generations: {raw['total_actual_generations']}/{raw['max_generations']}")

units = raw["units"]

print(f"\n=== Per-Task Metrics ===")
for tid in sorted(set(u["task_id"] for u in units)):
    for arm in ["C0", "C3"]:
        arm_t = [u for u in units if u["task_id"] == tid and u["arm"] == arm]
        if not arm_t:
            continue
        n = len(arm_t)
        eff = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["effective_success"])
        fmt = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["format_compliant"])
        ans = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["answer_correct"])
        print(f"  {tid}/{arm}: eff={eff}/{n} fmt={fmt}/{n} ans={ans}/{n}")

print(f"\n=== Arm Aggregates ===")
for arm in ["C0", "C3"]:
    gu = [u for u in units if u["arm"] == arm]
    n = len(gu)
    eff = sum(1 for u in gu if u["child_result"] and u["child_result"]["effective_success"])
    fmt = sum(1 for u in gu if u["child_result"] and u["child_result"]["format_compliant"])
    ans = sum(1 for u in gu if u["child_result"] and u["child_result"]["answer_correct"])
    path = sum(1 for u in gu if u["child_result"] and u["child_result"]["tool_path_valid"])
    print(f"  {arm}: eff={eff}/{n} ({eff/n:.1%}) fmt={fmt}/{n} ({fmt/n:.1%}) ans={ans}/{n} ({ans/n:.1%}) path={path}/{n}")

print(f"\n=== Paired C3 vs C0 ===")
c0_by_key = {f"{u['task_id']}/{u['seed_id']}": u for u in units if u["arm"] == "C0"}
c3_by_key = {f"{u['task_id']}/{u['seed_id']}": u for u in units if u["arm"] == "C3"}
common = set(c0_by_key.keys()) & set(c3_by_key.keys())
for k in sorted(common):
    e0 = c0_by_key[k]["child_result"]["effective_success"] if c0_by_key[k]["child_result"] else False
    e3 = c3_by_key[k]["child_result"]["effective_success"] if c3_by_key[k]["child_result"] else False
    a0 = c0_by_key[k]["child_result"]["answer_correct"] if c0_by_key[k]["child_result"] else False
    a3 = c3_by_key[k]["child_result"]["answer_correct"] if c3_by_key[k]["child_result"] else False
    print(f"  {k}: C0_eff={e0} C3_eff={e3} | C0_ans={a0} C3_ans={a3}")

print(f"\n=== Hypothesis Assessment ===")
print("C3 goal: preserve task execution while enforcing clean output")
print("Result: C3 improves format (100% vs 80%) BUT decreases answer correctness (40% vs 67%)")
print("Effective success: C0=66.7%, C3=40% -> C3 is WORSE")
print()
print("Root cause: C3 constraint still causes model to produce wrong answers")
print("The 'use exact tool result' instruction may confuse the model")
print()
print("VERDICT: NO-GO for C3")
