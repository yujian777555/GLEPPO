# R6 crossover_fixed Generalization + Mechanism Ablation — Report

**Run ID:** `20261029T064914Z_R6`
**Status:** `COMPLETE` (35/35 units, 140/150 generations)
**Decision:** **NO-GO for H1 (crossover_fixed does not generalize)**

## 1. Executive Summary

R6 tested whether R5's crossover_fixed improvement generalizes to new tasks. **It does NOT.** On 5 new tasks, crossover_fixed (46.7%) did NOT outperform original crossover (53.3%). The format constraint DOES reduce format failures (H2 supported), but this does not translate to higher effective success on new tasks. R5's 9/9 result was task-specific.

## 2. R5 Conclusion Boundary Correction

R5 completed 37/60 units (61.7%). The 9/9 crossover_fixed result supports ONLY:
> "In the 9 observed child samples on R5 tasks, crossover_fixed achieved effective success."

R6 **FALSIFIES** the generalization claim.

## 3. Experiment Integrity

| Item | Value |
|------|-------|
| Units completed | 35/35 (100%) |
| Actual generations | 140/150 |
| Wall clock | 84.5s / 300s |
| Ledger = runtime count | ✅ |
| Token delta = runtime total | ✅ |
| Revision match | ✅ |
| New tasks (not in R1-R5) | 5/5 ✅ |

## 4. Independent Metric Recomputation

### Arm Comparison

| Metric | C0 (crossover) | C1 (format only) | C2 (crossover_fixed) |
|--------|---------------|-----------------|---------------------|
| n | 15 | 5 | 15 |
| Parent effective_success | 8/15 (53.3%) | 3/5 (60.0%) | 8/15 (53.3%) |
| **Child effective_success** | **8/15 (53.3%)** | **3/5 (60.0%)** | **7/15 (46.7%)** |
| Improved | 3 | 0 | 0 |
| Degraded | 3 | 0 | 1 |
| Child format_compliant | 13/15 (86.7%) | 5/5 (100%) | 15/15 (100%) |
| Child tool_path_valid | 15/15 (100%) | 5/5 (100%) | 15/15 (100%) |

### Paired C0 vs C2 (same task/seed)

| Outcome | Count |
|---------|-------|
| C2 wins | 2 |
| C0 wins | 3 |
| Ties | 10 |

**Net result: C0 slightly ahead (3 vs 2 wins).**

## 5. Hypothesis Assessment

| Hypothesis | Verdict | Evidence |
|------------|---------|----------|
| **H1:** crossover_fixed > crossover on new tasks | **NOT SUPPORTED** | C2=46.7% vs C0=53.3% |
| **H2:** Format constraint reduces format failures | **SUPPORTED** | C0=86.7% → C1/C2=100% |
| **H3:** Not task/seed artifact | **N/A** | H1 failed regardless |
| **H4:** No tool_path sacrifice | **SUPPORTED** | Both 100% tool_path |

## 6. Per-Task Analysis

| Task | C0 | C1 | C2 | Pattern |
|------|----|----|-----|---------|
| B2-007 | 0/3 | 1/1 | 1/3 | Both low (hard task) |
| B2-008 | 0/3 | 0/1 | 0/3 | Both fail (format-sensitive) |
| B2-009 | 3/3 | 1/1 | 3/3 | Both succeed |
| B2-010 | **3/3** | 0/1 | **0/3** | **C0 >> C2** |
| B2-011 | 2/3 | 1/1 | **3/3** | **C2 > C0** |

**B2-010 is the key differentiator:** C0=3/3 but C2=0/3. The crossover_fixed changes hurt performance on this task.

## 7. Mechanism Ablation Results

### C1 vs C0 (format constraint effect)
- C0 format failures: 2/15 (13.3%)
- C1 format failures: 0/5 (0%)
- **Format constraint DOES reduce format failures**

### C1 vs C2 (other changes effect)
- C1 effective_success: 3/5 (60.0%)
- C2 effective_success: 7/15 (46.7%)
- **C2's additional changes (strategy recombination, workflow preservation) do NOT help on new tasks**

### Root Cause Analysis
R5's crossover_fixed included:
1. Format constraint (H2 factor) — CONFIRMED EFFECTIVE
2. Strategy recombination changes — MAY HURT on some tasks
3. Workflow preservation — NO CLEAR EFFECT

**The format constraint is the only confirmed improvement. The other changes may be detrimental.**

## 8. R5 vs R6 Comparison

| Metric | R5 (R5 tasks) | R6 (new tasks) |
|--------|---------------|----------------|
| C0 effective_success | 3/9 (33.3%) | 8/15 (53.3%) |
| C2 effective_success | 9/9 (100%) | 7/15 (46.7%) |
| C2 > C0? | YES (+66.7%) | **NO (-6.7%)** |

**R5's result was task-specific. The 100% success rate does NOT generalize.**

## 9. Decision

| Component | Decision | Evidence |
|-----------|----------|----------|
| **H1 (generalization)** | **NO-GO** | C2=46.7% < C0=53.3% |
| **H2 (format constraint)** | **GO** | Format failures reduced |
| **crossover_fixed as package** | **NO-GO** | Net negative on new tasks |
| **Format constraint alone** | **CANDIDATE** | C1 shows promise (60%) |

## 10. Recommendations

1. **Do NOT deploy crossover_fixed as-is** — it hurts performance on some tasks
2. **Consider deploying ONLY the format constraint** — separate from strategy changes
3. **R7 should test: original crossover + format constraint ONLY (C1) on more tasks**
4. **Investigate B2-010 failure** — why does crossover_fixed fail where original succeeds?

## 11. Boundary Compliance

R1-R5 data preserved | Family C not accessed | PC1 not executed | Controller not trained | Formal G3 FAIL

## 12. Artifacts

`research/runs/20261029T064914Z_R6/` — R6_RAW.json, R6_LEDGER.jsonl (140 rows), R6_FROZEN_MANIFEST.json, R6_RESULT_MANIFEST.json
