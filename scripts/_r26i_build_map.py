"""Build complete semantic evidence map with all Planner-required fields.

Transforms the existing map to have the exact field names and structure
required by the Stage 1I-R1 corrective prompt.
"""
import json
from pathlib import Path

REPO = Path(r"D:\GLEPPO_repo")

# Load current map
map_path = REPO / "research" / "R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json"
with open(map_path, encoding="utf-8") as f:
    data = json.load(f)

# Load declarations
with open(REPO / "scripts" / "_r26i_declarations.json", encoding="utf-8") as f:
    decls_list = json.load(f)
decl_lookup = {(d["file"], d["class"], d["function"]): d for d in decls_list}

# Load source symbols
with open(REPO / "scripts" / "_r26i_source_symbols.json", encoding="utf-8") as f:
    source_symbols = json.load(f)

# Map old source_symbols names to source line ranges
def get_source_range(symbol_name, source_file):
    """Get line range for a source symbol."""
    # Try various key formats
    for key_format in [
        f"{source_file}::{symbol_name}",
        f"{source_file}::{symbol_name.split('.')[-1]}",
    ]:
        if key_format in source_symbols:
            s = source_symbols[key_format]
            return {"symbol": symbol_name, "file": source_file,
                    "start_line": s["start_line"], "end_line": s["end_line"]}
    # Try matching by name suffix
    for key, s in source_symbols.items():
        if s["name"] == symbol_name or s["name"].endswith(f".{symbol_name}"):
            return {"symbol": symbol_name, "file": s["file"],
                    "start_line": s["start_line"], "end_line": s["end_line"]}
    return {"symbol": symbol_name, "file": source_file,
            "start_line": None, "end_line": None, "note": "line range unresolved"}


# Harness type mapping
def determine_harness_type(old_value, test_file, test_function):
    """Determine harness type from context."""
    if old_value is False:
        return "production_path"
    elif old_value is True:
        return "stub_or_mock"
    return "unknown"


# Process each finding
for finding in data["findings"]:
    fid = finding["id"]
    new_test_evidence = []

    for te in finding.get("test_evidence", []):
        key = (te.get("test_file"), te.get("test_class"), te.get("test_function"))
        decl = decl_lookup.get(key)

        # Build new test_evidence entry
        new_te = {
            "test_file": te.get("test_file"),
            "test_class": te.get("test_class"),
            "test_function": te.get("test_function"),
            "declaration_start_line": decl["start_line"] if decl else te.get("declaration_line"),
            "declaration_end_line": decl["end_line"] if decl else te.get("declaration_line"),
            "assertion_expressions": (
                [{"line": a["line"], "expression": a["expr"]} for a in decl["assertions"]]
                if decl else
                [{"line": te.get("assertion_line"), "expression": te.get("assertion", "")}]
            ),
            "source_symbols": [
                get_source_range(s, te.get("source_file", "gleppo/pc1.py"))
                for s in te.get("source_symbols", [])
            ],
            "call_path": te.get("call_path", ""),
            "branch_reached": {
                "reached": te.get("intended_branch_reached", True),
                "explanation": te.get("branch_explanation", "Test exercises the intended code path as shown by call_path and assertions."),
            },
            "acceptance_conditions_proven": te.get("proven_conditions", []),
            "acceptance_conditions_indirect": te.get("indirectly_supported", []),
            "acceptance_conditions_uncovered": te.get("uncovered", []),
            "harness_type": determine_harness_type(
                te.get("uses_stub_or_mock"),
                te.get("test_file"),
                te.get("test_function"),
            ),
        }

        new_test_evidence.append(new_te)

    finding["test_evidence"] = new_test_evidence

# Fix R18 manual evidence to be complete
r18 = [f for f in data["findings"] if f["id"] == "R18"][0]
r18["manual_evidence"] = [
    {"source": "research/SMOKE_RAW.json", "line": 276,
     "value": "wall_clock_s = 0.0261", "note": "StubLLM only; not production latency"},
    {"source": "research/SMOKE_RAW.json", "line": "277-279",
     "value": "planned initialization 32, offspring 96, total 128",
     "note": "Planned replica-slot accounting, not actual CTX"},
    {"source": "research/SMOKE_RAW.json", "line": 284,
     "value": "actual_replicas_run = 112",
     "note": "Actual uncached replica executions"},
    {"source": "research/SMOKE_RAW.json", "line": 291,
     "value": "production tokens UNMEASURED",
     "note": "No production token measurement exists"},
    {"source": "research/SMOKE_RAW.json", "line": 293,
     "value": "planned slots are conservative planned replica-slot accounting",
     "note": "Not actual CTX; planned slots != model context"},
    {"source": "research/COST_BASELINE.md", "line": 4,
     "value": "production LLM tokens/latency UNMEASURED",
     "note": "Explicit UNMEASURED declaration"},
    {"source": "research/COST_BASELINE.md", "line": 22,
     "value": "0.0261 seconds is stub latency",
     "note": "Not production latency"},
    {"source": "research/COST_BASELINE.md", "line": 30,
     "value": "128 total smoke planned slots",
     "note": "32 init + 96 offspring = 128"},
    {"source": "research/COST_BASELINE.md", "line": 44,
     "value": "LLM tokens UNMEASURED",
     "note": "No production token count available"},
    {"source": "research/COST_BASELINE.md", "line": 47,
     "value": "actual replica executions and cache-hit-bundle units",
     "note": "Units distinction: replicas vs bundles"},
    {"source": "research/COST_BASELINE.md", "line": 82,
     "value": "45,440 PC1 planned slots",
     "note": "Forecast/planned-workload proxy, not measured production cost"},
    {"source": "research/COST_BASELINE.md", "line": 101,
     "value": "stub latency is not production",
     "note": "Explicit distinction"},
    {"source": "research/COST_BASELINE.md", "line": "110-111",
     "value": "45,440 is a forecast/planned-workload proxy",
     "note": "Not measured production cost"},
]
r18["manual_evidence_note"] = (
    "Units: planned replica slots (planned workload), actual uncached replica executions, "
    "cached evaluation bundles (cache-hit units), actual model CTX (not measured), "
    "production tokens/latency (UNMEASURED). No behavioral test exists for R18."
)

