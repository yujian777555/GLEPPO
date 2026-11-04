"""R26 Stage 1I-R2: Hardened semantic evidence map validator (non-production audit helper).

Uses Python ast for test declarations. Validates:
- Schema version, structure, exact ID set R12-R53
- Required field types (not just presence)
- Declaration lines match AST exactly
- Source symbols: file exists, lines positive, range within file
- assertion_expressions, branch_reached, harness_type, manual_evidence
- NONE row semantics

DISCLAIMER: Validates declaration mapping/schema ONLY.
Does NOT prove assertion semantics, call-path truth, branch reachability,
or acceptance coverage.
"""
import ast
import json
import sys
import tempfile
from pathlib import Path
from collections import Counter

ALLOWED_EVIDENCE_TYPES = {"DIRECT", "INDIRECT", "MANUAL", "NONE"}
ALLOWED_DISPOSITIONS = {"VERIFIED_FIXED", "PARTIALLY_FIXED", "OPEN", "REGRESSION", "UNVERIFIABLE"}
ALLOWED_HARNESS_TYPES = {"production_path", "stub_or_mock"}
EXPECTED_SCHEMA_VERSION = "1.0"
EXPECTED_IDS = {f"R{i}" for i in range(12, 54)}

REQUIRED_FINDING_FIELDS = {
    "id", "original_review_document", "original_finding_heading",
    "original_failure_mode", "complete_original_acceptance_criteria",
    "test_evidence", "manual_evidence", "evidence_type", "disposition",
    "proven_acceptance_conditions", "indirectly_supported_conditions",
    "uncovered_acceptance_conditions", "disposition_rationale",
}
REQUIRED_TE_FIELDS = {
    "test_file", "test_class", "test_function",
    "declaration_start_line", "declaration_end_line",
    "assertion_expressions", "source_symbols", "call_path",
    "branch_reached", "acceptance_conditions_proven",
    "acceptance_conditions_indirect", "acceptance_conditions_uncovered",
    "harness_type",
}


