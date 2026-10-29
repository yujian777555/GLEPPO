"""R14 Independent Recomputation + Trigger Diagnostic."""
import json

BASE = "research/runs/20261029T121958Z_R14"
with open(f"{BASE}/R14_RAW.json") as f:
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

print(f"\n=== Trigger Signal Diagnostic ===")
val_signals = raw.get("trigger_diagnostic", [])
tp = fp = tn = fn = 0
for s in val_signals:
    val_ok = s["val_fmt"]
    final_ok = s["final_fmt"]
    if val_ok and final_ok: tn += 1
    elif val_ok and not final_ok: fn += 1
    elif not val_ok and final_ok: fp += 1
    elif not val_ok and not final_ok: tp += 1

print(f"TP (pred FAIL, actual FAIL): {tp}")
print(f"FP (pred FAIL, actual OK): {fp}")
print(f"FN (pred OK, actual FAIL): {fn}")
print(f"TN (pred OK, actual OK): {tn}")
n = tp + fp + fn + tn
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
npv = tn / (tn + fn) if (tn + fn) > 0 else 0
print(f"Precision: {precision:.1%}, Recall: {recall:.1%}, Specificity: {specificity:.1%}, NPV: {npv:.1%}")

print(f"\n=== C2 Decisions ===")
c2_units = [u for u in units if u["arm"] == "C2" and u.get("c2_decision")]
for u in c2_units:
    d = u["c2_decision"]
    cr = u.get("child_result") or {}
    print(f"  {u['task_id']}/{u['seed_id']}: {d['action']} val_fmt={d.get('val_fmt')} -> eff={cr.get('effective_success')} fmt={cr.get('format_compliant')}")

print(f"\n=== Hypothesis Assessment ===")
print("H1 (historical format-sensitive reproduces):")
hist_c0_fmt = sum(1 for u in units if u["group"]=="HIST" and u["arm"]=="C0" and u["child_result"] and u["child_result"]["format_compliant"])
print(f"  HIST C0 fmt: {hist_c0_fmt}/6 = {hist_c0_fmt/6:.1%} -> {'CONFIRMED' if hist_c0_fmt < 6 else 'NOT CONFIRMED'}")

print("H2 (validation predicts format failure):")
print(f"  Precision={precision:.1%}, Recall={recall:.1%} -> {'SUPPORTED' if recall > 0.5 else 'WEAK'}")

print("H3 (C2 improves effective_success):")
hist_c0_eff = sum(1 for u in units if u["group"]=="HIST" and u["arm"]=="C0" and u["child_result"] and u["child_result"]["effective_success"])
hist_c2_eff = sum(1 for u in units if u["group"]=="HIST" and u["arm"]=="C2" and u["child_result"] and u["child_result"]["effective_success"])
print(f"  HIST C0={hist_c0_eff}/6, C2={hist_c2_eff}/6 -> {'SUPPORTED' if hist_c2_eff > hist_c0_eff else 'NOT SUPPORTED'}")
