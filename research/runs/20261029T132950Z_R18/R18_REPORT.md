# GLEPPO R18 — C3 Task-Preserving Format Constraint

**Run ID:** `20261029T132950Z_R18`
**Status:** `COMPLETE` (30/30 units, 120/150 generations)
**Decision:** **NO-GO for C3**

## 1. B2-055 Root Cause

C0 sometimes gets DONE-33 (correct) but C1/C3 consistently get DONE-23 (wrong). The format constraint causes the model to use wrong numbers from tool outputs instead of the correct calculation result.

## 2. C0 vs C3 Results

| Metric | C0 | C3 | Δ |
|--------|----|----|---|
| **Effective success** | **10/15 (66.7%)** | **6/15 (40.0%)** | **-26.7%** |
| Format compliant | 12/15 (80%) | 15/15 (100%) | +20% |
| Answer correct | 10/15 (66.7%) | 6/15 (40.0%) | -26.7% |
| Tool path valid | 15/15 (100%) | 15/15 (100%) | 0% |

## 3. Per-Task Detail

| Task | C0 | C3 | Pattern |
|------|----|----|---------|
| B2-055 | **3/3** | **0/3** | **C3 destroys performance** |
| B2-061 | **3/3** | **0/3** | **C3 destroys performance** |
| B2-062 | 1/3 | **3/3** | C3 improves |
| B2-063 | 0/3 | 0/3 | Both fail |
| B2-064 | 3/3 | 3/3 | Both succeed |

## 4. Paired Comparison

C3 wins: 2 (B2-062 only)
C0 wins: 6 (B2-055, B2-061)
Ties: 7

## 5. Root Cause

C3 constraint "use exact tool result required by the task" **confuses the model** on format-sensitive tasks. Instead of computing 19*2-5=33, the model outputs DONE-23 (wrong number from tool output).

The constraint helps on B2-062 (tool result dependency) but hurts on B2-055/B2-061 (format-sensitive).

## 6. Decision

| Criterion | Status |
|-----------|--------|
| C3 improves effective_success | ❌ NO (40% vs 67%) |
| No systematic answer degradation | ❌ B2-055/B2-061: 3/3→0/3 |
| Tool path compliance | ✅ 100% both |
| Format improvement | ✅ 100% vs 80% |

**VERDICT: NO-GO for C3** — task-preserving constraint degrades answer correctness on format-sensitive tasks.

## 7. Implications

1. **Format constraint (C1/C3) consistently hurts** on format-sensitive tasks
2. **The problem is NOT about skipping steps** — it's about wrong answer selection
3. **C0 (no constraint) performs best** on format-sensitive tasks
4. **Need different approach** — perhaps post-hoc answer correction instead of prompt constraint

## 8. Boundary Compliance

R1-R17 data preserved | Family C not accessed | PC1 not executed | Controller not trained | Formal G3 FAIL

## 9. Artifacts

`research/runs/20261029T132950Z_R18/` — R18_RAW.json, R18_LEDGER.jsonl (120 rows)
