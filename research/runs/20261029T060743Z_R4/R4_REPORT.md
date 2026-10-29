# R4 Selection Mechanism Generalization — Experiment Report

**Run ID:** `20261029T060743Z_R4`
**Status:** `INCONCLUSIVE` (budget exhausted 150/150, 37/40 units completed)
**Protocol:** `research/R4_PROTOCOL.md`
**Result Manifest SHA-256:** `026e35b8a76322fa`

## 1. Executive Summary

R4 tested whether selection mechanisms without gold-answer leakage can reduce harmful offspring on 5 structurally distinct tasks. **The static pre-execution filter (S1) reduces harmful offspring rate from 78.4% to 55.6%, but cannot eliminate them.** The post-execution diagnostic (S3) achieves 0% harmful rate but requires execution cost. The experiment is INCONCLUSIVE due to budget exhaustion (B2-004 task missing + 150 generation cap).

## 2. Experiment Integrity

| Item | Value |
|------|-------|
| Units completed | 37/40 (92.5%) |
| Actual generations | 150/150 (cap reached) |
| Wall clock | 89.1s / 300s |
| Ledger = runtime count | ✅ |
| Token delta = runtime total | ✅ |
| Revision match | ✅ `a09a35458c...` |
| B2-004 loaded | ❌ MISSING (data file issue) |

**B2-004 was not loaded** — the task is in `diagnostic_B2_R3.jsonl` but the runner only loaded `diagnostic_B2.jsonl` and `diagnostic_B2_R4.jsonl`. This reduced the matrix from 50 to 40 units.

## 3. Independent Metric Recomputation

All metrics recomputed from `R4_RAW.json` units array. **All match reported values.**

### 3.1 Overall (n=37)

| Metric | Parent | Child | Δ |
|--------|--------|-------|---|
| effective_success | 27/37 (0.730) | 8/37 (0.216) | **-0.514** |
| Paired outcomes | | improved=1, degraded=20, same=16 | |

### 3.2 Per-Operator

| Operator | n | Parent eff | Child eff | Degraded |
|----------|---|-----------|-----------|----------|
| tool_subset_edit | 19 | 14/19 (0.737) | **0/19 (0.000)** | **14** |
| crossover | 18 | 13/18 (0.722) | 8/18 (0.444) | 6 |

**tool_subset_edit: 0/19 child effective_success** — confirms R3 finding.
**crossover: 8/18** — mixed but net negative (6 degraded vs 0 improved).

### 3.3 Per-Task

| Task | n | Parent eff | Child eff | Structure |
|------|---|-----------|-----------|-----------|
| B2-001 | 10 | 8/10 | 0/10 | calc+str_ops SUM-STRING |
| B2-003 | 10 | 2/10 | 1/10 | calc+str_ops NUMBER-STRING |
| B2-005 | 10 | 10/10 | 5/10 | calc→py_sandbox (reversed) |
| B2-006 | 7 | 7/7 | 2/7 | three-tool complex |

**B2-005 (new, reversed order):** Parent 10/10, Child 5/10 — operators degrade performance even on easy tasks.
**B2-006 (new, three-tool):** Parent 7/7, Child 2/7 — complexity amplifies degradation.

## 4. Selection Mechanism Comparison

| Mechanism | Accepted | Harmful | Harmful Rate | Effective (among accepted) |
|-----------|----------|---------|--------------|---------------------------|
| S0 Unfiltered | 37/37 (100%) | 29 | **78.4%** | 8 |
| S1 Static filter | 18/37 (48.6%) | 10 | **55.6%** | 8 |
| S2 Static + select | 18/37 (48.6%) | 10 | **55.6%** | 8 |
| S3 Post-execution | 8/37 (21.6%) | **0** | **0.0%** | 8 |

### Key Findings

