"""R16 Phase 3: M0-M3 candidate intervention signal comparison (offline)."""
import json
from pathlib import Path

print("=== M0-M3 Candidate Signal Comparison ===")
print()
print("M0: Existing C2 validation mechanism")
print("  - Run C0 child on validation seed, check format")
print("  - Limitation: different seed -> different output (root cause C)")
print()
print("M1: Deterministic format check on validation output")
print("  - Check 'Final answer:' prefix present")
print("  - Check no tool output before prefix")
print("  - Check non-empty answer after prefix")
print("  - Check answer <= 100 chars")
print("  - This is what M0 already does — same limitation")
print()
print("M2: Structural risk signal")
print("  - Check if workflow has str_ops step (format-sensitive)")
print("  - Check if task requires FORMAT in prompt")
print("  - Check if genotype has format constraint in prompt")
print("  - Can be computed BEFORE execution")
print()
print("M3: Combined signal")
print("  - M1 (post-validation) + M2 (pre-execution)")
print("  - If M2 says risky AND M1 says OK -> still intervene (catch FN)")

print()
print("=== Offline Evaluation on Historical Data ===")
print()

# Load all historical validation signals
runs = [
    ("R12", "research/runs/20261029T113122Z_R12/R12_RAW.json"),
    ("R14", "research/runs/20261029T121958Z_R14/R14_RAW.json"),
    ("R15", "research/runs/20261029T123113Z_R15/R15_RAW.json"),
]

all_signals = []
for name, path in runs:
    if not Path(path).exists():
        continue
    with open(path) as f:
        raw = json.load(f)
    for s in raw.get("trigger_diagnostic", []):
        all_signals.append({"round": name, **s})

# M0 evaluation (existing C2)
print("M0 (existing C2):")
tp = sum(1 for s in all_signals if s["val_fmt"] == False and s["final_fmt"] == False)
fp = sum(1 for s in all_signals if s["val_fmt"] == False and s["final_fmt"] == True)
fn = sum(1 for s in all_signals if s["val_fmt"] == True and s["final_fmt"] == False)
tn = sum(1 for s in all_signals if s["val_fmt"] == True and s["final_fmt"] == True)
print(f"  TP={tp} FP={fp} FN={fn} TN={tn}")
print(f"  Recall={tp}/{tp+fn} = {tp/(tp+fn) if (tp+fn)>0 else 0:.1%}")
print(f"  Precision={tp}/{tp+fp} = {tp/(tp+fp) if (tp+fp)>0 else 0:.1%}")

print()
print("M1 (deterministic format check):")
print("  Same as M0 — checks format on validation output")
print("  Limitation: validation output != final output (different seeds)")
print(f"  FN={fn} — validation says OK but final fails")
print(f"  Root cause: seed-dependent generation variance")

print()
print("M2 (structural risk signal):")
print("  Would flag format-sensitive tasks (str_ops in workflow)")
print("  B2-050 has str_ops -> M2 would flag as risky -> intervene")
print("  This catches FN=2 from R15!")
print("  But: M2 flags ALL format-sensitive tasks, including ones that don't fail")
print("  -> High FP rate on tasks like B2-049 (format OK but str_ops present)")

print()
print("M3 (combined):")
print("  Rule: intervene if M2 risky OR M1 says format fails")
print("  This catches FN=2 (M2 catches them)")
print("  But increases interventions on non-failing format-sensitive tasks")

print()
print("=== Recommendation ===")
print("M2 structural signal can catch B2-050-type misses.")
print("But requires defining 'format-sensitive task' without gold.")
print("Proposed rule: task has str_ops in required_tools -> risky -> intervene")
print()
print("This is PRE-EXECUTION (structural), not post-execution.")
print("No gold needed. No final answer needed.")
