"""R3 Independent Recomputation — Phase 2: Performance metrics from paired_rows."""
import json

BASE = "research/runs/20261029T052350Z_R3"
with open(f"{BASE}/R3_RAW.json") as f:
    raw = json.load(f)

pilot = raw["pilot"]

for op_name in ["tool_subset_edit", "crossover"]:
    agg = pilot["aggregate"][op_name]
    rows = agg["paired_rows"]
    n = len(rows)

    # Independent recomputation from raw paired rows
    parent_correct = sum(1 for r in rows if r["parent_answer_correct"])
    child_correct = sum(1 for r in rows if r["child_answer_correct"])
    parent_path = sum(1 for r in rows if r["parent_tool_path_valid"])
    child_path = sum(1 for r in rows if r["child_tool_path_valid"])
    parent_format_ok = sum(1 for r in rows if r["parent_format_compliant"])
    child_format_ok = sum(1 for r in rows if r["child_format_compliant"])
    parent_hard = sum(1 for r in rows if r["parent_hard_validity"])
    child_hard = sum(1 for r in rows if r["child_hard_validity"])
    parent_eff = sum(1 for r in rows if r["parent_effective_success"])
    child_eff = sum(1 for r in rows if r["child_effective_success"])
    parent_format_fail = n - parent_format_ok
    child_format_fail = n - child_format_ok
    beh_changed = sum(1 for r in rows if r["behavior_changed"])
    invalid = sum(1 for r in rows if not r["operator_valid"])
    deltas = [r["paired_correctness_delta"] for r in rows]

    print(f"=== {op_name} (n={n}) ===")
    print(f"  answer_correct:     parent={parent_correct}/{n} ({parent_correct/n:.3f})  child={child_correct}/{n} ({child_correct/n:.3f})")
    print(f"  tool_path_valid:    parent={parent_path}/{n} ({parent_path/n:.3f})  child={child_path}/{n} ({child_path/n:.3f})")
    print(f"  format_compliant:   parent={parent_format_ok}/{n} ({parent_format_ok/n:.3f})  child={child_format_ok}/{n} ({child_format_ok/n:.3f})")
    print(f"  hard_validity:      parent={parent_hard}/{n} ({parent_hard/n:.3f})  child={child_hard}/{n} ({child_hard/n:.3f})")
    print(f"  effective_success:  parent={parent_eff}/{n} ({parent_eff/n:.3f})  child={child_eff}/{n} ({child_eff/n:.3f})")
    print(f"  format_failures:    parent={parent_format_fail}  child={child_format_fail}")
    print(f"  behavior_changed:   {beh_changed}/{n} (diagnostic only)")
    print(f"  invalid_operators:  {invalid}/{n}")
    print(f"  paired_delta_mean:  {sum(deltas)/n:.3f}")
    print(f"  delta distribution: {deltas}")

    # Paired outcome table
    improved = sum(1 for r in rows if r["paired_correctness_delta"] > 0)
    degraded = sum(1 for r in rows if r["paired_correctness_delta"] < 0)
    same = sum(1 for r in rows if r["paired_correctness_delta"] == 0)
    print(f"  paired outcomes:    improved={improved}  degraded={degraded}  same={same}")

    # Full binary table
    print(f"  binary table (parent_correct, child_correct, delta):")
    for r in rows:
        p = int(r["parent_answer_correct"])
        c = int(r["child_answer_correct"])
        d = r["paired_correctness_delta"]
        path_c = "P" if r["child_tool_path_valid"] else "X"
        fmt_c = "F" if r["child_format_compliant"] else "!"
        print(f"    {r['task_id']}/{r['seed_id']}: parent={p} child={c} delta={d:+d} child_path={path_c} child_fmt={fmt_c}")
    print()

# Cross-check against reported aggregates
print("=== Cross-check against reported aggregates ===")
for op_name in ["tool_subset_edit", "crossover"]:
    agg = pilot["aggregate"][op_name]
    rows = agg["paired_rows"]
    n = len(rows)
    checks = [
        ("parent_answer_correct_rate", sum(1 for r in rows if r["parent_answer_correct"]) / n),
        ("child_answer_correct_rate", sum(1 for r in rows if r["child_answer_correct"]) / n),
        ("parent_tool_path_rate", sum(1 for r in rows if r["parent_tool_path_valid"]) / n),
        ("child_tool_path_rate", sum(1 for r in rows if r["child_tool_path_valid"]) / n),
        ("parent_hard_validity_rate", sum(1 for r in rows if r["parent_hard_validity"]) / n),
        ("child_hard_validity_rate", sum(1 for r in rows if r["child_hard_validity"]) / n),
        ("parent_effective_success_rate", sum(1 for r in rows if r["parent_effective_success"]) / n),
        ("child_effective_success_rate", sum(1 for r in rows if r["child_effective_success"]) / n),
    ]
    all_match = True
    for key, recomputed in checks:
        reported = agg[key]
        match = abs(recomputed - reported) < 1e-9
        if not match:
            print(f"  MISMATCH {op_name}.{key}: recomputed={recomputed} reported={reported}")
            all_match = False
    print(f"{op_name}: all metrics match = {all_match}")
