"""R26 Stage 1I-R1: Semantic evidence map declaration validator (non-production audit helper).

Validates the structured semantic evidence map against actual test declarations.
Uses Python ast module for parsing test source files.

DISCLAIMER: This helper verifies declaration mapping and schema consistency ONLY.
It does NOT prove assertion semantics, call-path truth, branch reachability,
or acceptance coverage. Those require separate semantic review.
"""
import ast
import json
import sys
import tempfile
import shutil
from pathlib import Path
from collections import Counter

# Allowed enums
ALLOWED_EVIDENCE_TYPES = {"DIRECT", "INDIRECT", "MANUAL", "NONE"}
ALLOWED_DISPOSITIONS = {"VERIFIED_FIXED", "PARTIALLY_FIXED", "OPEN", "REGRESSION", "UNVERIFIABLE"}

# Required fields per finding
REQUIRED_FINDING_FIELDS = {
    "id", "original_review_document", "original_finding_heading",
    "original_failure_mode", "complete_original_acceptance_criteria",
    "test_evidence", "manual_evidence", "evidence_type", "disposition",
    "proven_acceptance_conditions", "indirectly_supported_conditions",
    "uncovered_acceptance_conditions", "disposition_rationale",
}

# Required fields per test_evidence entry
REQUIRED_TE_FIELDS = {
    "test_file", "test_class", "test_function",
    "declaration_start_line", "declaration_end_line",
    "assertion_expressions", "source_symbols", "call_path",
    "branch_reached", "acceptance_conditions_proven",
    "acceptance_conditions_indirect", "acceptance_conditions_uncovered",
    "harness_type",
}


def parse_test_declarations(test_files, base_dir=None):
    """Parse test declarations using ast module. Returns dict keyed by (file, class, function)."""
    declarations = {}
    errors = []

    for rel_path in test_files:
        if base_dir:
            path = Path(base_dir) / rel_path
        else:
            path = Path(rel_path)

        if not path.exists():
            errors.append(f"Test source file missing or unreadable: {rel_path}")
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            errors.append(f"Cannot read test file {rel_path}: {e}")
            continue

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            errors.append(f"Syntax error in {rel_path}: {e}")
            continue

        # Collect class-level test functions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                        func_name = item.name
                        key = (rel_path, class_name, func_name)
                        if key in declarations:
                            errors.append(
                                f"Duplicate declaration: {rel_path}::{class_name}::{func_name}"
                            )
                        declarations[key] = {
                            "file": rel_path,
                            "class": class_name,
                            "function": func_name,
                            "start_line": item.lineno,
                            "end_line": item.end_lineno or item.lineno,
                        }

            # Module-level test functions (not inside a class)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                # Check if this is at module level (parent is Module)
                pass  # ast.walk doesn't give parent info; handle separately

        # Also handle module-level test functions
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                key = (rel_path, "<module>", node.name)
                if key not in declarations:
                    declarations[key] = {
                        "file": rel_path,
                        "class": "<module>",
                        "function": node.name,
                        "start_line": node.lineno,
                        "end_line": node.end_lineno or node.lineno,
                    }

    return declarations, errors


