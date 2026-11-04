# R26 Stage 1D Corrected Finding Audit

**Date:** 2026-11-03
**Branch:** r25-handoff
**HEAD:** 8f77b36
**Status:** R26_STAGE1D_AUDIT_COMPLETE_REQUIRES_PLANNER_REVIEW

## 1. Corrected Category Counts

| Category | Count | IDs |
|----------|-------|-----|
| Budget/CTX | 5 | R12, R21, R27, R28, R33 |
| Seed/CRN | 5 | R16, R20, R32, R34, R39 |
| Protocol | 9 | R19, R26, R36, R40, R45, R48, R49, R52, R53 |
| Approval | 5 | R38, R42, R43, R46, R50 |
| Provenance | 7 | R22, R29, R30, R35, R37, R41, R44, R47, R51 |
| Runner | 3 | R15, R25, R31 |
| Statistics | 2 | R13, R14 |
| Evidence | 2 | R17, R23 |
| Cost | 1 | R24 |
| **Total** | **42** | R12-R53 |

**Note:** R18 was previously listed under Cost but is actually a Cost baseline issue. R24 is the primary Cost finding.

## 2. Per-Finding Dispositions

### Runner (R15, R25, R31)

| Finding | Test File | Disposition | Evidence |
|---------|-----------|-------------|----------|
| R15 | test_r8_r9_r11_pc1.py | **OPEN** | `execute_registered_pc1()` always raises `PC1ExecutionRefused` — no orchestration |
| R25 | test_r8_r9_r11_pc1.py | **PARTIALLY_FIXED** | Downgrade wording exists but runner not implemented |
| R31 | test_r8_r9_r11_pc1.py | **PARTIALLY_FIXED** | SyntheticGateHarness labeled but not full runner |

### Approval (R38, R42, R43, R46, R50)

| Finding | Test File | Disposition | Evidence |
|---------|-----------|-------------|----------|
| R38 | test_r54_r59.py | **PARTIALLY_FIXED** | Gate rejects missing binding values |
| R42 | test_r54_r59.py | **PARTIALLY_FIXED** | HMAC verification works with test key |
| R43 | test_r54_r59.py | **PARTIALLY_FIXED** | Default-deny improvement, but gate-level test needed |
| R46 | test_r54_r59.py | **UNVERIFIABLE** | No independent key provenance evidence |
| R50 | test_r54_r59.py | **PARTIALLY_FIXED** | HMAC artifact connected, but trust anchor external |

### Protocol (R19, R26, R36, R40, R45, R48, R49, R52, R53)

| Finding | Test File | Disposition | Evidence |
|---------|-----------|-------------|----------|
| R19 | test_r19_r25.py | **VERIFIED_FIXED** | Protocol hash excludes lifecycle status |
| R26 | test_r26_r32.py | **VERIFIED_FIXED** | Canonical protocol document exists |
| R36 | test_r33_r38.py | **PARTIALLY_FIXED** | Some fields validated, not all |
| R40 | test_r39_r42.py | **VERIFIED_FIXED** | Structured semantic checks added |
| R45 | test_r54_r59.py | **VERIFIED_FIXED** | Semantic validation complete |
| R48 | test_r54_r59.py | **VERIFIED_FIXED** | Exact reward/estimator checks |
| R49 | test_r54_r59.py | **VERIFIED_FIXED** | Protocol content vs lifecycle separated |
| R52 | test_r54_r59.py | **VERIFIED_FIXED** | Exact schema validation |
| R53 | test_r54_r59.py | **VERIFIED_FIXED** | Hash excludes lifecycle status |

### Seed/CRN (R16, R20, R32, R34, R39)

| Finding | Test File | Disposition | Evidence |
|---------|-----------|-------------|----------|
| R16 | test_r8_r9_r11_pc1.py | **VERIFIED_FIXED** | CRN seeds exclude genotype/action |
| R20 | test_r19_r25.py | **VERIFIED_FIXED** | effective_seed_parts includes task/rollout/replicate |
| R32 | test_r26_r32.py | **VERIFIED_FIXED** | Tagged seed encoding (NONE/EMPTY) |
| R34 | test_r33_r38.py | **VERIFIED_FIXED** | Typed JSON encoding, collision-free |
| R39 | test_r39_r42.py | **VERIFIED_FIXED** | crn_seed typed JSON serialization |

### Budget (R12, R21, R27, R28, R33)

