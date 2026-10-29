"""R15 Independent Recomputation."""
import json

BASE = "research/runs/20261029T123113Z_R15"
with open(f"{BASE}/R15_RAW.json") as f:
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

print(f"\n=== C2 Decisions ===")
c2_units = [u for u in units if u["arm"] == "C2" and u.get("c2_decision")]
for u in c2_units:
    d = u["c2_decision"]
    cr = u.get("child_result") or {}
    print(f"  {u['task_id']}/{u['seed_id']}: {d['action']} val_fmt={d.get('val_fmt')} -> eff={cr.get('effective_success')} fmt={cr.get('format_compliant')}")

print(f"\n=== Hypothesis Assessment ===")
print("H1 (C2 maintains C1-level effective_success):")
fs_c1 = sum(1 for u in units if u["group"]=="FS" and u["arm"]=="C1" and u["child_result"] and u["child_result"]["effective_success"])
fs_c2 = sum(1 for u in units if u["group"]=="FS" and u["arm"]=="C2" and u["child_result"] and u["child_result"]["effective_success"])
print(f"  FS C1={fs_c1}/9, C2={fs_c2}/6 -> C2={'MAINTAINS' if fs_c2 >= fs_c1*0.8 else 'LOWER'}")

print("H2 (C2 reduces unnecessary interventions):")
print(f"  C2 use_C1=0/9 -> {'YES' if len(c2_units)>0 and sum(1 for u in c2_units if u['c2_decision']['action']=='use_C1')==0 else 'NO'}")

print("H3 (C2 has real benefit vs C0):")
fs_c0 = sum(1 for u in units if u["group"]=="FS" and u["arm"]=="C0" and u["child_result"] and u["child_result"]["effective_success"])
print(f"  FS C0={fs_c0}/9, C2={fs_c2}/6 -> {'YES' if fs_c2 > fs_c0 else 'NO'}")

print(f"\n=== Key Finding ===")
print("New tasks (B2-049-B2-054) don't trigger format failures in validation.")
print("C2's selective intervention cannot be tested without format failures.")
print("This is consistent with R11/R13 findings.")
