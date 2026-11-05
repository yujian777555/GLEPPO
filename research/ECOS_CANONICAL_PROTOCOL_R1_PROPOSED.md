# ECOS Canonical Protocol — R1.1 Proposed

**Version:** ECOS-CANONICAL-R1.1-PROPOSED
**Date:** 2026-11-05
**Status:** PROPOSED / NOT APPROVED
**Revision:** R1.1 (corrects R1 at commit 7423d5f)
**Requires:** Planner approval + independent review + formal amendment before execution

---

## A. Decision and Execution Units

| Unit | Definition | Budget Ledger |
|---|---|---|
| Operator decision | Select one of 5 operators at start of generation | N/A |
| Generation | Apply operator to λ=4 offspring, evaluate n_eval=3 each, (μ+λ) elitist selection | Candidate-task evaluation |
| Evolution episode | T=15 generations + initialization (μ=8) on one training task | Candidate-task evaluation |
| Task instance | {task_id, family, template_id, seed, input, gold} | N/A |
| Evaluation replica | One execution of one genotype on one task | Candidate-task evaluation |
| Rollout | H=3 trajectory under fixed policy (PC1 diagnostic only) | PC1 planned slots |
| PC1 state-action record | (state_id, action) with reward trace. **NOT a 32-dim vector.** | PC1 planned slots |
| CTX slot | One candidate-task evaluation slot | BudgetLedger |

**Integration status:** `evolution.py` does NOT import/call `state_vector`. `run_episode` receives external `operator_schedule(t,pop,history)`. No committed PPO controller consumes the 32-D vector. `StateActionRecord` stores `state_id`, not the 32-D vector.

## B. State Contract (32-D)

**Source:** gleppo/features.py:13-22 (FEATURE_NAMES), state_vector() at lines 43-117

| Index | Name | Formula | Range | Clipping | Missing | Notes |
|---|---|---|---|---|---|---|
| 0 | best_success | clip01(best_success) | [0,1] | clip01 | 0.0 | |
| 1 | mean_success | clip01(mean_success) | [0,1] | clip01 | 0.0 | |
| 2 | succ_gap | clip01(best - mean) | [0,1] | clip01 | 0.0 | |
| 3 | fail_format_rate | clip01(fail_rates['format_error']) | [0,1] | clip01 | 0.0 | |
| 4 | fail_tool_rate | clip01(fail_rates['tool_error']) | [0,1] | clip01 | 0.0 | |
| 5 | fail_wrong_rate | clip01(fail_rates['wrong_answer']) | [0,1] | clip01 | 0.0 | |
| 6 | fail_timeout_rate | clip01(fail_rates['timeout']) | [0,1] | clip01 | 0.0 | |
| 7 | valid_rate | clip01(valid_rate) | [0,1] | clip01 | 0.0 | |
| 8 | mean_turns | clip01(mean_turns / 24.0) | [0,1] | clip01 after /24 | 0.0 | |
| 9 | mean_tool_calls | clip01(mean_tool_calls / 8.0) | [0,1] | clip01 after /8 | 0.0 | |
| 10 | parent_last_delta | clip(delta, -1, 1) | [-1,1] | clip [-1,1] | 0.0 | |
| 11 | recent_eval_coverage | clip01(coverage) | [0,1] | clip01 | 0.0 | |
| 12 | div_tools | clip01(mean Jaccard distance, tool sets) | [0,1] | clip01 | 0.0 | |
| 13 | div_workflow | clip01(mean Jaccard distance, workflows) | [0,1] | clip01 | 0.0 | |
| 14 | div_prompt | clip01(mean Jaccard distance, 8-gram MinHash) | [0,1] | clip01 | 0.0 | |
| 15 | op_usage_entropy | clip01(entropy / log(5)) | [0,1] | clip01 after /log(5) | 0.0 | |
| 16 | op_mean_delta_1 | clip(op_delta[prompt_local_edit], -1, 1) | [-1,1] | clip [-1,1] | 0.0 | |
| 17 | op_mean_delta_2 | clip(op_delta[prompt_critique_rewrite], -1, 1) | [-1,1] | clip [-1,1] | 0.0 | |
| 18 | op_mean_delta_3 | clip(op_delta[tool_subset_edit], -1, 1) | [-1,1] | clip [-1,1] | 0.0 | |
| 19 | op_mean_delta_4 | clip(op_delta[workflow_step_edit], -1, 1) | [-1,1] | clip [-1,1] | 0.0 | |
| 20 | op_mean_delta_5 | clip(op_delta[crossover], -1, 1) | [-1,1] | clip [-1,1] | 0.0 | |
| 21 | op_unobserved_frac | clip01(unobserved / 5) | [0,1] | clip01 | N/A | |
| 22 | age_best | clip01(age_best / max(1,T)) | [0,1] | clip01 after /T | 0.0 | |
| 23 | pop_size_norm | clip01(pop_size_norm) | [0,1] | clip01 | 0.0 | **UNRESOLVED normalization source** |
| 24 | gen_frac | clip01(gen_t / max(1,T)) | [0,1] | clip01 after /T | 0.0 | |
| 25 | stagnation_frac | clip01(stagnation / max(1,T)) | [0,1] | clip01 after /T | 0.0 | |
| 26 | budget_used_frac | clip01(gen_t / max(1,T)) | [0,1] | clip01 after /T | 0.0 | **SOURCE DEFECT: same as gen_frac; no budget input** |
| 27 | best_delta_since_start | clip(delta, -1, 1) | [-1,1] | clip [-1,1] | 0.0 | |
| 28 | improve_last_3_frac | clip01(frac) | [0,1] | clip01 | 0.0 | |
| 29 | recency_top1 | clip01((1/gap[0]) / T) | [0,1] | clip01 | 0.0 | |
| 30 | recency_top2 | clip01((1/gap[1]) / T) | [0,1] | clip01 | 0.0 | |
| 31 | offspring_valid_last | clip01(frac) | [0,1] | clip01 | 0.0 | |

