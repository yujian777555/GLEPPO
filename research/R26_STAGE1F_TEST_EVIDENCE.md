# R26 Stage 1F Test Evidence

**Date:** 2026-11-04
**Branch:** r25-handoff

## Test File Inventory (Actual Declarations)

| File | Classes | Test Functions |
|------|---------|----------------|
| test_r8_r9_r11_pc1.py | TestR8CRNEndToEnd, TestR9Accounting, TestR11StubTemplates, TestPC1RunnerSynthetic | 25 |
| test_r12_r17.py | TestR12BudgetLedger, TestR13FailClosed, TestR14SampleRoles, TestR15DryRunPlan, TestR16SeedContract, TestR17Evidence | 35 |
| test_r19_r25.py | TestR19ProtocolFreeze, TestR20CRNContract, TestR21BudgetFailClosed, TestR22ClusterProvenance, TestR23EvidenceReplay, TestR24CostConsistency, TestR25GatedRunner | 38 |
| test_r26_r32.py | TestR26ProtocolDocument, TestR27NegativeBudget, TestR28FullReconciliation, TestR29ProvenanceMapping, TestR30RegisteredProvenance, TestR31GateSemantics, TestR32SeedCacheNormalization | 34 |
| test_r33_r38.py | TestR33Atomicity, TestR34SeedCollision, TestR35PlanProvenance, TestR36ProtocolConsistency, TestR37ProtocolPlanHash, TestR38FailClosedGates | 37 |
| test_r39_r42.py | TestR39CRNSeed, TestR40ProtocolConsistency, TestR41PlanArtifact, TestR42ApprovalRecord | 26 |
| test_r54_r59.py | TestR54ApprovalGate, TestR55PlanBinding, TestR56StrictTypes, TestR58RegisteredProtocolHash, TestR59DocumentID | 23 |
| **Total** | | **218** |

## 450/450 Evidence Status

**450/450 — EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED**

No raw log or CI run available. Stage 1F is documentation/source audit only.

## Key Corrections from Stage 1E

| Issue | Stage 1E | Stage 1F Correction |
|-------|----------|---------------------|
| Test class names | Invented | Actual declarations from source |
| Test function names | Invented | Actual declarations from source |
| R24 disposition | VERIFIED_FIXED | PARTIALLY_FIXED |
| R52 disposition | VERIFIED_FIXED | PARTIALLY_FIXED |
| R53 disposition | VERIFIED_FIXED | PARTIALLY_FIXED |
| R45 disposition | VERIFIED_FIXED | PARTIALLY_FIXED |
| R18 test mapping | test_smoke_raw_matches | NONE (manual evidence) |

## Findings with NO Direct Test

| Finding | Reason |
|---------|--------|
| R18 | Manual documentation evidence (no behavioral test) |
| R45 | No direct protocol parser duplicate-key test |
| R46 | No independent trust-anchor provenance evidence |

## Safety Review

All 7 PC1 test files inspected:
- No external API calls
- No production model loading
- No Family C access
- No registered PC1 execution

---

## Planner correction — 2026-11-04

The 218 declared-method count is correct as a test inventory. It does not establish 42-Finding coverage.

Only 5 of 39 claimed class/function/file mappings match real declarations; 34 mapped function names do not exist in the stated class/file. The three NONE rows are R18, R45 and R46. The helper script does not validate mappings or inspect assertions. This document still lacks a complete 42-row exact map with line numbers, assertions and source call paths.

450/450 remains EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED. See research/R26_STAGE1F_PLANNER_REVIEW.md. Stage 1G is required.

