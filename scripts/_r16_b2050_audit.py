"""R16 Phase 1: B2-050 root cause audit."""
import json

BASE = "research/runs/20261029T123113Z_R15"
with open(f"{BASE}/R15_RAW.json") as f:
    raw = json.load(f)

units = raw["units"]

print("=== B2-050 Decision Chain Audit ===")
b2050_c2 = [u for u in units if u["task_id"] == "B2-050" and u["arm"] == "C2"]
b2050_c0 = [u for u in units if u["task_id"] == "B2-050" and u["arm"] == "C0"]

print(f"\nB2-050 C2 decisions:")
for u in b2050_c2:
    d = u.get("c2_decision", {})
    cr = u.get("child_result") or {}
    print(f"  {u['seed_id']}: val_fmt={d.get('val_fmt')} action={d.get('action')}")
    print(f"    final: fmt={cr.get('format_compliant')} eff={cr.get('effective_success')}")
    print(f"    answer_preview: {cr.get('answer_preview', '')[:100]}")

print(f"\nB2-050 C0 results:")
for u in b2050_c0:
    cr = u.get("child_result") or {}
    print(f"  {u['seed_id']}: fmt={cr.get('format_compliant')} eff={cr.get('effective_success')}")
    print(f"    answer_preview: {cr.get('answer_preview', '')[:100]}")

print(f"\n=== Root Cause Analysis ===")
print("B2-050 task: 'First transform base to uppercase using str_ops.")
print("Then compute 6*3-2 using calc. Then use py_sandbox to compute result = 16+7.")
print("Report in BASE-NUMBER format.'")
print()
print("Expected: BASE-23")
print()
print("Validation says format OK (val_fmt=True)")
print("But final output has format failures (fmt=False)")
print()
print("Hypothesis A: Format checker implementation defect")
print("Hypothesis B: Validation prompt/rules blind spot")
print("Hypothesis C: Validation vs final generation context differs")
print("Hypothesis D: Irreducible prediction error")
print("Hypothesis E: Data/metric inconsistency")

# Check if validation and final use same checker
print(f"\n=== Checker Consistency Check ===")
print("Both validation and final use same format checker:")
print("  'Final answer:' prefix + non-empty + <=100 chars")
print("  If validation passes but final fails, the DIFFERENCE is in generation, not checker")

print(f"\n=== Key Insight ===")
print("Validation runs C0 child on validation seed.")
print("Final runs C0 child on final seed.")
print("Same child, DIFFERENT seeds -> different outputs possible")
print("Root cause: C (validation vs final generation context differs)")
print("The validation seed produces compliant output, final seed produces non-compliant")