**Source defects:**
- `budget_used_frac` (index 26) is computed from `gen_t/T`, identical to `gen_frac` (index 24). No budget-used input exists. Must be fixed in future code.
- `pop_size_norm` normalization source undocumented.

## C. Action Contract

5 operators: prompt_local_edit (1), prompt_critique_rewrite (2), tool_subset_edit (3), workflow_step_edit (4), crossover (5). One per generation, applied to all λ=4 offspring. Invalid → drop.

**Seed defect:** `evolution.py` passes `replicate_id=stable_seed(episode_id,t,j,operator_name)` to `effective_seed_parts`. Since `replicate_id` enters the seed, operator/action **indirectly** changes the evaluation seed. CRN pairing is **NOT** enforced across operator arms. Must be fixed in future code.

## D. Reward Contract

**Proposed formula (supersedes R24 only after formal amendment):**

```
r_t = clip(Δbest + 0.1 × valid_rate + 0.25 × Δmean, -0.5, 1.0)
```

**R24 conflict:** `effective_success(child) − effective_success(parent)` is NOT equivalent. No source defines `effective_success` as the combination of population-best delta, valid_rate, and population-mean delta. R24 preserved unchanged. This choice requires formal protocol amendment before execution.

**PC1 reward provenance:** `pc1.py:523-549` `compute_q_hat`/`compute_r_hat` consume pre-populated `gen_rewards`; they do NOT call `generation_reward`. The import/self-test is NOT proof of estimator reward identity. Record schema cannot verify the reward function used.

## E. Discounting

γ=0.95 (proposed; Phase 1 + shared code). R24 γ=0.99 conflicts — superseded only after formal amendment (NOT declared a proven error). GAE λ=0.95 and PPO config proposed only; no controller code implements them. Architecture, observation integration, rollout collection, advantage normalization, optimizer/update cadence: UNRESOLVED.

## F. Data Split

| Split | N | Templates | Seeds | SHA256 |
|---|---|---|---|---|
| Train A | 200 | TA1-TA7 | 0-199 | bc8e6225... |
| Train B | 200 | TB1-TB5 | 0-199 | c5b0d99d... |
| Val A | 50 | TA8-TA12 | 1000-1049 | 01591cb9... |
| Val B | 50 | TB6-TB9 | 1000-1049 | 6300f14a... |
| Family C (held-out) | 100 | TC1-TC5 | 0-99 | 67109af7... |
| R24 Confirm | 12 | UNMATERIALIZED | — | — |

**Phase 1 text inconsistency:** PHASE1_DESIGN.md:298-301 template ranges overlap despite disjointness requirement. Actual committed assignments in tasks.py/manifest.json are disjoint.

**R24 Confirm** is 4 tasks × 3 seeds labelled "Final evaluation". NOT Family C. No committed manifest. Unmaterialized distinct split — cannot be used until formal amendment.

## G. Baselines

| Tier | Baselines | Notes |
|---|---|---|
| **Mandatory** | B0, B0b, B1, B2, B3c (LinUCB), B6 (Q-learning), ECOS (PPO) | Phase 1 §4.5 mandates Q-learning |
| **Strong** | B3a (UCB1), B3b (EXP3), B3d (Neural bandit) | |
| **Optional** | B4 (continuous knob) | |
| **External reference** | B5 (FM rewrite) | Outside 5-op action set; NOT identical-action fairness |
| **Ablations** | A0-A3 | |

Best fixed operator: selected on validation only, frozen, then compared on Family C. R21-C1 is DAC comparison, NOT operator comparison.

## H. Outcomes

Primary: Succ_C(best) on Family C, paired bootstrap CI, Holm-Bonferroni. PC1: D≥0.15 AND advantage≥0.02 with CI margins 0.10/0.01, cluster bootstrap 10000 resamples seed 20261027, 40 collection-episode clusters.

**INCONCLUSIVE → SR1 STOP** (no additional diagnostic without amendment).

## I. Budget

| Component | Formula | Slots |
|---|---|---|
| Initialization | μ × n_eval = 8 × 3 | **24** |
| Offspring (max) | T × λ × n_eval = 15 × 4 × 3 | **180** |
| **Total (max)** | 24 + 180 | **204** |

Previous 180 omitted initialization. "32 initialization slots" was incorrect. Planned vs actual vs cache-bundle distinctions apply. **Early termination** (Phase 1 §3.5: best_success ≥ 0.95 or env exception) NOT implemented in `evolution.run_episode` — protocol/source discrepancy.

R24 limits (1000 episodes, 10 GPU-h, 5000 calls, 1M tokens, 24h): scope unresolved. Propose separate ledgers for agent execution / operator generation / controller training / evaluations / PC1 slots / GPU-wall / retries-cache.

## J. Seeds

Two independent paths with defects. `replicate_id` includes `operator_name` (indirect action dependence). CRN pairing NOT enforced. Future tests: same inputs → same seed across operators; field-change → seed-change; override collision-free; operator RNG separate.

## K. Stop Rules

PC1 FAIL → SR1 STOP. PC1 INCONCLUSIVE → SR1 STOP (no additional diagnostic). Training: budget / no-improvement-100 / validation-degradation (NEW operationalization proposed). Protocol amendment requires Planner approval.

---

*Status: PROPOSED / NOT APPROVED. Requires Planner decision and formal amendment.*
