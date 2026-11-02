"""R24 Stage B: Real tamper tests — actually invoke verifier on tampered data."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = Path("research/runs/20261102T131000Z_R21")
VERIFIER = Path("scripts/verify_r21_c1_independent.py")


def run_verifier(base_dir):
    """Run verifier on given directory, return exit code."""
    result = subprocess.run(
        [sys.executable, str(VERIFIER), "--base-dir", str(base_dir)],
        capture_output=True, text=True
    )
    return result.returncode


def test_tamper(name, modify_fn):
    """Create tampered copy, run verifier, check it fails."""
    with tempfile.TemporaryDirectory() as td:
        tampered = Path(td) / "R21"
        shutil.copytree(BASE, tampered)
        modify_fn(tampered)
        exit_code = run_verifier(tampered)
        passed = exit_code != 0  # Non-zero exit = verifier caught the tamper
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status} (exit={exit_code})")
        return passed


print("=== R24 Tamper Tests (Real Verifier Invocation) ===\n")

results = []

# 1. Modify raw file byte
def t1(path):
    f = path / "R21_RAW.json"
    content = f.read_text(encoding="utf-8")
    f.write_text(content.replace('"run_id"', '"runid_X"', 1), encoding="utf-8")
results.append(test_tamper("1. Modify raw byte", t1))

# 2. Modify token
def t2(path):
    f = path / "R21_LEDGER.jsonl"
    content = f.read_text(encoding="utf-8")
    f.write_text(content.replace('"output_tokens": 10', '"output_tokens": 99', 1), encoding="utf-8")
results.append(test_tamper("2. Modify ledger token", t2))

# 3. Delete ledger row
def t3(path):
    f = path / "R21_LEDGER.jsonl"
    lines = f.read_text(encoding="utf-8").strip().split("\n")
    f.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
results.append(test_tamper("3. Delete ledger row", t3))

# 4. Duplicate call_id
def t4(path):
    f = path / "R21_LEDGER.jsonl"
    lines = f.read_text(encoding="utf-8").strip().split("\n")
    lines[1] = lines[0]
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
results.append(test_tamper("4. Duplicate call_id", t4))

# 5. Delete unit
def t5(path):
    f = path / "R21_RAW.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    data["units"] = data["units"][:-1]
    f.write_text(json.dumps(data), encoding="utf-8")
results.append(test_tamper("5. Delete unit", t5))

# 6. Tamper DEV/CONFIRM
def t6(path):
    f = path / "R21_RAW.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    data["dev_tasks"] = ["B2-069"]
    f.write_text(json.dumps(data), encoding="utf-8")
results.append(test_tamper("6. Tamper DEV/CONFIRM", t6))

# 7. Modify C4 outcome
def t7(path):
    f = path / "R21_RAW.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    data["units"][0]["c4_result"]["source_valid"] = False
    f.write_text(json.dumps(data), encoding="utf-8")
results.append(test_tamper("7. Modify C4 outcome", t7))

# 8. Delete manifest
def t8(path):
    (path / "R21_RESULT_MANIFEST.json").unlink()
results.append(test_tamper("8. Delete manifest", t8))

# 9. Modify frozen manifest hash
def t9(path):
    f = path / "R21_FROZEN_MANIFEST.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    for k in data.get("files", {}):
        data["files"][k]["sha256"] = "0" * 64
    f.write_text(json.dumps(data), encoding="utf-8")
results.append(test_tamper("9. Modify frozen manifest hash", t9))

# 10. Add invalid task
def t10(path):
    f = path / "R21_RAW.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    data["units"].append({"unit_key": "FAKE/SEED/ARM", "task_id": "B2-999", "seed_id": "fake", "arm": "C0"})
    f.write_text(json.dumps(data), encoding="utf-8")
results.append(test_tamper("10. Add invalid task", t10))

print(f"\n=== Summary ===")
print(f"Passed: {sum(results)}/{len(results)}")
print(f"All tamper tests must FAIL (verifier catches tampering)")
if all(results):
    print("ALL TAMPER TESTS PASSED")
else:
    print("SOME TAMPER TESTS FAILED")
    sys.exit(1)
