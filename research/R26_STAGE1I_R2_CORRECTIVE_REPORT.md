# R26 Stage 1I-R2 Corrective Report

**Date:** 2026-11-04
**Branch:** r25-handoff

## Provenance

| Item | SHA |
|---|---|
| R1 source snapshot | 29325cfa16441154c833f381f208747b57627a79 |
| R1 parent | 539f74d5c898abc144992fff4a413a30744c1cc9 |
| R1 final commit | 4d2ff06ee01146533501589b264d33ddd30ffcbe |
| R1 Planner review commit | dcdcef5b2e7e68a6590d95c90c4caf453399c127 |
| R2 parent | 3d97847adf6f68dafe1f54855d27fe00e99e16ae |
| R2 final commit | 34ba848c4b8cf4fa07c9583e049b0bb7b0635aab |
| Main | 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e |

## Status

- Stage 1I: REQUEST_CHANGES (not accepted)
- Stage 1I-R1: REQUEST_CHANGES (not accepted)
- Stage 1I-R2: executor corrective work complete, awaiting Planner independent review
- Next gate: Planner independent review of Stage 1I-R2

## Work Package A — Corrected 42-Finding Map

### Changes from R1

**Acceptance criteria expanded** for all 42 rows. Multi-part requirements no longer compressed. Key expansions:
- R39: Added explicit schema/version tag requirement, canonical contract confirmation for all call sites
- R50: Added signed payload fields, independent trust-anchor, gate consumption, approved-path limitation
- R51: Added plan ID, version, canonical mapping hash, protocol-content binding, E2E registered-analysis requirements
- R44: Distinguished artifact path requirement, actual artifact loading, record validation against exact artifact

**Test evidence expanded** from 40 to 193 entries (across 39 mapped rows). Key additions per Planner F1:
- R12: +5 tests (cache_hit, shared_evaluator_deltas, multiple_generations, planned_independent, invalid_offspring)
- R14: +2 tests (test_r_hat_includes_extra_immediate, test_extra_immediate_does_not_pollute_q_hat)
- R17: +1 test (test_evidence_records_have_required_fields); source symbols corrected
- R20: +4 tests (task/rollout/replicate isolation, override_path); crn_seed location corrected
- R23: +1 test (test_round_trip_serialize_replay); source symbols corrected
- R26: +4 tests (document_fields_match_code, document_says_proposed, code_version_not_frozen, status_is_proposed)
- R28: +2 tests (test_ledger_components_sum_to_total for reconcile); noted constants-only test
- R30: +3 tests (missing_runtime, missing_evaluator); call path corrected to run_pc1_analysis
- R37: +3 tests (missing_plan_hash, wrong_protocol_hash, wrong_plan_hash); call path corrected
- R39: +6 tests (all 7 direct CRN tests + R16/R20 cross-genotype)
- R40: +4 tests (mutation_version/status/seed/reward)
- R41: +3 tests (tampered, defensive_copy, wrong_hash)
- R22/R29/R33/R35/R42: Added all relevant multi-part tests

**Source symbols corrected** (Planner F2/F3):
- R17/R23: build_evidence/save_evidence/replay_evidence → run_pc1_analysis/save_evidence_artifact/replay_from_artifact
- R20: crn_seed location corrected to gleppo/pc1.py:230-239 (not evaluator.py)
- R25: GatedPC1Runner → SyntheticGateHarness/create_default_gated_runner
- R28: test_registered_budget_exact noted as constants-only (does NOT call reconcile)
- R30/R37: Call path corrected to run_pc1_analysis early guards (not validate_records)
- R38: branch_reached=false with explanation naming early PROPOSED status guard
- R44: Isolated loader test identified as NOT E2E; source cited as MANUAL evidence
- R47: Call path corrected to hash comparison branch (not ID/version)
- R50: test_wrong_protocol_hash calls art.verify() not ApprovalGate.check(); separate tests documented
- R51: test_registered_hash_matches_computed is protocol hash NOT plan hash
- R52: validate_reward_schema → protocol_consistency_check + _check_exact_keys + _is_strict_number

**Null source ranges eliminated:** 0 null start_line/end_line in final map.

**Disposition re-evaluation** (from JSON mechanically):
| Disposition | Count |
|---|---|
| VERIFIED_FIXED | 28 |
| PARTIALLY_FIXED | 12 |
| OPEN | 1 |
| UNVERIFIABLE | 1 |
| **Total** | **42** |

Changed from R1's 26/14/1/1:
- R12, R17(uncovered noted), R26, R28, R40, R44(→PARTIALLY_FIXED): upgraded after complete test evidence
- R43, R47, R49, R50, R51: remain PARTIALLY_FIXED with corrected evidence
- R52: PARTIALLY_FIXED (was already)

R53 remains PARTIALLY_FIXED (INDIRECT only). R18 MANUAL. R46 UNVERIFIABLE. R15 OPEN.

## Work Package B — Validator Hardening

Rewrote `scripts/_r26i_validator.py` with:
- schema_version validation (must be 1.0)
- Field type validation (positive integers for lines, non-bool)
- Source symbol validation (file exists, lines valid, range within file)
- assertion_expressions structure validation
- branch_reached (bool + nonempty explanation)
- harness_type enum validation
- manual_evidence structure validation
- NONE row semantics enforcement
- Targeted error categories (TE_WRONG_OWNER, SRC_RANGE_INVALID, etc.)

### Self-test results (20 adversarial cases)

```
[PASS] valid_map_passes
[PASS] wrong_file_owner_rejected (existing file, wrong class/function)
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

Total: 20 tests, 20 passed, 0 failed
Overall: ALL PASS
```

Command: `python scripts/_r26i_validator.py --self-test` — exit code 0
Map validation: `python scripts/_r26i_validator.py --validate research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json --base-dir .` — VALIDATION PASSED

## Work Package C — Durable Records

Updated: FINAL_FINDING_AUDIT.md (addendum), TEST_EVIDENCE.md, PC1_AUDIT_SUMMARY.md, latest_plan.md, HANDOFF.md, NEXT_SESSION_PROMPT.md, status.json.

## Unresolved Issues

1. 450/450 EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED
2. Model/API calls (0) and production runtime (0) are Executor attestations
3. R21-C1 is DAC, not operator comparison
4. PPO superiority untested
5. Phase 1/R24/PC1 R4 protocol discrepancies unresolved
6. R15 OPEN (PC1 runner not implemented)
7. R46 UNVERIFIABLE (no trust-anchor provenance)

## Hard Boundary Attestation

No production source changes. No tests/ changes. No PC1. No Family C. No controller training. No Formal G3. No model/API calls. No main modification.

## Planner Independent Review Addendum

Planner decision: **REQUEST_CHANGES**. The R2 structural improvements are accepted, but R39, R41 and R48 are overclassified as VERIFIED_FIXED. A narrow R2.1 correction is required; see `research/R26_STAGE1I_R2_PLANNER_REVIEW.md` and `planner/GLEPPO_R26_STAGE1I_R2_1_CORRECTIVE_EXECUTOR_PROMPT.md`.

The 28/12/1/1 counts remain Executor-reported and are not accepted. Expected corrected counts are 25/15/1/1 after downgrading R39, R41 and R48. The 450/450 suite and 20/20 helper tests remain Executor-reported, not independently reproduced.