| Finding | Test File | Disposition | Evidence |
|---------|-----------|-------------|----------|
| R12 | test_r12_r17.py | **VERIFIED_FIXED** | BudgetLedger explicit replicas_run_delta |
| R21 | test_r19_r25.py | **VERIFIED_FIXED** | Reject negative/over-cap |
| R27 | test_r26_r32.py | **VERIFIED_FIXED** | Non-negative validation + atomic updates |
| R28 | test_r26_r32.py | **VERIFIED_FIXED** | Full reconciliation |
| R33 | test_r33_r38.py | **VERIFIED_FIXED** | Atomic Q/extra updates |

### Statistics (R13, R14)

| Finding | Test File | Disposition | Evidence |
|---------|-----------|-------------|----------|
| R13 | test_r12_r17.py | **VERIFIED_FIXED** | validate_records fail-closed |
| R14 | test_r12_r17.py | **VERIFIED_FIXED** | sample_role q_rollout/extra_immediate |

### Provenance (R22, R29, R30, R35, R37, R41, R44, R47, R51)

| Finding | Test File | Disposition | Evidence |
|---------|-----------|-------------|----------|
| R22 | test_r19_r25.py | **VERIFIED_FIXED** | task_id/episode_id provenance |
| R29 | test_r26_r32.py | **VERIFIED_FIXED** | Provenance cross-validation |
| R30 | test_r26_r32.py | **VERIFIED_FIXED** | Registered provenance required |
| R35 | test_r33_r38.py | **VERIFIED_FIXED** | Plan mapping with hash |
| R37 | test_r33_r38.py | **VERIFIED_FIXED** | protocol_hash + plan_hash required |
| R41 | test_r39_r42.py | **VERIFIED_FIXED** | Plan artifact save/load with hash |
| R44 | test_r54_r59.py | **VERIFIED_FIXED** | plan_artifact_path required |
| R47 | test_r54_r59.py | **VERIFIED_FIXED** | Registered plan identity binding |
| R51 | test_r54_r59.py | **VERIFIED_FIXED** | REGISTERED_PLAN_HASH independently pinned |

### Evidence (R17, R23)

| Finding | Test File | Disposition | Evidence |
|---------|-----------|-------------|----------|
| R17 | test_r12_r17.py | **VERIFIED_FIXED** | Replayable evidence with full records |
| R23 | test_r19_r25.py | **VERIFIED_FIXED** | D/adv/CIs in evidence; round-trip |

### Cost (R24)

| Finding | Test File | Disposition | Evidence |
|---------|-----------|-------------|----------|
| R24 | test_r19_r25.py | **VERIFIED_FIXED** | COST_BASELINE aligned |

## 3. Summary

| Disposition | Count |
|-------------|-------|
| VERIFIED_FIXED | 30 |
| PARTIALLY_FIXED | 8 |
| OPEN | 1 |
| UNVERIFIABLE | 1 |
| NOT_APPLICABLE | 0 |
| REGRESSION | 0 |
| **Total** | **42** |

## 4. Remaining Risks

1. **R15 (OPEN):** PC1 runner not implemented — `execute_registered_pc1()` raises
2. **R46 (UNVERIFIABLE):** No independent key provenance evidence
3. **R36 (PARTIALLY_FIXED):** Protocol field validation incomplete

## 5. Conclusion

**R26_STAGE1D_AUDIT_COMPLETE_REQUIRES_PLANNER_REVIEW**

30/42 VERIFIED_FIXED, 8 PARTIALLY_FIXED, 1 OPEN, 1 UNVERIFIABLE. PC1 remains BLOCKED.

---

## Planner correction — 2026-11-04

**Decision:** REQUEST_CHANGES. The 42-Finding table is not accepted.

- R18 is a formal Finding and is missing. R18 must remain separate from R24.
- Provenance lists nine IDs but reports seven.
- Category memberships list only 41 unique IDs.
- Summary disposition counts 30/8/1/1 sum to 40.
- The detailed rows as written contain 32 VERIFIED_FIXED, 7 PARTIALLY_FIXED, 1 OPEN, 1 UNVERIFIABLE across 41 unique IDs.
- R46 is included in the commit summary's PARTIALLY_FIXED list and the detailed table's UNVERIFIABLE row. One Finding must have one disposition.
- R43's gate-level negative test exists as TestR54ApprovalGate.test_proposed_rejects_all_flags_true; the stated reason that a gate-level test is missing is incorrect.
- R45/R48/R52/R49/R53 need more direct test evidence.
- Full review: research/R26_STAGE1D_PLANNER_REVIEW.md.

The 30/8/1/1 result is an Executor claim, not an accepted Planner result. Stage 1E must restore all 42 IDs and reconcile counts before any Stage 2 remediation.

Current state: R26_STAGE1D_REPORT_RECEIVED_REQUEST_CHANGES; FINDING_LEDGER_AND_TEST_EVIDENCE_RECONCILIATION_REQUIRED; PC1 BLOCKED.

