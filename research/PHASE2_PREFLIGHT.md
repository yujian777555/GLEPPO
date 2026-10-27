# Phase 2 Preflight — PC1 Cost Amendment, State Schema, Operator Freeze

**Date:** 2026-10-27  
**Status:** AMENDMENT FOR INDEPENDENT REVIEW. PC1 **must not be executed** until this document is reviewed and approved (protocol §1.1).  
**Policy:** append-only. Original Phase 1 registered values are preserved; every change is explicit.

---

## 1. Counting units (definitions)

| Unit | Symbol | Definition |
|---|---|---|
| **Candidate-task execution** | `CTX` | one agent genotype runs one task instance once (one agent episode, including its LLM turns and tool calls). Primary cost unit. |
| **Generation transition** | `GEN` | one evolution step: choose one operator, produce λ=4 offspring, evaluate them, survivor selection. λ offspring × n_eval replicas = λ×n_eval `CTX` per `GEN`. |
| **Controller rollout / evolution run** | `ROL` | one full episode of T=15 `GEN` on one task. `ROL = T × λ × n_eval` `CTX` (upper bound; early stop may reduce). |
| **Model call** | `LLM` | one LLM completion request (agent turn or operator proposal). |

Original PC1 arithmetic mixed these units. Below we convert everything to `CTX`.

---

## 2. Original PC1 registration (preserved, not edited)

From `research/PHASE1_DESIGN.md` §4.4 (verbatim values):

- ≥200 sampled states
- 5 actions per state
- ≥20 rollouts per (s,a)
- continuation horizon h=5
- λ=4 offspring per generation
- n_eval=3 per offspring
- Feasibility guard: "if myopia diagnostic requires >50k episodes, sample fewer states (≥100) or STOP"

**Original implied upper bound (full-generation implementation):**

`200 states × 5 actions × 20 rollouts × 5 steps × λ=4 × n_eval=3 = 1,200,000 CTX`

**Contradiction:** the design's 50,000-episode guard cannot hold if "episode" means `CTX`. This is a cost-arithmetic defect in Phase 1, not a failure of the research idea. It is resolved below.

---

## 3. Amended PC1 protocol (proposed; pending review)

### 3.1 Hard budget

**Hard cap: 50,000 CTX** (the Phase 1 guard, now interpreted as candidate-task executions).  
**Target: ≈41,000 CTX** (see arithmetic). No silent extension. If the diagnostic cannot conclude within the cap → **INCONCLUSIVE → SR1 (STOP)**, unless a future review preregisters exactly one bounded extension.

### 3.2 Revised sampling plan

| Parameter | Phase 1 (original) | Phase 2A amendment | Rationale |
|---|---|---|---|
| N_states | 200 | **80** | ≥100 was allowed by the original guard; 80 with R≥3 gives bootstrap CIs over states; recorded as deviation |
| Rollouts R per (s,a) | 20 | **4** | MC error drops as 1/√R; R=4 with paired seeds gives usable CIs on argmax disagreement; 20 was unaffordable |
| Continuation horizon h | 5 | **3** | delayed effects of 2 further generations suffice to rank Q vs r for a 15-gen episode; h=5 quadruples cost |
| n_eval (PC1 only) | 3 | **2** | PC1 estimates action ranking, not absolute success; main experiments keep n_eval=3 |
| Immediate-reward extra samples | — | **+2 per (s,a)** (total 6 for r̂ only, costing λ×2=8 CTX each) | r̂ is the myopic baseline; better estimated than Q̂ |

### 3.3 Cost arithmetic (amendment)

Per rollout of one (s,a):

1. Apply operator a to snapshot(s) → 1 generation of λ=4 offspring, evaluated n_eval=2 → **8 CTX** (this also yields r̂).
2. Continue h−1 = 2 more generations with uniform-random actions → 2 × 4 × 2 = **16 CTX** (this yields the continuation part of Q̂_h).
3. Per rollout: **24 CTX**.

| Component | Formula | CTX |
|---|---|---|
| Q̂ estimate (4 rollouts × 5 actions × 80 states) | 80×5×4×24 | 38,400 |
| Extra r̂ samples (2 extra × 5 × 80 × 8 CTX) | 80×5×2×8 | 6,400 |
| **Diagnostic subtotal** | | **44,800** |
| State collection (20 heuristic rollouts, 15 gens, n_eval=2) | 20×15×4×2 | 2,400 |
| **PC1 grand total** | | **47,200** |
| **Hard cap** | | **50,000** |
| Headroom (invalid offspring, retries) | | ≈2,800 |

