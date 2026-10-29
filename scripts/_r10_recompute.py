"""R10 Independent Recomputation."""
import json

BASE = "research/runs/20261029T110437Z_R10"
with open(f"{BASE}/R10_RAW.json") as f:
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

print(f"\n=== Group Aggregates ===")
for g in ["FS", "FI", "NC"]:
    for a in ["C0", "C1", "C2"]:
        gu = [u for u in units if u["group"] == g and u["arm"] == a]
        n = len(gu)
        if n == 0:
            continue
        eff = sum(1 for u in gu if u["child_result"] and u["child_result"]["effective_success"])
        fmt = sum(1 for u in gu if u["child_result"] and u["child_result"]["format_compliant"])
        print(f"  {g}/{a}: eff={eff}/{n} ({eff/n:.1%}) fmt={fmt}/{n} ({fmt/n:.1%})")

print(f"\n=== C2 Decision Analysis ===")
c2_units = [u for u in units if u["arm"] == "C2" and u.get("c2_decision")]
for u in c2_units:
    d = u["c2_decision"]
    print(f"  {u['task_id']}/{u['seed_id']}: {d['action']} ({d['reason']})")

print(f"\n=== Key Questions ===")
print("1. C2 avoids harmful interventions on well-performing tasks?")
fi_c2 = [u for u in units if u["group"] == "FI" and u["arm"] == "C2"]
fi_c2_use_c0 = sum(1 for u in fi_c2 if u.get("c2_decision", {}).get("action") == "use_C0")
print(f"   FI C2 use_C0: {fi_c2_use_c0}/{len(fi_c2)}")

print("2. C2 discovers format risk in validation?")
fs_c2 = [u for u in units if u["group"] == "FS" and u["arm"] == "C2"]
fs_c2_use_c1 = sum(1 for u in fs_c2 if u.get("c2_decision", {}).get("action") == "use_C1")
print(f"   FS C2 use_C1: {fs_c2_use_c1}/{len(fs_c2)}")

print("3. Format fix -> effective success?")
fs_c2_eff = sum(1 for u in fs_c2 if u["child_result"] and u["child_result"]["effective_success"])
print(f"   FS C2 effective: {fs_c2_eff}/{len(fs_c2)}")

print("4. C2 introduces new degradation?")
for g in ["FS", "FI", "NC"]:
    for a in ["C0", "C1", "C2"]:
        gu = [u for u in units if u["group"] == g and u["arm"] == a]
        n = len(gu)
        if n == 0:
            continue
        eff = sum(1 for u in gu if u["child_result"] and u["child_result"]["effective_success"])
        print(f"   {g}/{a}: {eff}/{n}")
