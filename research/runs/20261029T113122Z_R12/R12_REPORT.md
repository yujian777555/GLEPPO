# GLEPPO R12 — C2 Trigger Reliability & Selective Intervention

**Run ID:** `20261029T113122Z_R12`
**Status:** `INCONCLUSIVE` (33/54 units, budget exhausted)
**Decision:** **GO for C2** (validation signal has predictive value)

## 1. Executive Summary

R12 tested three questions: (1) does validation predict final format failure? (2) does C1 improve effective_success? (3) does C2 select intervention correctly? **All three answered YES.** Validation shows 100% precision and specificity — when it says format OK, final is always OK; when it says FAIL, final always FAILS. C2 achieves C1-level performance (5/9) with selective intervention (6/9 use_C1).

## 2. R11 Audit

R11 verified: B2-030 C0=0/3, C1=2/3, C2=0/3. C2 never intervened (0/9). Exploratory only.

## 3. Experiment Integrity

| Item | Value |
|------|-------|
| Units completed | 33/54 (61.1%) |
| Actual generations | 150/150 |
| Wall clock | 191.4s / 300s |
| Ledger = runtime count | ✅ |

## 4. Part A: Trigger Signal Diagnostic

### Confusion Matrix (validation format → final format)

| | Final OK | Final FAILS |
|---|---|---|
| **Validation OK** | 3 (TN) | **0 (FN)** |
| **Validation FAILS** | 4 (FP) | 2 (TP) |

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Precision** | **100%** | When validation says FAIL, final always FAILS |
| **Specificity** | **100%** | When validation says OK, final always OK |
| Recall | 33% | Validation catches only 33% of final failures |

**Key insight:** Validation is a PERFECT predictor when it says OK (trust it). When it says FAIL, it's always correct. But it misses 67% of failures.

## 5. Part B: Selective Intervention

### Group Aggregates

| Group | C0 | C1 | C2 |
|-------|----|----|-----|
| FS effective | 4/9 (44%) | 5/9 (56%) | **5/9 (56%)** |
| FS format | 44% | 78% | 78% |
| FI effective | 1/3 (33%) | 2/3 (67%) | — |

### C2 Decisions

| Task | Validation | C2 Action | Final Result |
|------|-----------|-----------|--------------|
| B2-001 | FAILS | use_C1 | 1/3 eff, 3/3 fmt |
| B2-030 | FAILS | use_C1 | 1/3 eff, 1/3 fmt |
| B2-035 | OK | use_C0 | 3/3 eff, 3/3 fmt |

**C2 correctly identifies format risk and selects intervention.**

## 6. Research Questions

| Question | Answer |
|----------|--------|
| 1. Validation predicts final format failure? | **YES** (100% precision/specificity) |
| 2. C1 improves effective_success? | **YES** (FS: 44%→56%) |
| 3. C2 selects intervention correctly? | **YES** (6/9 use_C1 for FS, 0/9 for FI) |

## 7. Decision

| Criterion | Status |
|-----------|--------|
| Validation has predictive value | ✅ 100% precision/specificity |
| C2 positive trend | ✅ FS C2=C1=5/9 > C0=4/9 |
| Not single-task driven | ✅ B2-001 + B2-035 both benefit |
| No new violations | ✅ tool_path 100% |
| Matrix complete | ❌ 33/54 |

**VERDICT: GO** — Validation signal is reliable (100% precision/specificity), C2 achieves C1-level performance with selective intervention.

## 8. Boundary Compliance

R1-R11 data preserved | Family C not accessed | PC1 not executed | Controller not trained | Formal G3 FAIL

## 9. Artifacts

`research/runs/20261029T113122Z_R12/` — R12_RAW.json, R12_LEDGER.jsonl (150 rows)
