# GLEPPO R26 ECOS Protocol Reconciliation — R1.1 Corrective Executor Task

**Repository:** `yujian777555/GLEPPO`  
**Branch:** `r25-handoff` only  
**Planner decision:** REQUEST_CHANGES  
**Reviewed Executor commit:** `7423d5f7c753430a2f361400e1b39cd5b125aaf6`  
**Planner review commit:** `d45bcd6fad598af06b53c11003da01b47c31e4ac`  
**Review report:** `research/R26_ECOS_PROTOCOL_RECONCILIATION_PLANNER_REVIEW.md`  
**Main:** `6bad0b77835a2d00c62287c0c7d9d91d1d186d5e` (must remain unchanged)

## 1. Objective

Correct the current R1 reconciliation in one focused documentation-only pass. R1 was not accepted because its proposed contract misstates the actual state vector, overclaims reward/PC1 identity, misses an action-dependent seed call site, incompletely reconciles PC1 sampling and split definitions, and miscalculates the candidate-evaluation budget.

Do not restart Stage 1I, repeat the 42-Finding audit, or broaden the research question. Correct the existing three deliverables in place and update the durable handoff/status.

The output must remain **PROPOSED / NOT APPROVED**. It is not an experiment authorization.

## 2. Git preflight

- Fetch origin and verify current branch is exactly `r25-handoff`.
- Verify HEAD is a descendant of reviewed commit `7423d5f7c753430a2f361400e1b39cd5b125aaf6` and Planner review commit `d45bcd6fad598af06b53c11003da01b47c31e4ac`.
- Record branch HEAD, main HEAD, ahead/behind and worktree state.
- Do not update/merge main, reset, rebase, force-push or overwrite unrelated work.
- All modifications remain documentation/planner/status only.

## 3. Mandatory read-only sources

Re-read the Planner review and the exact cited source lines:

- `research/R26_ECOS_PROTOCOL_RECONCILIATION_PLANNER_REVIEW.md`
- `research/R26_ECOS_PROTOCOL_RECONCILIATION.md`
- `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.md`
- `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.json`
- `research/PHASE1_DESIGN.md`
- `research/R24_ECOS_CONTROLLER_PREREGISTRATION.md`
- `research/PC1_PROTOCOL_R4_PROPOSED.md`
- `research/R26_ECOS_SCIENTIFIC_INTEGRITY_REVIEW.md`
- `gleppo/features.py`
- `gleppo/evolution.py`
- `gleppo/reward.py`
- `gleppo/evaluator.py`
- `gleppo/pc1.py`
- `gleppo/operators.py`
- `gleppo/tasks.py`
- `data/manifest.json`
- `status.json`, `planner/latest_plan.md`, `planner/GLEPPO_R26_HANDOFF.md`

Do not open `data/test_C.jsonl` or any Family C task payload/gold labels. Manifest metadata only may be cited.

## 4. Required corrections

### F1. Exact 32-D state schema and integration status

Use the exact ordered `FEATURE_NAMES` in `gleppo/features.py:13-22`; the canonical JSON must contain exactly 32 feature labels, not 25.

The ordered names are:

1. best_success
2. mean_success
3. succ_gap
4. fail_format_rate
5. fail_tool_rate
6. fail_wrong_rate
7. fail_timeout_rate
8. valid_rate
9. mean_turns
10. mean_tool_calls
11. parent_last_delta
12. recent_eval_coverage
13. div_tools
14. div_workflow
15. div_prompt
16. op_usage_entropy
17. op_mean_delta_1
18. op_mean_delta_2
19. op_mean_delta_3
20. op_mean_delta_4
21. op_mean_delta_5
22. op_unobserved_frac
23. age_best
24. pop_size_norm
25. gen_frac
26. stagnation_frac
27. budget_used_frac
28. best_delta_since_start
29. improve_last_3_frac
30. recency_top1
31. recency_top2
32. offspring_valid_last

For every index, record formula, source input, units/range, clipping, missing-value behavior and timing. Source transforms include (verify exact code):

- [0,1] clipping for success/failure/validity/coverage/diversity/entropy/progress fractions;
- mean_turns / 24 and mean_tool_calls / 8 before clipping;
- parent_last_delta, op_mean_delta_1..5 and best_delta_since_start clipped to [-1,1];
- operator entropy normalized by log(5);
- missing operator delta mapped to 0 and counted in op_unobserved_frac;
- age_best / max(1,T);
- recency values computed from inverse recency gap divided by T;
- pop_size_norm is an input whose normalization source must be explicitly identified or marked unresolved.

