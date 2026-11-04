# R26 Stage 1G Final Finding Audit

**Date:** 2026-11-04
**Branch:** r25-handoff
**SOURCE_SNAPSHOT:** 29325cfa16441154c833f381f208747b57627a79
**REPORT_COMMIT:** (this commit)
**CURRENT_BRANCH_HEAD:** (this commit)

## 1. Corrected Disposition Counts

From 42 rows in Stage 1F detailed table:
- **VERIFIED_FIXED: 27**
- **PARTIALLY_FIXED: 13**
- **OPEN: 1** (R15)
- **UNVERIFIABLE: 1** (R46)
- **Total: 42**

Stage 1F summary said 22/15/1/1 = 39 (WRONG). Corrected to 27/13/1/1 = 42.

## 2. Complete 42-Finding Register

| ID | Category | Source | Test File | Test Class | Test Function | Line | Disposition |
|----|----------|--------|-----------|------------|---------------|------|-------------|
| R12 | Budget | pc1.py | test_r12_r17.py | TestR12BudgetLedger | test_init_evaluation | 37 | VERIFIED_FIXED |
| R13 | Statistics | pc1.py | test_r12_r17.py | TestR13FailClosed | test_missing_action_rejected | 111 | VERIFIED_FIXED |
| R14 | Statistics | pc1.py | test_r12_r17.py | TestR14SampleRoles | test_q_hat_excludes_extra_immediate | 185 | VERIFIED_FIXED |
| R15 | Runner | pc1.py | test_r12_r17.py | TestR15DryRunPlan | test_registered_execution_refused | 231 | OPEN |
| R16 | Seed/CRN | evaluator.py | test_r12_r17.py | TestR16SeedContract | test_same_crn_identical_across_genotypes | 246 | VERIFIED_FIXED |
| R17 | Evidence | pc1.py | test_r12_r17.py | TestR17Evidence | test_evidence_contains_provenance | 312 | VERIFIED_FIXED |
| R18 | Cost | COST_BASELINE.md | NONE | NONE | NONE | NONE | VERIFIED_FIXED |
| R19 | Protocol | pc1.py | test_r19_r25.py | TestR19ProtocolFreeze | test_consistency_check_passes | 63 | VERIFIED_FIXED |
| R20 | Seed/CRN | evaluator.py | test_r19_r25.py | TestR20CRNContract | test_same_crn_identical_across_genotypes | 99 | VERIFIED_FIXED |
| R21 | Budget | pc1.py | test_r19_r25.py | TestR21BudgetFailClosed | test_negative_total_rejected | 174 | VERIFIED_FIXED |
| R22 | Provenance | pc1.py | test_r19_r25.py | TestR22ClusterProvenance | test_missing_episode_id_rejected_in_registered | 246 | VERIFIED_FIXED |
| R23 | Evidence | pc1.py | test_r19_r25.py | TestR23EvidenceReplay | test_evidence_contains_D_adv_CIs | 295 | VERIFIED_FIXED |
| R24 | Cost | COST_BASELINE.md | test_r19_r25.py | TestR24CostConsistency | test_smoke_raw_matches_cost_baseline | 343 | PARTIALLY_FIXED |
| R25 | Runner | pc1.py | test_r19_r25.py | TestR25GatedRunner | test_default_deny | 364 | PARTIALLY_FIXED |
| R26 | Protocol | pc1.py | test_r26_r32.py | TestR26ProtocolDocument | test_protocol_document_exists | 336 | VERIFIED_FIXED |
| R27 | Budget | pc1.py | test_r26_r32.py | TestR27NegativeBudget | test_negative_planned_slots_rejected | 64 | VERIFIED_FIXED |
| R28 | Budget | pc1.py | test_r26_r32.py | TestR28FullReconciliation | test_registered_budget_exact | 116 | VERIFIED_FIXED |
| R29 | Provenance | pc1.py | test_r26_r32.py | TestR29ProvenanceMapping | test_unknown_episode_rejected_specifically | 183 | VERIFIED_FIXED |
| R30 | Provenance | pc1.py | test_r26_r32.py | TestR30RegisteredProvenance | test_missing_manifest_hash_rejected | 249 | VERIFIED_FIXED |
| R31 | Runner | pc1.py | test_r26_r32.py | TestR31GateSemantics | test_all_booleans_true_still_denied | 372 | PARTIALLY_FIXED |
| R32 | Seed/CRN | evaluator.py | test_r26_r32.py | TestR32SeedCacheNormalization | test_none_and_empty_seed_distinguished | 299 | VERIFIED_FIXED |
| R33 | Budget | pc1.py | test_r33_r38.py | TestR33Atomicity | test_q_slot_negative_replicas_no_mutation | 68 | VERIFIED_FIXED |
| R34 | Seed/CRN | evaluator.py | test_r33_r38.py | TestR34SeedCollision | test_none_vs_literal_NONE_distinct | 127 | VERIFIED_FIXED |
| R35 | Provenance | pc1.py | test_r33_r38.py | TestR35PlanProvenance | test_plan_mapping_deterministic | 189 | VERIFIED_FIXED |
| R36 | Protocol | pc1.py | test_r33_r38.py | TestR36ProtocolConsistency | test_full_consistency_passes | 252 | PARTIALLY_FIXED |
| R37 | Provenance | pc1.py | test_r33_r38.py | TestR37ProtocolPlanHash | test_missing_protocol_hash_rejected | 326 | VERIFIED_FIXED |
| R38 | Approval | pc1.py | test_r33_r38.py | TestR38FailClosedGates | test_approval_empty_protocol_hash_denied | 369 | PARTIALLY_FIXED |
| R39 | Seed/CRN | evaluator.py | test_r39_r42.py | TestR39CRNSeed | test_same_params_reproducible | 65 | VERIFIED_FIXED |
| R40 | Protocol | pc1.py | test_r39_r42.py | TestR40ProtocolConsistency | test_full_consistency_passes | 104 | VERIFIED_FIXED |
| R41 | Provenance | pc1.py | test_r39_r42.py | TestR41PlanArtifact | test_save_load_roundtrip | 153 | VERIFIED_FIXED |
| R42 | Approval | pc1.py | test_r54_r59.py | TestR54ApprovalGate | test_no_signature_rejected | 89 | PARTIALLY_FIXED |
| R43 | Approval | pc1.py | test_r54_r59.py | TestR54ApprovalGate | test_proposed_rejects_all_flags_true | 69 | PARTIALLY_FIXED |
| R44 | Provenance | pc1.py | test_r54_r59.py | TestR55PlanBinding | test_missing_protocol_hash_rejected | 175 | VERIFIED_FIXED |
| R45 | Protocol | pc1.py | NONE | NONE | NONE | NONE | PARTIALLY_FIXED |
| R46 | Approval | pc1.py | NONE | NONE | NONE | NONE | UNVERIFIABLE |
| R47 | Provenance | pc1.py | test_r54_r59.py | TestR55PlanBinding | test_alternative_mapping_rejected | 201 | VERIFIED_FIXED |
| R48 | Protocol | pc1.py | test_r54_r59.py | TestR56StrictTypes | test_missing_field_rejected | 263 | PARTIALLY_FIXED |
| R49 | Protocol | pc1.py | test_r39_r42.py | TestR40ProtocolConsistency | test_mutation_status_not_checked | 118 | PARTIALLY_FIXED |
| R50 | Approval | pc1.py | test_r54_r59.py | TestR54ApprovalGate | test_wrong_protocol_hash_rejected | 146 | PARTIALLY_FIXED |
| R51 | Provenance | pc1.py | test_r54_r59.py | TestR58RegisteredProtocolHash | test_registered_hash_matches_computed | 284 | VERIFIED_FIXED |
| R52 | Protocol | pc1.py | test_r54_r59.py | TestR56StrictTypes | test_bool_true_rejected | 251 | PARTIALLY_FIXED |
| R53 | Protocol | pc1.py | test_r39_r42.py | TestR40ProtocolConsistency | test_mutation_seed_contract_fails | 130 | PARTIALLY_FIXED |

