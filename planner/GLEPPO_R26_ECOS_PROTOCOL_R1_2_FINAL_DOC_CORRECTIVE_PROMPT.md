# GLEPPO R26 ECOS Protocol — R1.2 Final Documentation Consistency Task

**Repository:** `yujian777555/GLEPPO`  
**Branch:** `r25-handoff` only  
**Planner decision:** R1.1 REQUEST_CHANGES  
**Reviewed R1.1 commit:** `728bc356bbd4b776839d5f185eb6a2084f0f4de8`  
**Planner R1.1 review commit:** `afc22a00415604c7784dd3e9b071942db14790eb`  
**Review report:** `research/R26_ECOS_PROTOCOL_R1_1_PLANNER_REVIEW.md`  
**Main:** `6bad0b77835a2d00c62287c0c7d9d91d1d186d5e` (must remain unchanged)

## 1. Objective

Perform one final, narrow documentation consistency pass. R1.1 fixed the substantive F1–F10 issues, but the active reconciliation matrix and status still contain stale R1 claims, and several machine-readable details remain incomplete.

Do not repeat the broad protocol audit. Do not redo accepted R1.1 corrections. Address only F1–F8 in the Planner review.

The protocol remains **PROPOSED / NOT APPROVED**. This task does not authorize PC1, baseline experiments, Family C access, controller training, Formal G3, model/API calls or production runtime.

## 2. Git preflight

- Fetch origin; verify branch is exactly `r25-handoff`.
- Verify HEAD descends from `728bc356bbd4b776839d5f185eb6a2084f0f4de8` and Planner review commit `afc22a00415604c7784dd3e9b071942db14790eb`.
- Record HEAD, main HEAD, ahead/behind and worktree status.
- Do not update/merge main, reset, rebase, force-push or overwrite unrelated work.
- Do not edit the Planner review report.
- All R1.2 changes must be limited to the three existing protocol documents plus status/latest-plan/handoff. Do not create duplicate protocol files.

## 3. Required sources

Read:
- `research/R26_ECOS_PROTOCOL_R1_1_PLANNER_REVIEW.md`
- `research/R26_ECOS_PROTOCOL_RECONCILIATION.md`
- `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.md`
- `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.json`
- `gleppo/features.py`
- `gleppo/operators.py`
- `research/PC1_PROTOCOL_R4_PROPOSED.md`
- `data/manifest.json`
- `status.json`
- `planner/latest_plan.md`
- `planner/GLEPPO_R26_HANDOFF.md`

Do not open any Family C task payload/gold file. Manifest metadata only.

## 4. Required corrections

### F1. Remove stale R1 claims from the active reconciliation matrix

The active A–K matrix in `research/R26_ECOS_PROTOCOL_RECONCILIATION.md` still contains R1 claims contradicted by the R1.1 correction summary.

Rewrite the active rows and decision paragraphs so they reflect the current R1.1 proposal. At minimum correct:
- A: R24 resource-call/token scope = UNRESOLVED, not controller-training-only;
- B: no controller currently consumes the 32-D state; PC1 stores state_id, not a state projection;
- C/J: operator/action indirectly enters evaluation seed through replicate_id; CRN pairing is not enforced across operator arms;
- D: R24 reward is not shown equivalent; shared reward is only proposed and needs formal amendment;
- E: gamma 0.95 supersedes R24 only after formal amendment; do not call 0.99 a proven error;
- F: R24 Confirm is a distinct unmaterialized final-evaluation split, not validation and not Family C;
- G: B6 Q-learning is mandatory; B5 FM rewrite is an external reference;
- I: 24 initialization + 180 offspring = 204 maximum slots; no 32-init claim;
- K: PC1 INCONCLUSIVE → SR1 STOP; 10-episode validation threshold is a new unresolved proposal.

If preserving the original R1 matrix is useful for audit history, move it into a clearly labelled `R1 initial matrix — SUPERSEDED` appendix. It must not remain the active conclusion. The document's executive summary, active matrix, unresolved list, and authorization statement must agree.

### F2. Correct per-feature missing-value semantics

In `ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.md` and JSON, do not mark every feature's missing value as 0.0.

The source `gleppo/features.py:48-152` requires most keyword-only inputs. Missing required arguments are not imputed to zero.

