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

---

## Planner Review of Stage 1I-R1 Evidence (2026-11-04)

**Decision: REQUEST_CHANGES — R1 NOT ACCEPTED.**

The Executor-reported validator output is not sufficient to accept the semantic map. Static review found:
- missing relevant tests for multiple multi-part Findings;
- false call paths for R28, R30, R37, R44, R47, R50 and R51;
- nonexistent/wrong source symbols in R17, R20, R23, R25, R48 and R52;
- 12 null source-symbol ranges that the validator does not inspect;
- a wrong_file_path self-test that points to a nonexistent file and duplicates missing_source_file;
- null declaration line values bypass exact-line checks.

The map's 42 IDs and Markdown/JSON disposition consistency are verified. The 26/14/1/1 arithmetic is mechanically correct, but semantic dispositions are not accepted.

Planner did not execute the helper or 450-test suite. The 15 self-tests and 450/450 remain EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED.

See research/R26_STAGE1I_R1_PLANNER_REVIEW.md and execute Stage 1I-R2 from planner/GLEPPO_R26_STAGE1I_R2_CORRECTIVE_EXECUTOR_PROMPT.md.


---

## Addendum: Stage 1I-R2 Validator Evidence (2026-11-04)

Validator: scripts/_r26i_validator.py (AST-based, hardened)
Self-test: 20 adversarial cases, ALL PASS, exit code 0
Map validation: PASSED (42 findings, 39 mapped, 3 NONE, 218 declarations)
Semantic map: 193 test_evidence entries, 0 null source ranges
Dispositions from JSON: 28/12/1/1 = 42

---

## R2.1 Validator Evidence (2026-11-04)

Self-test: 21/21 PASS (exit code 0). New: end_line_beyond_eof_rejected with SRC_RANGE_END_OUT_OF_FILE diagnostic.
Map validation: PASSED (42 findings, 39 mapped, 3 NONE).
Dispositions: 25/15/1/1 = 42 (mechanically derived).

---

## R2.1.1 Validator Self-Test Evidence (2026-11-05)

**Command:** `python scripts/_r26i_validator.py --self-test`
**Captured by:** Executor (not independently reproduced by Planner; no CI run available)
**Exit code:** 0

**Actual stdout (verbatim):**

`
======================================================================
R26 Stage 1I-R2 Validator Self-Test Results
======================================================================
  [PASS] valid_map_passes
  [PASS] wrong_file_owner_rejected
  [PASS] wrong_class_rejected
  [PASS] wrong_function_rejected
  [PASS] wrong_start_line_rejected
  [PASS] null_start_line_rejected
  [PASS] null_end_line_rejected
  [PASS] null_src_start_rejected
  [PASS] wrong_src_range_rejected
  [PASS] missing_id_rejected
  [PASS] duplicate_id_rejected
  [PASS] unknown_id_rejected
  [PASS] malformed_none_rejected
  [PASS] missing_file_rejected
  [PASS] wrong_cardinality_rejected
  [PASS] invalid_schema_rejected
  [PASS] invalid_branch_rejected
  [PASS] invalid_harness_rejected
  [PASS] empty_assertion_rejected
  [PASS] invalid_evidence_type_rejected
  [PASS] end_line_beyond_eof_rejected

Total: 21 tests, 21 passed, 0 failed
Overall: ALL PASS
`

Note: This is Executor-captured output. The Planner statically inspected the validator but did not independently execute the self-test.
