import json, collections, sys

path = r"D:\GLEPPO_repo\research\R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json"
d = json.load(open(path, encoding="utf-8"))

print("schema_version:", d.get("schema_version"))
print("top-level keys:", sorted(d.keys()))
findings = d.get("findings", [])
print("findings count:", len(findings))

ids = [f["id"] for f in findings]
print("IDs:", sorted(ids, key=lambda x: int(x[1:])))
expected = set("R" + str(i) for i in range(12, 54))
print("has all R12-R53:", set(ids) == expected)
print("missing:", expected - set(ids))
print("extra:", set(ids) - expected)
print("duplicates:", [k for k, v in collections.Counter(ids).items() if v > 1])

f0 = findings[0]
print("Fields in first finding:", sorted(f0.keys()))

required_fields = [
    "id", "original_review_document", "original_finding_heading",
    "original_failure_mode", "complete_original_acceptance_criteria",
    "test_evidence", "manual_evidence", "evidence_type", "disposition",
    "proven_acceptance_conditions", "indirectly_supported_conditions",
    "uncovered_acceptance_conditions", "disposition_rationale",
]
for f in findings:
    missing = [k for k in required_fields if k not in f]
    if missing:
        print(f"  {f.get('id','?')}: MISSING FIELDS: {missing}")

dispositions = collections.Counter(f["disposition"] for f in findings)
print("Dispositions:", dict(dispositions))
evidence_types = collections.Counter(f["evidence_type"] for f in findings)
print("Evidence types:", dict(evidence_types))

none_rows = [f["id"] for f in findings if not f.get("test_evidence")]
print("Rows with empty test_evidence:", none_rows)

mapped_rows = [f["id"] for f in findings if f.get("test_evidence")]
print("Mapped rows count:", len(mapped_rows))

# Check test_evidence entry fields
te_required = [
    "test_file", "test_class", "test_function",
    "declaration_start_line", "declaration_end_line",
    "assertion_expressions", "source_symbols",
    "call_path", "branch_reached",
    "acceptance_conditions_proven", "acceptance_conditions_indirect",
    "acceptance_conditions_uncovered", "harness_type",
]
for f in findings:
    for i, te in enumerate(f.get("test_evidence", [])):
        missing = [k for k in te_required if k not in te]
        if missing:
            print(f"  {f['id']} te[{i}]: MISSING: {missing}")