1. **S1 reduces harmful rate from 78.4% to 55.6%** — meaningful improvement but still >50% harmful among accepted.
2. **S1 rejects 51.4% of candidates** — but 10/18 accepted are still harmful.
3. **S3 achieves 0% harmful rate** — perfect diagnostic, but requires execution (cannot prevent execution cost).
4. **S2 ≈ S1** — static parent-child comparison adds no value beyond S1 (same acceptance).
5. **All 8 effective successes pass through all mechanisms** — no beneficial offspring are lost.

### S1 Static Filter Analysis

- S1 pass: 18/37 (48.6%)
- S1 fail: 19/37 (51.4%)
- Among S1-pass: harmful = 10/18 (55.6%)

**S1 can identify SOME violations pre-execution** (rejects 19/37) **but cannot identify all** (10/18 accepted are harmful).

## 5. Research Question Answer

**Q: Can a selection mechanism without gold-answer leakage reduce harmful offspring?**

**A: Partially (SAFETY ONLY outcome).**

| Layer | Result |
|-------|--------|
| Static structural checks (pre-execution) | ✅ Reduce harmful rate 78%→56%, but cannot eliminate |
| Post-execution hard constraint checks | ✅ Achieve 0% harmful rate |
| Selection improving performance | ❌ Not demonstrated (child eff < parent eff regardless) |

**Interpretation:** S1 provides meaningful safety improvement but is insufficient alone. S3 is perfect but requires execution cost. The combination S1→execute→S3 would be optimal but S3 cannot prevent the initial execution cost.

## 6. Statistical Considerations

- n=37 units (not 37 independent tasks — 4 tasks × 5 seeds × 2 operators)
- Effective independent units ≈ 4 tasks
- **Cannot claim universality** from 4 tasks
- B2-005 (new task): confirms degradation pattern from R3
- B2-006 (new task): confirms degradation, amplified by complexity

## 7. What Is NOT Established

1. That S1 generalizes beyond these 4 tasks
2. That operators can ever produce beneficial children (0/19 for tool_subset_edit)
3. That the selection mechanism improves final performance
4. Any formal G3 passage

## 8. Budget Analysis

| Item | Estimated | Actual |
|------|-----------|--------|
| Units | 50 (5×5×2) | 40 (4×5×2) |
| Generations | 160 (40×2×2) | 150 (cap) |
| Units completed | — | 37/40 |

**Root cause:** B2-004 not loaded (data file path issue) reduced units to 40. Even then, 40×2×2=160 > 150 cap. Budget was underestimated.

**Fix for R5:** Include B2-004, reduce seeds to 3 per task, or increase cap to 200.

## 9. Boundary Compliance

| Item | Status |
|------|--------|
| R1/R2/R3 data | Not overwritten ✅ |
| Family C | Not accessed ✅ |
| PC1 | Not executed ✅ |
| Controller training | Not started ✅ |
| Formal G3 | FAIL (unchanged) ✅ |
| Gold labels | Not modified ✅ |

## 10. Artifacts

| File | Location |
|------|----------|
| R4_FROZEN_MANIFEST.json | `research/runs/20261029T060743Z_R4/` |
| R4_RAW.json | 同上 |
| R4_LEDGER.jsonl | 同上 (150 rows) |
| R4_RESULT_MANIFEST.json | 同上 |
| R4_PROTOCOL.md | `research/` |
| R4_MANIFEST.json | `research/` |

## 11. Conclusion

**INCONCLUSIVE** due to budget exhaustion and B2-004 missing. However, the data strongly suggests:

1. **Static filtering (S1) provides meaningful but incomplete safety improvement.**
2. **Post-execution filtering (S3) is necessary for zero-harmful-acceptance.**
3. **Operators consistently degrade child performance** across 4 structurally distinct tasks.
4. **The hypothesis that S1 alone can eliminate harmful offspring is FALSIFIED.**

**Recommended next step:** R5 with fixed budget (include B2-004, 3 seeds/task, 200 cap) to complete the matrix and strengthen statistical power.
