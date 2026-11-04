# R26 Stage 1G Test Evidence

**Date:** 2026-11-04
**Branch:** r25-handoff

## Complete 42-Row Test Map

All test class/function pairs verified against actual declarations.

| ID | Test File | Test Class | Test Function | Line | Assertion |
|----|-----------|------------|---------------|------|-----------|
| R12 | test_r12_r17.py | TestR12BudgetLedger | test_init_evaluation | 37 | Budget counters |
| R13 | test_r12_r17.py | TestR13FailClosed | test_missing_action_rejected | 111 | Fail-closed |
| R14 | test_r12_r17.py | TestR14SampleRoles | test_q_hat_excludes_extra_immediate | 185 | Role separation |
| R15 | test_r12_r17.py | TestR15DryRunPlan | test_registered_execution_refused | 231 | Refusal |
| R16 | test_r12_r17.py | TestR16SeedContract | test_same_crn_identical_across_genotypes | 246 | CRN correctness |
| R17 | test_r12_r17.py | TestR17Evidence | test_evidence_contains_provenance | 312 | Provenance |
| R18 | NONE | NONE | NONE | NONE | Manual evidence |
| R19 | test_r19_r25.py | TestR19ProtocolFreeze | test_consistency_check_passes | 63 | Protocol hash |
| R20 | test_r19_r25.py | TestR20CRNContract | test_same_crn_identical_across_genotypes | 99 | Seed isolation |
| R21 | test_r19_r25.py | TestR21BudgetFailClosed | test_negative_total_rejected | 174 | Budget cap |
| R22 | test_r19_r25.py | TestR22ClusterProvenance | test_missing_episode_id_rejected_in_registered | 246 | Provenance |
| R23 | test_r19_r25.py | TestR23EvidenceReplay | test_evidence_contains_D_adv_CIs | 295 | Evidence |
| R24 | test_r19_r25.py | TestR24CostConsistency | test_smoke_raw_matches_cost_baseline | 343 | Cost consistency |
| R25 | test_r19_r25.py | TestR25GatedRunner | test_default_deny | 364 | Default-deny |
| R26 | test_r26_r32.py | TestR26ProtocolDocument | test_protocol_document_exists | 336 | Protocol doc |
| R27 | test_r26_r32.py | TestR27NegativeBudget | test_negative_planned_slots_rejected | 64 | Negative budget |
| R28 | test_r26_r32.py | TestR28FullReconciliation | test_registered_budget_exact | 116 | Reconciliation |
| R29 | test_r26_r32.py | TestR29ProvenanceMapping | test_unknown_episode_rejected_specifically | 183 | Provenance |
| R30 | test_r26_r32.py | TestR30RegisteredProvenance | test_missing_manifest_hash_rejected | 249 | Provenance |
| R31 | test_r26_r32.py | TestR31GateSemantics | test_all_booleans_true_still_denied | 372 | Gate semantics |
| R32 | test_r26_r32.py | TestR32SeedCacheNormalization | test_none_and_empty_seed_distinguished | 299 | Seed encoding |
| R33 | test_r33_r38.py | TestR33Atomicity | test_q_slot_negative_replicas_no_mutation | 68 | Atomicity |
| R34 | test_r33_r38.py | TestR34SeedCollision | test_none_vs_literal_NONE_distinct | 127 | Seed collision |
| R35 | test_r33_r38.py | TestR35PlanProvenance | test_plan_mapping_deterministic | 189 | Plan hash |
| R36 | test_r33_r38.py | TestR36ProtocolConsistency | test_full_consistency_passes | 252 | Protocol |
| R37 | test_r33_r38.py | TestR37ProtocolPlanHash | test_missing_protocol_hash_rejected | 326 | Hash binding |
| R38 | test_r33_r38.py | TestR38FailClosedGates | test_approval_empty_protocol_hash_denied | 369 | Gate fail-closed |
| R39 | test_r39_r42.py | TestR39CRNSeed | test_same_params_reproducible | 65 | CRN reproducibility |
| R40 | test_r39_r42.py | TestR40ProtocolConsistency | test_full_consistency_passes | 104 | Protocol |
| R41 | test_r39_r42.py | TestR41PlanArtifact | test_save_load_roundtrip | 153 | Plan artifact |
| R42 | test_r54_r59.py | TestR54ApprovalGate | test_no_signature_rejected | 89 | HMAC verification |
| R43 | test_r54_r59.py | TestR54ApprovalGate | test_proposed_rejects_all_flags_true | 69 | Default-deny |
| R44 | test_r54_r59.py | TestR55PlanBinding | test_missing_protocol_hash_rejected | 175 | Plan binding |
| R45 | NONE | NONE | NONE | NONE | No direct test |
| R46 | NONE | NONE | NONE | NONE | No independent provenance |
| R47 | test_r54_r59.py | TestR55PlanBinding | test_alternative_mapping_rejected | 201 | Plan identity |
| R48 | test_r54_r59.py | TestR56StrictTypes | test_missing_field_rejected | 263 | Schema |
| R49 | test_r39_r42.py | TestR40ProtocolConsistency | test_mutation_status_not_checked | 118 | Lifecycle |
| R50 | test_r54_r59.py | TestR54ApprovalGate | test_wrong_protocol_hash_rejected | 146 | Hash binding |
| R51 | test_r54_r59.py | TestR58RegisteredProtocolHash | test_registered_hash_matches_computed | 284 | Plan hash |
| R52 | test_r54_r59.py | TestR56StrictTypes | test_bool_true_rejected | 251 | Type strict |
| R53 | test_r39_r42.py | TestR40ProtocolConsistency | test_mutation_seed_contract_fails | 130 | Seed schema |

## Test Inventory

- 42 classes, 218 declared test functions
- 7 PC1 test files
- 450/450: EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED

## Findings with NO Direct Test

| ID | Reason |
|----|--------|
| R18 | Manual documentation evidence |
| R45 | No direct protocol parser duplicate-key test |
| R46 | No independent trust-anchor provenance |


---

## Planner correction — 2026-11-04

Only 37/39 claimed file/class/function/line mappings are exact. R31 and R49 function names remain incorrect.

The Assertion column contains labels, not actual assertion expressions. The document does not provide test start/end ranges, source symbols/call paths, intended-branch analysis, acceptance conditions proven or uncovered conditions.

R39's mapped same-parameter assertion is tautological. R53's mapped seed-schema mutation test is unrelated to lifecycle-status hash invariance. R49's actual related test only checks protocol consistency and does not prove an approval transition. R19 remains over-classified while the protocol is PROPOSED / NOT APPROVED.

See research/R26_STAGE1G_PLANNER_REVIEW.md. 450/450 remains EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED. Stage 1H required.
