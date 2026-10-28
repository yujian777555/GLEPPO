"""G3-DIAG-v2: Offline validation suite.

Phase 1 requirement 10: offline validation covering:
1. Gold label recomputation
2. Required tool checks
3. Run ID consistency
4. Manifest hash verification
5. Request ledger completeness
"""
import hashlib
import json
import os
import sys

RUN_ID = "20261028T130000Z"
PROTOCOL = "G3-DIAG-v2"


def check_gold_labels():
    """Recompute all gold labels from task inputs."""
    print("=== 1. Gold Label Recomputation ===")
    errors = []

    # Load tasks
    tasks = {}
    for fname in ["data/diagnostic_A2.jsonl", "data/diagnostic_B2.jsonl"]:
        with open(fname, encoding="utf-8") as f:
            for line in f:
                t = json.loads(line)
                tasks[t["task_id"]] = t

    # A2-001: (3*7) + (12-4) - (2*3) = 21 + 8 - 6 = 23
    expected = (3 * 7) + (12 - 4) - (2 * 3)
    got = tasks["A2-001"]["gold"]
    ok = got == str(expected)
    print(f"A2-001: gold={got} expected={expected} -> {'PASS' if ok else 'FAIL'}")
    if not ok:
        errors.append(f"A2-001 gold mismatch")

    # A2-002: 15*8 - (15+8) = 120 - 23 = 97
    expected = 15 * 8 - (15 + 8)
    got = tasks["A2-002"]["gold"]
    ok = got == str(expected)
    print(f"A2-002: gold={got} expected={expected} -> {'PASS' if ok else 'FAIL'}")
    if not ok:
        errors.append(f"A2-002 gold mismatch")

    # A2-003: (100-37)*2 + 5 = 63*2 + 5 = 131
    expected = (100 - 37) * 2 + 5
    got = tasks["A2-003"]["gold"]
    ok = got == str(expected)
    print(f"A2-003: gold={got} expected={expected} -> {'PASS' if ok else 'FAIL'}")
    if not ok:
        errors.append(f"A2-003 gold mismatch")

    # B2-001: 25*3-11 = 64; 'sum'->'SUM'; "64-SUM"
    expected = f"{25*3-11}-{'sum'.upper()}"
    got = tasks["B2-001"]["gold"]
    ok = got == expected
    print(f"B2-001: gold={got} expected={expected} -> {'PASS' if ok else 'FAIL'}")
    if not ok:
        errors.append(f"B2-001 gold mismatch")

    # B2-002: 14*3+7 = 49; 49-6 = 43
    expected = (14 * 3 + 7) - 6
    got = tasks["B2-002"]["gold"]
    ok = got == str(expected)
    print(f"B2-002: gold={got} expected={expected} -> {'PASS' if ok else 'FAIL'}")
    if not ok:
        errors.append(f"B2-002 gold mismatch")

    # B2-003: 8*8-4 = 60; 'hi'->'HI'; "60-HI"
    expected = f"{8*8-4}-{'hi'.upper()}"
    got = tasks["B2-003"]["gold"]
    ok = got == expected
    print(f"B2-003: gold={got} expected={expected} -> {'PASS' if ok else 'FAIL'}")
    if not ok:
        errors.append(f"B2-003 gold mismatch")

    return errors


