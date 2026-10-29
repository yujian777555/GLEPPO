"""R13 Phase 2: C2 mechanism re-evaluation + R13 experiment design."""
import json

BASE = "research/runs/20261029T113122Z_R12"
with open(f"{BASE}/R12_RAW.json") as f:
    raw = json.load(f)

units = raw["units"]

print("=== C2 Mechanism Re-evaluation ===")
print()
print("Proposition 1: Validation format status correlates with final format status")
print("  Evidence: Recall=100% (catches all failures), NPV=100% (never wrong when OK)")
print("  BUT: Precision=33.3% (many false alarms), Specificity=42.9%")
print("  Verdict: PARTIALLY SUPPORTED (good recall, poor precision)")
print()
print("Proposition 2: C1 format constraint reduces format failures on format-failure tasks")
print("  Evidence from R12:")
for tid in sorted(set(u["task_id"] for u in units)):
    c0 = [u for u in units if u["task_id"] == tid and u["arm"] == "C0"]
    c1 = [u for u in units if u["task_id"] == tid and u["arm"] == "C1"]
    if c0 and c1:
        c0_fmt = sum(1 for u in c0 if u["child_result"] and u["child_result"]["format_compliant"])
        c1_fmt = sum(1 for u in c1 if u["child_result"] and u["child_result"]["format_compliant"])
        print(f"  {tid}: C0 fmt={c0_fmt}/{len(c0)}, C1 fmt={c1_fmt}/{len(c1)}")
print("  Verdict: SUPPORTED on B2-001 (C0=0/3 -> C1=3/3)")
print()
print("Proposition 3: C2 selective intervention improves effective_success on new tasks")
print("  Evidence from R12:")
fs_c0 = sum(1 for u in units if u["group"]=="FS" and u["arm"]=="C0" and u["child_result"] and u["child_result"]["effective_success"])
fs_c1 = sum(1 for u in units if u["group"]=="FS" and u["arm"]=="C1" and u["child_result"] and u["child_result"]["effective_success"])
fs_c2 = sum(1 for u in units if u["group"]=="FS" and u["arm"]=="C2" and u["child_result"] and u["child_result"]["effective_success"])
print(f"  FS: C0={fs_c0}/9, C1={fs_c1}/9, C2={fs_c2}/9")
print(f"  Verdict: {'SUPPORTED' if fs_c2 > fs_c0 else 'NOT SUPPORTED'} (C2={fs_c2} vs C0={fs_c0})")

print()
print("=== C2 Intervention Analysis ===")
c2_units = [u for u in units if u["arm"] == "C2" and u.get("c2_decision")]
use_c1 = sum(1 for u in c2_units if u["c2_decision"]["action"] == "use_C1")
unnecessary = sum(1 for u in c2_units
                  if u["c2_decision"]["action"] == "use_C1"
                  and u["c2_decision"].get("val_fmt") == False
                  and u.get("child_result") and u["child_result"].get("format_compliant"))
print(f"Total C2 decisions: {len(c2_units)}")
print(f"use_C1 (intervention): {use_c1}")
print(f"use_C0 (no intervention): {len(c2_units) - use_c1}")
print(f"Unnecessary interventions (val FAIL but final OK): {unnecessary}")

print()
print("=== Uncertainty (n=9) ===")
print("Sample size is VERY SMALL. All conclusions have wide uncertainty.")
print("Cannot claim general predictive capability from 9 observations.")
