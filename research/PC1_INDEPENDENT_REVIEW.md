# Independent Review — Phase 2A / PC1 Amendment

**Date:** 2026-10-27  
**Reviewed ref:** `main` at `315796399116c4e1ec540f42d3e78a061043fb7e`  
**Review type:** read-only source/design audit; no code or experiments were executed by the reviewer.  
**Verdict:** **REQUEST CHANGES — PC1 NOT APPROVED.**  
**Current permission:** documentation and implementation corrections only. Do not run PC1 or make effectiveness claims. Do not deploy/run the production model until the evaluator correctness issue below is fixed and tested.

## Summary

The environment skeleton, manifests, and unit tests are useful progress, and Family C has not been executed according to the submitted records. However, source inspection found correctness issues that invalidate the current success metric and PC1 estimates. Passing the current tests is not enough to approve PC1.

## Blocking findings

### R1 — The evaluator does not measure answer correctness (P0, BLOCKER)

**Evidence:** `gleppo/tasks.py`, `_check_family_a`, `_check_family_b`, `_check_family_c`, `attach_checker`; `gleppo/interpreter.py`, `Interpreter._score`.

- Family A returns success when `calc` is enabled and the prompt contains `compute`; it does not compare the produced answer with the task's `gold`.
- Family B returns success when `calc` and `str_ops` are enabled and the prompt contains `transform`; it does not verify the sum/string output against `gold`.
- Family C checks that `sum` and `product` keys exist, but does not verify their values against the generated gold object.
- `Interpreter._score` delegates to these checkers, so this is the primary success metric in the current environment, not merely a StubLLM-only diagnostic.

**Impact:** a real model can produce a wrong answer and still be credited as successful. The reported A/B smoke success of 1.0 is therefore not evidence of task correctness. PC1's reward and any later controller evaluation would be invalid.

**Required fix:** make evaluator-side checkers compare normalized actual output against gold for A/B and parse/validate both required keys and exact values/constraints for C. Keep gold/reference values inside the evaluator only; controllers and operator prompts receive only the approved scalar outcome/failure category. Add adversarial tests: a genotype with all required keywords/tools but a deliberately wrong answer must fail; correct answer passes; malformed output fails; Family C wrong values fail despite correct keys. Ensure the production evaluator and stub evaluator have explicitly separated semantics rather than silently using strategy-keyword success as the research metric.

### R2 — PC1 state count contradicts the registered feasibility guard

**Evidence:** `research/PHASE1_DESIGN.md` §4.4 and `research/PHASE2_PREFLIGHT.md` §3.2.

Phase 1 states that if the diagnostic exceeds the budget, the number of sampled states may be reduced to **at least 100**, or the hypothesis should stop. The amendment reduces it to 80 and says the original guard allowed “≥100”; that explanation is incorrect.

**Required fix:** because no PC1 data has been collected, make a transparent pre-data amendment that either (a) uses at least 100 states, or (b) explicitly supersedes the minimum with a reasoned design amendment and updated power/uncertainty rationale. Do not claim 80 was allowed by the original registration. The preferred proposal for review is the budget-consistent design in §4 below.

### R3 — Immediate-reward and long-horizon estimates do not use the same reward

**Evidence:** `research/PHASE2_PREFLIGHT.md` §3.4 versus `research/PHASE1_DESIGN.md` §3.4 and `gleppo/evolution.py`.

The implemented reward is:

`clip(Δbest + 0.1 × valid_rate + 0.25 × Δmean, -0.5, 1.0)`.

But the PC1 amendment defines `r_hat(s,a)` as “mean immediate best-improvement” only, while `Q_hat` includes the actual generation reward. The disagreement statistic `argmax r_hat != argmax Q_hat` would then compare different objectives and could report disagreement caused by the definition mismatch rather than delayed effects.

**Required fix:** compute both `r_hat` and the first reward term of `Q_hat` using the exact same frozen reward function, including validity bonus, population-mean term, and clipping. If an alternate myopic reward is intended, it must be declared as a separate diagnostic and cannot be used as the preregistered PC1 statistic without a documented amendment.

### R4 — The proposed repeated samples are not independent under current caching/seeding

**Evidence:** `gleppo/evaluator.py` (`Evaluator.evaluate` cache key and seed parts), `gleppo/evolution.py` (episode RNG), `docs/RUNTIME_LOCK.md` §2, `research/PHASE2_PREFLIGHT.md` §3.4.

- The evaluator cache key is only `behavior_hash|task_id`. Repeated evaluations of the same genotype/task return the first result even when a PC1 rollout intends a new stochastic replicate. Cache hits therefore cannot be counted as new Monte Carlo samples.
- The evaluation seed contains `h[:8]` (genotype hash), so alternative actions do not share the same agent-evaluation random seeds as the PC1 CRN plan claims.
- The evolution seed uses Python's built-in `hash(task_id)`, which is randomized across Python processes unless `PYTHONHASHSEED` is pinned. The current unit test only establishes same-process repeatability, not cross-process reproducibility.

**Required fix:** implement a PC1 evaluation path with explicit `state_id / rollout_id / replicate_id` semantics. Distinct Monte Carlo replicates must not hit a cache entry for an earlier replicate; action alternatives should share the intended common random numbers while retaining distinct genotype outputs. Cache keys must include the effective seed/replicate and runtime/model revision. Replace process-randomized `hash()` seeding with a stable SHA256-derived integer and add a cross-process reproducibility test. Record cache hits separately and never count them as independent observations.

