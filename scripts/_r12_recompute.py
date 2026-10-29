"""R12 Independent Recomputation + Trigger Diagnostic."""
import json

BASE = "research/runs/20261029T113122Z_R12"
with open(f"{BASE}/R12_RAW.json") as f:
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

print(f"\n=== Trigger Signal Diagnostic (Part A) ===")
# Build confusion matrix: validation format -> final format
val_signals = raw.get("trigger_diagnostic", [])
tp = fp = tn = fn = 0
for s in val_signals:
    val_ok = s["val_fmt"]
    final_ok = s["final_fmt"]
    if val_ok and final_ok:
        tn += 1  # val says OK, final OK (true negative for "risk")
    elif val_ok and not final_ok:
        fp += 1  # val says OK, final FAILS (false negative for risk)
    elif not val_ok and final_ok:
        fn += 1  # val says FAIL, final OK (false positive for risk)
    elif not val_ok and not final_ok:
        tp += 1  # val says FAIL, final FAILS (true positive for risk)

print(f"  Validation OK, Final OK (TN): {tn}")
print(f"  Validation OK, Final FAILS (FN): {fp}")
print(f"  Validation FAILS, Final OK (FP): {fn}")
print(f"  Validation FAILS, Final FAILS (TP): {tp}")
if tp + fp > 0:
    precision = tp / (tp + fp)
    print(f"  Precision (val FAIL predicts final FAIL): {precision:.2%}")
if tp + fn > 0:
    recall = tp / (tp + fn)
    print(f"  Recall (val FAIL catches final FAIL): {recall:.2%}")
if tn + fp > 0:
    specificity = tn / (tn + fp)
    print(f"  Specificity (val OK predicts final OK): {specificity:.2%}")

print(f"\n=== C2 Decision Analysis ===")
c2_units = [u for u in units if u["arm"] == "C2" and u.get("c2_decision")]
for u in c2_units:
    d = u["c2_decision"]
    cr = u.get("child_result") or {}
    print(f"  {u['task_id']}/{u['seed_id']}: {d['action']} val_fmt={d.get('val_fmt')} -> eff={cr.get('effective_success')} fmt={cr.get('format_compliant')}")

print(f"\n=== Key Questions ===")
print("1. Does validation predict final format failure?")
print(f"   Answer: {'YES' if tp > 0 and fp == 0 else 'PARTIAL' if tp > 0 else 'NO'}")
print("2. Does C1 improve effective_success when format failures exist?")
fs_c0 = sum(1 for u in units if u['group']=='FS' and u['arm']=='C0' and u['child_result'] and u['child_result']['effective_success'])
fs_c1 = sum(1 for u in units if u['group']=='FS' and u['arm']=='C1' and u['child_result'] and u['child_result']['effective_success'])
print(f"   FS C0={fs_c0}/9 C1={fs_c1}/9 -> {'YES' if fs_c1 > fs_c0 else 'NO'}")
print("3. Does C2 select intervention and improve effective_success?")
fs_c2 = sum(1 for u in units if u['group']=='FS' and u['arm']=='C2' and u['child_result'] and u['child_result']['effective_success'])
print(f"   FS C2={fs_c2}/9 -> {'YES' if fs_c2 > fs_c0 else 'NO'}")
