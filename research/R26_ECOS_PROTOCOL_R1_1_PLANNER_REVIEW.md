# R26 ECOS Protocol R1.1 — Planner Independent Review

**Date:** 2026-11-05  
**Repository:** yujian777555/GLEPPO  
**Branch:** r25-handoff  
**Reviewed Executor commit:** 728bc356bbd4b776839d5f185eb6a2084f0f4de8  
**Prior R1 commit:** 7423d5f7c753430a2f361400e1b39cd5b125aaf6  
**Main:** 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e  
**Decision:** REQUEST_CHANGES — R1.1 is substantially improved but not yet internally consistent or complete enough to approve.

## 1. Executive decision

R1.1 correctly addresses the central scientific issues raised in the first Planner review:

- the canonical JSON now contains the exact 32 FEATURE_NAMES in source order;
- the duplicate `budget_used_frac` feature is identified as a source defect;
- the feature vector is correctly described as not consumed by the current evolution loop/controller;
- R24 and shared generation reward are no longer claimed equivalent;
- the action-dependent replicate-ID seed path is acknowledged;
- Phase 1 and PC1 R4 sampling are described as materially different;
- the episode evaluation maximum is corrected to 204 (24 initialization + 180 offspring);
- Q-learning is restored as mandatory and FM rewrite is separated as an external reference;
- the R24 call/token scope remains unresolved;
- canonical protocol status remains PROPOSED / NOT APPROVED.

However, the corrective pass leaves contradictions in the reconciliation report and status, and introduces several source-to-contract inaccuracies. The R1.1 canonical proposal must not yet be approved.

This is a narrow documentation-consistency review. It does not reopen F1–F10 wholesale and does not authorize any experiment.

## 2. Git / artifact verification

- `r25-handoff` HEAD = `728bc356bbd4b776839d5f185eb6a2084f0f4de8`.
- Main HEAD remains `6bad0b77835a2d00c62287c0c7d9d91d1d186d5e`.
- Branch relation to main: 251 ahead / 0 behind.
- Relative to R1 commit `7423d5f7c753430a2f361400e1b39cd5b125aaf6`: 7 commits ahead / 0 behind.
- The R1.1 JSON parses; `schema_version=1.1`; the ordered feature-name list has 32 entries and matches `gleppo/features.py:13-22`.
- Main was not modified.
- The compare range contains no changes under `gleppo/`, `tests/`, or `data/`; the three protocol deliverables and planner/status files are updated.
- No combined CI statuses or PR-triggered workflow runs were returned for the reviewed commit. This review does not claim tests or runtime were executed.
- The compare range also contains 15 added `scripts/` artifacts. These are outside the documentation-only R1.1 deliverables. In particular, `scripts/_fix_gold.py` writes diagnostic task JSONL/manifest files, `scripts/_check_tasks.py` reads diagnostic task gold values, and `scripts/_test_model.py` imports/loads `ProductionLLM` and performs local inference. They were not executed by this Planner review. Their provenance and non-execution must be recorded; do not run them as part of R1.2.

No Family C JSONL or task payload/gold file was opened. The manifest metadata only was inspected.

## 3. Findings requiring one focused R1.2 documentation pass

### F1 — The active A–K matrix in the reconciliation report still contains R1 false claims

`research/R26_ECOS_PROTOCOL_RECONCILIATION.md` appends an R1.1 correction summary, but the active A–K matrix and its surrounding decision paragraphs remain the R1 version. Examples:

- A: R24 model-call/token limits are still labelled controller-training compute only; R1.1 correctly says scope is unresolved.
- B: PC1 is still called a diagnostic projection and the controller is still said to use 32-D state; R1.1 correctly says PC1 stores only state_id and no controller consumes the vector.
- C/J: Action/genotype is still marked excluded from evaluation seeds; R1.1 correctly identifies operator/action entering indirectly through replicate_id.
- D: R24 reward is still called a simplified description/error and one shared reward is asserted; R1.1 correctly says the formulas are not shown equivalent and amendment is required.
- E: R24 gamma 0.99 is still called a preregistration error; R1.1 correctly says gamma 0.95 supersedes it only after amendment.
- F: R24 Confirm is still reclassified as additional validation; R1.1 correctly says it is a distinct unmaterialized final-evaluation split.
- G: B6 is still in the strong tier; R1.1 correctly makes Q-learning mandatory.
- I: candidate evaluation remains 180 and the old 32 initialization-slot statement remains; R1.1 correctly calculates 24 + 180 = 204.
- K: the matrix still permits one extra diagnostic after inconclusive and proposes a 10-episode validation rule as if canonical; R1.1 correctly restores INCONCLUSIVE → SR1 STOP and labels the 10-episode threshold as a new proposal.

Appending a correction summary does not make the active matrix internally consistent.

**Required correction:** Rewrite the active A–K rows/decision paragraphs to reflect R1.1. If the original R1 matrix must be preserved for audit history, move it under an explicitly labelled `R1 initial matrix — SUPERSEDED` appendix. The top-level executive conclusion, current matrix, unresolved list and authorization statement must all refer to R1.1 as the current proposal. Do not leave contradictory active conclusions.

