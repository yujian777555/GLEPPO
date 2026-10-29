"""R5 Phase 1: R4 audit and operator degradation attribution (zero-cost)."""
import json
from collections import Counter

BASE = "research/runs/20261029T060743Z_R4"
with open(f"{BASE}/R4_RAW.json") as f:
    raw = json.load(f)

units = raw["units"]

print("=" * 60)
print("R4 INCOMPLETENESS AUDIT")
print("=" * 60)

# 1. Missing units analysis
print(f"\n1. Unit completion: {raw['units_completed']}/{raw['total_units']}")
print(f"   Budget exhausted: {raw['budget_exhausted']}")
print(f"   Generations: {raw['total_actual_generations']}/{raw['max_generations']}")

# Expected units: 5 tasks x 5 seeds x 2 operators = 50
# Actual: 40 (B2-004 missing) x ... = 40, completed 37
expected_tasks = ["B2-001", "B2-003", "B2-004", "B2-005", "B2-006"]
expected_seeds = [f"r4-paired-seed-{i:03d}" for i in range(1, 6)]
expected_ops = ["tool_subset_edit", "crossover"]

# What tasks were actually loaded?
loaded_tasks = sorted(set(u["task_id"] for u in units))
print(f"\n   Loaded tasks: {loaded_tasks}")
print(f"   Missing tasks: {[t for t in expected_tasks if t not in loaded_tasks]}")

# 2. Which units are missing?
expected_unit_keys = set()
for t in expected_tasks:
    for s in expected_seeds:
        for o in expected_ops:
            expected_unit_keys.add(f"{t}/{s}/{o}")
actual_unit_keys = set(u["unit_key"] for u in units)
missing_units = expected_unit_keys - actual_unit_keys
print(f"\n   Expected units: {len(expected_unit_keys)}")
print(f"   Actual units: {len(actual_unit_keys)}")
print(f"   Missing units: {len(missing_units)}")
for mu in sorted(missing_units):
    print(f"     {mu}")

# 3. Selection mechanism denominator consistency
print(f"\n2. Selection mechanism denominators:")
for mech, r in raw["selection_results"].items():
    print(f"   {mech}: total={r['total_candidates']} accepted={r['accepted']} "
          f"harmful={r['harmful_accepted']} eff={r['effective_success_among_accepted']}")

# 4. S2 vs S1 analysis
print(f"\n3. S2 vs S1 analysis:")
s1_pass = sum(1 for u in units if u.get("s1_static_pass", False))
s2_accepted = raw["selection_results"]["S2_static_select"]["accepted"]
s1_accepted = raw["selection_results"]["S1_static_filter"]["accepted"]
print(f"   S1 pass: {s1_pass}/{len(units)}")
print(f"   S1 accepted: {s1_accepted}")
print(f"   S2 accepted: {s2_accepted}")
print(f"   S2 == S1: {s1_accepted == s2_accepted}")

# Why S2 == S1?
s2_same = 0
for u in units:
    s2 = u["selection"].get("S2_static_select", {})
    if s2.get("accepted") and s2.get("reason") == "accepted":
        sf = s2.get("static_features", {})
        if sf.get("hash_changed"):
            s2_same += 1
print(f"   S2 accepted with hash_changed: {s2_same}")
print(f"   Reason: S2 accepts iff S1 passes AND hash changed. Since operators always change hash, S2 == S1.")

print("\n" + "=" * 60)
print("OPERATOR DEGRADATION ATTRIBUTION")
print("=" * 60)

# tool_subset_edit analysis
print("\n--- tool_subset_edit (n=19) ---")
tse_units = [u for u in units if u["operator"] == "tool_subset_edit"]
path_violations = 0
tool_changes = []
for u in tse_units:
    cr = u.get("child_result") or {}
    if not cr.get("tool_path_valid", False):
        path_violations += 1
        tp = cr.get("tool_path_details", {})
        # Check what went wrong
        contract = tp.get("contract", [])
        seq = tp.get("successful_sequence", [])
        missing = tp.get("missing_or_wrong", [])
        tool_changes.append({
            "task": u["task_id"],
            "contract": [(c["tool"], c["expected_output"]) for c in contract],
            "actual": [(s["tool"], s["output"]) for s in seq],
            "missing": missing,
        })

print(f"   Tool path violations: {path_violations}/{len(tse_units)}")
print(f"   Sample violations:")
for tc in tool_changes[:3]:
    print(f"     {tc['task']}: need={tc['contract']} got={tc['actual']} missing={tc['missing']}")

# Categorize tool_subset_edit violations
print(f"\n   Violation categories:")
missing_tools = sum(1 for tc in tool_changes if tc["missing"])
wrong_order = sum(1 for tc in tool_changes if not tc["missing"] and [s[0] for s in tc["actual"]] != [c[0] for c in tc["contract"]])
wrong_output = sum(1 for tc in tool_changes if not tc["missing"] and tc["actual"] != tc["contract"])
print(f"     Missing tools: {missing_tools}")
print(f"     Wrong order: {wrong_order}")
print(f"     Wrong output: {wrong_output}")

# crossover analysis
print("\n--- crossover (n=18) ---")
co_units = [u for u in units if u["operator"] == "crossover"]
format_failures = 0
path_violations_co = 0
for u in co_units:
    cr = u.get("child_result") or {}
    if not cr.get("format_compliant", False):
        format_failures += 1
    if not cr.get("tool_path_valid", False):
        path_violations_co += 1

print(f"   Format failures: {format_failures}/{len(co_units)}")
print(f"   Tool path violations: {path_violations_co}/{len(co_units)}")

# Format failure details
print(f"\n   Format failure examples:")
for u in co_units:
    cr = u.get("child_result") or {}
    if not cr.get("format_compliant", False):
        print(f"     {u['task_id']}/{u['seed_id']}: answer={cr.get('answer_preview','')[:80]}")

# Effective success breakdown
print(f"\n--- Effective Success Breakdown ---")
for op in ["tool_subset_edit", "crossover"]:
    op_units = [u for u in units if u["operator"] == op]
    eff = sum(1 for u in op_units if u["child_result"] and u["child_result"]["effective_success"])
    answer_ok = sum(1 for u in op_units if u["child_result"] and u["child_result"]["answer_correct"])
    fmt_ok = sum(1 for u in op_units if u["child_result"] and u["child_result"]["format_compliant"])
    path_ok = sum(1 for u in op_units if u["child_result"] and u["child_result"]["tool_path_valid"])
    hard = sum(1 for u in op_units if u["child_result"] and u["child_result"]["hard_validity"])
    n = len(op_units)
    print(f"  {op}: n={n}")
    print(f"    answer_correct: {answer_ok}/{n} ({answer_ok/n:.2f})")
    print(f"    format_compliant: {fmt_ok}/{n} ({fmt_ok/n:.2f})")
    print(f"    tool_path_valid: {path_ok}/{n} ({path_ok/n:.2f})")
    print(f"    hard_validity: {hard}/{n} ({hard/n:.2f})")
    print(f"    effective_success: {eff}/{n} ({eff/n:.2f})")