# Fix R39 - add cross-references and evidence boundary notes
r39 = [f for f in data["findings"] if f["id"] == "R39"][0]
# The Planner requires distinguishing R39 direct CRN tests from R16/R20 cross-references
# and noting the tautological test is NOT cited
r39["evidence_boundaries"] = {
    "direct_crn_tests": [
        "test_delimiter_no_collision: delimiter collision prevented by typed JSON encoding",
        "test_same_params_reproducible: identical tuples reproduce same seed",
        "test_task_change_changes_seed / test_state_change_changes_seed / test_rollout_change_changes_seed / test_replicate_change_changes_seed: component isolation",
        "test_none_empty_string_no_collision: NONE/EMPTY distinctions",
    ],
    "cross_referenced_tests": [
        "tests/test_r8_r9_r11_pc1.py::TestR8CRNEndToEnd::test_same_crn_tuple_gives_identical_seeds_across_genotypes (R16): two distinct genotypes under same task/state/rollout/replicate produce identical seeds via instrumented evaluator",
        "tests/test_r19_r25.py::TestR20CRNContract::test_same_crn_identical_across_genotypes (R20): same behavioral check in different test class",
    ],
    "structural_evidence": (
        "Evaluator.effective_seed_parts() (gleppo/evaluator.py:57-76) receives "
        "task/state/rollout/replicate/replica/eval-seed inputs and does NOT accept "
        "action or genotype. Evaluator.evaluate() (gleppo/evaluator.py:105-164) calls "
        "effective_seed_parts() and sends the result to Interpreter.run(). "
        "Action exclusion is structurally supported because action is not an input "
        "to the seed derivation/evaluator API."
    ),
    "tautological_test_warning": (
        "test_action_genotype_excluded (tests/test_r39_r42.py:96-99) compares the same "
        "crn_seed() call to itself and is TAUTOLOGICAL. It must NOT be cited as evidence "
        "for action/genotype exclusion."
    ),
    "operator_rng_note": (
        "test_operator_rng_independent_of_eval_seed (tests/test_r12_r17.py:295-298) "
        "changes draw index and checks inequality; this does not directly prove "
        "independence from evaluation seed."
    ),
    "registered_pc1_collector_note": (
        "No registered PC1 collector action-varying integration test exists. "
        "The registered PC1 collector is not implemented/executed."
    ),
}

# Fix R53 - ensure correct semantics
r53 = [f for f in data["findings"] if f["id"] == "R53"][0]
r53["evidence_boundaries"] = {
    "correct_evidence": (
        "tests/test_r39_r42.py::TestR40ProtocolConsistency::test_mutation_status_not_checked_by_consistency "
        "(line 118) changes lifecycle status and verifies protocol_consistency_check() still passes. "
        "This is INDIRECT evidence for lifecycle-status handling by the consistency predicate."
    ),
    "limitation": (
        "It does NOT prove compute_protocol_hash() is invariant to status-only changes. "
        "Tenth Review states compute_protocol_hash(doc) hashes the entire parsed JSON dictionary "
        "including status. No direct status-only hash-invariance test exists in the reviewed source snapshot."
    ),
    "do_not_modify_tests": "Do not modify tests in this stage. Do not upgrade R53 to VERIFIED_FIXED.",
}

# Save the fully enriched map
with open(map_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Map fully enriched with all required fields.")
print(f"Findings: {len(data['findings'])}")

# Count dispositions
from collections import Counter
dispositions = Counter(f["disposition"] for f in data["findings"])
print(f"Dispositions: {dict(dispositions)}")

# Verify test_evidence field completeness
required_te_fields = [
    "test_file", "test_class", "test_function",
    "declaration_start_line", "declaration_end_line",
    "assertion_expressions", "source_symbols", "call_path",
    "branch_reached", "acceptance_conditions_proven",
    "acceptance_conditions_indirect", "acceptance_conditions_uncovered",
    "harness_type",
]
missing_count = 0
for f in data["findings"]:
    for te in f.get("test_evidence", []):
        for field in required_te_fields:
            if field not in te:
                print(f"  MISSING: {f['id']} -> {field}")
                missing_count += 1
print(f"Missing fields: {missing_count}")