def parse_test_declarations(test_files, base_dir=None):
    declarations = {}
    errors = []
    for rel_path in test_files:
        path = (Path(base_dir) / rel_path) if base_dir else Path(rel_path)
        if not path.exists():
            errors.append(f"FILE_MISSING:{rel_path}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except Exception as e:
            errors.append(f"FILE_UNREADABLE:{rel_path}:{e}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                        key = (rel_path, node.name, item.name)
                        if key in declarations:
                            errors.append(f"DUPLICATE_DECLARATION:{rel_path}::{node.name}::{item.name}")
                        declarations[key] = {"file": rel_path, "class": node.name,
                                             "function": item.name, "start_line": item.lineno,
                                             "end_line": item.end_lineno or item.lineno}
    return declarations, errors


def validate_source_symbols(src_syms, base_dir):
    issues = []
    for i, s in enumerate(src_syms):
        sym = s.get("symbol")
        if not sym or not isinstance(sym, str):
            issues.append(f"SRC_SYMBOL_EMPTY:entry[{i}]")
        sf = s.get("file")
        if not sf or not isinstance(sf, str):
            issues.append(f"SRC_FILE_EMPTY:entry[{i}]")
        else:
            fpath = (Path(base_dir) / sf) if base_dir else Path(sf)
            if not fpath.exists():
                issues.append(f"SRC_FILE_MISSING:{sf}")
            else:
                sl = s.get("start_line")
                el = s.get("end_line")
                if sl is None or not isinstance(sl, int) or isinstance(sl, bool) or sl < 1:
                    issues.append(f"SRC_START_LINE_INVALID:{sym}:{sl}")
                elif el is not None and isinstance(el, int) and not isinstance(el, bool):
                    if el < sl:
                        issues.append(f"SRC_RANGE_INVALID:{sym}:{sl}-{el}")
                    else:
                        try:
                            total = sum(1 for _ in fpath.open(encoding="utf-8"))
                            if sl > total:
                                issues.append(f"SRC_RANGE_OUT_OF_FILE:{sym}:{sl}>{total}")
                        except Exception:
                            pass
                if el is None or not isinstance(el, int) or isinstance(el, bool) or el < 1:
                    issues.append(f"SRC_END_LINE_INVALID:{sym}:{el}")
    return issues


def validate_map(map_path, test_files, base_dir=None):
    issues = []
    try:
        with open(map_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"MAP_LOAD_ERROR:{e}"], {}

    if not isinstance(data, dict):
        return ["MAP_NOT_OBJECT"], {}
    if data.get("schema_version") != EXPECTED_SCHEMA_VERSION:
        issues.append(f"SCHEMA_VERSION_INVALID:{data.get('schema_version')}")
    findings = data.get("findings")
    if not isinstance(findings, list):
        return ["FINDINGS_NOT_LIST"], {}

    if len(findings) != 42:
        issues.append(f"ROW_COUNT:{len(findings)}!=42")

    seen = []
    for f in findings:
        fid = f.get("id")
        if fid: seen.append(fid)
    counts = Counter(seen)
    for fid, c in counts.items():
        if c > 1: issues.append(f"DUPLICATE_ID:{fid}:{c}")
    missing = EXPECTED_IDS - set(seen)
    if missing: issues.append(f"MISSING_IDS:{sorted(missing, key=lambda x: int(x[1:]))}")
    unknown = set(seen) - EXPECTED_IDS
    if unknown: issues.append(f"UNKNOWN_IDS:{sorted(unknown)}")

    declarations, decl_errors = parse_test_declarations(test_files, base_dir)
    issues.extend(decl_errors)

    mapped = 0; none = 0
    for f in findings:
        fid = f.get("id", "?")
        for field in REQUIRED_FINDING_FIELDS:
            if field not in f: issues.append(f"MISSING_FIELD:{fid}:{field}")
        et = f.get("evidence_type")
        if et not in ALLOWED_EVIDENCE_TYPES: issues.append(f"EVIDENCE_TYPE_INVALID:{fid}:{et}")
        disp = f.get("disposition")
        if disp not in ALLOWED_DISPOSITIONS: issues.append(f"DISPOSITION_INVALID:{fid}:{disp}")

        tes = f.get("test_evidence", [])
        manual = f.get("manual_evidence", [])
        rationale = f.get("disposition_rationale", "")

        if not tes:
            none += 1
            if et not in ("MANUAL", "NONE"):
                issues.append(f"NONE_TYPE_MISMATCH:{fid}:{et}")
            if not rationale: issues.append(f"NONE_NO_RATIONALE:{fid}")
            if et == "MANUAL" and not manual: issues.append(f"MANUAL_NO_EVIDENCE:{fid}")
        else:
            mapped += 1

        for j, te in enumerate(tes):
            p = f"{fid}te[{j}]"
            for field in REQUIRED_TE_FIELDS:
                if field not in te: issues.append(f"TE_MISSING_FIELD:{p}:{field}")
            tf = te.get("test_file"); tc = te.get("test_class"); fn = te.get("test_function")
            if not tf or not isinstance(tf, str): issues.append(f"TE_FILE_EMPTY:{p}"); continue
            if not tc or not isinstance(tc, str): issues.append(f"TE_CLASS_EMPTY:{p}"); continue
            if not fn or not isinstance(fn, str): issues.append(f"TE_FUNC_EMPTY:{p}"); continue
            ds = te.get("declaration_start_line"); de = te.get("declaration_end_line")
            if ds is None or not isinstance(ds, int) or isinstance(ds, bool) or ds < 1:
                issues.append(f"TE_START_LINE_INVALID:{p}:{ds}")
            if de is None or not isinstance(de, int) or isinstance(de, bool) or de < 1:
                issues.append(f"TE_END_LINE_INVALID:{p}:{de}")
            key = (tf, tc, fn)
            if key not in declarations:
                fpath = (Path(base_dir) / tf) if base_dir else Path(tf)
                if not fpath.exists(): issues.append(f"TE_FILE_MISSING:{p}:{tf}")
                else:
                    cls_exists = any(k[0] == tf and k[1] == tc for k in declarations)
                    if not cls_exists: issues.append(f"TE_WRONG_OWNER_CLASS:{p}:{tc}")
                    else: issues.append(f"TE_WRONG_OWNER_FUNC:{p}:{fn}")
                continue
            decl = declarations[key]
            if isinstance(ds, int) and not isinstance(ds, bool) and ds != decl["start_line"]:
                issues.append(f"TE_LINE_MISMATCH:{p}:{ds}!={decl['start_line']}")
            if isinstance(de, int) and not isinstance(de, bool) and de != decl["end_line"]:
                issues.append(f"TE_END_LINE_MISMATCH:{p}:{de}!={decl['end_line']}")

            ae = te.get("assertion_expressions", [])
            if not isinstance(ae, list): issues.append(f"TE_ASSERTIONS_NOT_LIST:{p}")
            else:
                for a in ae:
                    if not isinstance(a, dict): issues.append(f"TE_ASSERTION_NOT_DICT:{p}"); continue
                    al = a.get("line")
                    if al is None or not isinstance(al, int) or isinstance(al, bool) or al < 1:
                        issues.append(f"TE_ASSERTION_LINE_INVALID:{p}:{al}")
                    if not a.get("expression"): issues.append(f"TE_ASSERTION_EMPTY:{p}")

            src_issues = validate_source_symbols(te.get("source_symbols", []), base_dir)
            for si in src_issues: issues.append(f"{p}:{si}")

            br = te.get("branch_reached")
            if not isinstance(br, dict): issues.append(f"TE_BRANCH_NOT_DICT:{p}")
            else:
                if not isinstance(br.get("reached"), bool): issues.append(f"TE_BRANCH_REACHED_NOT_BOOL:{p}")
                exp = br.get("explanation")
                if not exp or not isinstance(exp, str) or len(exp.strip()) < 5:
                    issues.append(f"TE_BRANCH_EXPLANATION_EMPTY:{p}")

            ht = te.get("harness_type")
            if ht not in ALLOWED_HARNESS_TYPES: issues.append(f"TE_HARNESS_INVALID:{p}:{ht}")

        for j, me in enumerate(manual):
            p = f"{fid}me[{j}]"
            if not me.get("source"): issues.append(f"ME_SOURCE_EMPTY:{p}")
            if me.get("line") is None: issues.append(f"ME_LINE_EMPTY:{p}")
            if not me.get("value"): issues.append(f"ME_VALUE_EMPTY:{p}")

    if mapped != 39 or none != 3:
        issues.append(f"CARDINALITY:{mapped}/{none}!=39/3")

    summary = {"total_findings": len(findings), "mapped_rows": mapped,
               "none_rows": none, "declarations_found": len(declarations),
               "expected_ids": 42}
    return issues, summary


def run_self_test():
    results = []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); tdir = td / "tests"; tdir.mkdir()
        (tdir / "test_fixture.py").write_text(
            'class TestFixture:\n    def test_valid(self):\n        assert True\n', encoding="utf-8")
        (tdir / "test_fixture2.py").write_text(
            'class TestFixture2:\n    def test_valid2(self):\n        assert True\n', encoding="utf-8")

        def build_full():
            findings = []
            for i in range(12, 51):
                findings.append({"id": f"R{i}", "original_review_document": "T.md",
                    "original_finding_heading": f"R{i} — T", "original_failure_mode": "T",
                    "complete_original_acceptance_criteria": ["c1"],
                    "test_evidence": [{"test_file": "tests/test_fixture.py", "test_class": "TestFixture",
                        "test_function": "test_valid", "declaration_start_line": 2, "declaration_end_line": 3,
                        "assertion_expressions": [{"line": 3, "expression": "assert True"}],
                        "source_symbols": [{"symbol": "f", "file": "tests/test_fixture.py", "start_line": 1, "end_line": 3}],
                        "call_path": "t->f", "branch_reached": {"reached": True, "explanation": "Valid call path exercised."},
                        "acceptance_conditions_proven": ["c1"], "acceptance_conditions_indirect": [],
                        "acceptance_conditions_uncovered": [], "harness_type": "production_path"}],
                    "manual_evidence": [], "evidence_type": "DIRECT", "disposition": "VERIFIED_FIXED",
                    "proven_acceptance_conditions": ["c1"], "indirectly_supported_conditions": [],
                    "uncovered_acceptance_conditions": [], "disposition_rationale": "R"})
            for i in range(51, 54):
                findings.append({"id": f"R{i}", "original_review_document": "T.md",
                    "original_finding_heading": f"R{i} — T", "original_failure_mode": "T",
                    "complete_original_acceptance_criteria": ["c1"], "test_evidence": [],
                    "manual_evidence": [{"source": "s.md", "line": 1, "value": "v", "note": "n"}],
                    "evidence_type": "MANUAL", "disposition": "PARTIALLY_FIXED",
                    "proven_acceptance_conditions": [], "indirectly_supported_conditions": [],
                    "uncovered_acceptance_conditions": ["c1"], "disposition_rationale": "Manual evidence."})
            return {"schema_version": "1.0", "findings": findings}

        mp = td / "map.json"
        tf = ["tests/test_fixture.py", "tests/test_fixture2.py"]
        def run(md, files=None):
            mp.write_text(json.dumps(md), encoding="utf-8")
            return validate_map(str(mp), files or tf, base_dir=str(td))

        def check(name, cond, diag_cat, issues):
            hit = any(diag_cat in i for i in issues) if diag_cat else True
            ok = cond and (hit if diag_cat else True)
            results.append((name, ok, [i for i in issues if diag_cat in i][:2] if diag_cat else issues[:2]))

        # 1. Valid map passes
        iss, _ = run(build_full())
        check("valid_map_passes", len(iss) == 0, None, iss)

        # 2. Wrong file path (existing file, wrong owner)
        bad = build_full(); bad["findings"][0]["test_evidence"][0]["test_file"] = "tests/test_fixture2.py"
        iss, _ = run(bad); check("wrong_file_owner_rejected", len(iss) > 0, "TE_WRONG_OWNER", iss)

        # 3. Wrong class
        bad = build_full(); bad["findings"][0]["test_evidence"][0]["test_class"] = "WrongClass"
        iss, _ = run(bad); check("wrong_class_rejected", len(iss) > 0, "TE_WRONG_OWNER_CLASS", iss)

        # 4. Wrong function
        bad = build_full(); bad["findings"][0]["test_evidence"][0]["test_function"] = "test_nonexistent"
        iss, _ = run(bad); check("wrong_function_rejected", len(iss) > 0, "TE_WRONG_OWNER_FUNC", iss)

        # 5. Wrong declaration line
        bad = build_full(); bad["findings"][0]["test_evidence"][0]["declaration_start_line"] = 999
        iss, _ = run(bad); check("wrong_start_line_rejected", len(iss) > 0, "TE_LINE_MISMATCH", iss)

        # 6. Null declaration start
        bad = build_full(); bad["findings"][0]["test_evidence"][0]["declaration_start_line"] = None
        iss, _ = run(bad); check("null_start_line_rejected", len(iss) > 0, "TE_START_LINE_INVALID", iss)

        # 7. Null declaration end
        bad = build_full(); bad["findings"][0]["test_evidence"][0]["declaration_end_line"] = None
        iss, _ = run(bad); check("null_end_line_rejected", len(iss) > 0, "TE_END_LINE_INVALID", iss)

        # 8. Null source start/end
        bad = build_full(); bad["findings"][0]["test_evidence"][0]["source_symbols"][0]["start_line"] = None
        iss, _ = run(bad); check("null_src_start_rejected", len(iss) > 0, "SRC_START_LINE_INVALID", iss)

        # 9. Wrong source symbol range
        bad = build_full(); bad["findings"][0]["test_evidence"][0]["source_symbols"][0]["start_line"] = 999
        iss, _ = run(bad); check("wrong_src_range_rejected", len(iss) > 0, "SRC_RANGE_INVALID", iss)

        # 10. Missing ID
        bad = build_full(); bad["findings"] = bad["findings"][:-1]
        iss, _ = run(bad); check("missing_id_rejected", len(iss) > 0, "MISSING_IDS", iss)

        # 11. Duplicate ID
        bad = build_full(); bad["findings"][1]["id"] = "R12"
        iss, _ = run(bad); check("duplicate_id_rejected", len(iss) > 0, "DUPLICATE_ID", iss)

        # 12. Unknown ID
        bad = build_full(); bad["findings"][0]["id"] = "R99"
        iss, _ = run(bad); check("unknown_id_rejected", len(iss) > 0, "UNKNOWN_IDS", iss)

        # 13. Malformed NONE row
        bad = build_full(); bad["findings"][39]["test_evidence"] = [{"test_file": "tests/test_fixture.py",
            "test_class": "TestFixture", "test_function": "test_valid", "declaration_start_line": 2,
            "declaration_end_line": 3, "assertion_expressions": [], "source_symbols": [],
            "call_path": "", "branch_reached": {"reached": True, "explanation": "x"},
            "acceptance_conditions_proven": [], "acceptance_conditions_indirect": [],
            "acceptance_conditions_uncovered": [], "harness_type": "stub_or_mock"}]
        iss, _ = run(bad); check("malformed_none_rejected", len(iss) > 0, "CARDINALITY", iss)

        # 14. Missing file
        bad = build_full(); bad["findings"][0]["test_evidence"][0]["test_file"] = "tests/nonexistent.py"
        iss, _ = run(bad); check("missing_file_rejected", len(iss) > 0, "TE_FILE_MISSING", iss)

        # 15. Wrong cardinality
        bad = build_full(); bad["findings"][38]["test_evidence"] = []
        bad["findings"][38]["evidence_type"] = "MANUAL"
        bad["findings"][38]["manual_evidence"] = [{"source": "s", "line": 1, "value": "v", "note": "n"}]
        iss, _ = run(bad); check("wrong_cardinality_rejected", any("CARDINALITY" in i for i in iss), "CARDINALITY", iss)

        # 16. Invalid schema version
        bad = build_full(); bad["schema_version"] = "2.0"
        iss, _ = run(bad); check("invalid_schema_rejected", len(iss) > 0, "SCHEMA_VERSION_INVALID", iss)

        # 17. Invalid branch_reached
        bad = build_full(); bad["findings"][0]["test_evidence"][0]["branch_reached"] = {"reached": "yes", "explanation": "x"}
        iss, _ = run(bad); check("invalid_branch_rejected", len(iss) > 0, "TE_BRANCH_REACHED_NOT_BOOL", iss)

        # 18. Invalid harness_type
        bad = build_full(); bad["findings"][0]["test_evidence"][0]["harness_type"] = "invalid"
        iss, _ = run(bad); check("invalid_harness_rejected", len(iss) > 0, "TE_HARNESS_INVALID", iss)

        # 19. Empty assertion
        bad = build_full(); bad["findings"][0]["test_evidence"][0]["assertion_expressions"] = [{"line": 3, "expression": ""}]
        iss, _ = run(bad); check("empty_assertion_rejected", len(iss) > 0, "TE_ASSERTION_EMPTY", iss)

        # 20. Invalid evidence type
        bad = build_full(); bad["findings"][0]["evidence_type"] = "INVALID"
        iss, _ = run(bad); check("invalid_evidence_type_rejected", len(iss) > 0, "EVIDENCE_TYPE_INVALID", iss)

    print("=" * 70)
    print("R26 Stage 1I-R2 Validator Self-Test Results")
    print("=" * 70)
    all_pass = True
    for name, ok, details in results:
        s = "PASS" if ok else "FAIL"
        if not ok: all_pass = False
        print(f"  [{s}] {name}")
        if details and not ok:
            for d in details: print(f"         -> {d}")
    print()
    print(f"Total: {len(results)} tests, {sum(1 for _,o,_ in results if o)} passed, {sum(1 for _,o,_ in results if not o)} failed")
    print(f"Overall: {'ALL PASS' if all_pass else 'SOME FAILED'}")
    return all_pass


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(0 if run_self_test() else 1)
    if "--validate" in sys.argv:
        idx = sys.argv.index("--validate")
        map_path = sys.argv[idx + 1]
        test_files = ["tests/test_r8_r9_r11_pc1.py", "tests/test_r12_r17.py",
                      "tests/test_r19_r25.py", "tests/test_r26_r32.py",
                      "tests/test_r33_r38.py", "tests/test_r39_r42.py", "tests/test_r54_r59.py"]
        base_dir = sys.argv[sys.argv.index("--base-dir") + 1] if "--base-dir" in sys.argv else None
        issues, summary = validate_map(map_path, test_files, base_dir=base_dir)
        print(json.dumps(summary, indent=2))
        if issues:
            print(f"\nVALIDATION FAILED: {len(issues)} issues")
            for i in issues: print(f"  - {i}")
            sys.exit(1)
        else:
            print("\nVALIDATION PASSED")
            sys.exit(0)
    print("Usage: python _r26i_validator.py --self-test | --validate <map.json> [--base-dir <dir>]")
    print("Disclaimer: Validates declaration mapping/schema ONLY.")
    sys.exit(0)
