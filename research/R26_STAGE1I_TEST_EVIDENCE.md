# R26 Stage 1I Test Evidence

**Date:** 2026-11-04
**Branch:** r25-handoff

## Declaration Map Validator

`scripts/_r26i_validator.py` — validates declaration existence and line numbers.

**Scope:** Declaration inventory only. Semantic evidence requires manual assertion/call-path review.

## R53 Corrected Mapping

| Field | Value |
|-------|-------|
| Test File | tests/test_r39_r42.py |
| Test Class | TestR40ProtocolConsistency |
| Test Function | test_mutation_status_not_checked_by_consistency |
| Line | 118 |
| Evidence Type | **Indirect** |
| Limitation | Proves consistency check ignores status, NOT hash invariance |

## R39 Cross-Reference Evidence

| Test | Class | Line | Supports |
|------|-------|------|----------|
| test_same_crn_identical_across_genotypes | TestR16SeedContract | 246 | CRN across genotypes |
| test_cache_identity_is_genotype_specific | TestR8CRNEndToEnd | 84 | Cache isolation |
| test_operator_rng_independent_of_eval_seed | TestR16SeedContract | 295 | RNG independence |

## 450/450 Provenance

**EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED** — no raw log or CI run available.

---

## Addendum: Stage 1I-R1 Validator and Self-Test Evidence (2026-11-04)

### Validator

**File:** scripts/_r26i_validator.py (non-production audit helper)
**Parser:** Python ast module (not regex)
**Disclaimer:** Validates declaration mapping/schema ONLY. Does NOT prove assertion semantics, call paths, branch reachability, or acceptance coverage.

### Self-Test Command

`python scripts/_r26i_validator.py --self-test`

### Self-Test Output (exit code 0)

`
[PASS] valid_map_passes
[PASS] wrong_file_path_rejected
[PASS] wrong_class_rejected
[PASS] wrong_function_rejected
[PASS] wrong_declaration_line_rejected
[PASS] missing_id_rejected
[PASS] duplicate_id_rejected
[PASS] unknown_id_rejected
[PASS] malformed_none_row_rejected
[PASS] missing_source_file_rejected
[PASS] wrong_cardinality_rejected
[PASS] wrong_declaration_end_line_rejected
[PASS] invalid_evidence_type_rejected
[PASS] invalid_disposition_rejected
[PASS] missing_required_field_rejected

Total: 15 tests, 15 passed, 0 failed
Overall: ALL PASS
`

### Actual Map Validation

`python scripts/_r26i_validator.py --validate research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json --base-dir .`

Result: VALIDATION PASSED (42 findings, 39 mapped, 3 NONE, 218 declarations)

### Semantic Evidence Map

- JSON: research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json (schema_version 1.0)
- Markdown: research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md (1520 lines, 42 formal rows R12-R53)
- Dispositions computed from JSON: 26 VERIFIED_FIXED + 14 PARTIALLY_FIXED + 1 OPEN + 1 UNVERIFIABLE = 42
