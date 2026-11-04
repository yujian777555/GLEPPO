# R26 ECOS Scientific Integrity Review

**Date:** 2026-11-04  
**Repository:** `yujian777555/GLEPPO`  
**Branch:** `r25-handoff`  
**Reviewed branch HEAD:** `571c34201dde4e63705319670e446cb0e058f086`  
**Main HEAD:** `6bad0b77835a2d00c62287c0c7d9d91d1d186d5e`  
**Branch relation at review:** 194 ahead / 0 behind  
**Review type:** Planner read-only scientific-claim and protocol-consistency audit

## 1. Executive decision

**IDEA_RETAINED_AS_A_FALSIFIABLE_RESEARCH_HYPOTHESIS; PPO_ADVANTAGE_NOT_ESTABLISHED; PROTOCOL_RECONCILIATION_REQUIRED; NO_EXPERIMENT_AUTHORIZED.**

The GLEPPO idea remains worth investigating: an execution-conditioned evolutionary controller selects among Agent-genotype variation operators while accounting for population state and possible delayed effects. However, the current repository evidence does not establish that adaptive operator selection beats a fixed operator, nor that PPO is better than a competent rule-based or contextual-bandit controller.

This review does not authorize PC1, Family-C access, controller training, Formal G3 efficacy, production runtime, or model/API calls. It does not modify production source, tests, frozen protocols, or historical results.

## 2. Critical correction: R21-C1 is not evidence that operator choice matters

The R25 scientific review states:

> Fixed strategy enough? UNLIKELY — R21-C1 shows operator matters.

That inference is unsupported by the cited experiment.

R21-C1 compares **C0 (LLM arithmetic execution)** against **C4 (DAC deterministic answer computation)**. It does not compare any of the five evolutionary operators, fixed-operator evolution, adaptive operator selection, random selection, rules, Bandits, or PPO.

R21-C1 reports C0 = 9/24 (37.5%) and C4 = 24/24 (100%), with McNemar exact p = 0.000061. All C4 evaluations used deterministic computation. The experiment supports the DAC/arithmetic-correctness claim under its stated task and semantic limitations; it cannot support the claim that an adaptive operator controller is needed.

Required correction to the claim ledger:

| Claim | Prior R25 wording | Correct status | Reason |
|---|---|---|---|
| A fixed operator is insufficient | “UNLIKELY” based on R21-C1 | **UNTESTED** | R21-C1 is C0-vs-DAC, not an operator/controller comparison |
| Operator choice affects Agent evolution | Implied by R21-C1 | **NOT ESTABLISHED BY R21-C1** | No operator arm appears in R21-C1 |
| Adaptive selection beats the best fixed operator | Implied motivation | **UNTESTED** | Requires matched, budget-equalized policy comparisons |
| PPO beats a rule-based controller | Open question | **UNTESTED** | No valid trained PPO comparison exists |
| PPO beats LinUCB/neural contextual Bandit | Central sequential claim | **UNTESTED** | PC1 has not been approved/executed; no controller training |
| The five operators have useful and stable effects | R25 describes the action space as effective | **PARTIALLY MOTIVATED, NOT ESTABLISHED AS A LIBRARY** | Earlier pilots show heterogeneous and sometimes harmful operator effects; behavior change is not performance gain |
| The state vector is useful | R25: YES | **DESIGN HYPOTHESIS** | Requires controlled feature ablations and same-state baselines |
| Reward reflects task quality | R25: YES | **NOT YET VALIDATED** | Reward/target alignment and reward hacking need empirical checks |
| 1,000 training episodes are sufficient | R25: PROBABLY | **UNKNOWN** | No convergence or learning-curve evidence |

Earlier R5–R18 pilot records may motivate operator heterogeneity and task-conditioned effects. They must not be conflated with proof that a learned adaptive selector outperforms the best fixed operator. Any such claim must cite the exact run, arms, task/seed coverage, paired outcomes, and limitations.

## 3. ECOS protocol drift: the current specification is not yet a single executable contract

Three documents and the implementation currently describe materially different controller objectives or protocol details.

### 3.1 Version comparison

