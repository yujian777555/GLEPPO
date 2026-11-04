# R26 PC1 Test Evidence

**Date:** 2026-11-03
**Branch:** r25-handoff

## Test Execution

| Command | Result | Exit Code |
|---------|--------|-----------|
| `python -m unittest discover -s tests` | 450/450 PASS | 0 |

## Test Coverage by Finding Category

| Category | Findings | Test File | Tests |
|----------|----------|-----------|-------|
| Budget/CTX | R12, R21, R27, R28, R33 | test_c7.py | 17 |
| Seed/CRN | R16, R20, R32, R34, R39 | test_c7.py | 17 |
| Protocol | R19, R26, R36, R40, R45, R48, R49, R52, R53 | test_c7r1c2_protocol.py | 10 |
| Approval | R38, R42, R43, R46, R50 | test_c7.py | 17 |
| Provenance | R22, R29, R30, R35, R37, R41, R44, R47, R51 | test_c7.py | 17 |
| Runner | R15, R25, R31 | test_c7.py | 17 |
| Statistics | R13, R14 | test_c7.py | 17 |
| Evidence | R17, R23 | test_c7.py | 17 |
| Cost | R18, R24 | test_c7.py | 17 |

## Key Test Files

1. **tests/test_c7.py** — 17 tests covering Budget, Seed/CRN, Approval, Provenance, Runner
2. **tests/test_c7r1c2_protocol.py** — 10 tests covering Protocol consistency

## Evidence Standard

- Test names ≠ coverage (must inspect test bodies)
- Hash checks must compare actual bytes
- CRN must verify all seed components
- Approval must verify trusted artifact

---

## Planner correction — 2026-11-03

The Stage 1C mapping above is **not accepted as finding-level test coverage**.

- tests/test_c7.py has 17 tests for genotype/operator/crossover, answer formatting and evidence-presence behavior. It does not import gleppo.pc1 or gleppo.evaluator; it cannot support the mapped PC1 budget, CRN, statistics, provenance, approval or runner findings.
- tests/test_c7r1c2_protocol.py has 10 tests for scripts/protocol_hash.py text normalization and textual hash update/verification. It does not test gleppo.pc1.parse_protocol_document() or protocol_consistency_check().
- The 450/450 full-suite result is Executor-reported only. No raw stdout/stderr, saved log or CI run URL is attached. Planner has not independently reproduced it.
- scripts/_r26c_finding_verify.py does not execute tests. It only checks file existence and counts test-function declarations; it prints NEEDS_DETAILED_VERIFICATION.

Relevant PC1 test candidates that must be inspected by exact function and assertion include:
tests/test_r8_r9_r11_pc1.py, tests/test_r12_r17.py, tests/test_r19_r25.py, tests/test_r26_r32.py, tests/test_r33_r38.py, tests/test_r39_r42.py and tests/test_r54_r59.py.

Until Stage 1D supplies exact test-function-to-finding mappings and safe reproducible outputs, the Stage 1C test evidence cannot substantiate 42/42 VERIFIED_FIXED.

---

## Stage 1D Planner correction — 2026-11-04

The Stage 1D test inventory identifies seven PC1-related suites with 218 declared test functions. The number is an accurate source inventory count, not a 42-Finding coverage proof.

The Stage 1D per-Finding table maps only five Findings and uses abbreviated/nonexistent test names. It does not provide exact function/assertion/source-call mappings for all 42. The test-inspection helper counts names/imports but does not inspect semantic assertions.

The 450/450 result has no raw log and no Actions/check-run result for commit ca0c909. Keep it EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED.

See research/R26_STAGE1D_PLANNER_REVIEW.md. Stage 1E must complete the evidence reconciliation before acceptance.

---

## Stage 1E Planner correction — 2026-11-04

The 218 count is accepted as the number of declared test functions across seven PC1-related suites. It is not a Finding-level coverage proof.

The Stage 1E 42-row map uses class/function names that do not match actual declarations: only 3 mapped class names exist, only 1 mapped function name exists under a different class, and 0 class/function pairs match. The assertion column contains descriptions rather than actual assertions. Exact test paths, line ranges, source symbols and call paths are missing.

R24, R52 and R53 require disposition correction unless additional exact existing evidence is identified. See research/R26_STAGE1E_PLANNER_REVIEW.md and Stage 1F prompt planner/GLEPPO_R26_STAGE1F_EXECUTOR_PROMPT.md.

---

## Stage 1F Planner correction — 2026-11-04

The Stage 1F test map is not yet exact. Across the seven PC1 suites, 218 declared test methods is the correct inventory count. However, among 39 Finding rows claiming a test, only 5 class/function/file triplets match actual declarations; 34 function names are not declared in the stated class/file. The three NONE rows are R18, R45 and R46.

The extractor helper only inventories class/function declarations and does not validate the 42-row map or inspect assertions/call paths. The Stage 1F test-evidence document contains no complete 42-row assertion/source-call map.

See research/R26_STAGE1F_PLANNER_REVIEW.md. Stage 1G must correct the map and dispositions. 450/450 remains EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED.



---

## Stage 1G Planner correction — 2026-11-04

The 218 declared-method count and 42 distinct test classes are independently confirmed. However, only 37/39 claimed file/class/function/line mappings are exact; R31 and R49 function names are wrong.

The Stage 1G Assertion column contains generic descriptions, not assertion expressions. No source call paths, intended-branch checks, or uncovered acceptance conditions are supplied. R39's mapped test is tautological; R53's mapped test is unrelated to status/hash invariance. The helper script is an inventory extractor, not a semantic map validator.

450/450 remains EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED. See research/R26_STAGE1G_PLANNER_REVIEW.md. Stage 1H required.

---

## Stage 1H Planner correction — 2026-11-04

The 39 direct declaration mappings are exact, but the Stage 1H evidence file still contains only ID/File/Class/Function/Line/Evidence Type. It does not include actual assertions, source symbols/call paths, intended-branch analysis, or acceptance conditions proved/uncovered.

R53 is still mapped to test_mutation_seed_contract_fails (seed_schema mutation) rather than the related status-consistency test; that status test remains indirect and does not prove status-only hash invariance. R39 must cross-reference R16/R20 instrumented genotype tests. R18 requires complete manual unit/token/production-cost evidence.

450/450 remains EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED. See research/R26_STAGE1H_PLANNER_REVIEW.md. Stage 1I required.