### R5 — The claimed train/validation template split is not implemented

**Evidence:** `gleppo/tasks.py`, `TEMPLATES_A`, `TEMPLATES_A_VAL`, `TEMPLATES_B`, `TEMPLATES_B_VAL`, `generate_split`.

- Train and validation template lists are identical.
- `template_id` is only metadata; it does not change the generated input text. Thus TA1–TA7/TB1–TB5 are labels on one wording pattern, not actual distinct templates.

**Impact:** the manifest has disjoint task IDs/seeds, but it does not establish the preregistered template-disjoint validation split. Generalization results must not be described as template generalization.

**Required fix:** implement real template-specific generation, make train/validation template sets disjoint as specified, regenerate and re-freeze manifests before any controller training, and add tests proving that template IDs map to distinct generation rules and that the train/validation template sets are disjoint. Family C remains untouched and must not be executed.

### R6 — The diversity features are similarities, not distances

**Evidence:** `gleppo/features.py`, `_jaccard` and `state_vector`; compare with Phase 1's definition of diversity as mean pairwise Jaccard distance.

The code stores `_jaccard(a,b) = |a∩b|/|a∪b|` directly in `div_tools`, `div_workflow`, and `div_prompt`. That is similarity, not distance. Higher values mean more alike, the opposite of the declared diversity semantics.

**Required fix:** either use `1 - Jaccard similarity` for the registered diversity features or explicitly amend/rename the features to similarity and update the state interpretation. Add tests for identical, disjoint, and partially overlapping sets. Update the schema version/manifest or protocol notes before controller training.

### R7 — PC1 cost accounting omits initial-population evaluations and mixes planned slots with actual CTX

**Evidence:** `research/PHASE2_PREFLIGHT.md` §3.3 and `gleppo/evolution.py` `init_population` / `EpisodeResult.total_ctx`.

The amended 47,200 total includes 20×15×λ×n_eval state-collection offspring slots, but not the initial population evaluations (20×μ×n_eval = 320 more slots at μ=8, n_eval=2). The current total is therefore at least 47,520 under the same full-slot convention, before resolving whether the state collector includes both random and heuristic rollouts. Also, the 50k calculation counts planned offspring evaluation slots even when offspring are invalid or results are cached; those are not actual CTX under the current definition.

**Required fix:** distinguish (a) planned evaluation slots, a conservative budget upper bound, (b) actual uncached candidate-task executions, (c) invalid offspring, (d) cache hits, and (e) LLM completions/tokens. Include initialization and all state-collection policies. The hard cap should apply to a clearly named conservative slot count; report actual CTX separately.

## Proposed PC1 amendment for review (not yet approved)

A possible budget-consistent candidate, still subject to implementation and statistical review:

- 100 sampled states (respecting the original minimum).
- 3 Q rollouts per state-action, horizon h=3, n_eval=2, λ=4.
- One additional immediate-reward sample per state-action; `r_hat` uses the three first-step rewards already collected in Q rollouts plus this extra sample, all under the same reward function.
- 40 independent state-collection episodes on training A/B only: 20 random-policy and 20 heuristic-policy; sample 100 states across these episode/task clusters.
- Cluster bootstrap by independent task/episode (not naive IID bootstrap over correlated states), with paired action comparisons and 10,000 resamples.
- Conservative planned-slot arithmetic:
  - Q rollouts: 100×5×3×3×4×2 = 36,000 slots.
  - Extra immediate draws: 100×5×1×4×2 = 4,000 slots.
  - State collection: 40×(8×2 + 15×4×2) = 5,440 slots.
  - **Total = 45,440 planned evaluation slots**, leaving 4,560 slots under a 50,000 cap.
- This arithmetic does **not** bound operator-proposal calls or total model completions. Before PC1, use production smoke measurements to estimate those separately and set a hard runtime/inference ceiling. If infeasible or inconclusive under the declared cap, apply SR1; do not silently extend.
- Define `r_hat` and `Q_hat` using the same reward. Define the Q estimator precisely as the h-step return under the preregistered fixed random continuation policy; do not call it optimal Q.

This is a proposed amendment, not an approved experiment protocol. The executor must record the final choices and their rationale before collecting PC1 data.

## Required remediation order

1. Fix evaluator correctness and add adversarial scoring tests.
2. Fix real template generation and split; regenerate manifest and record new digests.
3. Fix state-feature similarity/distance semantics and cross-process deterministic seeding.
4. Implement PC1-specific replicate/cache/CRN semantics and ensure reward identity between `r_hat` and `Q_hat`.
5. Correct budget units and add initialization/state-collection/operator-call accounting; measure a production-backend smoke run only after evaluator tests pass.
6. Submit the revised `research/PHASE2_PREFLIGHT.md` and this checklist for a second independent review.
7. Only after review approval may production G3 and PC1 be run. PPO training remains prohibited until PC1 PASS.

## Final decision

**REQUEST CHANGES. PC1 is not approved.** The idea is not rejected; the current evaluator and diagnostic protocol are not yet valid enough to test it. Do not deploy the production backend, run PC1, or start any controller training until the blockers above are fixed and re-reviewed.
