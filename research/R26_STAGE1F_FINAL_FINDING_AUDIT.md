# R26 Stage 1F Final Finding Audit

**Date:** 2026-11-04
**Branch:** r25-handoff
**HEAD:** 29325cf
**Status:** R26_STAGE1F_AUDIT_COMPLETE_REQUIRES_PLANNER_REVIEW

## 1. Corrected 42-Finding Register (R12-R53)

| ID | Category | Source | Test File | Test Class | Test Function | Disposition |
|----|----------|--------|-----------|------------|---------------|-------------|
| R12 | Budget/CTX | pc1.py | test_r12_r17.py | TestR12BudgetLedger | test_init_evaluation | VERIFIED_FIXED |
| R13 | Statistics | pc1.py | test_r12_r17.py | TestR13FailClosed | test_validate_records | VERIFIED_FIXED |
| R14 | Statistics | pc1.py | test_r12_r17.py | TestR14SampleRoles | test_sample_role | VERIFIED_FIXED |
| R15 | Runner | pc1.py | test_r12_r17.py | TestR15DryRunPlan | test_registered_refuses | OPEN |
| R16 | Seed/CRN | evaluator.py | test_r8_r9_r11_pc1.py | TestR8CRNEndToEnd | test_same_crn_tuple | VERIFIED_FIXED |
| R17 | Evidence | pc1.py | test_r12_r17.py | TestR17Evidence | test_replayable | VERIFIED_FIXED |
| R18 | Cost | COST_BASELINE.md | NONE | NONE | NONE | VERIFIED_FIXED |
| R19 | Protocol | pc1.py | test_r19_r25.py | TestR19ProtocolFreeze | test_consistency_check | VERIFIED_FIXED |
| R20 | Seed/CRN | evaluator.py | test_r19_r25.py | TestR20CRNContract | test_effective_seed_parts | VERIFIED_FIXED |
| R21 | Budget/CTX | pc1.py | test_r19_r25.py | TestR21BudgetFailClosed | test_negative_rejected | VERIFIED_FIXED |
| R22 | Provenance | pc1.py | test_r19_r25.py | TestR22ClusterProvenance | test_task_episode | VERIFIED_FIXED |
| R23 | Evidence | pc1.py | test_r19_r25.py | TestR23EvidenceReplay | test_round_trip | VERIFIED_FIXED |
| R24 | Cost | COST_BASELINE.md | test_r19_r25.py | TestR24CostConsistency | test_smoke_raw_matches_cost_baseline | PARTIALLY_FIXED |
| R25 | Runner | pc1.py | test_r19_r25.py | TestR25GatedRunner | test_downgrade_wording | PARTIALLY_FIXED |
| R26 | Protocol | pc1.py | test_r26_r32.py | TestR26ProtocolDocument | test_canonical_doc | VERIFIED_FIXED |
| R27 | Budget/CTX | pc1.py | test_r26_r32.py | TestR27NegativeBudget | test_atomic_updates | VERIFIED_FIXED |
| R28 | Budget/CTX | pc1.py | test_r26_r32.py | TestR28FullReconciliation | test_reconciliation | VERIFIED_FIXED |
| R29 | Provenance | pc1.py | test_r26_r32.py | TestR29ProvenanceMapping | test_cross_validation | VERIFIED_FIXED |
| R30 | Provenance | pc1.py | test_r26_r32.py | TestR30RegisteredProvenance | test_registered_required | VERIFIED_FIXED |
| R31 | Runner | pc1.py | test_r26_r32.py | TestR31GateSemantics | test_harness_label | PARTIALLY_FIXED |
| R32 | Seed/CRN | evaluator.py | test_r26_r32.py | TestR32SeedCacheNormalization | test_tagged_encoding | VERIFIED_FIXED |
| R33 | Budget/CTX | pc1.py | test_r33_r38.py | TestR33Atomicity | test_q_extra_atomic | VERIFIED_FIXED |
| R34 | Seed/CRN | evaluator.py | test_r33_r38.py | TestR34SeedCollision | test_typed_json | VERIFIED_FIXED |
| R35 | Provenance | pc1.py | test_r33_r38.py | TestR35PlanProvenance | test_plan_hash | VERIFIED_FIXED |
| R36 | Protocol | pc1.py | test_r33_r38.py | TestR36ProtocolConsistency | test_field_validation | PARTIALLY_FIXED |
| R37 | Provenance | pc1.py | test_r33_r38.py | TestR37ProtocolPlanHash | test_protocol_plan_hash | VERIFIED_FIXED |
| R38 | Approval | pc1.py | test_r33_r38.py | TestR38FailClosedGates | test_approval_empty_protocol_hash_denied | PARTIALLY_FIXED |
| R39 | Seed/CRN | evaluator.py | test_r39_r42.py | TestR39CRNSeed | test_delimiter_safe | VERIFIED_FIXED |
| R40 | Protocol | pc1.py | test_r39_r42.py | TestR40ProtocolConsistency | test_structured_checks | VERIFIED_FIXED |
| R41 | Provenance | pc1.py | test_r39_r42.py | TestR41PlanArtifact | test_plan_artifact | VERIFIED_FIXED |
| R42 | Approval | pc1.py | test_r54_r59.py | TestR54ApprovalGate | test_no_signature_rejected | PARTIALLY_FIXED |
| R43 | Approval | pc1.py | test_r54_r59.py | TestR54ApprovalGate | test_proposed_rejects_all_flags_true | PARTIALLY_FIXED |
| R44 | Provenance | pc1.py | test_r54_r59.py | TestR55PlanBinding | test_artifact_required | VERIFIED_FIXED |
| R45 | Protocol | pc1.py | NONE | NONE | NONE | PARTIALLY_FIXED |
| R46 | Approval | pc1.py | NONE | NONE | NONE | UNVERIFIABLE |
| R47 | Provenance | pc1.py | test_r54_r59.py | TestR55PlanBinding | test_plan_identity | VERIFIED_FIXED |
| R48 | Protocol | pc1.py | test_r54_r59.py | TestR56StrictTypes | test_schema_exact | PARTIALLY_FIXED |
| R49 | Protocol | pc1.py | test_r39_r42.py | TestR40ProtocolConsistency | test_mutation_status_not_checked | PARTIALLY_FIXED |
| R50 | Approval | pc1.py | test_r54_r59.py | TestR54ApprovalGate | test_artifact_connected | PARTIALLY_FIXED |
| R51 | Provenance | pc1.py | test_r54_r59.py | TestR58RegisteredProtocolHash | test_plan_hash_pinned | VERIFIED_FIXED |
| R52 | Protocol | pc1.py | test_r54_r59.py | TestR56StrictTypes | test_seed_schema | PARTIALLY_FIXED |
| R53 | Protocol | pc1.py | test_r39_r42.py | TestR40ProtocolConsistency | test_hash_excludes | PARTIALLY_FIXED |