**Critical defect:** `features.py` currently computes the feature named `budget_used_frac` from `gen_t/T`; it has no budget-used input. Mark this as a source defect and future code requirement. Do not describe it as measured budget use. Do not modify source/tests.

Also correct the integration claim:

- `evolution.py` does not import/call `state_vector`; `run_episode` receives an external `operator_schedule(t,pop,history)`.
- No committed PPO controller currently consumes the 32-D vector.
- `StateActionRecord` in `pc1.py` stores state_id, not the 32-D vector. Do not call it a projection of controller state.

### F2. Reward conflict and PC1 reward provenance

Do not claim R24's `effective_success(child)-effective_success(parent)` is equivalent to the shared generation reward. No source defines effective_success as the combination of population-best delta, valid_rate and population-mean delta.

The proposal may select the Phase 1/shared-code reward as its preferred future objective:

`clip(Δbest + 0.1 × valid_rate + 0.25 × Δmean, -0.5, 1.0)`

But explicitly state that this choice supersedes the R24 reward description and requires a formal protocol amendment before execution. Preserve R24 unchanged and do not call its formula a typo/error.

Inspect `pc1.py:523-549`: r_hat/q_hat consume pre-populated `gen_rewards`; they do not call `generation_reward`. The import/self-test is not proof of estimator reward identity. State what reward provenance the current record schema can/cannot verify and list future implementation requirements. No code changes.

### F3. Correct the full seed call-path claim

The helper `Evaluator.effective_seed_parts` excludes action directly, but `evolution.py` currently passes a `replicate_id` derived from `stable_seed(episode_id,t,j,operator_name)`. Because replicate_id enters effective_seed_parts, operator/action indirectly changes the effective evaluation seed.

Document this as a real current call-site defect. Do not claim paired common-random-number seeds across operator arms are already enforced.

Propose the later code change and exact tests:
- same task/state/rollout/replicate/replica inputs → same evaluation seed across all actions/operators;
- changing each declared seed field changes the seed;
- absent, empty and literal override values remain collision-free;
- operator-generation RNG remains separate and action-specific.

Do not modify source/tests now.

### F4. Reconcile Phase 1 PC1 diagnostic with R4

Explicitly compare:

- Phase 1: ≥200 states, ≥20 rollouts per state/action, horizon h=5 (`PHASE1_DESIGN.md:253-263`);
- PC1 R4: 100 states, 3 Q-rollouts, horizon 3, one extra immediate draw, N_EVAL=2, 40 clusters.

Treat R4 as a materially redesigned proposal, not as a direct implementation of the Phase 1 sample design. Either provide a defensible, evidence-backed rationale for the reduced design or mark the sample-size/horizon decision unresolved. Do not assert statistical adequacy without evidence.

Restore all R4 statistical decision details in both Markdown and JSON:
- D threshold 0.15;
- advantage threshold 0.02;
- CI margins 0.10 and 0.01;
- 40 collection-episode clusters;
- cluster bootstrap, 10,000 resamples, seed 20261027;
- PASS: point estimates meet thresholds and 95% CI lower bounds exclude the registered margins;
- FAIL: CI upper bounds below thresholds;
- INCONCLUSIVE: otherwise, with the current R4 rule INCONCLUSIVE → SR1 STOP.

Remove the unregistered “one additional diagnostic permitted” rule unless proposing a separate, explicitly amended protocol. PC1 R4 remains PROPOSED / NOT APPROVED; no data collection.

### F5. Correct split and template provenance

Phase 1's listed template ranges at `PHASE1_DESIGN.md:298-301` overlap despite the disjointness requirement. Actual committed `tasks.py` and `data/manifest.json` use disjoint assignments:

- Train A: TA1–TA7; validation A: TA8–TA12.
- Train B: TB1–TB5; validation B: TB6–TB9.
- Family C metadata: 100 tasks, seeds 0–99, templates TC1–TC5.

Explicitly record the Phase 1 text inconsistency and use the actual committed task generator/manifest for the current generated splits. Cite exact manifest hash and source revision where available. Do not claim missing generator Git SHA or per-task IDs exist in the manifest.

R24 Confirm is 4 tasks × 3 seeds and labelled “Final evaluation”, but it has no committed manifest/task identities. Do not reclassify it as additional validation. Mark it as a distinct unmaterialized R24 split that cannot be used until formal amendment. It is not Family C.

Do not access Family C JSONL or gold labels.

### F6. Correct candidate evaluation budget and episode termination

Current `EvolutionConfig`: μ=8, λ=4, T=15, n_eval=3. Each episode evaluates the initial μ population and offspring. Maximum full-length planned evaluations:

`μ × n_eval + T × λ × n_eval = 8×3 + 15×4×3 = 24 + 180 = 204`.