Invalid offspring that never execute consume **0 CTX** but are counted separately. Operator LLM proposal calls (op2 only in real mode) are counted as `LLM`, not `CTX`.

### 3.4 Common random numbers (CRN) and uncertainty

- **CRN:** for a given state snapshot s, the 4 rollouts of different actions share: (i) task instance id, (ii) evaluation replica seeds for offspring scoring (seeds derived from `hash(state_id, offspring_index, rep)`), (iii) tournament sampling seeds. Offspring *content* differs by operator (that is the treatment).
- **Estimators:** `r̂(s,a)` = mean immediate best-improvement over 6 draws; `Q̂(s,a)` = mean γ-discounted h-step return over 4 rollouts (γ=0.95, same as MDP).
- **Uncertainty:** bootstrap over the 80 states (10,000 resamples) for (i) disagreement rate D, (ii) mean advantage `E[Q̂(s,a_Q) − Q̂(s,a_r)]`.
- **Stratification:** report D by stagnation bin (0, 1–2, ≥3).

### 3.5 Pass / fail / inconclusive (thresholds unchanged from Phase 1)

- **PASS** iff `D ≥ 0.15` **and** mean advantage `≥ 0.02`, with the point estimates meeting thresholds **and** the 95% CI for D excluding 0.10 and the 95% CI for advantage excluding 0.01 (margin rule).
- **FAIL** iff both point estimates miss thresholds by the margin rule (CI entirely below).
- **INCONCLUSIVE** iff CIs overlap the margins.  
  **INCONCLUSIVE → SR1 applies: STOP the PPO hypothesis.** No threshold retuning after seeing results.

---

## 4. Observation-vector schema (canonical, d = 32)

Exactly three blocks: **A (12) + B (12) + C (8) = 32**. Feature order is fixed forever by this table. Tests assert shape, dtype, finiteness, order.

| # | Name | Block | Source | Norm | Update time | Missing rule | Uses execution feedback? |
|---|---|---|---|---|---|---|---|
| 0 | `best_success` | A | eval subset, population best | [0,1] | every gen | 0.0 at gen 0 before eval | **yes** |
| 1 | `mean_success` | A | eval subset, population mean | [0,1] | every gen | 0.0 | **yes** |
| 2 | `succ_gap` | A | best − mean | [0,1] | every gen | 0.0 | **yes** |
| 3 | `fail_format_rate` | A | pop-mean failure histogram | [0,1] | every gen | 0.0 | **yes** |
| 4 | `fail_tool_rate` | A | same | [0,1] | every gen | 0.0 | **yes** |
| 5 | `fail_wrong_rate` | A | same | [0,1] | every gen | 0.0 | **yes** |
| 6 | `fail_timeout_rate` | A | same | [0,1] | every gen | 0.0 | **yes** |
| 7 | `valid_rate` | A | last offspring batch | [0,1] | every gen | 1.0 at gen 0 (no offspring yet) | **yes** |
| 8 | `mean_turns` | A | pop-mean agent turns | /24 → [0,1] | every gen | 0.0 | **yes** |
| 9 | `mean_tool_calls` | A | pop-mean tool calls | /8 → [0,1] | every gen | 0.0 | **yes** |
| 10 | `parent_last_delta` | A | last operator's mean (offspring−parent) success | clip [-1,1] | every gen | 0.0 at gen 0 | **yes** |
| 11 | `recent_eval_coverage` | A | fraction of pop evaluated in last 2 gens | [0,1] | every gen | 1.0 | **yes** |
| 12 | `div_tools` | B | mean pairwise Jaccard over tool-sets | [0,1] | every gen | 0.0 if pop&lt;2 | no |
| 13 | `div_workflow` | B | mean pairwise Jaccard over workflow signatures | [0,1] | every gen | 0.0 | no |
| 14 | `div_prompt` | B | mean pairwise Jaccard over prompt 8-grams | [0,1] | every gen | 0.0 | no |
| 15 | `op_usage_entropy` | B | Shannon entropy of operator usage counts / log(K) | [0,1] | every gen | 0.0 at gen 0 | no |
| 16 | `op_mean_delta_1` | B | mean success-delta of `prompt_local_edit` | clip [-1,1] | every gen | **0.0 if unobserved** | **yes** |
| 17 | `op_mean_delta_2` | B | `prompt_critique_rewrite` | clip [-1,1] | every gen | 0.0 if unobserved | **yes** |
| 18 | `op_mean_delta_3` | B | `tool_subset_edit` | clip [-1,1] | every gen | 0.0 if unobserved | **yes** |
| 19 | `op_mean_delta_4` | B | `workflow_step_edit` | clip [-1,1] | every gen | 0.0 if unobserved | **yes** |
| 20 | `op_mean_delta_5` | B | `crossover` | clip [-1,1] | every gen | 0.0 if unobserved | **yes** |
| 21 | `op_unobserved_frac` | B | fraction of operators never used so far | [0,1] | every gen | 1.0 at gen 0 | no |
| 22 | `age_best` | B | gens since best improvement / T | [0,1] | every gen | 0.0 at gen 0 | no |
| 23 | `pop_size_norm` | B | μ_current / μ_init (schema stability constant) | [0,1] | every gen | 1.0 | no |
| 24 | `gen_frac` | C | t / T | [0,1] | every gen | 0.0 | no |
| 25 | `stagnation_frac` | C | stagnation_rounds / T | [0,1] | every gen | 0.0 | no |
| 26 | `budget_used_frac` | C | t / T (declared separately from gen_frac for future budget variants) | [0,1] | every gen | 0.0 | no |
| 27 | `best_delta_since_start` | C | (best_t − best_0) clip [-1,1] | clip | every gen | 0.0 | **yes** |
| 28 | `improve_last_3_frac` | C | fraction of last ≤3 gens with best improvement | [0,1] | every gen | 0.0 | **yes** |
| 29 | `recency_top1` | C | 1/gap for most recent operator (gap≥1), /T | [0,1] | every gen | 0.0 at gen 0 | no |
| 30 | `recency_top2` | C | second-most-recent operator recency | [0,1] | every gen | 0.0 | no |
| 31 | `offspring_valid_last` | C | validity rate of last offspring batch (duplicate-safe alias of f7 used in ablations) | [0,1] | every gen | 1.0 at gen 0 | **yes** |

