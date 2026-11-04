# R26 Stage 1H Final Finding Audit

**Date:** 2026-11-04
**Branch:** r25-handoff
**SOURCE_SNAPSHOT:** 29325cfa16441154c833f381f208747b57627a79
**STAGE1G_REPORT_COMMIT:** 69781d1166f9e28e7535915aad00af859c1b2734
**CURRENT_BRANCH_HEAD:** 0b1d5ca (at time of Stage 1H work)

## 1. Corrected Disposition Counts

From 42 rows (R12-R53):
- **VERIFIED_FIXED: 26** (was 27; R19 downgraded)
- **PARTIALLY_FIXED: 14** (was 13; R19 added)
- **OPEN: 1** (R15)
- **UNVERIFIABLE: 1** (R46)
- **Total: 42**

## 2. Key Corrections from Stage 1G

| ID | Stage 1G Issue | Stage 1H Correction |
|----|----------------|---------------------|
| R31 | Wrong function name | `test_all_booleans_true_still_denied_for_proposed_protocol` |
| R49 | Wrong function name | `test_mutation_status_not_checked_by_consistency` |
| R39 | Tautological test | Replaced with non-tautological tests |
| R53 | Unrelated mapping | Corrected to related/indirect evidence |
| R19 | VERIFIED_FIXED | **PARTIALLY_FIXED** (protocol still PROPOSED) |
| R18 | No line refs | Added exact line references |

## 3. Complete 42-Finding Register (Corrected)

| ID | Category | Test Class | Test Function | Line | Disposition |
|----|----------|------------|---------------|------|-------------|
| R12 | Budget | TestR12BudgetLedger | test_init_evaluation | 37 | VERIFIED_FIXED |
| R13 | Statistics | TestR13FailClosed | test_missing_action_rejected | 111 | VERIFIED_FIXED |
| R14 | Statistics | TestR14SampleRoles | test_q_hat_excludes_extra_immediate | 185 | VERIFIED_FIXED |
| R15 | Runner | TestR15DryRunPlan | test_registered_execution_refused | 231 | OPEN |
| R16 | Seed/CRN | TestR16SeedContract | test_same_crn_identical_across_genotypes | 246 | VERIFIED_FIXED |
| R17 | Evidence | TestR17Evidence | test_evidence_contains_provenance | 312 | VERIFIED_FIXED |
| R18 | Cost | NONE | NONE | NONE | VERIFIED_FIXED |
| R19 | Protocol | TestR19ProtocolFreeze | test_protocol_status_not_approved | 79 | **PARTIALLY_FIXED** |
| R20 | Seed/CRN | TestR20CRNContract | test_same_crn_identical_across_genotypes | 99 | VERIFIED_FIXED |
| R21 | Budget | TestR21BudgetFailClosed | test_negative_total_rejected | 174 | VERIFIED_FIXED |
| R22 | Provenance | TestR22ClusterProvenance | test_missing_episode_id_rejected_in_registered | 246 | VERIFIED_FIXED |
| R23 | Evidence | TestR23EvidenceReplay | test_evidence_contains_D_adv_CIs | 295 | VERIFIED_FIXED |
| R24 | Cost | TestR24CostConsistency | test_smoke_raw_matches_cost_baseline | 343 | PARTIALLY_FIXED |
| R25 | Runner | TestR25GatedRunner | test_default_deny | 364 | PARTIALLY_FIXED |
| R26 | Protocol | TestR26ProtocolDocument | test_protocol_document_exists | 336 | VERIFIED_FIXED |
| R27 | Budget | TestR27NegativeBudget | test_negative_planned_slots_rejected | 64 | VERIFIED_FIXED |
| R28 | Budget | TestR28FullReconciliation | test_registered_budget_exact | 116 | VERIFIED_FIXED |
| R29 | Provenance | TestR29ProvenanceMapping | test_unknown_episode_rejected_specifically | 183 | VERIFIED_FIXED |
| R30 | Provenance | TestR30RegisteredProvenance | test_missing_manifest_hash_rejected | 249 | VERIFIED_FIXED |
| R31 | Runner | TestR31GateSemantics | **test_all_booleans_true_still_denied_for_proposed_protocol** | 372 | PARTIALLY_FIXED |
| R32 | Seed/CRN | TestR32SeedCacheNormalization | test_none_and_empty_seed_distinguished | 299 | VERIFIED_FIXED |
| R33 | Budget | TestR33Atomicity | test_q_slot_negative_replicas_no_mutation | 68 | VERIFIED_FIXED |
| R34 | Seed/CRN | TestR34SeedCollision | test_none_vs_literal_NONE_distinct | 127 | VERIFIED_FIXED |
| R35 | Provenance | TestR35PlanProvenance | test_plan_mapping_deterministic | 189 | VERIFIED_FIXED |
| R36 | Protocol | TestR36ProtocolConsistency | test_full_consistency_passes | 252 | PARTIALLY_FIXED |
| R37 | Provenance | TestR37ProtocolPlanHash | test_missing_protocol_hash_rejected | 326 | VERIFIED_FIXED |
| R38 | Approval | TestR38FailClosedGates | test_approval_empty_protocol_hash_denied | 369 | PARTIALLY_FIXED |
| R39 | Seed/CRN | TestR39CRNSeed | **test_delimiter_no_collision** | 68 | VERIFIED_FIXED |
| R40 | Protocol | TestR40ProtocolConsistency | test_full_consistency_passes | 104 | VERIFIED_FIXED |
| R41 | Provenance | TestR41PlanArtifact | test_save_load_roundtrip | 153 | VERIFIED_FIXED |
| R42 | Approval | TestR54ApprovalGate | test_no_signature_rejected | 89 | PARTIALLY_FIXED |
| R43 | Approval | TestR54ApprovalGate | test_proposed_rejects_all_flags_true | 69 | PARTIALLY_FIXED |
| R44 | Provenance | TestR55PlanBinding | test_missing_protocol_hash_rejected | 175 | VERIFIED_FIXED |
| R45 | Protocol | NONE | NONE | NONE | PARTIALLY_FIXED |
| R46 | Approval | NONE | NONE | NONE | UNVERIFIABLE |
| R47 | Provenance | TestR55PlanBinding | test_alternative_mapping_rejected | 201 | VERIFIED_FIXED |
| R48 | Protocol | TestR56StrictTypes | test_missing_field_rejected | 263 | PARTIALLY_FIXED |
| R49 | Protocol | TestR40ProtocolConsistency | **test_mutation_status_not_checked_by_consistency** | 118 | PARTIALLY_FIXED |
| R50 | Approval | TestR54ApprovalGate | test_wrong_protocol_hash_rejected | 146 | PARTIALLY_FIXED |
| R51 | Provenance | TestR58RegisteredProtocolHash | test_registered_hash_matches_computed | 284 | VERIFIED_FIXED |
| R52 | Protocol | TestR56StrictTypes | test_bool_true_rejected | 251 | PARTIALLY_FIXED |
| R53 | Protocol | TestR40ProtocolConsistency | test_mutation_seed_contract_fails | 130 | PARTIALLY_FIXED |