| Dimension | PHASE1_DESIGN.md | R24 preregistration | PC1 R4 proposal / implementation | Audit finding |
|---|---|---|---|---|
| Decision unit | One operator per generation; one episode is a 15-generation evolution run on one training task | Says immediate attribution “per episode”; episode semantics are not fully reconciled | PC1 samples state-action pairs and estimates immediate and continuation values | Must define one canonical unit and distinguish generation, evolution episode, rollout, and candidate-task execution |
| State | Explicit 32-dimensional state: execution outcomes, diversity/operator history, progress | High-level task features, operator history, effective-success trend; no exact 32-D schema | PC1 state/action records and estimator inputs | R24 state description is not an exact implementation-level schema |
| Action | Five discrete operators, one per generation | Same five operators | Five PC1 actions | Broad action set agrees; operator semantics and per-generation application still require one frozen contract |
| Reward | Generation reward: Δbest + 0.1·valid_rate + 0.25·Δmean, clipped [-0.5, 1.0] | Immediate effective_success(child) − effective_success(parent) | Uses `gleppo.reward.generation_reward` for r-hat and Q-hat | **Material reward conflict**; these objectives are not interchangeable |
| Discount | γ = 0.95 | γ = 0.99; GAE λ = 0.95 | γ = 0.95 in shared reward module and PC1 R4 | **Gamma conflict** between R24 and actual shared implementation |
| Training/evaluation split | Train A+B; validation for model selection; Family C once after freeze | 4 train / 4 validation / 4 confirm tasks, 3 seeds each | PC1 is restricted to training-family diagnostic data | Must reconcile family/task identities and prevent any confirm leakage |
| Baselines | B0/B0b, random, rule, UCB/EXP3/LinUCB/neural Bandit, FM rewrite, Q-learning, PPO, ablations | Fixed, random, rule, PPO | PC1 is a myopia diagnostic, not a controller comparison | R24 baseline list is materially smaller than Phase 1 mandatory suite |
| Primary outcome | Succ_C(best), also Succ_C(mean) and final selected Agent | effective_success_rate plus answer/tool/format/constraint metrics | PC1 disagreement D and continuation advantage | Separate controller-training reward, primary test endpoint, diagnostic endpoint, and safety metrics |
| Budget | Equal T×λ×n_eval candidate-task executions per method/task; separate feasibility limits | 1,000 episodes, 10 GPU hours, 5,000 model calls, 1M tokens, 24 hours | PC1 hard cap 50,000 planned evaluation slots, target 45,440 | These are different budget units and different stages; never add or compare them as if they were the same budget |

### 3.2 Source-level consistency check

The current source confirms that:

- `gleppo/reward.py` defines `GAMMA = 0.95`;
- `generation_reward` computes `clip(Δbest + 0.1·valid_rate + 0.25·Δmean, -0.5, 1.0)`;
- `gleppo/evolution.py` calls that shared function to populate each generation's reward;
- `gleppo/pc1.py` imports the same function and uses it for PC1's r-hat/Q-hat estimators;
- `research/PC1_PROTOCOL_R4_PROPOSED.md` is explicitly **PROPOSED / NOT APPROVED** and describes a myopia diagnostic, not an authorization to collect data or train a controller.

Therefore, the Phase 1 / shared-code / PC1 reward identity is currently internally aligned at γ = 0.95. R24's immediate parent-child reward and γ = 0.99 remain conflicting historical preregistration fields. Do not silently choose one, overwrite the old document, or claim all specifications agree.

### 3.3 Required protocol reconciliation before any training

A later Planner-reviewed protocol reconciliation must produce a single versioned contract that explicitly decides:

1. canonical state schema, dimension, feature timing, missing-value semantics, and feature leakage rules;
2. action semantics and whether exactly one operator is selected per generation;
3. episode/rollout/generation/CTX definitions;
4. the one reward used by evolution, PC1, controller training, and reported mechanism analysis, or an explicit justified separation if the objectives differ;
5. γ, GAE λ, PPO hyperparameters, and return/advantage calculation;
6. Train/Validation/Confirm family and task identities, seed structure, and one-time confirmation access;
7. mandatory baselines and identical state/action/evaluation budgets;
8. primary endpoint, secondary metrics, safety constraints, cost metrics, and multiplicity correction;
9. controller-training budget, PC1 diagnostic budget, and model-call/token accounting as separate ledgers;
10. stopping rules, minimum effect sizes, confidence intervals, and exact STOP/REVISE decisions.