### F2 — Feature missing-value semantics are incorrect

The 32 names and most formulas now match the source, but the canonical Markdown and JSON mark `missing=0.0` for almost every feature.

In `gleppo/features.py:48-71`, most `state_vector()` inputs are required keyword-only arguments with no defaults. Missing `best_success`, `mean_success`, `valid_rate`, `mean_turns`, `mean_tool_calls`, `parent_last_delta`, `recent_eval_coverage`, `age_best`, `pop_size_norm`, `gen_t`, `T`, `stagnation`, `best_delta_since_start`, `improve_last_3_frac`, or `offspring_valid_last` is not imputed to zero; the call cannot be made without the argument.

Actual fallback behavior is narrower:

- absent failure-rate keys use `fail_rates.get(..., 0.0)`;
- missing/None operator deltas map to zero and increment `op_unobserved_frac`;
- fewer than two recency gaps produce zero for the unavailable recency slots;
- empty operator usage yields zero entropy;
- fewer than two population members leaves diversity at zero.

The source reference for `state_vector()` is also wrong: it starts at line 48 and extends through line 152, not lines 43–117.

**Required correction:** For every feature, distinguish required input/no imputation from actual default/fallback behavior. Identify degenerate-population fallbacks separately from missing data. Correct the source line range. Keep `pop_size_norm` normalization provenance unresolved.

### F3 — PC1 CI decision rule is not fully encoded in Markdown or JSON

R1.1 restores all numeric PC1 thresholds and bootstrap parameters, but does not encode the exact R4 decision rule.

Current JSON:
- `pc1_sampling.r4_statistics` contains thresholds, margins, clusters, bootstrap count/seed;
- `stop_rules.pc1_fail` says `D < 0.15 OR advantage < 0.02 (with CI)`;
- `stop_rules.pc1_inconclusive` says `CI overlaps threshold`.

That is not equivalent to R4's three-way rule. In particular, a point estimate below threshold with an upper CI still above threshold is not automatically FAIL; it may be INCONCLUSIVE.

**Required correction:** Add an explicit machine-readable `decision_rule` and identical Markdown wording:

- PASS only when point estimates meet D ≥ 0.15 and advantage ≥ 0.02, and the 95% CI lower bounds exceed the registered margins D=0.10 and advantage=0.01;
- FAIL when the corresponding 95% CI upper bounds are below the registered thresholds;
- otherwise INCONCLUSIVE → SR1 STOP.

State that the CI margins are on D-rate and reward-return/advantage scales respectively. Do not permit another diagnostic. Keep R4 PROPOSED / NOT APPROVED and sample-size/horizon justification unresolved.

### F4 — Split hashes and manifest provenance are incomplete in the machine-readable contract

The committed `data/manifest.json` contains SHA-256 values for all five splits. R1.1 JSON includes only the Family C split hash. The Markdown table abbreviates each hash to eight characters.

Exact manifest split hashes:

- train_A: `bc8e62255bebb3975a9c37b9422ab792a2891dfee783d9e060709f82a7cbc3f9`
- train_B: `c5b0d99d4cbde9c7a7ab73979061a706482618c871cbc4bd0ceb59c3157a9b9b`
- val_A: `01591cb93bd445ec879c706fe80f7c9924184536f0b280fea6d0b4558b40c5ee`
- val_B: `6300f14a85acb04c9496a2d3796d69c19f4889813b785855165ca1ca5dadbe79`
- test_C: `67109af7d01e262f6c03ea75e27959e5136e2ce1700c56957f27853320a6bcb9`

The manifest file's Git blob SHA at the reviewed commit is `2e5ef26786ab72b0885d5b5f575272c3b6442af4`. This is a Git blob SHA, not a split-file SHA-256. The manifest records generator name and timestamp but no generator Git SHA; do not invent one.

**Required correction:** Put all five full split hashes in JSON and Markdown. Record the manifest blob SHA and reviewed snapshot commit separately from split SHA-256 values. Explicitly say the generator source revision at data-generation time is not recorded in the manifest.

### F5 — Baseline fairness contract requested in R1.1 is still missing

The R1.1 proposal correctly assigns B6 mandatory and B5 external, and says the best fixed operator is selected on validation only. But it does not define the common comparison contract requested by the corrective task.

The JSON baseline object has tiers and a fixed-selection note, but no explicit fields for:
- identical initial population/genotype seeds;
- paired task/evaluation seeds (subject to fixing the action-dependent seed defect);
- identical candidate-task evaluation budget including initialization;
- what state information each controller/bandit may observe;
- identical termination/stopping conditions;
- separate model-call/token and candidate-evaluation accounting;
- which arms share the five-operator action set and which are external references.

**Required correction:** Add a concise comparison-fairness contract for core same-action-set arms. Where current code cannot guarantee parity (especially CRN pairing and 32-D state integration), mark the item NOT IMPLEMENTED / BLOCKED rather than claiming fairness. Keep B5 outside identical-action-set comparisons.