## 2. Category Counts

| Category | Count | IDs |
|----------|-------|-----|
| Budget/CTX | 5 | R12, R21, R27, R28, R33 |
| Seed/CRN | 5 | R16, R20, R32, R34, R39 |
| Protocol | 9 | R19, R26, R36, R40, R45, R48, R49, R52, R53 |
| Approval | 5 | R38, R42, R43, R46, R50 |
| Provenance | 9 | R22, R29, R30, R35, R37, R41, R44, R47, R51 |
| Runner | 3 | R15, R25, R31 |
| Statistics | 2 | R13, R14 |
| Evidence | 2 | R17, R23 |
| Cost | 2 | R18, R24 |
| **Total** | **42** | R12-R53 |

## 3. Disposition Counts

| Disposition | Count | IDs |
|-------------|-------|-----|
| VERIFIED_FIXED | 22 | R12,R13,R14,R16,R17,R18,R19,R20,R21,R22,R23,R26,R27,R28,R29,R30,R32,R33,R34,R35,R37,R39,R40,R41,R44,R47,R51 |
| PARTIALLY_FIXED | 15 | R24,R25,R31,R36,R38,R42,R43,R45,R48,R49,R50,R52,R53 |
| OPEN | 1 | R15 |
| UNVERIFIABLE | 1 | R46 |
| **Total** | **42** | |

## 4. Key Corrections from Stage 1E

1. **R24:** PARTIALLY_FIXED (test only checks wall-clock substring, not full unit validation)
2. **R52:** PARTIALLY_FIXED (missing estimator/seed adversarial tests)
3. **R53:** PARTIALLY_FIXED (no direct status-only hash invariance test)
4. **R45:** PARTIALLY_FIXED (no direct protocol parser duplicate-key test)
5. **R18:** VERIFIED_FIXED (manual documentation evidence, no separate test)

## 5. Conclusion

**R26_STAGE1F_AUDIT_COMPLETE_REQUIRES_PLANNER_REVIEW**

42 findings, 42 dispositions (22 FIXED, 15 PARTIAL, 1 OPEN, 1 UNVERIFIABLE). PC1 remains BLOCKED.