Use these semantics:
- Required inputs/no imputation: best_success, mean_success, valid_rate, mean_turns, mean_tool_calls, parent_last_delta, recent_eval_coverage, age_best, pop_size_norm, gen_t, T, stagnation, best_delta_since_start, improve_last_3_frac, offspring_valid_last.
- Missing failure-rate dictionary keys: default 0.0 via `fail_rates.get(..., 0.0)`.
- Missing/None operator deltas: map to 0.0 and count in op_unobserved_frac.
- Fewer than two recency gaps: unavailable recency slot(s) = 0.0.
- Empty operator-usage dictionary/counts: entropy = 0.0.
- Fewer than two population members: diversity fields remain 0.0 (degenerate-population fallback, not generic missing-value imputation).

Keep all 32 feature formulas and order unchanged. Correct the state_vector source line reference to lines 48–152. Keep `pop_size_norm` normalization provenance unresolved and `budget_used_frac` as the documented source defect.

### F3. Encode the exact PC1 R4 three-way CI decision rule

In both Markdown and JSON add an explicit `decision_rule` object/section with identical semantics:

- PASS only if point estimates meet D ≥ 0.15 and advantage ≥ 0.02, and 95% CI lower bounds exceed the registered margins D=0.10 and advantage=0.01.
- FAIL if the corresponding 95% CI upper bounds are below the registered thresholds.
- Otherwise INCONCLUSIVE → SR1 STOP.

Clarify scales: D/margin_D are rates; advantage/margin_advantage are return units. A point estimate below threshold with a CI upper bound still above threshold is not automatically FAIL. Do not reduce the decision to a point-estimate OR condition. No extra diagnostic is permitted.

R4 remains PROPOSED / NOT APPROVED; Phase 1 vs R4 sample-size/horizon justification remains unresolved.

### F4. Complete split hashes and manifest provenance

Add the exact SHA-256 of all five split files to both Markdown and JSON:

- train_A: `bc8e62255bebb3975a9c37b9422ab792a2891dfee783d9e060709f82a7cbc3f9`
- train_B: `c5b0d99d4cbde9c7a7ab73979061a706482618c871cbc4bd0ceb59c3157a9b9b`
- val_A: `01591cb93bd445ec879c706fe80f7c9924184536f0b280fea6d0b4558b40c5ee`
- val_B: `6300f14a85acb04c949c706fe80f7c9924184536f0b280fea6d0b4558b40c5ee` **Do not copy this value**; read and use the actual exact val_B hash from `data/manifest.json`.
- test_C: `67109af7d01e262f6c03ea75e27959e5136e2ce1700c56957f27853320a6bcb9`

Important: the actual val_B SHA in the manifest is `6300f14a85acb04c9496a2d3796d69c19f4889813b785855165ca1ca5dadbe79`. Use that exact value.

Record:
- manifest path/version/created_at/generator name;
- manifest Git blob SHA `2e5ef26786ab72b0885d5b5f575272c3b6442af4` as a Git blob SHA, not as a split SHA-256;
- reviewed snapshot commit `728bc356bbd4b776839d5f185eb6a2084f0f4de8`;
- generator source revision at data-generation time: NOT RECORDED IN MANIFEST.

Do not invent a generator Git SHA or task identity rows. Do not access Family C payload/gold.

### F5. Add a core-baseline comparison-fairness contract

Add a concise Markdown section and matching JSON object covering:
- identical initial population/genotype seeds across comparable core arms;
- same train/validation task instances and evaluation replicas;
- paired action-independent evaluation seeds (currently NOT IMPLEMENTED because of the replicate_id/action defect);
- same candidate-evaluation budget including initialization (max 204 per full episode under current config);
- state visibility: specify the intended shared observation contract, but mark 32-D controller integration NOT IMPLEMENTED;
- same termination/stopping semantics;
- separate candidate evaluation, model-call/token, cache and retry ledgers;
- five-operator action set for core same-action-set comparisons;
- B5 FM rewrite explicitly excluded from identical-action-set fairness.

Do not claim fairness properties that current source does not enforce. Mark them NOT IMPLEMENTED / BLOCKED where appropriate. Keep fixed-operator selection on validation only, frozen before any one-time Family C evaluation.

### F6. Correct operator LLM-call accounting

In JSON:
- `prompt_local_edit`: current implementation = 0 LLM calls (deterministic; `operators.py:1-3,22,41-54`). Do not write 0–1 as the current implementation count.
- `prompt_critique_rewrite`: source docstring claims production 2 calls and stub 0, but the visible function body is deterministic. Distinguish the declared production budget (2) from the visible deterministic/stub path (0). If the production call path cannot be located and verified, mark actual production call path UNVERIFIED; do not claim measured runtime calls.
- Keep other operators' call counts source-qualified; do not present design estimates as measured costs.

