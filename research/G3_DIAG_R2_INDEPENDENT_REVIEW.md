# Independent Review — G3-DIAG-v2-R2

**Review date:** 2026-10-29  
**Reviewed commit:** `d1a10a04f237f98bab32867fb8e8400788219458`  
**Run ID:** `20261029T040254Z_R2`  
**Verdict:** `ACCEPT WITH LIMITATIONS — DIAGNOSTIC EVIDENCE ONLY`

## 1. Evidence/accounting audit

I inspected `research/G3_DIAG_R2_RAW.json`, `research/G3_DIAG_R2_LEDGER.jsonl`, `research/G3_DIAG_R2_MANIFEST.json`, and `research/G3_DIAG_R2_REPORT.md`.

- Raw runtime generation count: 30.
- Ledger rows: 30.
- Unique, monotonically increasing call IDs: 30/30.
- Sum of per-call output-token deltas: 771, matching the raw runtime total.
- Raw run reports ledger/counter and token-sum checks as passing.
- The reference/child pairs reuse the same per-task/per-turn seed digests for both operators; this supports paired comparison for this diagnostic.
- All three baseline tool-path contracts pass.
- Model revision matches the frozen revision recorded in the run.

These checks support acceptance of the run as a bounded, internally consistent diagnostic. They do not independently prove a performance improvement or formal G3 passage.

## 2. Recomputed operator outcomes

### Baseline

| Task | Tool-path contract | Task answer correct |
|---|---|---:|
| B2-001 | PASS | 1 |
| B2-002 | PASS | 0 |
| B2-003 | PASS | 1 |

Baseline answer correctness is 2/3, based on one replicate per task. B2-002 is a known failure and cannot be described merely as a tool-path success: the tools return 49 then 43, but the final answer is `37`, while the gold answer is `43`.

### tool_subset_edit

| Task | Parent correct/path | Child correct/path | Interpretation |
|---|---|---|---|
| B2-001 | 1 / PASS | 0 / FAIL | Correctness and required path degraded |
| B2-002 | 0 / PASS | 0 / FAIL | No correctness gain; required path degraded |
| B2-003 | 1 / PASS | 1 / FAIL | Answer happens to remain correct, but required path is violated |

Recomputed result: behavior_changed = 3/3, child path validity = 0/3, child correctness = 1/3. The behavior-change threshold passes, but this is **not operator success**. It is evidence that the edit can change the genotype/execution and that the current child violates the task's tool-path constraint on every task.

### crossover

| Task | Parent correct/path | Child correct/path | Interpretation |
|---|---|---|---|
| B2-001 | 1 / PASS | 0 / PASS | Tool path retained; answer/format correctness degraded |
| B2-002 | 0 / PASS | 0 / PASS | No correctness gain; baseline task still unsolved |
| B2-003 | 1 / PASS | 0 / PASS | Tool path retained; answer/format correctness degraded |

Recomputed result: behavior_changed = 3/3, child path validity = 3/3, child correctness = 0/3. The behavior-change threshold passes, but the paired outcome is negative: two previously correct parent answers become incorrect, and no child task is correct.

## 3. Scientific interpretation

The diagnostic supports only these claims:

1. Both operators can cause observable execution/answer changes under the tested paired seeds.
2. `tool_subset_edit` can remove or replace a required tool step and thereby violate the frozen tool-path contract.
3. `crossover` preserves the required tool path in these three cases but disrupts answer correctness/format.
4. Behavior change is not a positive outcome metric. It can reflect degradation.
5. The current experiment does **not** demonstrate that either operator improves fitness, that the evolutionary selection mechanism rejects harmful children, or that an EC controller should be trained.

The task suite is still too small (three tasks, one replicate per task) for a performance claim. B2-002 also has a baseline correctness failure. Do not relabel it as a pass simply because its tools followed the required path.

## 4. Decision on the requested gates

| Gate | Decision |
|---|---|
| R2 diagnostic evidence | ACCEPT WITH LIMITATIONS |
| Claim that operator behavior is observable | ACCEPT, narrowly |
| Claim of operator effectiveness/performance gain | NOT ESTABLISHED |
| Formal G3 | FAIL — unchanged |
| Formal G3 protocol revision | Do not request approval on the strength of 3/3 behavior changes alone; prepare a revised protocol proposal after a valid task/metric pilot |
| PC1 / controller training | NOT APPROVED / NOT RUN |
| Family C | Not accessed |

## 5. Next phase — R3 performance-validity pilot

Do not rerun the same 30-call R2 matrix. First freeze a small, corrected task/metric protocol:

1. Preserve B2-001/002/003 and all R2 artifacts unchanged.
2. Keep B2-002 marked as a failed baseline result. Add a new task ID (e.g. `B2-004`) for a separately specified two-stage tool task; do not overwrite or relabel B2-002. Require the final answer to be copied from the second tool result, without placing the gold answer in the task text.
3. Run a baseline canary with three distinct predeclared seeds. Require every required tool path to pass and at least 2/3 final answers to be correct; otherwise stop and redesign the task offline.
4. Define child success before running: hard validity requires required-tool path compliance and format compliance; performance is gold answer correctness. Report behavior change separately, never as a success criterion.
5. Run a bounded paired pilot over B2-001, B2-003 and the new B2-004 with at least three paired seeds per task, within a new hard cap of 100 actual model generations and 300 seconds. If the budget is insufficient for the complete predeclared matrix, stop and label it INCONCLUSIVE.
6. Include the unmodified reference, `tool_subset_edit`, and `crossover`. Report parent/child answer correctness, hard-validity rate, path pass rate, paired correctness deltas, and output-format failures. Treat a child that breaks a required path as invalid even if its answer string happens to match gold.
7. Do not begin PC1 or controller training. Formal G3 remains FAIL until a separate review approves a complete protocol that includes all required operators, sufficient replication, and predeclared acceptance thresholds.

## 6. Required implementation and handoff

- Update `planner/latest_plan.md` and `status.json` to reflect that R2 has run; the currently recorded status still says R2 has not run and must be corrected.
- Add R3 protocol and task files with hashes frozen before the model run.
- Add regression tests for the new task and for separating hard validity from task correctness.
- Run offline tests, then the canary, then the bounded paired pilot only if the canary gate passes.
- Preserve raw JSON, per-generation ledger, manifest, and independent recomputation output. No success claims based only on the `behavior_changed` counter.
