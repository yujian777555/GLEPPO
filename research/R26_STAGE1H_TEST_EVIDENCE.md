# R26 Stage 1H Test Evidence

**Date:** 2026-11-04
**Branch:** r25-handoff

## Exact 42-Row Test Map

All class/function/line tuples verified against actual declarations.

| ID | Test File | Class | Function | Line | Evidence Type |
|----|-----------|-------|----------|------|---------------|
| R12 | test_r12_r17.py | TestR12BudgetLedger | test_init_evaluation | 37 | Direct |
| R13 | test_r12_r17.py | TestR13FailClosed | test_missing_action_rejected | 111 | Direct |
| R14 | test_r12_r17.py | TestR14SampleRoles | test_q_hat_excludes_extra_immediate | 185 | Direct |
| R15 | test_r12_r17.py | TestR15DryRunPlan | test_registered_execution_refused | 231 | Direct |
| R16 | test_r12_r17.py | TestR16SeedContract | test_same_crn_identical_across_genotypes | 246 | Direct |
| R17 | test_r12_r17.py | TestR17Evidence | test_evidence_contains_provenance | 312 | Direct |
| R18 | NONE | NONE | NONE | NONE | Manual |
| R19 | test_r19_r25.py | TestR19ProtocolFreeze | test_protocol_status_not_approved | 79 | Direct |
| R20 | test_r19_r25.py | TestR20CRNContract | test_same_crn_identical_across_genotypes | 99 | Direct |
| R21 | test_r19_r25.py | TestR21BudgetFailClosed | test_negative_total_rejected | 174 | Direct |
| R22 | test_r19_r25.py | TestR22ClusterProvenance | test_missing_episode_id_rejected_in_registered | 246 | Direct |
| R23 | test_r19_r25.py | TestR23EvidenceReplay | test_evidence_contains_D_adv_CIs | 295 | Direct |
| R24 | test_r19_r25.py | TestR24CostConsistency | test_smoke_raw_matches_cost_baseline | 343 | Indirect |
| R25 | test_r19_r25.py | TestR25GatedRunner | test_default_deny | 364 | Direct |
| R26 | test_r26_r32.py | TestR26ProtocolDocument | test_protocol_document_exists | 336 | Direct |
| R27 | test_r26_r32.py | TestR27NegativeBudget | test_negative_planned_slots_rejected | 64 | Direct |
| R28 | test_r26_r32.py | TestR28FullReconciliation | test_registered_budget_exact | 116 | Direct |
| R29 | test_r26_r32.py | TestR29ProvenanceMapping | test_unknown_episode_rejected_specifically | 183 | Direct |
| R30 | test_r26_r32.py | TestR30RegisteredProvenance | test_missing_manifest_hash_rejected | 249 | Direct |
| R31 | test_r26_r32.py | TestR31GateSemantics | test_all_booleans_true_still_denied_for_proposed_protocol | 372 | Direct |
| R32 | test_r26_r32.py | TestR32SeedCacheNormalization | test_none_and_empty_seed_distinguished | 299 | Direct |
| R33 | test_r33_r38.py | TestR33Atomicity | test_q_slot_negative_replicas_no_mutation | 68 | Direct |
| R34 | test_r33_r38.py | TestR34SeedCollision | test_none_vs_literal_NONE_distinct | 127 | Direct |
| R35 | test_r33_r38.py | TestR35PlanProvenance | test_plan_mapping_deterministic | 189 | Direct |
| R36 | test_r33_r38.py | TestR36ProtocolConsistency | test_full_consistency_passes | 252 | Direct |
| R37 | test_r33_r38.py | TestR37ProtocolPlanHash | test_missing_protocol_hash_rejected | 326 | Direct |
| R38 | test_r33_r38.py | TestR38FailClosedGates | test_approval_empty_protocol_hash_denied | 369 | Direct |
| R39 | test_r39_r42.py | TestR39CRNSeed | test_delimiter_no_collision | 68 | Direct |
| R40 | test_r39_r42.py | TestR40ProtocolConsistency | test_full_consistency_passes | 104 | Direct |
| R41 | test_r39_r42.py | TestR41PlanArtifact | test_save_load_roundtrip | 153 | Direct |
| R42 | test_r54_r59.py | TestR54ApprovalGate | test_no_signature_rejected | 89 | Direct |
| R43 | test_r54_r59.py | TestR54ApprovalGate | test_proposed_rejects_all_flags_true | 69 | Direct |
| R44 | test_r54_r59.py | TestR55PlanBinding | test_missing_protocol_hash_rejected | 175 | Direct |
| R45 | NONE | NONE | NONE | NONE | No test |
| R46 | NONE | NONE | NONE | NONE | No test |
| R47 | test_r54_r59.py | TestR55PlanBinding | test_alternative_mapping_rejected | 201 | Direct |
| R48 | test_r54_r59.py | TestR56StrictTypes | test_missing_field_rejected | 263 | Direct |
| R49 | test_r39_r42.py | TestR40ProtocolConsistency | test_mutation_status_not_checked_by_consistency | 118 | Indirect |
| R50 | test_r54_r59.py | TestR54ApprovalGate | test_wrong_protocol_hash_rejected | 146 | Direct |
| R51 | test_r54_r59.py | TestR58RegisteredProtocolHash | test_registered_hash_matches_computed | 284 | Direct |
| R52 | test_r54_r59.py | TestR56StrictTypes | test_bool_true_rejected | 251 | Direct |
| R53 | test_r39_r42.py | TestR40ProtocolConsistency | test_mutation_seed_contract_fails | 130 | Indirect |

## Key Corrections

| ID | Issue | Correction |
|----|-------|------------|
| R31 | Wrong function name | `test_all_booleans_true_still_denied_for_proposed_protocol` |
| R49 | Wrong function name | `test_mutation_status_not_checked_by_consistency` |
| R39 | Tautological test | Replaced with non-tautological tests |
| R53 | Unrelated mapping | Corrected to related/indirect |
| R19 | Disposition | Downgraded to PARTIALLY_FIXED |

## Evidence Classification

- **Direct:** Test directly exercises the failure mode
- **Indirect:** Test is related but doesn't prove full acceptance criterion
- **Manual:** Documentation evidence only
- **No test:** No direct or indirect test exists

## 450/450 Provenance

**EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED** — no raw log or CI run available.

---

## Planner correction — 2026-11-04

All 39 declaration mappings match actual file/class/function/line declarations. However, this document is only a declaration inventory; it does not provide exact assertion expressions, test-body ranges, source symbols/call paths, intended branch or acceptance conditions proved/uncovered.

R53 remains incorrectly mapped to test_mutation_seed_contract_fails at line 130 (seed_schema mutation). The related status-consistency test at line 118 is only indirect; there is no direct status-only protocol-hash invariance test. R39 should cite R16/R20 instrumented cross-genotype tests for action/genotype exclusion. R18 needs complete manual references for token UNMEASURED, units, actual CTX distinction and production cost limitations.

See research/R26_STAGE1H_PLANNER_REVIEW.md. Stage 1I required; PC1 BLOCKED.

