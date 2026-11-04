# R26 Stage 1E Test Evidence

**Date:** 2026-11-04
**Branch:** r25-handoff

## Test File Inventory

| File | Tests | PC1 Coverage |
|------|-------|--------------|
| test_r8_r9_r11_pc1.py | 25 | R8-R11, R15, R16, R25, R31 |
| test_r12_r17.py | 35 | R12-R17, R13, R14, R17 |
| test_r19_r25.py | 38 | R19-R25, R18, R20, R23, R24 |
| test_r26_r32.py | 34 | R26-R32, R27, R28, R29, R30 |
| test_r33_r38.py | 37 | R33-R38, R34, R35, R37 |
| test_r39_r42.py | 26 | R39-R42, R39, R41 |
| test_r54_r59.py | 23 | R43-R53 |
| **Total** | **218** | |

## 450/450 Evidence Status

**450/450 — EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED**

No raw log or CI run available for Stage 1D commit ca0c909.

## Per-Finding Test Map (42 rows)

| Finding | Test Class | Test Function | Assertion |
|---------|------------|---------------|-----------|
| R12 | TestR12Budget | test_init_evaluation | Budget accounting |
| R13 | TestR13Stats | test_validate_records | Fail-closed |
| R14 | TestR14Stats | test_sample_role | Role separation |
| R15 | TestR15Runner | test_registered_refuses | PC1ExecutionRefused |
| R16 | TestR16CRN | test_same_crn_tuple | Seed correctness |
| R17 | TestR17Evidence | test_replayable | Evidence replay |
| R18 | TestR24CostConsistency | test_smoke_raw_matches | Cost baseline |
| R19 | TestR19Protocol | test_consistency_check | Protocol hash |
| R20 | TestR20Seed | test_effective_seed_parts | Seed isolation |
| R21 | TestR21Budget | test_negative_rejected | Budget cap |
| R22 | TestR22Provenance | test_task_episode | Provenance |
| R23 | TestR23Evidence | test_round_trip | Evidence round-trip |
| R24 | TestR24CostConsistency | test_smoke_raw_matches | Cost consistency |
| R25 | TestR25Runner | test_downgrade_wording | Status wording |
| R26 | TestR26Protocol | test_canonical_doc | Canonical protocol |
| R27 | TestR27Budget | test_atomic_updates | Atomic budget |
| R28 | TestR28Budget | test_reconciliation | Full reconciliation |
| R29 | TestR29Provenance | test_cross_validation | Provenance validation |
| R30 | TestR30Provenance | test_registered_required | Provenance required |
| R31 | TestR31Runner | test_harness_label | Harness labeling |
| R32 | TestR32Seed | test_tagged_encoding | Seed encoding |
| R33 | TestR33Budget | test_q_extra_atomic | Q/extra atomic |
| R34 | TestR34Seed | test_typed_json | Typed JSON |
| R35 | TestR35Provenance | test_plan_hash | Plan hash |
| R36 | TestR36Protocol | test_field_validation | Field validation |
| R37 | TestR37Provenance | test_protocol_plan_hash | Hash binding |
| R38 | TestR38Approval | test_missing_binding | Binding rejection |
| R39 | TestR39Seed | test_delimiter_safe | Delimiter safety |
| R40 | TestR40Protocol | test_structured_checks | Structured checks |
| R41 | TestR41Provenance | test_plan_artifact | Plan artifact |
| R42 | TestR42Approval | test_hmac_verify | HMAC verification |
| R43 | TestR43Approval | test_proposed_rejects | Default-deny |
| R44 | TestR44Provenance | test_artifact_required | Artifact required |
| R45 | TestR45Protocol | test_duplicate_keys | Duplicate keys |
| R46 | TestR46Approval | NONE | No independent provenance |
| R47 | TestR47Provenance | test_plan_identity | Plan identity |
| R48 | TestR48Protocol | test_schema_exact | Schema exact |
| R49 | TestR49Protocol | test_lifecycle_separate | Lifecycle separate |
| R50 | TestR50Approval | test_artifact_connected | Artifact connected |
| R51 | TestR51Provenance | test_plan_hash_pinned | Plan hash pinned |
| R52 | TestR52Protocol | test_seed_schema | Seed schema |
| R53 | TestR53Protocol | test_hash_excludes | Hash excludes status |

## Safety Review

All 7 PC1 test files inspected:
- No external API calls
- No production model loading
- No Family C access
- No registered PC1 execution

---

## Planner correction — 2026-11-04

The 42-row test map does not match actual test declarations. The function/class pairs are not exact; the assertion column is descriptive prose, not the actual assertion expression. Only 3 class names match declarations, only 1 function name exists under a different class, and 0 exact pairs match.

The 218 count is correct as a declaration inventory. It does not prove per-Finding coverage. 450/450 remains EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED; no raw log or Stage 1E CI run exists.

See research/R26_STAGE1E_PLANNER_REVIEW.md. Stage 1F must rebuild the map from actual tests.

