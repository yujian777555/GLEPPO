"""R13 Phase 1: R12 confusion matrix audit — correct labels."""
import json

BASE = "research/runs/20261029T113122Z_R12"
with open(f"{BASE}/R12_RAW.json") as f:
    raw = json.load(f)

units = raw["units"]

# Build confusion matrix with CORRECT labels
# Positive class = "final format failure" (risk)
# TP: validation predicts FAIL, final FAILS
# FP: validation predicts FAIL, final OK
# FN: validation predicts OK, final FAILS
# TN: validation predicts OK, final OK

val_signals = []
for u in units:
    if u["arm"] == "C2" and u.get("c2_decision"):
        val_fmt = u["c2_decision"].get("val_fmt")  # True=OK, False=FAILS
        final_fmt = u["child_result"]["format_compliant"] if u["child_result"] else None
        val_signals.append({
            "task": u["task_id"], "seed": u["seed_id"],
            "val_fmt": val_fmt, "final_fmt": final_fmt,
        })

print("=== R12 Confusion Matrix (positive = final format FAILURE) ===")
print(f"Total validation records: {len(val_signals)}")

# Correct labels:
# "Predicts FAIL" = validation format NOT compliant (val_fmt=False)
# "Predicts OK" = validation format compliant (val_fmt=True)
# "Final FAILS" = final format NOT compliant (final_fmt=False)
# "Final OK" = final format compliant (final_fmt=True)

tp = sum(1 for s in val_signals if s["val_fmt"] == False and s["final_fmt"] == False)  # pred FAIL, actual FAIL
fp = sum(1 for s in val_signals if s["val_fmt"] == False and s["final_fmt"] == True)   # pred FAIL, actual OK
fn = sum(1 for s in val_signals if s["val_fmt"] == True and s["final_fmt"] == False)   # pred OK, actual FAIL
tn = sum(1 for s in val_signals if s["val_fmt"] == True and s["final_fmt"] == True)    # pred OK, actual OK

print(f"\nTP (pred FAIL, actual FAIL): {tp}")
print(f"FP (pred FAIL, actual OK): {fp}")
print(f"FN (pred OK, actual FAIL): {fn}")
print(f"TN (pred OK, actual OK): {tn}")

n = tp + fp + fn + tn
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
npv = tn / (tn + fn) if (tn + fn) > 0 else 0
accuracy = (tp + tn) / n if n > 0 else 0

print(f"\n=== Derived Metrics (positive = format FAILURE) ===")
print(f"Precision = TP/(TP+FP) = {tp}/{tp+fp} = {precision:.1%}")
print(f"Recall = TP/(TP+FN) = {tp}/{tp+fn} = {recall:.1%}")
print(f"Specificity = TN/(TN+FP) = {tn}/{tn+fp} = {specificity:.1%}")
print(f"NPV = TN/(TN+FN) = {tn}/{tn+fn} = {npv:.1%}")
print(f"Accuracy = (TP+TN)/N = {tp+tn}/{n} = {accuracy:.1%}")

# Expected from instruction: Precision=33.3%, Recall=100%, Specificity=42.9%, NPV=100%, Accuracy=55.6%
print(f"\n=== Compare with Expected ===")
print(f"Precision: computed={precision:.1%} expected=33.3% -> {'MATCH' if abs(precision-0.333)<0.01 else 'MISMATCH'}")
print(f"Recall: computed={recall:.1%} expected=100% -> {'MATCH' if abs(recall-1.0)<0.01 else 'MISMATCH'}")
print(f"Specificity: computed={specificity:.1%} expected=42.9% -> {'MATCH' if abs(specificity-0.429)<0.01 else 'MISMATCH'}")
print(f"NPV: computed={npv:.1%} expected=100% -> {'MATCH' if abs(npv-1.0)<0.01 else 'MISMATCH'}")
print(f"Accuracy: computed={accuracy:.1%} expected=55.6% -> {'MATCH' if abs(accuracy-0.556)<0.01 else 'MISMATCH'}")

# Show individual records
print(f"\n=== Individual Records ===")
for s in val_signals:
    print(f"  {s['task']}/{s['seed']}: val_fmt={s['val_fmt']} final_fmt={s['final_fmt']}")
