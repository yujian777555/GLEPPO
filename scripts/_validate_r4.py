"""R4 offline validation: test selection mechanisms."""
import sys
sys.path.insert(0, ".")

from gleppo.genotype import make_task_compatible_reference, validate_genotype
from gleppo.r4_selection import static_check_s1, static_check_s2, run_selection_mechanisms

print("=== S1 Static Checks on Reference Genotypes ===")
for tid in ["B2-001", "B2-003", "B2-004", "B2-005", "B2-006"]:
    g = make_task_compatible_reference(tid)
    r = static_check_s1(g, tid)
    status = "PASS" if r["pass"] else "FAIL"
    v = r["violations"][:2] if r["violations"] else []
    print(f"  {tid}: S1={status} violations={v}")

print("\n=== S2 Static Selection (identical genotypes) ===")
for tid in ["B2-001", "B2-004"]:
    g = make_task_compatible_reference(tid)
    r = static_check_s2(g, g, tid)
    print(f"  {tid}: accepted={r['accepted']} reason={r['reason']}")

print("\n=== Full Selection Mechanisms (no execution results) ===")
for tid in ["B2-001", "B2-006"]:
    g = make_task_compatible_reference(tid)
    sel = run_selection_mechanisms(g, g, tid)
    for mech, result in sel.items():
        if mech == "S0_unfiltered":
            print(f"  {tid}/{mech}: accepted={result['accepted']}")
        elif mech == "S1_static_filter":
            print(f"  {tid}/{mech}: pass={result['pass']}")
        elif mech == "S2_static_select":
            print(f"  {tid}/{mech}: accepted={result['accepted']} reason={result['reason']}")
        elif mech == "S3_post_exec_diag":
            print(f"  {tid}/{mech}: pass={result['pass']} note={result['note']}")

print("\n=== Task Structural Distinctness ===")
contracts = {
    "B2-001": ["calc", "str_ops"],
    "B2-003": ["calc", "str_ops"],
    "B2-004": ["py_sandbox", "calc"],
    "B2-005": ["calc", "py_sandbox"],
    "B2-006": ["calc", "str_ops", "py_sandbox"],
}
for tid, tools in contracts.items():
    g = make_task_compatible_reference(tid)
    wf_tools = [s.tool for s in g.workflow if s.type == "tool"]
    match = wf_tools == tools
    print(f"  {tid}: contract={tools} workflow={wf_tools} match={match}")

print("\n=== ALL CHECKS DONE ===")
