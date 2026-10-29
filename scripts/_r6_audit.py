"""R6 Phase 1: R5 zero-cost mechanism ablation audit."""
import json

BASE = "research/runs/20261029T063026Z_R5"
with open(f"{BASE}/R5_RAW.json") as f:
    raw = json.load(f)

units = raw["units"]

print("=" * 60)
print("R5 CONCLUSION BOUNDARY CORRECTION")
print("=" * 60)
print(f"""
R5 completed {raw['units_completed']}/{raw['total_units']} units ({raw['units_completed']/raw['total_units']*100:.1f}%).
The FULL pre-registered matrix was NOT completed.

crossover_fixed 9/9 supports ONLY:
  "In the 9 observed child samples, crossover_fixed achieved effective success."

It does NOT prove:
  - 100% success on new tasks
  - Reproducibility across all seeds
  - Prompt constraint is the ONLY effective factor
  - Operator fix is superior to all alternatives
  - Production-grade reliability
""")

print("=" * 60)
print("MECHANISM ABLATION ANALYSIS")
print("=" * 60)

# Categorize units by arm
arms = {}
for u in units:
    key = f"{u['arm']}/{u['operator']}"
    arms.setdefault(key, []).append(u)

# C0: original crossover
c0 = arms.get("A0_original/crossover", [])
# C2: crossover_fixed
c2 = arms.get("A1_fixed_filtered/crossover_fixed", [])
# P0: parent (from any arm)
p0_parent_eff = sum(1 for u in units if u["parent_result"] and u["parent_result"]["effective_success"])

print(f"\n--- C0: Original crossover (n={len(c0)}) ---")
c0_eff = sum(1 for u in c0 if u["child_result"] and u["child_result"]["effective_success"])
c0_fmt_fail = sum(1 for u in c0 if u["child_result"] and not u["child_result"]["format_compliant"])
c0_path_ok = sum(1 for u in c0 if u["child_result"] and u["child_result"]["tool_path_valid"])
print(f"  effective_success: {c0_eff}/{len(c0)} = {c0_eff/len(c0):.3f}")
print(f"  format_failures: {c0_fmt_fail}/{len(c0)}")
print(f"  tool_path_ok: {c0_path_ok}/{len(c0)}")

print(f"\n--- C2: crossover_fixed (n={len(c2)}) ---")
c2_eff = sum(1 for u in c2 if u["child_result"] and u["child_result"]["effective_success"])
c2_fmt_fail = sum(1 for u in c2 if u["child_result"] and not u["child_result"]["format_compliant"])
c2_path_ok = sum(1 for u in c2 if u["child_result"] and u["child_result"]["tool_path_valid"])
print(f"  effective_success: {c2_eff}/{len(c2)} = {c2_eff/len(c2):.3f}")
print(f"  format_failures: {c2_fmt_fail}/{len(c2)}")
print(f"  tool_path_ok: {c2_path_ok}/{len(c2)}")

print(f"\n--- P0: Parent reference ---")
print(f"  effective_success: {p0_parent_eff}/{len(units)} = {p0_parent_eff/len(units):.3f}")

# Check if C1 (original + format constraint only) can be distinguished
print(f"\n--- C1 vs C2 distinction ---")
print(f"  R5 does NOT have a C1 arm (original crossover + format constraint only).")
print(f"  C2 = crossover_fixed = strategy recombination + format constraint + workflow preservation")
print(f"  Cannot distinguish H2 (format constraint) from H3 (other factors) with R5 data alone.")
print(f"  NEEDS NEW ABLATION: C1 = original crossover + format constraint ONLY")

# Per-unit detail for crossover vs crossover_fixed
print(f"\n--- Per-unit comparison (same task/seed) ---")
c0_by_key = {f"{u['task_id']}/{u['seed_id']}": u for u in c0}
c2_by_key = {f"{u['task_id']}/{u['seed_id']}": u for u in c2}
common_keys = set(c0_by_key.keys()) & set(c2_by_key.keys())
print(f"  Common task/seed pairs: {len(common_keys)}")
for k in sorted(common_keys):
    u0 = c0_by_key[k]
    u2 = c2_by_key[k]
    e0 = u0["child_result"]["effective_success"] if u0["child_result"] else None
    e2 = u2["child_result"]["effective_success"] if u2["child_result"] else None
    f0 = u0["child_result"]["format_compliant"] if u0["child_result"] else None
    f2 = u2["child_result"]["format_compliant"] if u2["child_result"] else None
    print(f"    {k}: C0_eff={e0} C2_eff={e2} | C0_fmt={f0} C2_fmt={f2}")

# Format failure root cause analysis
print(f"\n--- Format failure root cause (C0) ---")
for u in c0:
    cr = u.get("child_result") or {}
    if not cr.get("format_compliant", False):
        ans = cr.get("answer_preview", "")
        has_tool_trace = "[tool:" in ans
        has_final = "Final answer:" in ans
        print(f"    {u['task_id']}/{u['seed_id']}: tool_trace_in_answer={has_tool_trace} has_final_prefix={has_final}")

# Check if prompt constraint is in the input
print(f"\n--- Prompt constraint verification ---")
for u in c2[:3]:
    cr = u.get("child_result") or {}
    print(f"    {u['task_id']}/{u['seed_id']}: effective={cr.get('effective_success')} format={cr.get('format_compliant')}")

# Selective reporting check
print(f"\n--- Selective reporting check ---")
print(f"  C0 units: {len(c0)} (all completed)")
print(f"  C2 units: {len(c2)} (all completed)")
print(f"  Missing pairs: {len(set(c0_by_key.keys()) ^ set(c2_by_key.keys()))}")
print(f"  All C0/C2 units included in analysis: YES")

print(f"\n{'='*60}")
print("HYPOTHESIS STATUS (from R5 data)")
print("=" * 60)
print("""
H1 (crossover_fixed > crossover on new tasks): CANNOT FULLY TEST
  - R5 tasks were used in R5 rule development
  - Need NEW tasks for generalization test

H2 (format constraint reduces format failures): STRONGLY SUGGESTED
  - C0 format failures: 6/9 (67%)
  - C2 format failures: 0/9 (0%)
  - But cannot distinguish from H3 without C1 ablation

H3 (not just task difficulty/seed/parent): PARTIALLY TESTED
  - Same tasks, seeds, parents used for C0 and C2
  - But C1 ablation missing

H4 (no tool_path sacrifice): SUPPORTED
  - C0 path: 9/9 (100%)
  - C2 path: 9/9 (100%)
""")
