# R26 ECOS Protocol Reconciliation — Planner Independent Review

**Date:** 2026-11-05  
**Repository:** yujian777555/GLEPPO  
**Branch:** r25-handoff  
**Reviewed Executor commit:** 7423d5f7c753430a2f361400e1b39cd5b125aaf6  
**Accepted base:** 362f343f43befc7f43c00ba5edd1059b01d523d1  
**Main:** 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e  
**Decision:** REQUEST_CHANGES — canonical protocol is not ready for approval.

## 1. Executive decision

The three deliverables exist, the JSON parses, the proposal is labelled PROPOSED / NOT APPROVED, the reviewed branch is based on the accepted R2.1.1 work, and no production source or tests were changed in this documentation phase.

However, independent source-to-contract checks found material omissions and incorrect claims. The current R1 proposal must not be approved or used as an executable contract.

The most serious defects are:

1. The JSON state schema contains only 25 feature labels for a claimed 32-dimensional vector, several labels do not match the source, and the implementation's `budget_used_frac` currently duplicates generation progress.
2. R24's reward is not shown to be equivalent to the shared generation reward; PC1's estimators consume pre-supplied reward traces rather than recomputing the shared reward.
3. The evolution call site derives `replicate_id` using `operator_name`, so the operator/action indirectly enters the effective evaluation seed despite the helper itself omitting it.
4. The PC1 design changes Phase 1's diagnostic from ≥200 states / ≥20 rollouts / horizon 5 to 100 states / 3 Q-rollouts / horizon 3 without fully reconciling the change or preserving the R4 CI decision rule.
5. The Phase 1 task-template split conflicts with the actual committed task generator/manifest, and the R24 Confirm split is reclassified without evidence.
6. Candidate-evaluation budget omits initialization evaluations; the report's stated 32 initialization slots are inconsistent with the active configuration, which yields 24.
7. Stop rules and baseline tiers silently change prior requirements or introduce thresholds not found in the cited preregistration.

This is a protocol-quality REQUEST_CHANGES, not a rejection of ECOS as a research direction. One focused corrective pass is required. Do not restart the 42-Finding audit and do not run experiments.

## 2. Git and artifact verification

At review:

- `r25-handoff` HEAD = `7423d5f7c753430a2f361400e1b39cd5b125aaf6`.
- The reviewed commit is six commits ahead of the accepted R2.1.1 base `362f343f43befc7f43c00ba5edd1059b01d523d1`, with zero commits behind.
- Main HEAD remains `6bad0b77835a2d00c62287c0c7d9d91d1d186d5e`.
- Branch relation to main: 244 ahead / 0 behind.
- The reconciliation Markdown, canonical Markdown and canonical JSON exist.
- The JSON parses and has `schema_version=1.0`, `status=PROPOSED_NOT_APPROVED`.
- The reviewed diff range contains documentation/planner/status changes only; no production source or `tests/` changes.
- No combined commit statuses or PR-triggered workflow runs were returned for the reviewed commit. This review does not claim CI or independent runtime execution.

Only `data/manifest.json` metadata was inspected for split provenance. No Family C JSONL, task payload or gold label was opened, loaded, executed or tuned.

## 3. Findings requiring correction

### F1 — The 32-dimensional state contract is not faithfully represented, and is not integrated into the evolution loop

**Evidence**

- `gleppo/features.py:10-24` declares `STATE_DIM=32` and the exact 32-entry `FEATURE_NAMES`.
- `gleppo/features.py:118-147` constructs the actual vector.
- `gleppo/features.py:139-142` shows the critical issue: the entry named `budget_used_frac` is currently computed as `_clip01(gen_t / max(1, T))`, duplicating `gen_frac`; `state_vector()` has no budget-used input.
- `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.json` lists 11 + 8 + 6 = 25 feature labels while declaring 12 + 12 + 8 = 32 dimensions. It omits or mislabels actual fields.
- The JSON/Markdown incorrectly describe some fields: actual source has five separate `op_mean_delta_1..5`, `op_unobserved_frac`, `age_best`, and `pop_size_norm`; it does not have the proposed B-block names `best` and `mean`.
- Actual A-block field `recent_eval_coverage` and C-block field `offspring_valid_last` are missing from the proposed feature lists.
- `gleppo/evolution.py:14-17,183-216` does not import or call `state_vector`; `run_episode` receives an externally supplied `operator_schedule(t,pop,history)`.
- `gleppo/pc1.py:389-407` shows `StateActionRecord` stores a `state_id`, not a 32-dimensional state vector. The claim that PC1 uses a “diagnostic projection” of the controller state is not supported by this record schema.