## 3. Category Counts

| Category | Count | IDs |
|----------|-------|-----|
| Budget | 5 | R12, R21, R27, R28, R33 |
| Seed/CRN | 5 | R16, R20, R32, R34, R39 |
| Protocol | 9 | R19, R26, R36, R40, R45, R48, R49, R52, R53 |
| Approval | 5 | R38, R42, R43, R46, R50 |
| Provenance | 9 | R22, R29, R30, R35, R37, R41, R44, R47, R51 |
| Runner | 3 | R15, R25, R31 |
| Statistics | 2 | R13, R14 |
| Evidence | 2 | R17, R23 |
| Cost | 2 | R18, R24 |
| **Total** | **42** | R12-R53 |

## 4. Key Corrections

1. Disposition counts: 27/13/1/1 = 42 (not 22/15/1/1 = 39)
2. All 42 test mappings use actual class/function declarations
3. R24, R45, R52, R53 remain PARTIALLY_FIXED
4. R18 has manual evidence (no behavioral test)
5. R45, R46 have NO direct tests

## 5. Conclusion

**R26_STAGE1G_AUDIT_COMPLETE_REQUIRES_PLANNER_REVIEW**

42 findings, 42 dispositions (27 FIXED, 13 PARTIAL, 1 OPEN, 1 UNVERIFIABLE). PC1 remains BLOCKED.
