# Planner Latest Plan — R3 Independent Review Complete / R4 Proposal

**Branch:** `c7-g3-diag-v2-r1-fastpath`
**R3 reviewed commit:** `1c51a718ebc85c4dd6b0ed6ebdad9e25238aba7e`
**R3 Run ID:** `20261029T052350Z_R3`
**Independent review:** `research/G3_DIAG_R3_INDEPENDENT_REVIEW.md`

## R3 Independent Review Verdict

**ACCEPT NEGATIVE RESULTS WITH LIMITATIONS.**

- All R3 metrics independently recomputed from `R3_RAW.json` paired_rows: 16/16 match reported values.
- All integrity checks pass (hashes, ledger, tokens, counts).
- **tool_subset_edit: NEGATIVE.** 0/9 child hard_validity (always breaks tool path). McNemar exact p=0.0156.
- **crossover: NEGATIVE.** answer_correct 77.8%→44.4% (-33.3%). Format failures 6/9. McNemar p=0.125.
- Statistical power LOW (n=9, effective n≈3 tasks). Cannot prove universality.
- Offline selection audit: hard constraint filter rejects ALL tool_subset_edit children (0 survive). Format check identifies crossover degradation. All mechanisms are post-execution.

## What is established

1. R3 is internally consistent and independently verifiable.
2. Both operators degrade child effective_success in the tested conditions.
3. Post-execution hard constraint filtering (tool_path + format) is a viable selection strategy.
4. Pre-execution prevention would require static analysis of child workflow/tool changes.

## What is NOT established

1. Universality of operator degradation (n=9, 3 tasks).
2. That selection mechanisms generalize beyond the current task set.
3. That the operators can ever produce beneficial children.
4. Any performance improvement claim.

## Next experiment: R4 Selection-Mechanism Validation (PROPOSAL)

**Status: PROPOSED — NOT AUTHORIZED. Requires Planner approval before execution.**

| Parameter | Value |
|-----------|-------|
| Hypothesis | Hard filter (tool_path+format) + parent-child selection rejects ≥90% harmful children |
| Falsification | Filter accepts >10% harmful OR rejects >20% beneficial |
| Tasks | B2-001, B2-003, B2-004, B2-005 (new), B2-006 (new) |
| Seeds | 5 pre-registered |
| Operators | tool_subset_edit, crossover, workflow_step_edit (control) |
| Selection mechanisms | M1-M4 (unfiltered, hard filter, filter+select, random) |
| Max model.generate | 150 |
| Max wall clock | 600s |
| Statistical method | McNemar exact, Wilson 95% CI |
| Stop rules | Budget exhausted → INCONCLUSIVE; Canary fail → STOP |

**Requires before execution:**
1. Freeze new tasks B2-005, B2-006 with gold labels and tool-path contracts.
2. Pre-register R4 protocol with SHA-256 manifest.
3. Planner authorization for 150 model.generate calls.

## Frozen boundaries (unchanged)

- Formal G3 remains FAIL.
- PC1 remains unapproved/unexecuted.
- Family C remains unaccessed.
- Controller training remains unauthorized.
- R1/R2/R3 raw data preserved.
