"""G3-DIAG-v2: create corrected diagnostic tasks with verified gold labels.

Phase 1 offline fixes:
- A2-001 gold: 21 -> 23 (arithmetic error)
- B2-001: remove phantom 75, make input/requirements/answer consistent
- B2-002: clean up wording, add tool path verification requirement
- B2-003: add tool path verification requirement
- All gold labels independently recomputed
"""
import hashlib
import json
import os
import time

# Fixed Run ID for this experiment (must match protocol/report/manifest)
RUN_ID = "20261028T130000Z"
PROTOCOL = "G3-DIAG-v2"

# Corrected A2 tasks (strategy-sensitive)
A2_TASKS = [
    {
        "task_id": "A2-001",
        "family": "A",
        "template_id": "A2-T1",
        "input": "Solve step by step: (3*7) + (12-4) - (2*3). Show each intermediate result, then give the final answer.",
        "gold": "23",
        "required_tools": ["calc"],
        "description": "Multi-step arithmetic requiring intermediate results. (3*7)=21, (12-4)=8, (2*3)=6, 21+8-6=23",
    },
    {
        "task_id": "A2-002",
        "family": "A",
        "template_id": "A2-T2",
        "input": "If x=15 and y=8, compute: first find x*y, then subtract x+y from the product. State the intermediate product before the final answer.",
        "gold": "97",
        "required_tools": ["calc"],
        "description": "Two-stage computation. x*y=120, x+y=23, 120-23=97",
    },
    {
        "task_id": "A2-003",
        "family": "A",
        "template_id": "A2-T3",
        "input": "Calculate (100-37)*2 + 5. First report the subtraction result, then the multiplication, then the final sum.",
        "gold": "131",
        "required_tools": ["calc"],
        "description": "Three-stage computation. 100-37=63, 63*2=126, 126+5=131",
    },
]

# Corrected B2 tasks (tool-dependent)
B2_TASKS = [
    {
        "task_id": "B2-001",
        "family": "B",
        "template_id": "B2-T1",
        "input": "Compute 25*3-11 using the calc tool, then transform the word 'sum' to uppercase using str_ops. Report as SUM-STRING (i.e. NUMBER-WORD).",
        "gold": "64-SUM",
        "required_tools": ["calc", "str_ops"],
        "description": "Requires calc AND str_ops. 25*3-11=64, 'sum' uppercased to 'SUM', format: 64-SUM",
    },
    {
        "task_id": "B2-002",
        "family": "B",
        "template_id": "B2-T2",
        "input": "Use py_sandbox to compute result = 14*3+7. Then use calc to compute 49-6. Report the final result.",
        "gold": "43",
        "required_tools": ["py_sandbox", "calc"],
        "description": "Requires py_sandbox AND calc. py_sandbox: 14*3+7=49, calc: 49-6=43",
    },
    {
        "task_id": "B2-003",
        "family": "B",
        "template_id": "B2-T3",
        "input": "Compute 8*8-4 using calc, then transform 'hi' to uppercase using str_ops. Report as NUMBER-STRING.",
        "gold": "60-HI",
        "required_tools": ["calc", "str_ops"],
        "description": "Requires calc AND str_ops. 8*8-4=60, 'hi' uppercased to 'HI', format: 60-HI",
    },
]


def verify_gold_labels():
    """Independently recompute all gold labels."""
    print("=== Gold Label Verification ===")
    errors = []

    # A2-001: (3*7) + (12-4) - (2*3)
    expected = (3 * 7) + (12 - 4) - (2 * 3)
    got = A2_TASKS[0]["gold"]
    status = "PASS" if got == str(expected) else "FAIL"
    if status == "FAIL":
        errors.append(f"A2-001: expected {expected}, got {got}")
    print(f"A2-001: {got} == {expected} -> {status}")

    # A2-002: x=15, y=8; x*y - (x+y) = 120 - 23 = 97
    expected = 15 * 8 - (15 + 8)
    got = A2_TASKS[1]["gold"]
    status = "PASS" if got == str(expected) else "FAIL"
    if status == "FAIL":
        errors.append(f"A2-002: expected {expected}, got {got}")
    print(f"A2-002: {got} == {expected} -> {status}")

    # A2-003: (100-37)*2 + 5 = 63*2 + 5 = 131
    expected = (100 - 37) * 2 + 5
    got = A2_TASKS[2]["gold"]
    status = "PASS" if got == str(expected) else "FAIL"
    if status == "FAIL":
        errors.append(f"A2-003: expected {expected}, got {got}")
    print(f"A2-003: {got} == {expected} -> {status}")

    # B2-001: 25*3-11 = 64; 'sum' uppercased = 'SUM'; gold = "64-SUM"
    expected_num = 25 * 3 - 11
    expected_str = "sum".upper()
    expected = f"{expected_num}-{expected_str}"
    got = B2_TASKS[0]["gold"]
    status = "PASS" if got == expected else "FAIL"
    if status == "FAIL":
        errors.append(f"B2-001: expected {expected}, got {got}")
    print(f"B2-001: {got} == {expected} -> {status}")

    # B2-002: py_sandbox: 14*3+7 = 49; calc: 49-6 = 43
    intermediate = 14 * 3 + 7
    expected = intermediate - 6
    got = B2_TASKS[1]["gold"]
    status = "PASS" if got == str(expected) else "FAIL"
    if status == "FAIL":
        errors.append(f"B2-002: expected {expected}, got {got}")
    print(f"B2-002: {got} == {expected} -> {status}")

    # B2-003: 8*8-4 = 60; 'hi' uppercased = 'HI'; gold = "60-HI"
    expected_num = 8 * 8 - 4
    expected_str = "hi".upper()
    expected = f"{expected_num}-{expected_str}"
    got = B2_TASKS[2]["gold"]
    status = "PASS" if got == expected else "FAIL"
    if status == "FAIL":
        errors.append(f"B2-003: expected {expected}, got {got}")
    print(f"B2-003: {got} == {expected} -> {status}")

    return errors


