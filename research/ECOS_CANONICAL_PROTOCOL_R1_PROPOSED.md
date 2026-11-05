# ECOS Canonical Protocol — R1 Proposed

**Version:** ECOS-CANONICAL-R1-PROPOSED
**Date:** 2026-11-05
**Status:** PROPOSED / NOT APPROVED
**Requires:** Planner approval + independent review before any execution

---

## A. Decision and Execution Units

| Unit | Definition | Budget Ledger |
|---|---|---|
| Operator decision | Select one of 5 operators at start of generation | N/A (decision, not cost) |
| Generation | Apply operator to λ=4 offspring, evaluate n_eval=3 each, (μ+λ) elitist selection | Candidate-task evaluation (T×λ×n_eval) |
| Evolution episode | T=15 generations on one training task instance | 180 evaluations per episode |
| Task instance | {task_id, family, template_id, seed, input, gold} | N/A (data) |
| Evaluation replica | One execution of one genotype on one task | 1 slot in evaluation budget |
| Rollout | One trajectory of H=3 steps under fixed random policy (PC1 diagnostic) | PC1 planned slots |
| PC1 state-action record | (state, action) pair with reward trace from PC1 collection | PC1 planned slots |
| CTX slot | One candidate-task evaluation slot | BudgetLedger planned_slots |
| Model call | One LLM inference call | Controller-training model_calls |
| Token | One input+output token | Controller-training tokens |
| Wall-clock | Wall time elapsed | Controller-training wall_clock |
| GPU-hour | GPU time elapsed | Controller-training gpu_hours |

**Nesting:** Operator decision → Generation → Episode → Task instance. Evaluation replica nested in generation. PC1 records are diagnostic samples.

## B. State Contract

**Dimension:** 32 (STATE_DIM in gleppo/features.py)

| Block | Dims | Features |
|---|---|---|
| A: Execution outcomes | 12 | best_success, mean_success, succ_gap, fail_format_rate, fail_tool_rate, fail_wrong_rate, fail_timeout_rate, valid_rate, mean_turns, mean_tool_calls, parent_last_delta (packed) |
| B: Population/operator history | 12 | diversity (3: tool Jaccard, workflow Jaccard, prompt MinHash), op_count/mean_delta (5+5→compressed 5 means + 1 entropy), best/mean/age |
| C: Progress | 8 | gen_t/T, stagnation_rounds/T, budget_used_frac, best_ever_delta, recency top-2 (2), improve_last_3 |

- **Normalization:** _clip01() to [0,1]. Exact fitting constants UNRESOLVED.
- **Decision-time availability:** All features from current and past generations only.
- **Gold exclusion:** Never in state, genotype, or operator prompts.
- **PC1 state:** Diagnostic projection; not identical to 32-dim controller state.

## C. Action Contract

| ID | Name | Semantics |
|---|---|---|
| 1 | prompt_local_edit | 1-3 sentence edit to system_prompt (template or 1 paraphrase call) |
| 2 | prompt_critique_rewrite | Full system_prompt rewrite from failure trace (2 LLM calls) |
| 3 | tool_subset_edit | Add one missing tool OR drop one (alternating) |
| 4 | workflow_step_edit | Change one non-finalize step's type/tool/prompt_slot |
| 5 | crossover | Prompt sentence union + tool union + workflow alternation |

- **Selection:** One operator per generation, applied to all λ=4 offspring.
- **Fallback:** Invalid offspring dropped (counted in valid_rate). No parent re-credit.
- **RNG:** Operator generation RNG separate from evaluation RNG. Action/genotype excluded from evaluation seed.

## D. Reward Contract

**Canonical formula (ONE shared reward):**

```
r_t = clip(Δbest + 0.1 × valid_rate + 0.25 × Δmean, -0.5, 1.0)
```

- **Source:** gleppo/reward.py:generation_reward()
- **Weights:** w_best=1.0, w_valid=0.1, w_mean=0.25
- **Clip:** [-0.5, 1.0]
- **Attribution:** Per generation (controller); per (state, action) (PC1 diagnostic)
- **R24 reconciliation:** R24's effective_success(child) − effective_success(parent) is a simplified description of Δbest. The shared function is canonical.

## E. Discounting and Return

| Parameter | Value | Source |
|---|---|---|
| Gamma (γ) | 0.95 | Phase 1 §3.4 + gleppo/reward.py |
| GAE lambda (λ) | 0.95 | R24 (compatible with γ=0.95) |
| PPO learning rate | 3e-4 | R24 |
| PPO clip epsilon | 0.2 | R24 |
| Entropy coefficient | 0.01 | R24 |
| Value coefficient | 0.5 | R24 |
| Max grad norm | 0.5 | R24 |

