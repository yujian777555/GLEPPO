"""R16 Phase 2: Historical confusion matrix recomputation."""
import json
from pathlib import Path

# Collect trigger diagnostic data from R12, R14, R15
runs = [
    ("R12", "research/runs/20261029T113122Z_R12/R12_RAW.json"),
    ("R14", "research/runs/20261029T121958Z_R14/R14_RAW.json"),
    ("R15", "research/runs/20261029T123113Z_R15/R15_RAW.json"),
]

print("=== Historical Confusion Matrix (positive = format FAILURE) ===")
print()

all_signals = []
for name, path in runs:
    if not Path(path).exists():
        print(f"{name}: NOT FOUND")
        continue
    with open(path) as f:
        raw = json.load(f)
    td = raw.get("trigger_diagnostic", [])
    print(f"{name}: {len(td)} validation records")
    for s in td:
        all_signals.append({"round": name, **s})
    
    # Per-round confusion matrix
    tp = sum(1 for s in td if s["val_fmt"] == False and s["final_fmt"] == False)
    fp = sum(1 for s in td if s["val_fmt"] == False and s["final_fmt"] == True)
    fn = sum(1 for s in td if s["val_fmt"] == True and s["final_fmt"] == False)
    tn = sum(1 for s in td if s["val_fmt"] == True and s["final_fmt"] == True)
    n = tp + fp + fn + tn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0
    print(f"  TP={tp} FP={fp} FN={fn} TN={tn}")
    print(f"  Precision={precision:.1%} Recall={recall:.1%} Specificity={specificity:.1%} NPV={npv:.1%}")
    print()

# Combined
print("=== Combined (all rounds) ===")
tp = sum(1 for s in all_signals if s["val_fmt"] == False and s["final_fmt"] == False)
fp = sum(1 for s in all_signals if s["val_fmt"] == False and s["final_fmt"] == True)
fn = sum(1 for s in all_signals if s["val_fmt"] == True and s["final_fmt"] == False)
tn = sum(1 for s in all_signals if s["val_fmt"] == True and s["final_fmt"] == True)
n = tp + fp + fn + tn
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
npv = tn / (tn + fn) if (tn + fn) > 0 else 0
accuracy = (tp + tn) / n if n > 0 else 0

print(f"N = {n}")
print(f"TP={tp} FP={fp} FN={fn} TN={tn}")
print(f"Precision = {tp}/{tp+fp} = {precision:.1%}")
print(f"Recall = {tp}/{tp+fn} = {recall:.1%}")
print(f"Specificity = {tn}/{tn+fp} = {specificity:.1%}")
print(f"NPV = {tn}/{tn+fn} = {npv:.1%}")
print(f"Accuracy = {tp+tn}/{n} = {accuracy:.1%}")

print(f"\n=== Task-Level Breakdown ===")
for s in all_signals:
    print(f"  {s['round']}/{s['task']}: val_fmt={s['val_fmt']} final_fmt={s['final_fmt']}")