### F6 — Action LLM-call counts do not match the active source description

R1.1 JSON records `prompt_local_edit` as `0-1` LLM calls. The active `gleppo/operators.py:1-3,22,41-54` explicitly describes it as deterministic with 0 LLM calls and implements deterministic text edits.

For `prompt_critique_rewrite`, the function docstring says production uses 2 LLM calls and stub mode is deterministic/0 calls, while the function body at lines 57-75 shown in the current module is a deterministic rewrite. The canonical JSON's `llm_calls=2` must not be presented as an independently verified active runtime call count without identifying the production call path.

**Required correction:** Set `prompt_local_edit` current implementation calls to 0. For `prompt_critique_rewrite`, distinguish documented production budget (2) from the visible deterministic function/stub path (0), and mark the actual production call path as unverified if it cannot be located. Do not use unverified call counts as measured costs.

### F7 — status/latest-plan/handoff are not synchronized to the R1.1 completion

The top-level `status.json` says R1.1 is ready for Planner review, but nested records remain stale:

- `r26_ecos_protocol_reconciliation.key_decisions` still records the R1 claim that the shared reward is canonical and R24 gamma 0.99 is an error;
- its unresolved blockers remain the old R1 list;
- `r26_ecos_protocol_reconciliation_r1_1.status` remains `CORRECTIVE_TASK_ISSUED`, not corrective pass complete;
- no final R1.1 commit/provenance is recorded in that nested object;
- `hard_rules` contains historical Stage 1I R1/R2 REQUEST_CHANGES instructions that are not labelled historical/superseded, despite R2.1.1 being ACCEPTED and reconciliation now being active.

`planner/latest_plan.md` still describes R1.1 as the active Executor task and its next gate as Executor completion → Planner review, even though the final paragraph says it is complete. The handoff says complete but does not record final commit `728bc356...` or the branch/main relation.

**Required correction:** Synchronize current R1.1 status, final SHA, branch/main refs, corrected unresolved blockers and next gate. Preserve prior Stage 1I review history, but clearly mark old gate instructions as historical/superseded rather than active hard rules. Set latest_plan's current gate to Planner R1.1 review.

### F8 — Unrelated helper scripts appear in the R1→R1.1 compare range

The Git compare from R1 to R1.1 shows 15 added `scripts/` files, which are not among the documentation-only R1.1 deliverables. They include audit scripts and diagnostic helpers; notably `_fix_gold.py` writes diagnostic task files/manifests and `_test_model.py` loads `ProductionLLM` for local inference.

No `data/`, `tests/`, or `gleppo/` files were changed in the compare range, and this review did not execute the scripts. Their introduction is nevertheless outside the stated documentation/planner/status-only scope unless they are explicitly identified as inherited artifacts from a separate prior workstream.

**Required correction:** Add a short provenance note to status/handoff stating these scripts are unrelated inherited Stage 1I artifacts, were not executed or modified during R1.1, and no diagnostic task data/manifest was written by this pass. Do not execute or edit them in R1.2. If their provenance cannot be established, leave them untouched and report the limitation; do not silently claim the entire compare range was documentation-only.

## 4. Accepted R1.1 corrections

Retain these corrections; do not redo them:

- exact ordered 32 FEATURE_NAMES;
- budget_used_frac duplicate-progress source defect;
- controller/PC1 state integration limitations;
- R24/shared reward non-equivalence and amendment requirement;
- action-dependent replicate_id seed defect;
- Phase 1 vs R4 sampling redesign and unresolved sample adequacy;
- actual disjoint template assignment and R24 Confirm unmaterialized distinction;
- 204 maximum episode slots (24 init + 180 offspring);
- unresolved R24 resource scope;
- B6 mandatory and B5 external reference;
- gamma 0.95 only supersedes R24 after formal amendment;
- R4 INCONCLUSIVE → SR1 STOP;
- canonical status PROPOSED / NOT APPROVED.

## 5. Decision and next action

**REQUEST_CHANGES — R1.1 is not accepted yet.**

Issue one final narrow R1.2 documentation consistency task covering F1–F8 above. Do not reopen the full scientific review or repeat F1–F10 analysis. Update the existing reconciliation, canonical Markdown/JSON, status/latest-plan/handoff only. No production source, tests, data, manifest, or historical protocol changes.

After R1.2 is committed, stop for Planner review. If the listed documentation inconsistencies are resolved, the canonical proposal can be considered for approval with its explicit unresolved blockers and implementation gates.

## 6. Hard gates remain unchanged

- PC1 BLOCKED; PC1 R4 PROPOSED / NOT APPROVED.
- Formal G3 FAIL.
- Family C NOT ACCESSED; no payload/gold access.
- Registered PC1 NOT EXECUTED.
- Controller training NOT AUTHORIZED / NOT STARTED.
- No model/API calls, production runtime, signing-key access or baseline experiments.
- No source, tests, task data, manifest, raw evidence or historical protocol changes.
- No main update/merge/rebase/reset/force-push.
- No cross-project code/data/report reuse.