## 4. R39 Non-Tautological Evidence

Tautological: `test_same_params_reproducible` (line 65) — same call compared to itself.

Non-tautological tests:
- `test_delimiter_no_collision` (line 68) — verifies delimiter safety
- `test_task_change_changes_seed` (line 74) — task isolation
- `test_state_change_changes_seed` (line 77) — state isolation
- `test_rollout_change_changes_seed` (line 80) — rollout isolation
- `test_replicate_change_changes_seed` (line 83) — replicate isolation
- `test_none_empty_string_no_collision` (line 86) — encoding safety

## 5. R18 Manual Evidence

- SMOKE_RAW.json line 276: wall_clock_s = 0.0261
- SMOKE_RAW.json lines 277-279: planned init 32, offspring 96, total 128
- SMOKE_RAW.json line 284: actual_replicas_run = 112
- COST_BASELINE.md line 22: stub wall-clock 0.0261 s
- COST_BASELINE.md line 30: total planned smoke slots 128

## 6. R19 Disposition

R19 requires "explicit Planner/protocol approval before registered PC1 data collection."
Current protocol: PROPOSED / NOT APPROVED.
Test confirms status is proposed.
**Downgraded to PARTIALLY_FIXED.**

## 7. Conclusion

**R26_STAGE1H_AUDIT_COMPLETE_REQUIRES_PLANNER_REVIEW**

42 findings, 42 dispositions (26 FIXED, 14 PARTIAL, 1 OPEN, 1 UNVERIFIABLE). PC1 remains BLOCKED.

---

## Planner correction — 2026-11-04

**Planner decision:** REQUEST_CHANGES. The Stage 1H row arithmetic is correct at 26/14/1/1 = 42, and all 39 direct declaration tuples match the frozen source snapshot. The source snapshot is 29325cfa16441154c833f381f208747b57627a79; Stage 1H parent is 0b1d5cac084966040a2a1820675605cc428776fc; Stage 1H report/final branch HEAD is 532ee8adf498e83967016723d28cb1e7dc30bf5f.

The semantic map is incomplete. R53 still maps to test_mutation_seed_contract_fails at line 130, which mutates seed_schema rather than lifecycle status/hash. The related status test at line 118 is indirect only and does not prove compute_protocol_hash excludes status. R39 must cross-reference R16/R20 instrumented cross-genotype tests. R18 must include the exact token/units/production-cost references listed in research/R26_STAGE1H_PLANNER_REVIEW.md.

The helper remains a declaration inventory, not a map validator. Handoff and cumulative records were not updated in the Stage 1H Executor commit.

See research/R26_STAGE1H_PLANNER_REVIEW.md. Stage 1I required. PC1 remains BLOCKED.

