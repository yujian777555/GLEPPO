# R26 Stage 1I-R1 Corrective Report

**Date:** 2026-11-04
**Branch:** r25-handoff
**Stage 1I parent / pre-work HEAD:** e2cb353037368a82b5dd9c7b53a1d40f21425750
**Stage 1I Executor commit:** a1e6e65e671c876d028492bfed164205c54df08b
**Stage 1I Planner review commit:** dfd7ef909ba4ee97e01c4bb57b0177ae8869d61c
**Stage 1I-R1 parent:** 539f74d5c898abc144992fff4a413a30744c1cc9
**Stage 1I-R1 final commit:** (this commit)
**Main:** 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e (unchanged)

## Status

- Stage 1I: REQUEST_CHANGES (Planner decision, not yet accepted)
- Stage 1I-R1: executor corrective work complete, awaiting Planner independent review
- Next gate: Planner independent review of Stage 1I-R1 (not PC1, not protocol reconciliation)

## Work Package A — Semantic Evidence Map

Created both:
- `research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json` — canonical machine-readable source (schema_version 1.0)
- `research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md` — human-readable rendering (1520 lines, 42 formal rows)

### Map structure

- 42 Finding objects (R12 through R53), each appearing exactly once
- No unknown IDs, no duplicate IDs, no missing IDs
- Each Finding contains all 13 required fields:
  `id`, `original_review_document`, `original_finding_heading`, `original_failure_mode`,
  `complete_original_acceptance_criteria`, `test_evidence`, `manual_evidence`,
  `evidence_type`, `disposition`, `proven_acceptance_conditions`,
  `indirectly_supported_conditions`, `uncovered_acceptance_conditions`, `disposition_rationale`

### Test evidence entries (40 entries across 39 mapped rows)

Each test_evidence entry contains all 13 required fields:
- `test_file` (normalized repository-relative)
- `test_class`, `test_function`
- `declaration_start_line`, `declaration_end_line` (exact, from AST extraction)
- `assertion_expressions` (array of {line, expression} from AST)
- `source_symbols` (array with symbol name, file, start_line, end_line)
- `call_path` (concrete test-to-source call path)
- `branch_reached` ({reached: bool, explanation: str})
- `acceptance_conditions_proven`, `acceptance_conditions_indirect`, `acceptance_conditions_uncovered`
- `harness_type` (production_path | stub_or_mock)

### Disposition counts (computed mechanically from JSON)

| Disposition | Count |
|---|---|
| VERIFIED_FIXED | 26 |
| PARTIALLY_FIXED | 14 |
| OPEN | 1 |
| UNVERIFIABLE | 1 |
| **Total** | **42** |

Arithmetic: 26 + 14 + 1 + 1 = 42.

These counts were re-evaluated row-level against complete original acceptance criteria.
They match the prior reported counts, but now have per-row support in the JSON map.

### Rows without test mapping (NONE)

- R18 (MANUAL): cost baseline reconciliation — 13 manual evidence entries with exact source/line/value/note
- R45 (NONE): no test evidence available
- R46 (UNVERIFIABLE): no independent trust-anchor provenance

## Mandatory R53 Semantics

- Correct evidence: `tests/test_r39_r42.py::TestR40ProtocolConsistency::test_mutation_status_not_checked_by_consistency` (line 118)
- This is INDIRECT evidence for lifecycle-status handling by the consistency predicate
- It does NOT prove `compute_protocol_hash()` is invariant to status-only changes
- Tenth Review states `compute_protocol_hash(doc)` hashes the entire parsed JSON dictionary including status
- No direct status-only hash-invariance test exists
- R53 remains PARTIALLY_FIXED. Tests not modified.

## Mandatory R39 Semantics

The map distinguishes:
- **Direct CRN encoding tests:** delimiter collision, task/state/rollout/replicate field isolation, NONE/EMPTY distinctions (7 tests in `TestR39CRNSeed`)
- **R16/R20 instrumented evaluator tests:** `test_same_crn_tuple_gives_identical_seeds_across_genotypes` in both `test_r8_r9_r11_pc1.py` and `test_r19_r25.py`, comparing seed logs for two distinct genotypes under same task/state/rollout/replicate tuple
- **Structural evidence:** `effective_seed_parts()` (gleppo/evaluator.py:57-76) does not accept action or genotype; action exclusion structurally supported
- **Tautological test:** `test_action_genotype_excluded` (line 96-99) compares same `crn_seed()` call to itself — NOT cited as evidence
- **Operator RNG note:** `test_operator_rng_independent_of_eval_seed` changes draw index and checks inequality — does not directly prove independence from evaluation seed
- **Registered PC1 collector:** not implemented/executed; no action-varying integration test exists