**Required correction**

1. Publish the exact ordered 32-feature table using the names in `FEATURE_NAMES`, with one row per index.
2. Record the actual transform for every feature:
   - [0,1] clipped features;
   - signed [-1,1] fields (`parent_last_delta`, five operator deltas, `best_delta_since_start`);
   - explicit scales such as `mean_turns/24`, `mean_tool_calls/8`, `age_best/T`, `gen_t/T`, `stagnation/T`, and the recency formula;
   - `op_usage_entropy / log(5)`;
   - missing operator deltas mapped to zero with `op_unobserved_frac`;
   - unresolved input semantics such as `pop_size_norm`.
3. Do not describe all 32 values as [0,1].
4. Mark `budget_used_frac` as a current source defect / unresolved feature until its definition is fixed in a later approved code phase, or propose an explicit rename to a second generation-progress feature. Do not silently claim it measures budget.
5. State plainly that a feature-construction utility exists, but no committed PPO controller currently consumes it in `run_episode`. Do not say “the controller uses 32-D state”.
6. State plainly that PC1 records currently identify states by ID and do not contain the 32-D vector. Do not call them a feature projection without an implementation source.

### F2 — Reward equivalence is asserted without evidence; PC1 does not recompute the shared reward in its estimator

**Evidence**

- Phase 1 `research/PHASE1_DESIGN.md:185-196` specifies generation-level reward from population-best change, validity rate and population-mean change.
- `gleppo/reward.py:15-34` implements that generation reward.
- `gleppo/evolution.py:162-163` calls `generation_reward(best, prev_best, mean, prev_mean, valid_rate)`.
- R24 `research/R24_ECOS_CONTROLLER_PREREGISTRATION.md:24-28` instead states `effective_success(child) - effective_success(parent)`, with “immediate (per episode)” attribution. It does not define `effective_success` as the population-best/mean/validity aggregate.
- `gleppo/pc1.py:523-549` computes `r_hat` and `q_hat` from already-populated `StateActionRecord.gen_rewards`. These functions do not call `generation_reward`.
- In `pc1.py`, `generation_reward` is imported at line 22 and is called by the zero-cost protocol self-check at line 1495; that does not prove the PC1 estimator's supplied reward traces were generated by it.

**Required correction**

1. Remove the assertion that R24 is merely a simplified description of `Δbest`. The two formulas are materially different unless a missing definition is supplied.
2. The proposal may prefer the Phase 1/shared-code generation reward, but must state that this explicitly supersedes the R24 reward definition and requires a formal protocol amendment before execution.
3. Clarify whether PC1 raw records contain enough source metrics to recompute the shared reward. If not, document that reward provenance is not enforced by the estimator and list the future runner/schema change required.
4. Do not claim PC1 “uses the shared reward” solely because the module imports the function.

### F3 — Action/operator leaks into the evaluation seed through the evolution call site

**Evidence**

- `gleppo/evaluator.py:55-76` derives effective seed parts from task/state/rollout/replicate/replica fields and does not directly include action or genotype.
- However, `gleppo/evolution.py:136` supplies:
  `replicate_id=stable_seed(episode_id, t, j, operator_name) % 100000`.
- `replicate_id` is then consumed by `Evaluator.effective_seed_parts`, so the action/operator indirectly changes the evaluation seed.
- `gleppo/pc1.py:230-244` has a separate `crn_seed` and operator RNG path.

**Required correction**

