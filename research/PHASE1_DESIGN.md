# GLEPPO Phase 1 Design — ECOS Problem & Method Specification

**Project:** GLEPPO (https://github.com/yujian777555/GLEPPO)  
**Date:** 2026-10-26  
**Primary candidate (frozen):** **M1 — Execution-Conditioned Operator Selection (ECOS)**  
**Frozen (not developed):** M2 FMPS (Failure-Mode-Conditioned Parent Selection)  
**Scope of this document:** design only. No controller, no environment, no training, no API calls, no experimental results.  
**Inputs used:** `docs/PROJECT_CHARTER.md`, `docs/RESEARCH_PLAN.md`, `docs/LITERATURE_LEDGER.md`, `research/GLEET_BASELINE_AUDIT.md`, `research/CANDIDATE_MECHANISMS.md`, `research/P0.1_EXECUTOR_REPORT.md`, and the Phase 1 task specification.  
**Binding protocol:** `docs/PHASE1_DESIGN_PROTOCOL.md` (planner, 2026-10-26). This document is written against that protocol and preserves P0.1 conditions C1–C5.

---

## 0. Executive decision

**Phase 1 decision: GO — with one hard pre-training condition (PC1) and one falsifiable stop rule (SR1).**

PPO (multi-step return, on-policy) has a **credible, non-articifial advantage** over contextual bandit **only if** operator choice has delayed effects on population state and future improvement. That sequential structure is real in ECOS (diversity investment, staged module construction, stagnation-escape sequences — §4), but it is **not guaranteed to dominate noise**. Therefore:

- GO authorizes Phase 2 environment build **and** a cheap **myopia diagnostic** (§4.4).
- **PC1:** PPO/controller training may not start until the myopia diagnostic passes on the implemented environment.
- **SR1:** if the diagnostic shows the decision problem is essentially myopic, **STOP** the PPO hypothesis (do not wrap it as RL to justify PPO). A contextual-bandit study would be a different project and is out of scope.

---

## 1. Agent genotype

### 1.1 Design goals

1. **Inspectable:** every field is human-readable; diffs between genotypes are meaningful.
2. **Causally effective (G3):** legal edits must change real task-execution behavior (success rate, tool calls, or trajectory structure) on at least one task in the suite — verified in Phase 2 before any controller training.
3. **Bounded:** small enough that evolution is affordable and operators are meaningful (not free-form code synthesis).
4. **Fixed substrate:** base model, tool universe, and runtime interpreter are frozen at Phase 2 start and identical for all methods.

### 1.2 Structured representation (JSON schema)

```json
{
  "genotype_id": "uuid4",
  "system_prompt": "string, UTF-8, 20–800 tokens, no gold-answer leakage",
  "tools": ["calc", "py_sandbox", "str_ops"],
  "workflow": [
    {"step_id": 1, "type": "llm", "prompt_slot": "analyze"},
    {"step_id": 2, "type": "tool", "tool": "calc", "input_from": "analyze"},
    {"step_id": 3, "type": "llm", "prompt_slot": "answer"}
  ],
  "meta": {
    "parent_ids": ["uuid4", "..."],
    "operator_history": ["prompt_local_edit", "..."],
    "created_gen": 3
  }
}
```

Field constraints (validity):

| Field | Constraint | Violation → |
|---|---|---|
| `system_prompt` | 20–800 tokens; must contain a final-answer instruction template slot `{{answer}}` or explicit "Final answer:" line | invalid genotype |
| `tools` | subset of `{"calc","py_sandbox","str_ops"}`; 1–3 tools | invalid |
| `workflow` | 2–6 steps; `type ∈ {llm, tool, branch, finalize}`; `tool` ∈ enabled tools; no cycles; `finalize` exactly once, last | invalid |
| `branch` | max 2 arms; each arm 1–2 steps | invalid |
| runtime | max 8 interpreter iterations; max 24 LLM turns per episode | timeout → failure |

**Canonical serialization (for hashing and crossover):** JSON, UTF-8, keys sorted (`tools` sorted lexicographically; `workflow` kept in step order; `meta` excluded from behavior hash). Behavior hash = SHA256 of serialized `{system_prompt, tools, workflow}`. `meta` is provenance only and never affects execution.

**Do not** evolve free-form Python agent code (that is ADAS/DGM territory and breaks "restricted operator library" framing). Genotype is a **declarative agent spec** executed by a fixed interpreter. **What evolves:** `system_prompt`, `tools`, `workflow` (via the 5 operators only). **What is frozen:** base model, tool implementations/schemas, interpreter, decoding, parent selection, survivor selection, μ/λ/T, evaluator.

### 1.3 Fixed runtime substrate (frozen at Phase 2)

| Component | Specification |
|---|---|
| Base model | `Qwen2.5-7B-Instruct` (or one substitute declared once in `docs/RUNTIME_LOCK.md` before Phase 2 coding; **one** model for all methods and all phases) |
| Decoding (agent execution) | temperature 0.7, top_p 0.95, max 512 tokens/turn; per-episode RNG seed = `hash(task_id, eval_rep, agent_id)` for reproducibility |
| Decoding (operator LLM calls) | temperature 0.8, seed = `hash(operator, parent_id, gen, draw)` |
| Tool `calc` | deterministic arithmetic on a restricted expression grammar |
| Tool `py_sandbox` | deterministic, network-less, 2s timeout, no filesystem writes, stdlib only |
| Tool `str_ops` | deterministic string transforms (case, split, join, regex subset) |
| Interpreter | steps through `workflow`, collects `trace = {turns, tool_calls, errors, final_answer}` |
| Failure taxonomy | `format_error`, `tool_error`, `wrong_answer`, `timeout`, `invalid_genotype` |

Gold labels live in the evaluator only. **Never** in genotype, controller state, or operator prompts.

### 1.4 Worked examples

**Valid genotype (G1):** tools `[calc, str_ops]`; workflow: `llm:analyze → tool:calc → llm:answer` with `Final answer: {{answer}}`. On task A-0017 ("If x=12 and y=5, what is 3x+2y?") may produce correct `46`.

**Legal edit to G1 by `prompt_local_edit` (G2):** `system_prompt` changed from "Solve step by step." to "Solve step by step. Compute intermediate values explicitly before answering." — measurable effect expected on multi-step A/B tasks (higher `wrong_answer` → success).

**Legal edit by `tool_add` (G3):** tools `[calc, str_ops, py_sandbox]` — enables different tool-call traces; must change at least one observable in Phase 2 causality checks (§1.5).

**Invalid:** workflow with `tool:py_sandbox` while `py_sandbox ∉ tools`; or 7 steps; or missing `finalize`. Invalid offspring do not enter the population; they count against validity rate.

### 1.5 Causality check (Phase 2 gate G3, before any controller work)

For each operator and each of 3 fixed seeds, apply to the same parent and measure on a 20-task smoke set:

- Δ success rate ≠ 0 **or** Δ tool-call histogram ≠ 0 **or** Δ mean turns ≠ 0.

If an operator never changes any observable, drop it from the library **before** freezing K. Record the result in `research/G3_CAUSALITY.md` (Phase 2).

---

## 2. Evolution operators (fixed library, one decision family)

**Decision family (C2 honored):** **operator selection only.** Parent selection, survivor selection, population size, and offspring count are **frozen** for all methods (PPO, bandits, rules, FM-rewrite).

### 2.1 Frozen evolution parameters

| Parameter | Value | Rationale |
|---|---|---|
| Population μ | 8 | cost-bounded; enough for diversity stats |
| Offspring per generation λ | 4 | one operator × 4 draws/parents |
| Generations per episode T | 15 | short-horizon but multi-step (supports §4) |
| Parent selection | tournament, k=2, on current eval success | fixed; not a learned decision |
| Survivor selection | (μ+λ) elitist truncation to μ | fixed |
| Init population | 8 random valid genotypes from seed 20261026 | same for all methods |
| Operator application | one operator `a_t` per generation; applied to produce all λ offspring (selected parents vary per offspring via frozen tournament) | "one operator per generation" as specified |

### 2.2 Operator library (K = 5)

| ID | Name | Inputs | Edit scope | LLM proposal calls | Output schema | Failure handling | Uses execution feedback? | Typical delayed effect |
|---|---|---|---|---|---|---|---|---|
| 1 | `prompt_local_edit` | parent `system_prompt` | 1–2 sentences | 0 (template) or 1 paraphrase | valid `system_prompt` | if invalid → offspring invalid | no | low; exploitation |
| 2 | `prompt_critique_rewrite` | parent + last failure trace (type + tool error string, **no gold**) | full `system_prompt` rewrite | 1 critique + 1 rewrite = 2 | valid `system_prompt` ≤800 tokens | if LLM fails/invalid → offspring invalid | **yes** (failure trace) | medium; can rebuild approach |
| 3 | `tool_subset_edit` | parent `tools` | add one missing tool **or** drop one (alternating) | 0 | `tools` 1–3 | if would go to 0 tools → invalid | no | high (scaffolding); delayed |
| 4 | `workflow_step_edit` | parent `workflow` | one non-`finalize` step's `type`/`tool`/`prompt_slot` from fixed templates | 0 | valid `workflow` | if schema violated → invalid | no | high; only useful after tools exist |
| 5 | `crossover` | parent + mate (frozen tournament) | prompt sentence union; tool union (cap 3); workflow step alternation | 0 | valid genotype | if result invalid → try 1 fallback (parent clone + prompt splice); else invalid | no | high diversity injection |

**B5 (FM-rewrite) is NOT inside K.** It is an external baseline strategy: unrestricted LLM rewrite of the whole genotype (DGM/Promptbreeder style), same λ and evaluation budget. Keeping it outside K keeps the action set semantically closed and makes "PPO over a restricted library" vs "always FM" a clean comparison.

Invalid offspring are **counted and dropped** (never silently replaced by parent clones in the success metric). Parent is not re-credited. `valid_rate` is logged every generation.

### 2.3 Why K = 5 and not more

Small K keeps bandit baselines strong and sample complexity honest. Operators are chosen to span **exploitation (1), repair (2), scaffolding (3, 4), diversity (5)** — the four roles needed for delayed-effect structure in §4.

---

## 3. PPO MDP (strict)

An episode = **one evolution run** on **one training task instance** (not one operator pull).

### 3.1 State `s_t ∈ R^d` (only decision-time signals)

Concatenation of three blocks (d = 32 as designed; exact feature list frozen in Phase 2 code constants):

**A. Execution-outcome block (novelty-relevant; 12 dims)** — from the evaluation subset of the current training task only:

1. `best_success` — population-best success rate (n_eval repeats)
2. `mean_success` — population mean success
3. `succ_gap` — `best_success − mean_success`
4. `fail_format_rate`, `fail_tool_rate`, `fail_wrong_rate`, `fail_timeout_rate` — population-mean failure histogram (4 dims)
5. `valid_rate` — fraction of last offspring batch that produced valid genotypes
6. `mean_turns`, `mean_tool_calls` — cost/behavior intensity
7. `parent_last_delta` — success(offspring) − success(parent) for last applied operator

**B. Population / operator-history block (12 dims):**

8. diversity: mean pairwise Jaccard distance over tool-sets, workflow signatures, and prompt 8-gram MinHash (3 dims)
9. `op_count[k]` normalized, `op_mean_delta[k]` for k=1..5 (10 dims) → compressed to 5 empirical means + 1 entropy = 6 dims, plus 3 diversity dims, plus 3 (best/mean/age) = 12 dims (exact packing in Phase 2)

**C. Progress block (8 dims):**

10. `gen_t / T`, `stagnation_rounds / T`, `budget_used_frac`, `best_ever_delta_since_start`
11. one-hot-ish top-2 recent operators' recency (2 dims), `improve_last_3` (fraction of last 3 gens with best improvement)

No gold answers, no test labels, no evaluator internals beyond the failure taxonomy labels above.

### 3.2 Action

`a_t ∈ {1,2,3,4,5}` — categorical (softmax policy). **One operator for the whole generation.**

### 3.3 Transition

```
s_t  --choose a_t-->  parents_t = frozen_tournament(pop_t)
      --> offspring_t = Apply(a_t, parents_t)   # λ=4, validity-checked
      --> eval_t = ExecuteAndScore(offspring_t, task, n_eval)
      --> pop_{t+1} = (μ+λ)_elitist(pop_t ∪ offspring_t)
      --> s_{t+1} = featurize(pop_{t+1}, history, t+1)
```

Environment is **stochastic** (LLM sampling, tournament) but **stationary** given (task, model lock, seeds).

### 3.4 Reward

Per generation t:

```
r_t = w1 * (best_success_{t} - best_success_{t-1})        # population-best improvement, dense
    + w2 * 0.1 * (valid_rate_t)                            # validity bonus (capped)
    + w3 * (mean_success_t - mean_success_{t-1}) * 0.25    # population lift (secondary)
```

Defaults: `w1=1.0`, `w2=1.0`, `w3=1.0`, rewards clipped to [-0.5, 1.0].  
**Primary optimization target is the discounted return** `R = Σ_{t=0}^{T-1} γ^t r_t` with **γ = 0.95** (not 0.999 — episodes are 15 steps; GLEET's 0.999 targets 2000-step numeric runs).

No test labels. No budget-shaped reward (charter non-goal).

### 3.5 Termination

- `t = T` (15 generations), or
- `best_success ≥ 0.95` on the training eval subset (early success), or
- environment exception → terminal with last state, reward 0 (counted as failure run).

### 3.6 How the action influences long-horizon task performance (why this is not a bandit pull)

| Mechanism | Immediate effect | Delayed effect | Who captures it |
|---|---|---|---|
| Diversity investment (`crossover`, `tool_subset_edit`) | often Δbest ≈ 0 this gen | higher diversity → later `prompt_critique_rewrite` / `workflow_step_edit` finds improvements that exploitation cannot | multi-step return (PPO/Q), **not** myopic bandit |
| Staged scaffolding (`tool_subset_edit` then `workflow_step_edit`) | add-tool alone rarely helps | enables workflow edits to change execution traces and success | multi-step |
| Stagnation-escape sequence | 1–2 gens of neutral/negative r | breakthrough gen gets large r; credit must propagate backward | multi-step (γ^k) |
| Over-exploitation (`prompt_local_edit` only) | steady small gains | diversity collapse → late-episode stagnation; total return lower | multi-step (penalty appears later) |

A contextual bandit maximizes `E[r_t | s_t, a_t]` and is **provably optimal only when actions have no effect on future contexts/rewards**. ECOS violates that: `a_t` changes `pop_{t+1}` and thus `s_{t+1}` and the distribution of future rewards.

---

## 4. Positive test of the contextual-bandit alternative

### 4.1 The alternative (steelman)

Let a **contextual bandit** observe the same `s_t`, choose `a_t`, receive only `r_t`, and update. Variants to use as baselines:

- **B3a UCB1** (context-free)
- **B3b EXP3** (context-free, adversarial-ish)
- **B3c linear contextual bandit** (LinUCB) on the same `s_t`
- **B3d neural contextual bandit** (optional, one hidden layer) — strongest non-sequential learned control

If ECOS were purely "pick the best operator given current context", B3c/B3d would be the right tool and PPO would be unjustified complexity.

### 4.2 Why PPO is not an artificial wrap (the sequential claim)

Three properties make the MDP non-myopic **by construction**, not by narrative:

1. **Action → state coupling:** offspring enter the population via elitist (μ+λ); population statistics (diversity, failure histogram, operator success history) are part of `s_{t+1}`. There is no "reset of context" between pulls.
2. **Delayed reward pathways are explicit** (§3.6 table): operators differ in *when* they pay off, not only *whether* they pay off. `tool_subset_edit` is the canonical example: weak immediate reward, high enabling value.
3. **Objective is episode return**, `Σ γ^t r_t`, not the immediate `r_t`. PPO optimizes the former; bandits optimize the latter. When the two optima diverge, PPO is the correct model.

This matches the classical exploration–exploitation sequential framing used by GLEET (PPO over an optimization trajectory), and the adaptive-operator-selection literature — but here the state includes **real agent-execution outcomes**, and the objects are **LLM-agent genotypes**.

### 4.3 What PPO must show for the advantage to be real (pre-registered)

| ID | Claim | Test (Phase 2 diagnostic / Phase 3 result) |
|---|---|---|
| Q1 | Optimal action is sometimes non-greedy w.r.t. immediate `r_t` | Myopia diagnostic (§4.4): rate of states where `argmax_a Q_total(s,a) ≠ argmax_a r(s,a)` |
| Q2 | Multi-step credit matters | PPO (or Q-learning with γ>0) > LinUCB on held-out Family-C |
| Q3 | Execution features carry the gain | Ablation A1 (fitness-only state) loses to full ECOS |
| Q4 | Not just "richer features" | B3c/B3d use **identical** `s_t`; if they match PPO, the sequential claim fails → SR1 |

**Honesty clause:** if Q1 rate is low and Q2 fails, the correct conclusion is **"this decision problem is a contextual bandit; STOP the PPO hypothesis"** — not "enlarge the action space" or "add modules".

### 4.4 Myopia diagnostic (PC1 — run before any PPO training)

On the implemented environment (Phase 2), for a sample of ≥200 states collected from random and heuristic rollouts on **training-family tasks only**:

1. Estimate immediate reward `r̂(s,a)` for all 5 actions by Monte-Carlo (≥20 rollouts per (s,a) pair on the sampled states, re-evaluating offspring only — states held fixed).
2. Estimate discounted continuation value `Q̂(s,a)` with a short horizon `h=5` from the same samples (roll out each (s,a) for h steps with a fixed random policy afterwards).
3. Compute disagreement rate `D = P[argmax_a r̂(s,a) ≠ argmax_a Q̂(s,a)]`.
4. **Pass criterion (pre-registered):** `D ≥ 0.15` **and** `E[Q̂(s, a_Q) − Q̂(s, a_r)] ≥ 0.02` (absolute advantage of non-myopic choice in return units).  
   **Fail:** otherwise → **SR1 STOP** before PPO investment. May still publish a bandit-only study later (out of scope here).

Also record `D` stratified by stagnation bins — delayed effects should concentrate in high-stagnation states if the story is true.

### 4.5 Value-based RL baseline (is Q-learning needed?)

**Yes — include Q-learning (tabular or small MLP DQN-style) as B6.** Reasons:

1. RL-EA survey (arXiv:2308.13420) documents operator-selection RL as mostly **Q-learning**. Omitting it would leave the strongest historical comparison out.
2. Q-learning with γ>0 also captures delayed effects; it isolates "on-policy PPO vs value-based RL" from "RL vs bandit".
3. Cost is modest (same environment, discrete actions).

If Q-learning matches PPO, that is not a STOP for the sequential hypothesis — it is a method comparison. **SR1 is about bandit vs RL, not PPO vs DQN.**

### 4.6 Summary answer to "why PPO?"

> ECOS is a finite-horizon MDP in which operator choice changes the population, and therefore changes which operators pay off later. Delayed pathways (diversity investment, scaffolding, stagnation escape) are first-class in the design. PPO optimizes discounted multi-step return; contextual bandits optimize myopic reward. The design **pre-registers** a myopia diagnostic and a kill baseline (identical-state contextual bandit). If the decision problem turns out myopic, we STOP — we do not wrap a bandit problem as RL.

---

## 5. Task environment and data split

### 5.1 Task families (concrete)

| Family | Role | Type | Success metric | Why here |
|---|---|---|---|---|
| **A** | Train | arithmetic word problems, 1–3 steps | exact match (normalized) | tool `calc` useful; failure `wrong_answer` common |
| **B** | Train | tool-composition tasks (compute then transform/format) | exact match | needs `calc`+`str_ops` or `py_sandbox`; `tool_error` appears |
| **A_val / B_val** | Validation (model selection only) | same generators, **disjoint seeds & templates** | exact match | overfit check within families |
| **C** | **Held-out test** | structured constraint / formatting tasks (e.g., "output JSON with keys k1..k3 satisfying rules") | schema+constraint check | **different failure modes** (`format_error` dominant); never trained on |

Family C is a **family shift**, not a random split — the controller must transfer *how to choose operators*, not memorize task content.

### 5.2 Instance generation and isolation

- Each instance: `{task_id, family, template_id, seed, input, gold}`.
- **Generator locked** in Phase 2 (`data/gen_*.py`), seed space declared:
  - Train A: `seed ∈ [0, 199]`, templates `TA1..TA8`
  - Train B: `seed ∈ [0, 199]`, templates `TB1..TB6`
  - Val A′: `seed ∈ [1000, 1049]`, templates `TA1..TA8` minus `TA8` (hold out one template)
  - Val B′: `seed ∈ [1000, 1049]`, templates `TB1..TB6` minus `TB6`
  - Test C: `seed ∈ [0, 99]`, templates `TC1..TC5` — **all** templates and seeds disjoint from train/val
- **Manifest freeze:** `data/manifest.json` lists every `task_id`, SHA256 of the JSONL split file, generator git hash, and a freeze timestamp. Written **before** controller training; any change invalidates results.
- **Access control in code (Phase 2):** evaluator process holds gold labels; controller process receives only `s_t` features and scalar rewards. Held-out C golds are never loaded into the training process (separate file, optional encryption-at-rest not required — **process isolation + code path separation** is enough if enforced by tests).
- **License stance:** v1 uses **generated tasks** (original templates) so no third-party dataset license is assumed. Any later external benchmark (e.g. a public agent suite) requires a written license/split audit in `docs/BENCHMARK_LICENSE.md` before use — never assume a public name implies a usable train/test split or redistribution rights.

### 5.3 Sizes (design targets; exact counts may shrink if cost requires — must be re-declared in the freeze)

| Split | N tasks | Used for |
|---|---|---|
| Train A+B | 400 | PPO/Q/bandit training episodes |
| Val A′+B′ | 100 | hyperparameters, early stopping, model selection |
| Test C | 100 | **frozen-controller final eval only** |

---

## 6. Pre-registered evaluation protocol and baselines

### 6.1 Primary metric

**`Succ_C(best)`** = task success rate of the **best genotype** found during an evolution run (by training-family eval score during run; selected without C labels), measured **on Family-C tasks** after the controller is frozen.  
Also report `Succ_C(mean)` (population mean) and success of the single final selected agent.

Budget-equalized: every method gets the same **T × λ × n_eval** agent-execution episodes per task.

### 6.2 Baseline suite (mandatory)

| ID | Method | What is fixed | What is adaptive |
|---|---|---|---|
| **B0** | Fixed operator = `prompt_local_edit` always | everything | nothing |
| **B0b** | Fixed operator = `prompt_critique_rewrite` always (second floor) | everything | nothing |
| **B1** | Uniform random over K | parent/survivor/μ/λ/T | nothing |
| **B2** | Hand adaptive: 1/5-success rule — if last operator improved best in ≥2 of last 5 uses keep it; else switch to `crossover`; if stagnation ≥ 4 force `tool_subset_edit` | same | operator choice by rule |
| **B3a** | UCB1 over K | same | counts/means |
| **B3b** | EXP3 over K | same | weights |
| **B3c** | LinUCB on **identical state `s_t`** | same | linear payoffs |
| **B3d** | Neural contextual bandit on identical `s_t` (1 hidden layer) | same | nonlinear myopic |
| **B4** | GLEET-style single knob: continuous `u∈[0,1]` maps to operator mixture (softmax temperature / weighted sample), trained with the **same PPO code** | same | continuous intensity only |
| **B5** | FM-rewrite always (unrestricted LLM rewrite of whole genotype; same λ, same eval budget) | parent/survivor/μ/λ/T | nothing (always FM) |
| **B6** | Q-learning / DQN (γ=0.95) on same MDP | same | value-based RL |
| **ECOS** | PPO on same MDP (γ=0.95) | same | policy-gradient RL |

**Ablations (required for mechanism claims):**

- **A0:** ECOS with **no execution-feature block** (strip block A entirely; population+progress only) — protocol-required probe that execution feedback is used.
- **A1:** ECOS with **fitness-only state** (only `best_success`/`mean_success`/`gen_t`; strip failure histogram, diversity, operator history).
- **A2:** ECOS without operator-history block.
- **A3:** ECOS with myopic reward only (`r_t` immediate, γ=0) — should collapse toward bandit; if it matches full ECOS, sequential claim is weak.

### 6.3 Fairness controls

- Same genotype schema, same 5 operators for all methods except B5 (which replaces variation entirely).
- Same frozen tournament parent selection, (μ+λ) survivor, μ=8, λ=4, T=15.
- Same base model, decoding, tools, interpreter.
- Same task manifests and seeds for evaluation replications.
- Same total agent-execution budget per method per task.
- Training: ECOS/B6/B3d/B4 see only Train A+B; all methods see Val for model selection; **C evaluated once per seed after freeze** (no re-tuning on C).

### 6.4 Seeds and uncertainty

- Evolution/run seeds: **≥5** per method per task-family protocol (Phase 3); **≥3** for early smoke tests.
- **Controller training seeds:** ≥3 independent PPO/Q/neural-bandit training seeds each (policy init + rollout RNG); report mean and CI across training seeds × evolution seeds.
- Agent stochasticity: each genotype scored with **n_eval = 3** independent execution replicas (seeds derived from `task_id, eval_rep`).
- Statistics: paired bootstrap over tasks (10k resamples), report mean ± 95% CI; primary comparison ECOS vs B3c and vs B3d and vs B2.
- Multiple comparisons: Holm correction across the pre-registered primary comparisons (ECOS−B3c, ECOS−B3d, ECOS−B2, ECOS−B5, ECOS−B6).

---

## 7. Real-execution metrics and failure handling

| Event | Treatment |
|---|---|
| `invalid_genotype` | does not enter population; counts in `valid_rate`; reward includes validity term |
| `timeout` / `tool_error` / `format_error` / `wrong_answer` | success = 0 for that replica; contributes to failure histogram in state |
| LLM stochasticity | n_eval=3 replicas; genotype score = mean success over replicas |
| Randomness in operators | operators with LLM draws use hashed seeds; multiple draws recorded in `meta.operator_history` |
| Repeated evaluation | parent re-scored only when its eval is older than 2 generations (cost control; same rule for all methods) |
| Evaluation noise (primary uncertainty) | CI over evolution seeds × tasks; optional variance decomposition (agent vs evolution) in Appendix |
| Validation use | model selection / early stopping / hyperparameters **only** |
| Test C use | **frozen** controller, single final evaluation protocol, no adaptation |

**Primary result:** `Succ_C(best)` under fixed budget.  
**Secondary:** `Succ_C(mean)`, validity rate, diversity trajectory, best-success trajectory, wall-clock, LLM tokens (reported, not claimed as contribution).

---

## 8. Cost / feasibility estimation (method, not fabricated budgets)

Exact costs are **TBD until measured**. The estimation method (pre-registered formulas):

Let per task:

- `E_task = T × λ × n_eval` agent-task execution episodes (base: 15×4×3 = **180**)
- `L_task` = mean LLM turns per agent-task episode (measure in Phase 2 smoke; assume 3–8 → TBD)
- `O_op` = extra LLM calls per operator application (only ops 2 and optionally 1; ≈ 1–2 calls)

Per evolution run:

- Agent-execution episodes: `E_task`
- LLM calls ≈ `E_task × L_task + T × O_op` (order-of-magnitude)

Controller training (ECOS):

- Env steps per episode = T = 15
- Episodes per PPO epoch = `N_train_tasks_sampled × episodes_per_task` (declare: 8 tasks/epoch × 2 episodes)
- Env steps for training ≈ `epochs × 8 × 2 × 15` (TBD after smoke; report actual)
- **No claim** of total GPU/API cost until Phase 2 smoke test writes `research/COST_BASELINE.md` with measured `L_task`, tokens, wall-clock.

Feasibility thresholds (pre-registered):

- If a single evolution run exceeds **5000** agent-task episodes (budget control), reduce n_eval to 2 and/or T to 12 — re-declare in freeze.
- If myopia diagnostic (§4.4) requires > 50k episodes, sample fewer states (≥100) or STOP as cost-infeasible for the sequential claim.

---

## 9. GO / REVISE / STOP for Phase 1

### 9.1 Decision

# **GO** (to Phase 2 environment build), conditional on PC1 and SR1.

### 9.2 Why GO

1. **Genotype, operators, and MDP are fully specified** (§1–3) — an independent implementer can start coding without guessing schema, K, μ, λ, T, or reward form.
2. **PPO vs contextual bandit has a pre-registered, falsifiable sequential theory** (§3.6, §4) with an explicit myopia diagnostic and identical-state bandit baselines. We are not wrapping a bandit problem as RL — we are testing whether it is one.
3. **Strong baselines are mandatory and budget-equalized** (§6), including B3c/B3d (identical-state bandits), B5 (FM-rewrite), B6 (Q-learning).
4. **Data isolation and freeze method** (§5.2) are concrete (hash manifests, process-level label isolation).
5. **Charter non-goals held:** one decision family (M1 only); budget allocation not the contribution; no GLEET code; no novelty claims from PPO-over-agents.

### 9.3 Primary innovation risks (must appear in any writeup)

| Risk | Level | Guard |
|---|---|---|
| Decision problem is actually myopic → PPO unnecessary | **High** | PC1 diagnostic + B3c/B3d + SR1 |
| Gain from state engineering, not sequential learning | High | A1 ablation + identical-state bandits |
| FM-rewrite (B5) dominates restricted library | High | equal-budget comparison; if B5 wins on C, restricted-library claim is dead → REVISE scope to "when do restricted operators suffice" or STOP |
| Literature collision (C4; DRL-PSO/RLEPSO/HELIOS unverified) | Medium-High | re-check before publication claims |
| LLM noise swamps delayed credit | Medium | n_eval, CI, A3 myopic-reward ablation |
| Genotype too small → effects trivial | Medium | G3 causality check; drop no-op operators before freeze |
| Q-learning matches PPO | Low (not a kill) | B6 comparison is informative, not fatal |

### 9.4 Falsifiable stop conditions (binding)

| ID | Condition | Action |
|---|---|---|
| **SR1** | Myopia diagnostic fails (§4.4 pass criteria not met) | **STOP** PPO hypothesis before training |
| **SR2** | Phase 3: ECOS not > B3c **and** not > B3d on Family-C (paired 95% CI includes 0 for both) | **STOP** as scoped (C5) |
| **SR3** | A1 (fitness-only) ≈ full ECOS | REVISE claim to "state features matter" at best; if B3c with features matches, STOP |
| **SR4** | G3 causality fails for ≥3/5 operators | REVISE operator library once; second failure → STOP |
| **SR5** | Cost smoke infeasible (§8 thresholds) | REVISE scale once (T/n_eval); second failure → STOP |

**No third mechanism** may be introduced to rescue a failed STOP.

---

## 10. Unresolved questions (honest)

1. **Base model lock:** `Qwen2.5-7B-Instruct` is a design default; hardware/API availability may force one substitute — must be written to `docs/RUNTIME_LOCK.md` before coding (one-time, no silent swaps).
2. **Exact feature packing** of block B (12 dims) is specified in prose; implementer freezes the vector layout in code constants and records it in Phase 2.
3. **Literature collision** still search-bounded (P0.1 C4); HELIOS, DRL-PSO, RLEPSO unverified.
4. **n_eval=3** may prove too noisy or too expensive; adjustment allowed only via §8 feasibility rule and must be re-declared in the manifest freeze.
5. **Family-C difficulty** must be pilot-checked in Phase 2 (not near 0% or near 100% for init populations) or the family is replaced **before** any controller training.
6. **Operator I/O measured cost** (LLM proposal calls for ops 1–2) is specified as counts (≤2 per application); token cost TBD in Phase 2 smoke.

---

## 11. Phase 2 handoff (what the next executor should do)

1. Write `docs/RUNTIME_LOCK.md` (model + decoding + tools + interpreter version).
2. Implement genotype schema, interpreter, 5 operators; run **G3 causality** → `research/G3_CAUSALITY.md`.
3. Implement task generators A/B/C + manifest freeze → `data/manifest.json`.
4. Implement evolution loop with frozen parent/survivor rules; log traces.
5. Implement **myopia diagnostic** → `research/MYOPIC_DIAGNOSTIC.md`. **Gate PC1.**
6. Implement baselines B0–B6 in the same harness.
7. Only after PC1 pass: implement PPO trainer (independent code; no GLEET source).

Out of scope for Phase 2: held-out C training use, paper claims, M2, budget-allocation novelty.