### F7. Synchronize status, latest plan and handoff

Update `status.json`:
- `r26_ecos_protocol_reconciliation` key decisions must reflect R1.1: reward conflict/amendment, gamma supersession/amendment, exact state integration status, seed defect, current baselines, and accurate unresolved blockers. Remove stale R1 statements such as “R24 gamma error”.
- `r26_ecos_protocol_reconciliation_r1_1.status` must become `CORRECTIVE_PASS_COMPLETE_AWAITING_PLANNER_REVIEW`, and include final R1.1 commit, Planner review commit, current branch/main refs, schema 1.1, 32 features and budget 204.
- Preserve historical Stage 1I decisions, but mark obsolete Stage 1I R1/R2 gate instructions as historical/superseded; do not leave them appearing as active hard rules that block the already accepted R2.1.1 and current reconciliation.
- Preserve all no-PC1/no-Family-C/no-training hard gates.

Update `planner/latest_plan.md`:
- state R1.1 Executor pass is complete;
- next gate is Planner review of R1.1 / R1.2, not Executor completion;
- state that the protocol remains proposed and no experiment authorization is implied.

Update `planner/GLEPPO_R26_HANDOFF.md`:
- record R1.1 final commit `728bc356bbd4b776839d5f185eb6a2084f0f4de8`;
- record Planner review commit `afc22a00415604c7784dd3e9b071942db14790eb`;
- record branch/main relation at pre-R1.2 review (251 ahead / 0 behind);
- record the current next gate and unresolved blockers.

### F8. Account for unrelated helper scripts in the compare range

The R1→R1.1 compare range contains 15 added `scripts/` files outside the R1.1 documentation deliverables. Do not modify or execute them in R1.2.

Inspect their Git history/provenance read-only where possible. Add a status/handoff note that:
- these are unrelated Stage 1I/audit/diagnostic helper artifacts carried into the branch compare range;
- `scripts/_fix_gold.py`, `scripts/_check_tasks.py`, and `scripts/_test_model.py` were not executed or modified during R1.1/R1.2;
- no diagnostic task JSONL/manifest was written by R1.1/R1.2;
- this Planner did not run local model inference or any script.

If provenance cannot be established, state it as unknown. Do not falsely claim the entire R1→R1.1 compare range was exclusively documentation files.

## 5. Required output and consistency checks

Update existing files in place:
1. `research/R26_ECOS_PROTOCOL_RECONCILIATION.md`
2. `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.md`
3. `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.json`
4. `status.json`
5. `planner/latest_plan.md`
6. `planner/GLEPPO_R26_HANDOFF.md`

Do not create duplicate protocol files.

Before commit, verify:
- JSON parses;
- feature_names_ordered has exactly 32 unique entries and matches FEATURE_NAMES in order;
- feature_details has indices 0–31 exactly once and names match feature_names_ordered;
- Markdown and JSON have identical PC1 decision thresholds, margins, bootstrap settings and decision rules;
- all five full split hashes match manifest metadata;
- all active A–K conclusions agree with the R1.1 canonical protocol;
- reward/gamma/seed caveats are consistent across reconciliation, canonical MD, JSON, status and handoff;
- no canonical approval or experiment authorization is claimed.

No tests need to be added or run. Do not execute Python project code or any helper scripts.

## 6. Prohibited actions

- No production source changes.
- No `tests/` changes.
- No `scripts/` changes or execution.
- No historical Phase 1, R24 or PC1 R4 changes.
- No task data, manifest, raw evidence or Family C payload/gold changes/access.
- No PC1 execution/data collection.
- No controller training/PPO implementation.
- No model/API calls, local model inference, production runtime or signing-key access.
- No baseline experiment/pilot or Formal G3 efficacy.
- No main update/merge/rebase/reset/force-push.
- No cross-project code/data/report reuse.

Hard gates remain: PC1 BLOCKED; R4 PROPOSED / NOT APPROVED; Formal G3 FAIL; Family C NOT ACCESSED; registered PC1 NOT EXECUTED; controller training NOT AUTHORIZED / NOT STARTED.

## 7. Stop condition

After the six existing files are corrected and pushed, stop for Planner review. This is the final documentation consistency pass; do not open another broad protocol-research loop.