def validate_map(map_path, test_files, base_dir=None):
    """Validate semantic evidence map against actual test declarations."""
    issues = []

    # Load map
    try:
        with open(map_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"Cannot load map file: {e}"]

    findings = data.get("findings", [])

    # 1. Exact cardinality: 42 findings
    if len(findings) != 42:
        issues.append(f"Expected exactly 42 findings, got {len(findings)}")

    # 2. ID set: R12-R53 exactly once
    expected_ids = {f"R{i}" for i in range(12, 54)}
    seen_ids = []
    for f in findings:
        fid = f.get("id")
        if fid is None:
            issues.append("Finding with missing id field")
            continue
        seen_ids.append(fid)

    seen_set = set(seen_ids)
    # Duplicates
    id_counts = Counter(seen_ids)
    for fid, count in id_counts.items():
        if count > 1:
            issues.append(f"Duplicate Finding ID: {fid} (appears {count} times)")

    # Missing IDs
    missing = expected_ids - seen_set
    if missing:
        issues.append(f"Missing Finding IDs: {sorted(missing, key=lambda x: int(x[1:]))}")

    # Unknown IDs
    unknown = seen_set - expected_ids
    if unknown:
        issues.append(f"Unknown Finding IDs: {sorted(unknown)}")

    # 3. Parse test declarations
    declarations, decl_errors = parse_test_declarations(test_files, base_dir)
    issues.extend(decl_errors)

    # 4. Per-finding validation
    mapped_count = 0
    none_count = 0

    for f in findings:
        fid = f.get("id", "?")

        # Required fields
        for field in REQUIRED_FINDING_FIELDS:
            if field not in f:
                issues.append(f"{fid}: missing required field '{field}'")

        # Evidence type enum
        et = f.get("evidence_type")
        if et not in ALLOWED_EVIDENCE_TYPES:
            issues.append(f"{fid}: invalid evidence_type '{et}' (allowed: {ALLOWED_EVIDENCE_TYPES})")

        # Disposition enum
        disp = f.get("disposition")
        if disp not in ALLOWED_DISPOSITIONS:
            issues.append(f"{fid}: invalid disposition '{disp}' (allowed: {ALLOWED_DISPOSITIONS})")

        test_evidence = f.get("test_evidence", [])
        manual_evidence = f.get("manual_evidence", [])
        rationale = f.get("disposition_rationale", "")

        # NONE rows: empty test_evidence, MANUAL or NONE evidence type, non-empty rationale
        if not test_evidence:
            none_count += 1
            if et not in ("MANUAL", "NONE"):
                issues.append(f"{fid}: no test_evidence but evidence_type is '{et}' (must be MANUAL or NONE)")
            if not rationale:
                issues.append(f"{fid}: no test_evidence but empty disposition_rationale")
            # Check manual evidence exists for MANUAL type
            if et == "MANUAL" and not manual_evidence:
                issues.append(f"{fid}: evidence_type MANUAL but empty manual_evidence")
        else:
            mapped_count += 1

        # Validate each test_evidence entry
        for i, te in enumerate(test_evidence):
            prefix = f"{fid} te[{i}]"

            # Required TE fields
            for field in REQUIRED_TE_FIELDS:
                if field not in te:
                    issues.append(f"{prefix}: missing required field '{field}'")

            test_file = te.get("test_file")
            test_class = te.get("test_class")
            test_function = te.get("test_function")
            decl_start = te.get("declaration_start_line")
            decl_end = te.get("declaration_end_line")

            if not test_file or not test_class or not test_function:
                issues.append(f"{prefix}: missing test_file/class/function")
                continue

            # Check file exists in declarations (file ownership)
            key = (test_file, test_class, test_function)
            if key not in declarations:
                # Check if file exists at all
                if base_dir:
                    fpath = Path(base_dir) / test_file
                else:
                    fpath = Path(test_file)
                if not fpath.exists():
                    issues.append(f"{prefix}: test file '{test_file}' does not exist")
                else:
                    # File exists but declaration not found
                    # Check if class exists
                    class_keys = [k for k in declarations if k[0] == test_file and k[1] == test_class]
                    if not class_keys:
                        issues.append(f"{prefix}: class '{test_class}' not found in '{test_file}'")
                    else:
                        func_keys = [k for k in class_keys if k[2] == test_function]
                        if not func_keys:
                            issues.append(f"{prefix}: function '{test_function}' not found in class '{test_class}'")
                        else:
                            issues.append(f"{prefix}: declaration tuple not uniquely resolved")
                continue

            decl = declarations[key]

            # Verify declaration line(s)
            if decl_start is not None and decl_start != decl["start_line"]:
                issues.append(
                    f"{prefix}: declaration_start_line mismatch (map={decl_start}, actual={decl['start_line']})"
                )
            if decl_end is not None and decl_end != decl["end_line"]:
                issues.append(
                    f"{prefix}: declaration_end_line mismatch (map={decl_end}, actual={decl['end_line']})"
                )

    # 5. Cardinality check: 39 mapped / 3 NONE (unless different)
    if mapped_count != 39 or none_count != 3:
        issues.append(
            f"Cardinality discrepancy: {mapped_count} mapped / {none_count} NONE "
            f"(expected 39/3). Semantic audit may reveal justified difference."
        )

    return issues, {
        "total_findings": len(findings),
        "mapped_rows": mapped_count,
        "none_rows": none_count,
        "declarations_found": len(declarations),
        "expected_ids": 42,
    }


