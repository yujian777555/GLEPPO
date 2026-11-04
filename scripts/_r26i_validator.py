"""R26 Stage 1I-R1: Declaration map validator with self-tests (non-production audit helper).

Validates the semantic evidence map's declaration mapping.
Does NOT validate assertion semantics, call paths, or acceptance coverage.
"""
import json
import sys
import re
from pathlib import Path


def parse_declarations(test_files):
    """Parse test declarations using regex (simplified AST-like)."""
    declarations = {}
    for fname in test_files:
        path = Path(fname)
        if not path.exists():
            raise FileNotFoundError(f"Test file missing: {fname}")
        content = path.read_bytes().decode("utf-8", errors="replace")
        lines = content.split("\n")

        current_class = None
        for i, line in enumerate(lines, 1):
            cm = re.match(r'^class\s+(\w+)', line)
            if cm:
                current_class = cm.group(1)
                if current_class not in declarations:
                    declarations[current_class] = []
                continue
            fm = re.match(r'\s+def\s+(test_\w+)\(', line)
            if fm and current_class:
                declarations[current_class].append({
                    "name": fm.group(1),
                    "line": i,
                    "file": fname,
                })
    return declarations


def validate_map(map_path, test_files):
    """Validate semantic evidence map against actual declarations."""
    issues = []

    with open(map_path, encoding="utf-8") as f:
        data = json.load(f)

    findings = data.get("findings", [])
    if len(findings) != 42:
        issues.append(f"Expected 42 findings, got {len(findings)}")

    expected_ids = {f"R{i}" for i in range(12, 54)}
    seen_ids = set()

    declarations = parse_declarations(test_files)

    for finding in findings:
        fid = finding.get("id")
        if fid in seen_ids:
            issues.append(f"Duplicate ID: {fid}")
        seen_ids.add(fid)

        if fid not in expected_ids:
            issues.append(f"Unknown ID: {fid}")

        test_evidence = finding.get("test_evidence", [])
        evidence_type = finding.get("evidence_type", "")

        if evidence_type == "NONE" and test_evidence:
            issues.append(f"{fid}: NONE evidence but has test_evidence")

        for te in test_evidence:
            test_file = te.get("test_file")
            test_class = te.get("test_class")
            test_function = te.get("test_function")
            test_line = te.get("declaration_line")

            if test_class not in declarations:
                issues.append(f"{fid}: class {test_class} not found")
                continue

            funcs = declarations[test_class]
            matching = [f for f in funcs if f["name"] == test_function]
            if not matching:
                issues.append(f"{fid}: function {test_function} not in {test_class}")
                continue

            actual_line = matching[0]["line"]
            if test_line and test_line != actual_line:
                issues.append(f"{fid}: line mismatch (reported={test_line}, actual={actual_line})")

    missing = expected_ids - seen_ids
    if missing:
        issues.append(f"Missing IDs: {sorted(missing, key=lambda x: int(x[1:]))}")

    return issues


def run_self_test():
    """Self-test with temporary fixtures."""
    import tempfile
    import shutil

    test_results = []

    with tempfile.TemporaryDirectory() as td:
        # Create test fixture
        test_dir = Path(td) / "tests"
        test_dir.mkdir()
        test_file = test_dir / "test_fixture.py"
        test_file.write_text("""
class TestFixture:
    def test_valid(self):
        assert True
""", encoding="utf-8")

        # Create valid map
        valid_map = {
            "schema_version": "1.0",
            "findings": [
                {
                    "id": "R12",
                    "test_evidence": [{"test_file": "tests/test_fixture.py", "test_class": "TestFixture", "test_function": "test_valid", "declaration_line": 3}],
                    "evidence_type": "DIRECT",
                    "disposition": "VERIFIED_FIXED",
                }
            ] + [
                {
                    "id": f"R{i}",
                    "test_evidence": [],
                    "evidence_type": "NONE",
                    "disposition": "VERIFIED_FIXED",
                }
                for i in range(13, 54)
            ],
        }
        map_path = Path(td) / "map.json"
        map_path.write_text(json.dumps(valid_map), encoding="utf-8")

        # Test 1: Valid map passes
        issues = validate_map(str(map_path), [str(test_file)])
        test_results.append(("valid_map", len(issues) == 0))

        # Test 2: Wrong function name fails
        bad_map = json.loads(json.dumps(valid_map))
        bad_map["findings"][0]["test_evidence"][0]["test_function"] = "test_nonexistent"
        map_path.write_text(json.dumps(bad_map), encoding="utf-8")
        issues = validate_map(str(map_path), [str(test_file)])
        test_results.append(("wrong_function", len(issues) > 0))

        # Test 3: Missing ID fails
        bad_map = json.loads(json.dumps(valid_map))
        bad_map["findings"] = bad_map["findings"][:-1]
        map_path.write_text(json.dumps(bad_map), encoding="utf-8")
        issues = validate_map(str(map_path), [str(test_file)])
        test_results.append(("missing_id", len(issues) > 0))

    print("Self-test results:")
    for name, passed in test_results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")

    return all(passed for _, passed in test_results)


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        success = run_self_test()
        sys.exit(0 if success else 1)

    if "--validate" in sys.argv:
        map_path = sys.argv[sys.argv.index("--validate") + 1]
        test_files = [
            "tests/test_r8_r9_r11_pc1.py",
            "tests/test_r12_r17.py",
            "tests/test_r19_r25.py",
            "tests/test_r26_r32.py",
            "tests/test_r33_r38.py",
            "tests/test_r39_r42.py",
            "tests/test_r54_r59.py",
        ]
        issues = validate_map(map_path, test_files)
        if issues:
            print(f"VALIDATION FAILED: {len(issues)} issues")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
        else:
            print("VALIDATION PASSED")
            sys.exit(0)

    print("Usage:")
    print("  python _r26i_validator.py --self-test")
    print("  python _r26i_validator.py --validate <map.json>")
    print("\nDisclaimer: Validates declaration mapping/schema only.")
    print("Does NOT prove assertion semantics, call paths, or acceptance coverage.")