R39 disposition: VERIFIED_FIXED (delimiter safety, tuple reproduction, component isolation directly tested; action/genotype exclusion structurally supported + behaviorally cross-verified via R16/R20).

## Mandatory R18 Manual Evidence

Complete references included:
- SMOKE_RAW.json: lines 276, 277-279, 284, 291, 293
- COST_BASELINE.md: lines 4, 22, 30, 44, 47, 82, 101, 110-111

Explicit distinction: planned replica slots vs actual uncached replica executions vs cached evaluation bundles vs actual model CTX vs production tokens/latency. UNMEASURED preserved.

## Work Package B — Validator

Replaced `scripts/_r26i_validator.py` with AST-based validator (non-production audit helper).

### Features
- CLI: `--validate <map.json> [--base-dir <dir>]` and `--self-test`
- Parses test declarations using Python `ast` module (not regex)
- Keys: (normalized file path, class name, function name) with exact start/end lines
- Fails on missing/unreadable test source files
- Requires exact ID set R12-R53 exactly once (rejects duplicates, missing, unknown)
- Verifies exact declaration line(s) for mapped tests
- Rejects duplicate/ambiguous class/function declarations
- NONE rows: requires empty test_evidence + MANUAL/NONE evidence type + non-empty rationale
- Enforces 39 mapped / 3 NONE cardinality
- Validates required fields and allowed enums
- Prints machine-readable JSON summary + human-readable diagnostics
- Disclaimer: verifies declaration mapping/schema ONLY

### Self-test results (15 adversarial cases)

```
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
```

Command: `python scripts/_r26i_validator.py --self-test`
Exit code: 0

### Actual map validation

Command: `python scripts/_r26i_validator.py --validate research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json --base-dir .`
Result: VALIDATION PASSED (42 findings, 39 mapped, 3 NONE, 218 declarations)

## Work Package C — Durable Records

Updated:
- `research/R26_STAGE1I_FINAL_FINDING_AUDIT.md` — dated addendum linking to R1 corrective report
- `research/R26_STAGE1I_TEST_EVIDENCE.md` — validator/self-test evidence
- `research/R26_PC1_AUDIT_SUMMARY.md` — Stage 1I-R1 status
- `planner/latest_plan.md` — Stage 1I-R1 corrective work
- `planner/GLEPPO_R26_HANDOFF.md` — R1 status
- `planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md` — next gate
- `status.json` — complete Stage 1I and R1 objects

## Unresolved Issues

1. 450/450 test result is EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED (no raw log/CI)
2. Model/API calls (0) and production runtime calls (0) are Executor attestations
3. R21-C1 is DAC comparison, not operator comparison — must not be cited as operator selection evidence
4. PPO superiority over fixed/rule/LinUCB remains untested
5. Phase 1/R24/PC1 R4 reward/state/gamma/split/budget discrepancies remain unresolved
6. R15 OPEN: PC1 runner not implemented
7. R46 UNVERIFIABLE: no independent trust-anchor provenance

## Hard Boundary Attestation

| Item | Status |
|---|---|
| Production source changes | NONE |
| Test suite changes | NONE |
| Registered PC1 execution | NOT EXECUTED |
| Family C access | NOT ACCESSED |
| Controller training | NOT AUTHORIZED / NOT STARTED |
| Formal G3 efficacy | FAIL |
| External model/API calls | 0 (Executor-reported) |
| Production runtime calls | 0 (Executor-reported) |
| Main branch modified | NO |

Independently verifiable (from repository): map content, validator behavior, test declarations, source structure.
Executor-reported (not independently verifiable): model/API call count, production runtime call count, 450/450 test result.

---

## Planner provenance correction (2026-11-04)

The Executor report above uses “(this commit)” for the Stage 1I-R1 final commit. The exact verified value is:

- R1 source snapshot: 29325cfa16441154c833f381f208747b57627a79
- R1 parent: 539f74d5c898abc144992fff4a413a30744c1cc9
- R1 final commit: 4d2ff06ee01146533501589b264d33ddd30ffcbe
- R1 Planner review commit: dcdcef5b2e7e68a6590d95c90c4caf453399c127

This provenance correction does not imply Planner acceptance. Stage 1I-R1 remains REQUEST_CHANGES. See research/R26_STAGE1I_R1_PLANNER_REVIEW.md.