def run_self_test():
    """Self-test with temporary fixtures proving validator rejects adversarial cases."""
    test_results = []

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        test_dir = td / "tests"
        test_dir.mkdir()

        # Create a valid test fixture file
        fixture_content = '''class TestFixture:
    def test_valid(self):
        assert True

    def test_other(self):
        assert True
'''
        (test_dir / "test_fixture.py").write_text(fixture_content, encoding="utf-8")

        # Create a second fixture for multi-file tests
        fixture2 = '''class TestFixture2:
    def test_valid2(self):
        assert True
'''
        (test_dir / "test_fixture2.py").write_text(fixture2, encoding="utf-8")

        # Helper to build a valid map
        def build_valid_map():
            findings = []
            # R12: mapped to test_fixture.py::TestFixture::test_valid
            findings.append({
                "id": "R12",
                "original_review_document": "TEST.md",
                "original_finding_heading": "R12 — Test",
                "original_failure_mode": "test",
                "complete_original_acceptance_criteria": ["c1"],
                "test_evidence": [{
                    "test_file": "tests/test_fixture.py",
                    "test_class": "TestFixture",
                    "test_function": "test_valid",
                    "declaration_start_line": 2,
                    "declaration_end_line": 3,
                    "assertion_expressions": [{"line": 3, "expression": "assert True"}],
                    "source_symbols": [],
                    "call_path": "test -> func",
                    "branch_reached": {"reached": True, "explanation": "test"},
                    "acceptance_conditions_proven": ["c1"],
                    "acceptance_conditions_indirect": [],
                    "acceptance_conditions_uncovered": [],
                    "harness_type": "production_path",
                }],
                "manual_evidence": [],
                "evidence_type": "DIRECT",
                "disposition": "VERIFIED_FIXED",
                "proven_acceptance_conditions": ["c1"],
                "indirectly_supported_conditions": [],
                "uncovered_acceptance_conditions": [],
                "disposition_rationale": "test",
            })
            # R13-R53: empty test_evidence (NONE rows)
            for i in range(13, 54):
                findings.append({
                    "id": f"R{i}",
                    "original_review_document": "TEST.md",
                    "original_finding_heading": f"R{i} — Test",
                    "original_failure_mode": "test",
                    "complete_original_acceptance_criteria": ["c1"],
                    "test_evidence": [],
                    "manual_evidence": [],
                    "evidence_type": "NONE",
                    "disposition": "OPEN",
                    "proven_acceptance_conditions": [],
                    "indirectly_supported_conditions": [],
                    "uncovered_acceptance_conditions": ["c1"],
                    "disposition_rationale": "No test evidence available.",
                })
            return {"schema_version": "1.0", "findings": findings}

        map_path = td / "map.json"
        test_files = ["tests/test_fixture.py", "tests/test_fixture2.py"]

        def run_validation(map_data, files=None):
            map_path.write_text(json.dumps(map_data), encoding="utf-8")
            return validate_map(str(map_path), files or test_files, base_dir=str(td))

        # === Test 1: Valid map passes ===
        valid_map = build_valid_map()
        issues, summary = run_validation(valid_map)
        # Note: cardinality will fail (1 mapped / 41 NONE vs 39/3), but we test that
        # the declaration matching itself passes. We'll adjust for self-test.
        # Actually, for the self-test to prove "valid map passes", we need cardinality to match.
        # Let me build a map with 39 mapped and 3 NONE.
        def build_full_valid_map():
            findings = []
            # 39 mapped rows (R12-R50)
            for i in range(12, 51):
                findings.append({
                    "id": f"R{i}",
                    "original_review_document": "TEST.md",
                    "original_finding_heading": f"R{i} — Test",
                    "original_failure_mode": "test",
                    "complete_original_acceptance_criteria": ["c1"],
                    "test_evidence": [{
                        "test_file": "tests/test_fixture.py",
                        "test_class": "TestFixture",
                        "test_function": "test_valid",
                        "declaration_start_line": 2,
                        "declaration_end_line": 3,
                        "assertion_expressions": [{"line": 3, "expression": "assert True"}],
                        "source_symbols": [],
                        "call_path": "test -> func",
                        "branch_reached": {"reached": True, "explanation": "test"},
                        "acceptance_conditions_proven": ["c1"],
                        "acceptance_conditions_indirect": [],
                        "acceptance_conditions_uncovered": [],
                        "harness_type": "production_path",
                    }],
                    "manual_evidence": [],
                    "evidence_type": "DIRECT",
                    "disposition": "VERIFIED_FIXED",
                    "proven_acceptance_conditions": ["c1"],
                    "indirectly_supported_conditions": [],
                    "uncovered_acceptance_conditions": [],
                    "disposition_rationale": "test",
                })
            # 3 NONE rows (R51, R52, R53)
            for i in range(51, 54):
                findings.append({
                    "id": f"R{i}",
                    "original_review_document": "TEST.md",
                    "original_finding_heading": f"R{i} — Test",
                    "original_failure_mode": "test",
                    "complete_original_acceptance_criteria": ["c1"],
                    "test_evidence": [],
                    "manual_evidence": [{"source": "test.md", "line": 1, "value": "v", "note": "n"}],
                    "evidence_type": "MANUAL",
                    "disposition": "PARTIALLY_FIXED",
                    "proven_acceptance_conditions": [],
                    "indirectly_supported_conditions": ["c1"],
                    "uncovered_acceptance_conditions": [],
                    "disposition_rationale": "Manual evidence only.",
                })
            return {"schema_version": "1.0", "findings": findings}

        # Test 1: Valid map passes
        issues, summary = run_validation(build_full_valid_map())
        test_results.append(("valid_map_passes", len(issues) == 0, issues if issues else []))

        # Test 2: Wrong file path
        bad = build_full_valid_map()
        bad["findings"][0]["test_evidence"][0]["test_file"] = "tests/wrong_file.py"
        issues, _ = run_validation(bad)
        test_results.append(("wrong_file_path_rejected", len(issues) > 0, issues[:2]))

        # Test 3: Wrong class
        bad = build_full_valid_map()
        bad["findings"][0]["test_evidence"][0]["test_class"] = "WrongClass"
        issues, _ = run_validation(bad)
        test_results.append(("wrong_class_rejected", len(issues) > 0, issues[:2]))

        # Test 4: Wrong function
        bad = build_full_valid_map()
        bad["findings"][0]["test_evidence"][0]["test_function"] = "test_nonexistent"
        issues, _ = run_validation(bad)
        test_results.append(("wrong_function_rejected", len(issues) > 0, issues[:2]))

        # Test 5: Wrong declaration line
        bad = build_full_valid_map()
        bad["findings"][0]["test_evidence"][0]["declaration_start_line"] = 999
        issues, _ = run_validation(bad)
        test_results.append(("wrong_declaration_line_rejected", len(issues) > 0, issues[:2]))

        # Test 6: Missing Finding ID
        bad = build_full_valid_map()
        bad["findings"] = bad["findings"][:-1]  # Remove last
        issues, _ = run_validation(bad)
        test_results.append(("missing_id_rejected", len(issues) > 0, issues[:2]))

        # Test 7: Duplicate Finding ID
        bad = build_full_valid_map()
        bad["findings"][1]["id"] = "R12"  # Duplicate R12
        issues, _ = run_validation(bad)
        test_results.append(("duplicate_id_rejected", len(issues) > 0, issues[:2]))

        # Test 8: Unknown Finding ID
        bad = build_full_valid_map()
        bad["findings"][0]["id"] = "R99"
        issues, _ = run_validation(bad)
        test_results.append(("unknown_id_rejected", len(issues) > 0, issues[:2]))

        # Test 9: Malformed NONE row with non-NONE function/line
        bad = build_full_valid_map()
        bad["findings"][39]["test_evidence"] = [{  # R51 is NONE row (index 39)
            "test_file": "tests/test_fixture.py",
            "test_class": "TestFixture",
            "test_function": "test_valid",
            "declaration_start_line": 2,
            "declaration_end_line": 3,
            "assertion_expressions": [],
            "source_symbols": [],
            "call_path": "",
            "branch_reached": {"reached": True, "explanation": ""},
            "acceptance_conditions_proven": [],
            "acceptance_conditions_indirect": [],
            "acceptance_conditions_uncovered": [],
            "harness_type": "stub_or_mock",
        }]
        issues, _ = run_validation(bad)
        test_results.append(("malformed_none_row_rejected", len(issues) > 0, issues[:2]))

        # Test 10: Missing/unreadable source file
        bad = build_full_valid_map()
        bad["findings"][0]["test_evidence"][0]["test_file"] = "tests/nonexistent.py"
        issues, _ = run_validation(bad)
        test_results.append(("missing_source_file_rejected", len(issues) > 0, issues[:2]))

        # Test 11: Wrong mapped/NONE cardinality (e.g., only 38 mapped)
        bad = build_full_valid_map()
        # Move one mapped row to NONE
        bad["findings"][38]["test_evidence"] = []  # R50 becomes NONE
        bad["findings"][38]["evidence_type"] = "MANUAL"
        bad["findings"][38]["manual_evidence"] = [{"source": "s", "line": 1, "value": "v", "note": "n"}]
        bad["findings"][38]["disposition_rationale"] = "Manual."
        issues, _ = run_validation(bad)
        cardinality_issues = [i for i in issues if "Cardinality" in i]
        test_results.append(("wrong_cardinality_rejected", len(cardinality_issues) > 0, cardinality_issues[:2]))

        # Test 12: Wrong end line
        bad = build_full_valid_map()
        bad["findings"][0]["test_evidence"][0]["declaration_end_line"] = 999
        issues, _ = run_validation(bad)
        test_results.append(("wrong_declaration_end_line_rejected", len(issues) > 0, issues[:2]))

        # Test 13: Invalid evidence type
        bad = build_full_valid_map()
        bad["findings"][0]["evidence_type"] = "INVALID"
        issues, _ = run_validation(bad)
        test_results.append(("invalid_evidence_type_rejected", len(issues) > 0, issues[:2]))

        # Test 14: Invalid disposition
        bad = build_full_valid_map()
        bad["findings"][0]["disposition"] = "INVALID"
        issues, _ = run_validation(bad)
        test_results.append(("invalid_disposition_rejected", len(issues) > 0, issues[:2]))

        # Test 15: Missing required finding field
        bad = build_full_valid_map()
        del bad["findings"][0]["disposition_rationale"]
        issues, _ = run_validation(bad)
        test_results.append(("missing_required_field_rejected", len(issues) > 0, issues[:2]))

    # Print results
    print("=" * 70)
    print("R26 Stage 1I-R1 Validator Self-Test Results")
    print("=" * 70)
    all_passed = True
    for name, passed, details in test_results:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"  [{status}] {name}")
        if details and not passed:
            for d in details:
                print(f"         -> {d}")

    print()
    print(f"Total: {len(test_results)} tests, {sum(1 for _,p,_ in test_results if p)} passed, {sum(1 for _,p,_ in test_results if not p)} failed")
    print(f"Overall: {'ALL PASS' if all_passed else 'SOME FAILED'}")

    return all_passed


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        success = run_self_test()
        sys.exit(0 if success else 1)

    if "--validate" in sys.argv:
        idx = sys.argv.index("--validate")
        if idx + 1 >= len(sys.argv):
            print("Error: --validate requires a map path argument")
            sys.exit(2)
        map_path = sys.argv[idx + 1]

        # Default test files
        test_files = [
            "tests/test_r8_r9_r11_pc1.py",
            "tests/test_r12_r17.py",
            "tests/test_r19_r25.py",
            "tests/test_r26_r32.py",
            "tests/test_r33_r38.py",
            "tests/test_r39_r42.py",
            "tests/test_r54_r59.py",
        ]

        # Optional: --base-dir
        base_dir = None
        if "--base-dir" in sys.argv:
            base_dir = sys.argv[sys.argv.index("--base-dir") + 1]

        issues, summary = validate_map(map_path, test_files, base_dir=base_dir)

        # Machine-readable summary
        print(json.dumps(summary, indent=2))

        if issues:
            print(f"\nVALIDATION FAILED: {len(issues)} issues")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
        else:
            print("\nVALIDATION PASSED")
            sys.exit(0)

    print("Usage:")
    print("  python _r26i_validator.py --self-test")
    print("  python _r26i_validator.py --validate <map.json> [--base-dir <dir>]")
    print()
    print("Disclaimer: Validates declaration mapping/schema only.")
    print("Does NOT prove assertion semantics, call paths, branch reachability,")
    print("or acceptance coverage.")
    sys.exit(0)
