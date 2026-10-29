"""G3-DIAG-v2-R1: Independent manifest verifier.

Verifies all SHA-256 hashes in the manifest match actual files on disk.
Also checks ledger completeness and budget accounting consistency.
"""
import hashlib
import json
import sys

MANIFEST_PATH = "research/G3_DIAG_R1_MANIFEST.json"
RAW_PATH = "research/G3_DIAG_R1_RAW.json"
LEDGER_PATH = "research/G3_DIAG_R1_LEDGER.jsonl"


def verify_manifest():
    """Verify all artifact hashes match."""
    print("=== Manifest Hash Verification ===")
    errors = []

    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    for path, info in manifest["artifacts"].items():
        if info.get("missing"):
            print(f"  MISSING: {path}")
            errors.append(f"Missing artifact: {path}")
            continue

        try:
            actual_sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        except FileNotFoundError:
            print(f"  NOT FOUND: {path}")
            errors.append(f"File not found: {path}")
            continue

        if actual_sha == info["sha256"]:
            print(f"  OK: {path}")
        else:
            print(f"  MISMATCH: {path} expected={info['sha256'][:16]} actual={actual_sha[:16]}")
            errors.append(f"Hash mismatch: {path}")

    return errors


def verify_ledger():
    """Verify ledger completeness and uniqueness."""
    print("\n=== Ledger Verification ===")
    errors = []

    rows = []
    with open(LEDGER_PATH, encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))

    print(f"  Ledger rows: {len(rows)}")

    # Unique call_ids
    ids = [r["call_id"] for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate call_ids in ledger")
        print("  FAIL: duplicate call_ids")
    else:
        print(f"  OK: unique call_ids ({min(ids)}..{max(ids)})")

    # Monotonic
    if ids != sorted(ids):
        errors.append("call_ids not monotonic")
        print("  FAIL: call_ids not monotonic")
    else:
        print("  OK: call_ids monotonic")

    # Required fields
    required = ["call_id", "input_tokens", "output_tokens", "duration_s", "status", "error"]
    for i, row in enumerate(rows):
        missing = [f for f in required if f not in row]
        if missing:
            errors.append(f"Row {i}: missing {missing}")
            print(f"  FAIL: row {i} missing {missing}")

    if not errors:
        print("  OK: all required fields present")

    return errors, rows


def verify_budget():
    """Verify budget accounting consistency."""
    print("\n=== Budget Verification ===")
    errors = []

    with open(RAW_PATH, encoding="utf-8") as f:
        raw = json.load(f)

    _, rows = verify_ledger()  # already loaded above
    with open(LEDGER_PATH, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]

    # Ledger rows == runtime counter
    ledger_count = len(rows)
    runtime_count = raw.get("total_actual_generations", -1)
    if ledger_count == runtime_count:
        print(f"  OK: ledger ({ledger_count}) == runtime ({runtime_count})")
    else:
        errors.append(f"Ledger ({ledger_count}) != runtime ({runtime_count})")
        print(f"  FAIL: ledger ({ledger_count}) != runtime ({runtime_count})")

    # Token delta sum == runtime total
    delta_sum = sum(r["output_tokens"] for r in rows)
    runtime_tokens = raw.get("token_delta_sum", -1)
    if delta_sum == runtime_tokens:
        print(f"  OK: token delta sum ({delta_sum}) == reported ({runtime_tokens})")
    else:
        errors.append(f"Token delta sum ({delta_sum}) != reported ({runtime_tokens})")
        print(f"  FAIL: token delta sum ({delta_sum}) != reported ({runtime_tokens})")

    # Within hard cap
    cap = raw.get("max_generations", 30)
    if ledger_count <= cap:
        print(f"  OK: {ledger_count} generations <= cap {cap}")
    else:
        errors.append(f"Exceeded generation cap: {ledger_count} > {cap}")
        print(f"  FAIL: exceeded cap {cap}")

    # Wall clock
    wall = raw.get("total_wall_s", 0)
    max_wall = raw.get("max_wall_s", 300)
    if wall <= max_wall:
        print(f"  OK: wall clock {wall}s <= {max_wall}s")
    else:
        errors.append(f"Exceeded wall clock: {wall}s > {max_wall}s")
        print(f"  FAIL: exceeded wall clock")

    return errors


def main():
    print("G3-DIAG-v2-R1 Independent Manifest Verifier")
    print(f"Manifest: {MANIFEST_PATH}")
    print()

    all_errors = []
    all_errors.extend(verify_manifest())
    all_errors.extend(verify_ledger()[0])
    all_errors.extend(verify_budget())

    print(f"\n=== VERIFICATION SUMMARY ===")
    print(f"Total errors: {len(all_errors)}")
    if all_errors:
        print("ERRORS:")
        for e in all_errors:
            print(f"  - {e}")
    else:
        print("ALL CHECKS PASSED")

    return len(all_errors) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