def check_required_tools():
    """Verify required_tools match task requirements."""
    print("\n=== 2. Required Tool Checks ===")
    errors = []

    expected_tools = {
        "A2-001": ["calc"],
        "A2-002": ["calc"],
        "A2-003": ["calc"],
        "B2-001": ["calc", "str_ops"],
        "B2-002": ["py_sandbox", "calc"],
        "B2-003": ["calc", "str_ops"],
    }

    tasks = {}
    for fname in ["data/diagnostic_A2.jsonl", "data/diagnostic_B2.jsonl"]:
        with open(fname, encoding="utf-8") as f:
            for line in f:
                t = json.loads(line)
                tasks[t["task_id"]] = t

    for tid, expected in expected_tools.items():
        got = tasks[tid]["required_tools"]
        ok = got == expected
        print(f"{tid}: {got} -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            errors.append(f"{tid} required_tools mismatch: expected {expected}, got {got}")

    return errors


def check_run_id_consistency():
    """Verify Run ID is consistent across all artifacts."""
    print("\n=== 3. Run ID Consistency ===")
    errors = []

    # Check manifest
    manifest_path = "research/G3_DIAG_V2_MANIFEST.json"
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        manifest_rid = manifest.get("run_id")
        ok = manifest_rid == RUN_ID
        print(f"Manifest run_id: {manifest_rid} -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            errors.append(f"Manifest run_id mismatch: expected {RUN_ID}, got {manifest_rid}")
    else:
        print(f"Manifest not found: {manifest_path} -> FAIL")
        errors.append("Manifest not found")

    # Check raw data (if exists)
    raw_path = "research/G3_DIAG_V2_RAW.json"
    if os.path.exists(raw_path):
        with open(raw_path, encoding="utf-8") as f:
            raw = json.load(f)
        raw_rid = raw.get("run_id")
        ok = raw_rid == RUN_ID
        print(f"Raw data run_id: {raw_rid} -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            errors.append(f"Raw data run_id mismatch: expected {RUN_ID}, got {raw_rid}")
    else:
        print(f"Raw data not yet generated (expected for Phase 1)")

    # Check protocol
    protocol_path = "research/G3_DIAG_V2_PROTOCOL.md"
    if os.path.exists(protocol_path):
        with open(protocol_path, encoding="utf-8") as f:
            content = f.read()
        ok = RUN_ID in content
        print(f"Protocol contains run_id: -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            errors.append(f"Protocol missing run_id {RUN_ID}")
    else:
        print(f"Protocol not yet created (expected for Phase 1)")

    return errors


def check_manifest_hashes():
    """Verify task file hashes match manifest."""
    print("\n=== 4. Manifest Hash Verification ===")
    errors = []

    manifest_path = "research/G3_DIAG_V2_MANIFEST.json"
    if not os.path.exists(manifest_path):
        print("Manifest not found -> FAIL")
        return ["Manifest not found"]

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    for name, info in manifest.get("tasks", {}).items():
        path = f"data/{name}.jsonl"
        if not os.path.exists(path):
            print(f"{path}: not found -> FAIL")
            errors.append(f"{path} not found")
            continue

        actual_sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        expected_sha = info["sha256"]
        ok = actual_sha == expected_sha
        print(f"{path}: sha256 match -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            errors.append(f"{path} hash mismatch: expected {expected_sha[:16]}, got {actual_sha[:16]}")

    return errors


def check_request_ledger():
    """Verify request ledger completeness (if exists)."""
    print("\n=== 5. Request Ledger Completeness ===")
    errors = []

    ledger_path = "research/G3_DIAG_V2_LEDGER.jsonl"
    if not os.path.exists(ledger_path):
        print("Ledger not yet generated (expected for Phase 1)")
        return []

    # Load ledger
    entries = []
    with open(ledger_path, encoding="utf-8") as f:
        for line in f:
            entries.append(json.loads(line))

    print(f"Ledger entries: {len(entries)}")

    # Check each entry has required fields
    required_fields = ["request_id", "task_id", "operator", "parent_id", "replicate", "request_type", "timestamp"]
    for i, entry in enumerate(entries):
        missing = [f for f in required_fields if f not in entry]
        if missing:
            errors.append(f"Entry {i}: missing fields {missing}")
            print(f"Entry {i}: missing {missing} -> FAIL")

    # Check request_id is sequential
    for i, entry in enumerate(entries):
        if entry.get("request_id") != i + 1:
            errors.append(f"Entry {i}: request_id {entry.get('request_id')} != {i+1}")
            print(f"Entry {i}: request_id mismatch -> FAIL")

    if not errors:
        print("Ledger completeness: PASS")

    return errors


def main():
    print(f"G3-DIAG-v2 Offline Validation Suite")
    print(f"Run ID: {RUN_ID}")
    print(f"Protocol: {PROTOCOL}")
    print()

    all_errors = []
    all_errors.extend(check_gold_labels())
    all_errors.extend(check_required_tools())
    all_errors.extend(check_run_id_consistency())
    all_errors.extend(check_manifest_hashes())
    all_errors.extend(check_request_ledger())

    print(f"\n=== VALIDATION SUMMARY ===")
    print(f"Total errors: {len(all_errors)}")
    if all_errors:
        print("ERRORS:")
        for e in all_errors:
            print(f"  - {e}")
    else:
        print("ALL OFFLINE CHECKS PASSED")

    return len(all_errors) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