This is a future documentation/review gate. It is not permission to execute PC1 or train.

## 4. What the actual research hypothesis should be

The defensible core hypothesis is not “PPO is better because it is deep reinforcement learning.”

It is:

**When Agent-genotype variation operators alter the future population state and have reproducible delayed effects, can a sequential controller exploit that cross-generation structure to improve held-out Agent task success over the best fixed operator, a competent rule-based controller, and contextual Bandit controllers that receive the identical state?**

The evolutionary-computation contribution must be in the operator-selection/evolution-control mechanism and its measurable effect on the evolving Agent population. PPO is one candidate optimizer for that control problem, not the contribution by itself.

The mechanism requires evidence for both:

- **Non-myopia:** for a nontrivial, reproducible subset of states, the action maximizing continuation value differs from the action maximizing immediate reward, with a positive continuation advantage under the pre-specified PC1 criteria.
- **Policy value:** a trained sequential controller improves held-out task success against fixed, random, rule-based, LinUCB/neural contextual Bandit, and other mandatory baselines under matched conditions.

Passing the first diagnostic does not prove the second claim. If PC1 fails or is inconclusive under its approved protocol, the PPO hypothesis must stop under the registered stop rule rather than be rescued by post-hoc threshold changes or action-space expansion.

## 5. Current gates and boundaries

At this review:

- Stage 1H Planner decision: REQUEST_CHANGES.
- Stage 1I: current documentation-only semantic evidence task; not started by Executor.
- PC1: BLOCKED; R4 protocol remains PROPOSED / NOT APPROVED.
- Formal G3: FAIL.
- Production genotype-causality evidence: not established.
- Family C: NOT ACCESSED and remains prohibited.
- Controller training: NOT AUTHORIZED / NOT STARTED.
- Registered PC1: NOT EXECUTED.
- External model/API calls and production runtime: NOT AUTHORIZED.
- Main branch: unchanged.

The R25 proposed gate order remains a planning boundary, not an execution authorization: G3-PREFLIGHT → approved PC1 → ECOS training → G3-EFFICACY. A preflight-ready label must not be rewritten as Formal G3 PASS.

## 6. Planner decisions

1. Retain ECOS as a candidate research direction; do not claim the method has already improved Agent evolution.
2. Correct the R25 inference that R21-C1 demonstrates operator effects. Preserve the historical R25 report and record this correction in this addendum.
3. Treat fixed-vs-adaptive, PPO-vs-rule, PPO-vs-LinUCB, state-feature value, reward validity, and operator-library sufficiency as open empirical questions.
4. Complete R26 Stage 1I first. Do not widen that Executor stage into source/test changes or experiments.
5. After Stage 1I independent review, conduct a separate protocol reconciliation and scientific-design review before any request to approve PC1.
6. No PC1 execution, Family C access, controller training, Formal G3 efficacy, model/API calls, or production runtime in this review.

## 7. Source references checked

- `research/R25_ECOS_SCIENTIFIC_REVIEW.md` — R25 claims and limitations, especially “Fixed strategy enough?”.
- `research/runs/20261102T131000Z_R21/R21_C1_REPORT.md` — actual C0-vs-C4 DAC experiment and its task-level results.
- `research/R25_R21_C1_REVIEW.md` and `research/R21_C1_INDEPENDENT_REVIEW_R23.md` — independent R21-C1 acceptance and the `source_valid` proxy limitation.
- `research/PHASE1_DESIGN.md` §§3–4, 6, 9 — 32-D state, sequential MDP, reward, PC1 myopia hypothesis, baselines, and stop rules.
- `research/R24_ECOS_CONTROLLER_PREREGISTRATION.md` — alternative immediate reward, γ = 0.99, task split, and training budget.
- `research/PC1_PROTOCOL_R4_PROPOSED.md` — proposed PC1 diagnostic reward/estimators/budget; not approved.
- `gleppo/reward.py` and `gleppo/evolution.py` — actual shared reward implementation.
- `gleppo/pc1.py` — PC1 estimator and registered-execution refusal.
- `status.json` R5–R21 records — historical pilot outcomes and the distinction between operator-specific pilot effects and controller-policy superiority.

**No source, test, protocol, raw experiment, or frozen manifest was modified by this review.**