1. Correct the reconciliation's claim that action is excluded from the effective evaluation seed at all call sites.
2. Record that paired common-random-number behavior across operator arms is not established by the current evolution call path.
3. Propose a later code amendment that derives evaluation seeds from a shared, action-independent typed schema and keeps operator-generation RNG separate.
4. List tests that must prove same task/state/rollout/replica inputs produce identical evaluation seeds across different actions/operators, while changes to each seed field change the seed.
5. Do not modify code or tests in this corrective documentation phase.

### F4 — PC1 R4 changes the Phase 1 myopia diagnostic but the proposal does not fully reconcile the redesign

**Evidence**

- Phase 1 `research/PHASE1_DESIGN.md:253-263` calls for at least 200 states, at least 20 Monte Carlo rollouts per state/action and continuation horizon h=5.
- PC1 R4 `research/PC1_PROTOCOL_R4_PROPOSED.md:15-29` specifies 100 states, 3 Q-rollouts, horizon 3, one extra immediate draw, and N_EVAL=2.
- R4 §7 specifies D/advantage thresholds, CI margins (0.10 and 0.01), cluster bootstrap over 40 collection episodes, 10,000 resamples and a fixed bootstrap seed.
- R4 §7 explicitly says INCONCLUSIVE → SR1 STOP.
- The new canonical proposal omits the CI margins and bootstrap contract from its machine-readable diagnostic definition, and instead permits “one additional diagnostic” after inconclusive.

**Required correction**

1. Explicitly mark R4 as a materially redesigned diagnostic relative to Phase 1, not a directly equivalent implementation of the Phase 1 sample plan.
2. Provide a rationale for the reduced state/rollout/horizon counts or mark the sample design unresolved. Do not claim adequacy without evidence.
3. Preserve all R4 statistical details in both Markdown and JSON: D threshold, advantage threshold, CI margins, cluster unit, bootstrap count, bootstrap seed and exact PASS/FAIL/INCONCLUSIVE rule.
4. Remove “one additional diagnostic permitted” unless a separately justified and approved amendment is proposed. R4's current rule is INCONCLUSIVE → SR1 STOP.
5. Keep R4 PROPOSED / NOT APPROVED; no diagnostic collection is authorized.

### F5 — Train/validation template split conflicts with Phase 1 text and the actual committed task generator

**Evidence**

- Phase 1 `research/PHASE1_DESIGN.md:287-303` says train/validation templates should be disjoint, but its listed template ranges at lines 298-301 overlap:
  - Train A TA1–TA8 vs validation A TA1–TA7;
  - Train B TB1–TB6 vs validation B TB1–TB5.
- Actual `gleppo/tasks.py:282-286,376-381` defines disjoint sets:
  - Train A TA1–TA7; validation A TA8–TA12;
  - Train B TB1–TB5; validation B TB6–TB9.
- `data/manifest.json:1-78` records 200/200 train, 50/50 validation and 100 Family C task counts, seed starts, templates and split-file hashes.
- R24 `research/R24_ECOS_CONTROLLER_PREREGISTRATION.md:43-51` defines 4 train, 4 validation and 4 confirm tasks × 3 seeds, but no matching Confirm split is present in the committed manifest.
- R24 labels Confirm as “Final evaluation”, not as validation.

**Required correction**

1. Explicitly record the Phase 1 template-range inconsistency.
2. For the currently committed generated splits, use the actual `tasks.py` / `data/manifest.json` disjoint template assignment, and cite the manifest hash and task-generator source revision. Do not combine contradictory Phase 1 template lists with the manifest.
3. Do not reclassify R24 Confirm as “additional validation”. It was registered as final evaluation. Record it as a distinct, currently unmaterialized split with no verified task identities; it cannot be used until formally amended.
4. Keep Family C as the Phase 1 held-out set, and continue to prohibit reading/executing/tuning its task payload or gold labels.
5. Do not claim the manifest contains per-task identity rows or generator Git SHA if it does not; distinguish manifest metadata from the generated JSONL files.