**R24 gamma=0.99 is a preregistration error.** γ=0.95 is canonical (Phase 1 + implementation agree).

## F. Data Split

| Split | Tasks | Purpose | Access |
|---|---|---|---|
| Train A+B | 400 (seeds A:[0,199], B:[0,199]) | Controller training | Full |
| Val A_val+B_val | 100 (seeds [1000,1049]) | Hyperparameter selection | Full |
| Confirm (R24) | 12 (4 tasks × 3 seeds) | Additional validation | Full |
| Family C (held-out) | 100 (seeds [0,99]) | One-time final eval | **NEVER loaded/tuned** |

**R24 "confirm" ≠ Family C.** R24 confirm is a third validation split. Family C is the held-out test.

**Task identities:** Templates TA1-TA8, TB1-TB6, TC1-TC5. Exact manifest must be committed before training.

## G. Baselines

| Tier | Baselines | Purpose |
|---|---|---|
| **Mandatory** | B0 (fixed=prompt_local_edit), B0b (fixed=prompt_critique_rewrite), B1 (random), B2 (rule), B3c (LinUCB), ECOS (PPO) | Core adaptive-vs-fixed comparison |
| **Strong** | B3a (UCB1), B3b (EXP3), B3d (Neural bandit), B6 (Q-learning) | Bandit/RL comparisons |
| **Optional** | B4 (continuous knob), B5 (FM rewrite), A0-A3 (ablations) | Mechanism claims |

**Fairness:** Identical state, action set, initialization, seeds, budget (T×λ×n_eval), stopping rule, model-call accounting.

**R21-C1 is DAC comparison, NOT operator comparison.**

## H. Outcomes

| Endpoint | Definition | Analysis |
|---|---|---|
| **Primary** | Succ_C(best) on Family C | Paired bootstrap CI, Holm-Bonferroni |
| Secondary | Succ_C(mean), final agent success | Descriptive |
| PC1 diagnostic | D (disagreement), advantage | PASS if D≥0.15 AND adv≥0.02 |
| Training reward | Σ γ^t r_t (discounted return) | Learning curve |
| Safety | format_error, tool_error, wrong_answer, timeout, invalid_genotype | Failure rates |
| Cost | T×λ×n_eval per task | Budget accounting |

**Primary estimand:** Paired difference in Succ_C(best) between ECOS and best baseline. Analysis unit = task instance.

## I. Budget Ledgers

| Ledger | Units | Value | Stage |
|---|---|---|---|
| Candidate-task evaluation | Executions/task | T×λ×n_eval = 180 | Training/eval |
| Controller training | Episodes | 1000 | Training |
| Controller training | GPU hours | 10 | Training |
| Controller training | Model calls | 5000 | Training |
| Controller training | Tokens | 1M | Training |
| Controller training | Wall clock | 24 hours | Training |
| PC1 planned slots | Evaluation slots | 45,440 | PC1 diagnostic |
| PC1 hard cap | Evaluation slots | 50,000 | PC1 guard |

**Never add incomparable units.** Planned slots ≠ actual CTX ≠ calls ≠ tokens.

## J. Seeds and Reproducibility

**Proposed canonical seed schema:**

```json
{
  "version": "crn-v3",
  "base_tag": ["none"] | ["empty"] | ["value", "override"],
  "task_id": "string",
  "state_id": "string",
  "rollout_id": "int",
  "replicate_id": "int",
  "replica_index": "int"
}
```

- **Encoding:** Typed JSON (collision-free)
- **Action/genotype:** NEVER in evaluation seed
- **Operator RNG:** Separate (operator_rng_seed)
- **Current state:** TWO independent paths exist (crn_seed in pc1.py, effective_seed_parts in evaluator.py). Unification deferred to code phase.

## K. Stop Rules and Gates

| Rule | Condition | Action |
|---|---|---|
| PC1 FAIL | D < 0.15 OR advantage < 0.02 (with CI) | STOP PPO hypothesis (SR1) |
| PC1 INCONCLUSIVE | CI overlaps threshold | One additional diagnostic permitted, then STOP if still inconclusive |
| Training stop | Budget exhausted OR no improvement 100 episodes OR validation degradation | Stop training |
| Validation degradation | Val reward declining ≥10 consecutive episodes | Stop training |
| Protocol amendment | Any change to reward/gamma/thresholds/budget | Requires Planner approval |
| PC1 gate | PC1 PASS + Planner approval + independent review + production runtime | May proceed to training |
| Training gate | All R24 prerequisites (R21-C1 accept + PC1 + G3 + Planner) | May start training |
| Held-out gate | Controller frozen | One-time Family C evaluation |

**No post-hoc threshold changes. No gate passed merely because report is labelled ready.**

---

*Status: PROPOSED / NOT APPROVED. Requires Planner decision.*
