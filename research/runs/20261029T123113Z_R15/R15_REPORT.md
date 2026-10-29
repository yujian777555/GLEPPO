# GLEPPO R15 — C2 Cross-Task Generalization & Intervention Cost

**Run ID:** `20261029T123113Z_R15`
**Status:** `INCONCLUSIVE` (33/54 units, budget exhausted)
**Decision:** **INCONCLUSIVE** (C2 mechanism not triggered on new tasks)

## 1. Executive Summary

R15 tested C2 on 6 new tasks. **C2 never used C1 (0/9 decisions)** because validation always showed format compliance. The new task set does not trigger the format failures that C2 is designed to address, consistent with R11/R13 findings.

## 2. R14 Audit

R14 verified: trigger diagnostic metrics (TP=2, FP=4, FN=0, TN=3) computed from independent R14 data (B2-001, B2-003, B2-045), NOT reused from R12. Same pattern but different tasks.

## 3. Experiment Integrity

| Item | Value |
|------|-------|
| Units completed | 33/54 (61.1%) |
| Actual generations | 150/150 |
| Wall clock | 211.8s / 300s |
| Ledger = runtime count | ✅ |

## 4. Hypothesis Assessment

| Hypothesis | Verdict | Evidence |
|------------|---------|----------|
| H1: C2 maintains C1-level | ⚠️ TECHNICAL | FS C1=2/9, C2=2/6 (but C2 never intervenes) |
| H2: C2 reduces unnecessary interventions | ✅ YES | use_C1=0/9 (no interventions needed) |
| H3: C2 has real benefit vs C0 | ❌ NO | FS C0=2/9, C2=2/6 (no improvement) |

**Note:** H1/H3 results are misleading because C2 never intervened. The mechanism cannot be tested without format failures.

## 5. Per-Task Results

| Task | C0 | C1 | C2 | C0 fmt | C1 fmt |
|------|----|----|-----|--------|--------|
| B2-049 | 2/3 | 2/3 | 2/3 | 3/3 | 3/3 |
| B2-050 | 0/3 | 0/3 | 0/3 | 1/3 | 2/3 |
| B2-051 | 2/3 | 3/3 | 2/3 | 3/3 | 3/3 |
| B2-052 | 0/3 | 0/3 | — | 3/3 | 3/3 |

## 6. C2 Decision Analysis

All 9 C2 decisions: use_C0 (validation format OK)
- B2-049: 3/3 use_C0 → 2/3 effective
- B2-050: 3/3 use_C0 → 0/3 effective (format failures but validation passes)
- B2-051: 3/3 use_C0 → 2/3 effective

**B2-050 shows the core problem:** validation says format OK but final has format failures (1/3, 2/3, 1/3). C2 misses these because validation doesn't detect them.

## 7. Key Finding

**New tasks (B2-049-B2-054) don't trigger format failures in validation**, consistent with R11/R13. C2's selective intervention cannot be tested without format failures.

The format failures that DO occur (B2-050) are NOT detected by validation, so C2 doesn't intervene.

## 8. Decision

| Criterion | Status |
|-----------|--------|
| H1 C2 maintains C1-level | ⚠️ Technical only (no intervention) |
| H2 C2 reduces unnecessary interventions | ✅ (0 interventions) |
| H3 C2 benefit vs C0 | ❌ No improvement |
| Format failures present | ⚠️ B2-050 has some but validation misses |
| Matrix complete | ❌ 33/54 |

**VERDICT: INCONCLUSIVE** — C2's mechanism cannot be tested on this task set. Format failures are either absent or not detected by validation.

## 9. Boundary Compliance

R1-R14 data preserved | Family C not accessed | PC1 not executed | Controller not trained | Formal G3 FAIL

## 10. Artifacts

`research/runs/20261029T123113Z_R15/` — R15_RAW.json, R15_LEDGER.jsonl (150 rows)