**Dimension check:** 12 + 12 + 8 = **32**.  
**Operator-history packing clarified:** counts feed only `op_usage_entropy` and `op_unobserved_frac`; per-operator **means** are separate features 16–20.  
**Ablation mapping:** A0 drops indices 0–11 (and 27–28, 31 which are execution-derived); A1 keeps only {0,1,24}; A2 drops 15–21.

---

## 5. Operator / runtime ambiguities resolved

| Ambiguity | Resolution (frozen) |
|---|---|
| `prompt_local_edit` 0 or 1 LLM call | **0 LLM calls.** Deterministic template paraphrase (fixed synonym table + sentence-order preserve). |
| Base model | See `docs/RUNTIME_LOCK.md`. Phase 2A tests and G3 run in **STUB mode** (deterministic, no network). Real-model lock is pinned but marked `PENDING_DEPLOYMENT`. |
| Canonical serialization | JSON, `sort_keys=True`, `ensure_ascii=False`, `separators=(',',':')`; `tools` sorted; `workflow` in step order; `meta` excluded from behavior hash. Behavior hash = SHA256 of serialized `{system_prompt, tools, workflow}`. |
| Failure trace content for op2 | Only `failure_category` + truncated tool error string (≤200 chars) + turn count. **Never** gold answers, reference outputs, or evaluator internals. |
| Cache keys | `sha256(genotype_hash + task_id + eval_rep + decoding_profile)`. Cache is per-process, in-memory only in 2A. Cannot store C-family results (C is never executed). |

---

## 6. Deviations from Phase 1 registration (complete list)

1. N_states 200 → 80 (original guard allowed ≥100; 80 chosen to fit R and h inside cap).
2. R 20 → 4 for Q̂; r̂ gets 6 draws.
3. h 5 → 3.
4. n_eval 3 → 2 **for PC1 only** (main experiments unchanged at 3).
5. PC1 hard cap interpreted as **CTX**; amended total 47,200 ≤ 50,000.

Nothing else in Phase 1 is changed. μ=8, λ=4, T=15, K=5, γ=0.95, thresholds 0.15 / 0.02 are untouched.

---

## 7. Review checklist (for independent reviewer)

- [ ] Counting units unambiguous
- [ ] Amended total ≤ hard cap with headroom for invalid/retries
- [ ] CRN and uncertainty plan adequate for D and advantage CIs
- [ ] Inconclusive → STOP rule acceptable
- [ ] State schema sums to 32; missing-value rules complete
- [ ] Operator ambiguity resolved; no per-run choices left
- [ ] All Phase 1 deviations listed

**Until boxes are checked and this file is acknowledged in a commit, PC1 stays unexecuted.**
