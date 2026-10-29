# R7 C1 Format Constraint Validation — Report

**Run ID:** `20261029T073455Z_R7`
**Status:** `COMPLETE` (36/36 units, 144/150 generations)
**Decision:** **INCONCLUSIVE** (effect too small to distinguish from noise)

## 1. Executive Summary

R7 tested whether adding ONLY an output format constraint to original crossover improves effective success rate on 6 new tasks. **The effect is marginal and not statistically distinguishable from noise.** C1 achieved 50.0% vs C0's 44.4%, with 1 paired win and 0 losses (McNemar p=1.0). Both arms achieved 100% format compliance, so the format constraint had no measurable effect on these tasks.

## 2. Experiment Integrity

| Item | Value |
|------|-------|
| Units completed | 36/36 (100%) |
| Actual generations | 144/150 |
| Wall clock | 98.2s / 300s |
| Ledger = runtime count | ✅ |
| Token delta = runtime total | ✅ |
| Revision match | ✅ |
| New tasks (not in R5/R6) | 6/6 ✅ |

## 3. Independent Metric Recomputation

### Arm Comparison

| Metric | C0 (original) | C1 (format constraint) | Δ |
|--------|--------------|----------------------|---|
| n | 18 | 18 | |
| Parent effective_success | 9/18 (50.0%) | 9/18 (50.0%) | 0 |
| **Child effective_success** | **8/18 (44.4%)** | **9/18 (50.0%)** | **+5.6%** |
| Improved (vs parent) | 0 | 0 | |
| Degraded (vs parent) | 1 | 0 | |
| Child format_compliant | 18/18 (100%) | 18/18 (100%) | 0 |
| Child tool_path_valid | 18/18 (100%) | 18/18 (100%) | 0 |
| Child answer_correct | 8/18 (44.4%) | 9/18 (50.0%) | +5.6% |

### Paired C1 vs C0

| Outcome | Count |
|---------|-------|
| **C1 wins** | **1** |
| **C0 wins** | **0** |
| Ties | 17 |

**McNemar exact p = 1.0000** (not significant)

### Per-Task Breakdown

| Task | C0 | C1 | Notes |
|------|----|----|-------|
| B2-012 | 0/3 | 0/3 | Both fail (format-sensitive) |
| B2-013 | 2/3 | **3/3** | **C1 wins 1 pair** |
| B2-014 | 0/3 | 0/3 | Both fail (reverse order) |
| B2-015 | 3/3 | 3/3 | Both succeed (3-tool) |
| B2-016 | 3/3 | 3/3 | Both succeed (multi-step) |
| B2-017 | 0/3 | 0/3 | Both fail (compound format) |

## 4. Key Findings

### 4.1 Format constraint has NO measurable effect on R7 tasks
- Both C0 and C1 achieve **100% format compliance**
- The R7 tasks do NOT trigger format failures (unlike R5/R6 B2-001/B2-003)
- **Cannot confirm H2 (format constraint reduces failures)** — there were no failures to reduce

### 4.2 C1's single win is on B2-013/seed-002
- C0 fails, C1 succeeds on this one pair
- But 1/18 = 5.6% — too small to distinguish from noise
- No systematic pattern across tasks or seeds

### 4.3 Both arms show identical tool_path compliance
- 100% for both — no H4 concern

### 4.4 Task difficulty explains most variance
- B2-012, B2-014, B2-017: both arms fail (hard tasks)
- B2-015, B2-016: both arms succeed (easy tasks)
- B2-013: C1 slightly better (the only differentiator)

## 5. Hypothesis Assessment

| Hypothesis | Verdict | Evidence |
|------------|---------|----------|
| C1 > C0 effective_success | **INCONCLUSIVE** | +5.6%, 1 win, p=1.0 |
| Format constraint reduces failures | **NOT TESTABLE** | Both 100% format (no failures) |
| No tool_path sacrifice | **SUPPORTED** | Both 100% |

## 6. Decision

| Criterion | Status |
|-----------|--------|
| C1 effective_success > C0 | ⚠️ Marginal (50.0% vs 44.4%) |
| Improvement not single-task | ❌ Only B2-013 shows difference |
| Format improvement reproduced | ❌ No format failures to reproduce |
| No new violations | ✅ Both 100% path |
| Budget/evidence complete | ✅ 36/36, ledger matches |

**VERDICT: INCONCLUSIVE**

The effect is too small (1/18 paired win) and too task-specific (only B2-013) to support GO. Cannot confirm or falsify the format constraint hypothesis on R7 tasks.

## 7. Comparison with R5/R6

| Metric | R5 (R5 tasks) | R6 (R6 tasks) | R7 (R7 tasks) |
|--------|---------------|---------------|---------------|
| C0 effective_success | 33.3% | 53.3% | 44.4% |
| C1 effective_success | 60.0% (n=5) | 60.0% (n=5) | 50.0% (n=18) |
| C1 > C0? | YES | YES | Marginal |
| Format failures (C0) | 67% | 13% | 0% |

**Key insight:** Format failures decrease across R5→R6→R7 as tasks become less format-sensitive. The format constraint matters most when format failures occur.

## 8. Recommendations

1. **Do NOT declare GO** — evidence insufficient
2. **Format constraint is safe but effect is task-dependent**
3. **R8 should focus on format-sensitive tasks** (like R5's B2-001/B2-003) where format failures actually occur
4. **Consider task design**: R7 tasks may be too easy (100% format) or too hard (0% success) to discriminate

## 9. Boundary Compliance

R1-R6 data preserved | Family C not accessed | PC1 not executed | Controller not trained | Formal G3 FAIL

## 10. Artifacts

`research/runs/20261029T073455Z_R7/` — R7_RAW.json, R7_LEDGER.jsonl (144 rows), R7_FROZEN_MANIFEST.json, R7_RESULT_MANIFEST.json