### F6 — Candidate-evaluation budget omits initialization and the episode termination contract is inconsistent

**Evidence**

- `gleppo/evolution.py:1-29` sets μ=8, λ=4, T=15 and n_eval=3.
- `gleppo/evolution.py:80-103,190-216` evaluates the initial μ individuals and records `planned_init_slots = μ × n_eval`, then adds λ × n_eval per generation.
- Maximum planned evaluations per full 15-generation episode are therefore:
  `8×3 + 15×4×3 = 24 + 180 = 204`, not 180.
- The reconciliation says “Initialization slots (32) must be included”, which is also inconsistent with μ=8 and n_eval=3.
- Phase 1 `research/PHASE1_DESIGN.md:200-204` defines early termination at T=15 OR best_success ≥0.95 OR environment exception.
- The current `run_episode` loop in `evolution.py:190-216` runs `range(cfg.T)` and does not implement the best_success ≥0.95 early-stop condition.

**Required correction**

1. Correct the maximum per-episode planned evaluation budget to 204 under the current μ/λ/T/n_eval configuration, with initialization separated from offspring evaluations.
2. Remove the unsupported “32 initialization slots” statement.
3. Reconcile Phase 1 early-success termination with current source behavior. Either preserve it as a required later implementation change or propose a documented protocol amendment to fixed-T episodes.
4. Distinguish maximum planned slots from actual executed CTX/replica counts and cache-bundle hits.
5. Keep the PC1 R4 45,440 slot arithmetic separate; that arithmetic is internally consistent with its current constants.

### F7 — R24 resource limits are assigned a scope not specified by R24

**Evidence**

- R24 `research/R24_ECOS_CONTROLLER_PREREGISTRATION.md:62-70` lists 1,000 episodes, 10 GPU hours, 5,000 model calls, 1M tokens and 24 hours.
- It does not define whether model calls/tokens include agent execution, operator-generation LLM calls, controller calls, retries, or all of them.
- Phase 1 `research/PHASE1_DESIGN.md:58-62,123-129` specifies up to 24 LLM turns per Agent episode and operator-specific calls; the current operators module also resolves `prompt_local_edit` to deterministic zero-call behavior.
- The reconciliation assigns all R24 limits to “controller training” without source support.

**Required correction**

1. Mark the R24 budget scope as unresolved rather than asserting it applies only to controller training.
2. Define separate proposed ledgers for Agent execution calls/tokens, operator-generation calls/tokens, controller training compute, PC1 slots, candidate-task evaluations and wall/GPU time.
3. State which ledgers are hard caps and how cache hits, retries, failed calls and initialization are counted.
4. Do not invent a combined total across incomparable units.

### F8 — Baseline tiers and fairness statement are inconsistent with Phase 1

**Evidence**

- Phase 1 `research/PHASE1_DESIGN.md:223-230` identifies B3c LinUCB and B3d neural contextual Bandit as the identical-state contextual controls; B3d is optional there.
- Phase 1 `research/PHASE1_DESIGN.md:265-273` explicitly says to include Q-learning as B6.
- Phase 1 `research/PHASE1_DESIGN.md:129` defines B5 FM rewrite as an external strategy outside the five-operator action set.
- The new protocol demotes B6 to “strong” and declares identical action-set fairness for all baselines, including B5.

**Required correction**

1. Keep B6 mandatory unless the new protocol explicitly amends Phase 1 and justifies the deferral.
2. Separate same-action-set controller comparisons from external reference strategies such as FM rewrite. Do not assert identical action sets for B5.
3. State that the best fixed operator is selected on validation only, then frozen before Family C; no selection/tuning on Family C.
4. Define common initialization, seed pairing, candidate-evaluation budget, model-call/token accounting and stopping rules for every comparable arm.
5. Keep the claim that R21-C1 is not an operator/controller comparison.

### F9 — Stop rules, CI decision logic and PPO configuration are incomplete or silently changed

**Evidence**