The previous 180 figure omits initialization. The “32 initialization slots” statement is incorrect.

Correct the contract to distinguish 24 initialization slots and 180 maximum offspring slots, 204 maximum total, planned vs actual executions, cache-bundle hits and early termination.

Phase 1 also defines early termination when best_success ≥0.95 or on environment exception. Current `evolution.run_episode` does not implement that early-stop condition. Mark this as a protocol/source discrepancy and either retain it as a future implementation requirement or propose an explicit amendment to fixed-T episodes. Do not modify source.

### F7. Do not invent the scope of R24 resource limits

R24 lists 1,000 episodes, 10 GPU hours, 5,000 model calls, 1M tokens and 24 hours, but does not define which model-call types are included.

Do not label all limits as controller-training-only. Mark call/token scope unresolved and propose separate ledgers for:
- Agent execution LLM calls/tokens;
- operator-generation LLM calls/tokens;
- controller training compute;
- candidate-task evaluations/replicas;
- PC1 planned slots;
- GPU hours and wall clock;
- retries, failures and cache behavior.

Keep incomparable units separate. Do not invent a combined total.

### F8. Correct baseline tiers and comparison fairness

- Phase 1 §4.5 explicitly says include Q-learning as B6. Keep it mandatory unless explicitly amending that requirement with a justification.
- B5 FM rewrite is an external strategy outside the five-operator action set. Do not claim identical action-set fairness for B5. Separate core same-action-set controller comparisons from external reference strategies.
- Select the best fixed operator on validation only, freeze it, then compare on Family C once the controller is frozen.
- Define identical initialization, paired seeds, state access, action set, evaluation budget, stopping and cost accounting for comparable core arms.
- Preserve the statement that R21-C1 is not an operator/controller comparison.

### F9. Stop rules, gamma and PPO configuration

- Preserve PC1 R4 INCONCLUSIVE → SR1 STOP; do not add another diagnostic without an approved amendment.
- The proposed “validation reward declining for 10 consecutive episodes” is a new operational threshold, not present in R24. Label it as a new proposal with rationale or leave validation-degradation operationalization unresolved.
- Phase 1 + current shared code support proposing γ=0.95. Do not call R24 γ=0.99 a proven preregistration error. State that γ=0.95 would supersede R24 only after formal amendment and approval.
- GAE λ=0.95 and R24 PPO scalar hyperparameters remain proposed only; no controller code implements them. Mark architecture, observation integration, rollout collection, advantage normalization, optimizer/update cadence and other absent semantics unresolved.

### F10. JSON must be a real machine-readable mirror

Update the existing files in place (do not create duplicate R1 filenames):
1. `research/R26_ECOS_PROTOCOL_RECONCILIATION.md`
2. `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.md`
3. `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.json`

Use a clear revision marker (e.g. R1.1) while retaining the same protocol document identity. JSON must parse, contain exactly 32 feature labels, include all PC1 CI/cluster parameters, accurate budget math, actual split template IDs, reward/seed call-site caveats, unresolved values and source provenance/units for numeric parameters.

Add a deterministic consistency check in the Executor's own offline reasoning or a documented script-free check; do not add tests or source code in this phase.

## 5. Durable updates

Update:
- `status.json`: record Planner REQUEST_CHANGES, reviewed SHA, exact blockers, corrected next gate and unchanged hard gates.
- `planner/latest_plan.md`: state R1 was not accepted and R1.1 corrective task is active.
- `planner/GLEPPO_R26_HANDOFF.md`: append the review decision and precise R1.1 task handoff. Preserve R2.1.1 ACCEPT and its SHA chain.

Do not mark canonical protocol approved. Do not overwrite the Planner review report.

## 6. Prohibited actions

- No production source changes.
- No `tests/` changes.
- No edits to historical Phase 1, R24 or PC1 R4 documents.
- No task data, manifests, raw evidence or Family C payload/gold access.
- No PC1 execution or data collection.
- No controller training or PPO implementation.
- No model/API calls, production runtime or signing-key access.
- No baseline experiment/pilot or Formal G3 efficacy.
- No main update/merge/rebase/reset/force-push.
- No cross-project code/data/report reuse.

Hard gates remain: PC1 BLOCKED; R4 PROPOSED / NOT APPROVED; Formal G3 FAIL; Family C NOT ACCESSED; registered PC1 NOT EXECUTED; controller training NOT AUTHORIZED / NOT STARTED.

## 7. Stop condition

After the corrected three documents and status/latest-plan/handoff are committed and pushed, stop and request Planner independent review.

This is one focused corrective pass. Do not begin experiments or create another broad protocol-research phase.