def verify_required_tools():
    """Check that required_tools match task requirements."""
    print("\n=== Required Tools Verification ===")
    errors = []

    # A2 tasks require only calc
    for t in A2_TASKS:
        if t["required_tools"] != ["calc"]:
            errors.append(f"{t['task_id']}: expected ['calc'], got {t['required_tools']}")
            print(f"{t['task_id']}: FAIL - {t['required_tools']}")
        else:
            print(f"{t['task_id']}: PASS - {t['required_tools']}")

    # B2-001: calc + str_ops
    if B2_TASKS[0]["required_tools"] != ["calc", "str_ops"]:
        errors.append(f"B2-001: expected ['calc', 'str_ops'], got {B2_TASKS[0]['required_tools']}")
        print(f"B2-001: FAIL - {B2_TASKS[0]['required_tools']}")
    else:
        print(f"B2-001: PASS - {B2_TASKS[0]['required_tools']}")

    # B2-002: py_sandbox + calc
    if B2_TASKS[1]["required_tools"] != ["py_sandbox", "calc"]:
        errors.append(f"B2-002: expected ['py_sandbox', 'calc'], got {B2_TASKS[1]['required_tools']}")
        print(f"B2-002: FAIL - {B2_TASKS[1]['required_tools']}")
    else:
        print(f"B2-002: PASS - {B2_TASKS[1]['required_tools']}")

    # B2-003: calc + str_ops
    if B2_TASKS[2]["required_tools"] != ["calc", "str_ops"]:
        errors.append(f"B2-003: expected ['calc', 'str_ops'], got {B2_TASKS[2]['required_tools']}")
        print(f"B2-003: FAIL - {B2_TASKS[2]['required_tools']}")
    else:
        print(f"B2-003: PASS - {B2_TASKS[2]['required_tools']}")

    return errors


def write_tasks():
    """Write corrected task files."""
    os.makedirs("data", exist_ok=True)
    for name, tasks in [("diagnostic_A2", A2_TASKS), ("diagnostic_B2", B2_TASKS)]:
        path = f"data/{name}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for t in tasks:
                f.write(json.dumps(t, sort_keys=True) + "\n")
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        print(f"\n{path}: {len(tasks)} tasks, sha256={sha[:16]}")
    return


def write_manifest():
    """Write manifest with consistent Run ID."""
    manifest = {
        "run_id": RUN_ID,
        "protocol": PROTOCOL,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "gold_corrections": {
            "A2-001": "21 -> 23 (arithmetic error: (3*7)+(12-4)-(2*3)=23)",
            "B2-001": "64-75 -> 64-SUM (phantom 75 removed; redesigned to calc+str_ops consistent task)",
        },
        "tool_path_verification": {
            "B2-001": "Must verify calc AND str_ops called in trace",
            "B2-002": "Must verify py_sandbox AND calc called in trace",
            "B2-003": "Must verify calc AND str_ops called AND str_ops output='HI'",
        },
        "tasks": {},
    }
    for name, tasks in [("diagnostic_A2", A2_TASKS), ("diagnostic_B2", B2_TASKS)]:
        path = f"data/{name}.jsonl"
        manifest["tasks"][name] = {
            "count": len(tasks),
            "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(),
            "task_ids": [t["task_id"] for t in tasks],
        }

    os.makedirs("research", exist_ok=True)
    path = "research/G3_DIAG_V2_MANIFEST.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print(f"\nManifest: {path} sha256={sha[:16]}")
    print(f"Run ID: {RUN_ID}")
    return manifest


def main():
    print(f"G3-DIAG-v2 Task Creation & Verification")
    print(f"Run ID: {RUN_ID}")
    print(f"Protocol: {PROTOCOL}")
    print()

    # Step 1: Verify gold labels
    gold_errors = verify_gold_labels()

    # Step 2: Verify required tools
    tool_errors = verify_required_tools()

    # Step 3: Write tasks
    write_tasks()

    # Step 4: Write manifest
    write_manifest()

    # Summary
    total_errors = len(gold_errors) + len(tool_errors)
    print(f"\n=== SUMMARY ===")
    print(f"Gold label errors: {len(gold_errors)}")
    print(f"Required tool errors: {len(tool_errors)}")
    if total_errors == 0:
        print("ALL CHECKS PASSED")
    else:
        print("ERRORS FOUND:")
        for e in gold_errors + tool_errors:
            print(f"  - {e}")

    return total_errors == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