- PC1 R4 §7 says PASS requires the registered point estimates and CI lower-bound margins; FAIL requires CI upper bounds below thresholds; otherwise INCONCLUSIVE → SR1 STOP.
- The canonical JSON reduces this to D/advantage point thresholds with a vague “with CI” phrase and omits margin_D=0.10, margin_adv=0.01, cluster bootstrap and seed.
- The canonical proposal permits one extra diagnostic after INCONCLUSIVE, which conflicts with R4.
- R24 `research/R24_ECOS_CONTROLLER_PREREGISTRATION.md:72-77` says “validation degradation” but does not define a 10-consecutive-episode threshold. The proposed 10-episode rule is a new design choice and must be labelled as such.
- R24 supplies PPO scalar hyperparameters, but no committed PPO controller implementation exists; architecture, observation integration, rollout collection, advantage normalization, optimizer/update cadence and other training semantics are not verified.

**Required correction**

1. Restore the exact PC1 R4 CI/margin/bootstrap decision logic or clearly propose an amendment with rationale and approval dependency.
2. Do not permit an extra diagnostic after inconclusive under the current R4 contract.
3. Mark the 10-episode validation-degradation rule as a new proposed operationalization, not a historical R24 rule; leave unresolved if no defensible threshold is available.
4. Keep GAE λ=0.95 and R24 PPO scalar hyperparameters as proposed values only; identify missing PPO implementation details as unresolved.
5. Do not treat γ=0.99 as an “error” merely because Phase 1 and current shared code use 0.95. The proposal may choose γ=0.95, but must state that this explicitly supersedes R24 and requires a protocol amendment before execution.

### F10 — The JSON is not yet a complete machine-readable mirror

The JSON currently omits or misstates:
- seven feature labels/dimensions relative to the claimed 32-D state;
- per-feature transforms and the `budget_used_frac` defect;
- exact PC1 CI margins, bootstrap cluster/count/seed and complete decision logic;
- full split template assignments and source manifest provenance;
- exact reward conflict and PC1 supplied-reward provenance;
- the action-dependent replicate-ID call-site defect;
- initialization budget and early-termination semantics;
- full stop-rule provenance and unresolved PPO implementation details.

**Required correction**

The JSON must mirror the corrected Markdown's decisions and unresolved fields. Every numeric parameter must have a source/provenance reference and explicit unit. Do not silently fill unresolved values with guessed defaults. Validate feature counts and cross-document consistency mechanically before submission.

## 4. Items accepted from this submission

The following parts are retained:

- Three deliverables were created and the JSON is syntactically valid.
- Main remains unchanged.
- No production source, tests, task data, raw evidence or frozen historical protocol was modified in this phase.
- The PC1 R4 slot arithmetic 36,000 + 4,000 + 5,440 = 45,440 is consistent with its stated constants.
- R21-C1 is correctly described as a DAC/arithmetic comparison, not an operator/controller comparison.
- The canonical proposal remains PROPOSED / NOT APPROVED and no experiment authorization is claimed.

## 5. Decision and next action

**REQUEST_CHANGES — R26 ECOS Protocol Reconciliation R1 is not accepted.**

A single focused corrective pass is requested in:

`planner/GLEPPO_R26_ECOS_PROTOCOL_RECONCILIATION_R1_CORRECTIVE_PROMPT.md`

This is not permission to change source/tests or run experiments. The Executor must correct the three documents and durable status/handoff records, then stop for a second Planner review.

No Stage 1I audit restart is required. Do not open a third broad research loop.

## 6. Hard gates remain unchanged

- PC1 BLOCKED; PC1 R4 PROPOSED / NOT APPROVED.
- Formal G3 FAIL.
- Family C NOT ACCESSED; no task payload or gold inspection/execution/tuning.
- Registered PC1 NOT EXECUTED.
- Controller training NOT AUTHORIZED / NOT STARTED.
- No model/API calls, production runtime, signing-key access or baseline experiments.
- No production source, tests, task data, manifests, raw evidence or historical protocol changes.
- No main update/merge/rebase/reset/force-push.
- No cross-project code/data/report reuse.
