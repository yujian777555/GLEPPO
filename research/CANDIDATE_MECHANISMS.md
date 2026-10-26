# Candidate Research Mechanisms for GLEPPO (P0.1)

**Status:** proposals only. Not implemented. No experiment has been run. Numbers appearing as "criterion thresholds" are *decision rules for future experiments*, not results.  
**Date:** 2026-10-26  
**Constraint honored:** at most two candidates; each specifies state, action, reward, train/test split, strong baselines, novelty risk, and a falsifiable GO/NO-GO test. "Apply PPO to agent evolution" is **not** accepted as a contribution.

---

## What must be true for either candidate to count as a contribution

From the project charter and the GLEET / related-work audit (`research/GLEET_BASELINE_AUDIT.md`, `docs/LITERATURE_LEDGER.md`):

1. The decision problem is **agent-evolution-specific** (not a re-skin of numeric hyper-parameter control).
2. The controller consumes **real task-execution feedback**, not only a scalar fitness oracle.
3. The policy is **trained across a task distribution** and evaluated on **held-out task families** after freezing.
4. The policy beats **fixed, random, a strong hand-designed adaptive rule, and a non-RL learned adaptive baseline** (bandit or equivalent) under equal evaluation budgets and multiple seeds.
5. Limited-budget allocation is **not** the central claim (charter non-goal).
6. GLEET code is **not** reused (no license); implementations must be independent.

If a candidate fails 4 or 3 in a well-run experiment, the outcome is REVISE or STOP — not "add more modules".

---

## Shared protocol (applies to both candidates)

**Agent genotype (must be chosen in Phase 1; both candidates assume the same minimal genotype):** a small, inspectable LLM-agent configuration, e.g. a structured bundle `(system prompt, tool subset, workflow graph / policy stub)`. Genotype edits must change observable execution behavior on at least one task (G3 environment gate).

**Environment:** population of such agents; each generation produces offspring via a restricted variation library; each evaluated on a **task episode** with real execution (tool calls, intermediate steps, final answer). Evaluator must be fixed before controller training and must not leak test labels into controller state.

**Reward hygiene:** primary reward comes from task outcomes on a declared evaluation subset; no access to held-out test labels; variance from LLM stochasticity is measured and reported (multi-seed, re-eval policies documented).

**Training/val/test split (both candidates):**

- **Train families** (controller training only): e.g. Family-A tasks (knowledge QA) + Family-B tasks (structured tool use).
- **Validation:** Family-A′/B′ held-out instances (same families, unseen tasks) for model selection / hyper-parameters.
- **Test (frozen controller):** Family-C tasks (different family, e.g. multi-step planning or interactive tools) never seen during training or validation.  
  Exact family definitions are a Phase 1 deliverable; the *existence* of a held-out family is non-negotiable.

**Minimum baseline suite (both candidates):**

| ID | Baseline | Role |
|---|---|---|
| B0 | Fixed single operator / fixed parent rule (hand-picked) | floor |
| B1 | Random decision with the same action set | floor |
| B2 | Hand-designed adaptive rule (e.g. success-rate 1/5-rule or stagnation-triggered diversity injection) | strong non-learned |
| B3 | Non-RL adaptive: UCB1 / EXP3 bandit over the same discrete action set (or linear-context bandit if state features are used) | **strongest control for "is RL needed?"** — ShinkaEvolve (arXiv:2509.19349) already uses bandit-based selection in LLM program/harness evolution, so this baseline is industry-standard, not strawman |
| B4 | GLEET-style continuous intensity split (single knob ∈ [0,1]) with the same PPO trainer | weak structural control (optional but recommended) |
| B5 | LLM-as-operator baseline where applicable (FM rewrite like DGM/Promptbreeder/ADAS), equal evaluation budget | ecological control for the LLM-evolution literature |

Primary metric: final task success rate of the best agent (and population mean) on held-out Family-C, under a fixed total number of agent-execution evaluations. Secondary: offspring validity rate, diversity, per-generation improvement curve, wall-clock/LLM-token cost (reported, not the claim).

---

## Candidate M1 — Execution-Conditioned Operator Selection (ECOS)

**One-sentence claim to be tested:** *A small PPO policy that selects which variation operator to apply to a parent LLM-agent, conditioned on population statistics and real execution outcomes, finds better agents on held-out task families than fixed, random, adaptive-rule, and bandit operator selection.*

### Why this and not "PPO on agent evolution"

- Operator selection is already a standard RL-EA category (RL-EA survey 2308.13420) in numeric EC; the claimable delta is the **execution-feedback state** and **LLM-agent + held-out family protocol**, not "RL selects operators".
- LLM-agent evolution systems (Promptbreeder, ADAS, DGM, AlphaEvolve) use FM rewrite / archive logic, not a trained operator policy over a restricted library. The scientific question is whether *learning which restricted operator to fire* beats both (a) simple adaptive rules and (b) always-on FM rewrite.

### State (only signals available at decision time)

Per candidate parent (and population aggregates):

1. **Execution outcome features** (the novelty-relevant part): recent success rate on a fixed eval subset; failure-type histogram (parse/format, tool error, wrong answer, timeout); average steps/tokens; validity of produced trajectories.
2. **Population features:** fitness mean/std/best; behavioral diversity (e.g. embedding dispersion of trajectories or genotype edit signatures); operator success history (counts and mean improvement per operator).
3. **Progress features:** generations elapsed, stagnation counter (rounds without improvement), relative gain of last offspring vs parent.

No test labels, no privileged evaluator internals.

### Action

Discrete, **one** decision family (charter: do not combine families):

- `a ∈ {1..K}` variation operators, e.g.: (i) prompt local edit, (ii) prompt rewrite w/ self-critique, (iii) tool-subset add/drop, (iv) workflow-step reorder, (v) crossover with another parent, (vi) FM-guided rewrite (if kept, count as one operator).
- Policy: categorical (softmax). PPO with discrete actions is acceptable and simpler than GLEET's Gaussian split.

### Reward

`r_t = (succ(offspring) − succ(parent))` on the declared eval subset of the *current training task*, plus a small validity bonus (offspring executes without crash). Optional shaping: failure-type reduction, capped and ablated.  
Not: pure score without reference to parent; not budget shaping as the main term.

### Training

- PPO (or equivalent on-policy RL) trained only on Train families; val for selection; freeze; Test on Family-C.
- Multiple seeds (≥5 for the controller training itself if affordable; ≥10 eval seeds per test task set for confidence intervals).
- Ablations: (A1) state without execution features (fitness-only) — tests whether execution feedback is actually used; (A2) state without operator history; (A3) reward without validity term.

### Strong baselines

B0–B5 above. **B3 (bandit) is the kill-criterion baseline.**

### Novelty risks (must be honest in any writeup)

| Risk | Severity | Mitigation |
|---|---|---|
| "RL selects operators" is old (RL-EA survey 2308.13420) | High | Position contribution as *execution-conditioned* selection for *LLM agents* with held-out-family transfer; require ablation A1. Note: survey says operator-selection RL-EAs are almost all Q-learning — a PPO-vs-Q-learning contrast is *supporting* evidence only, not the contribution |
| Learned operator/selection modules already exist (Lange et al. 2304.03995 meta-BBO GA) | High | Differentiate: PPO training, execution-feedback state, LLM agents, held-out *task-family* transfer; cite and compare conceptually |
| ADAS/DGM already "automatically choose how to improve agents" with FMs | High | Compare under equal evaluation budget (B5); claim only if trained policy wins or is far cheaper |
| ShinkaEvolve already uses bandit selection for LLM evolution | Medium-High | B3 becomes the *central* kill baseline; "learned controller" must mean something bandits cannot do (state-dependent credit across generations, or transfer) |
| Action space too small → bandit matches PPO | Medium | That is exactly what NO-GO tests; if bandit matches, STOP this candidate (do not enlarge action space to force PPO to win) |
| Evaluator noise → reward unreliable | Medium | Multi-seed eval, report variance; noise-aware ablation |

### Falsifiable GO / NO-GO

**Experiment (Phase 3):** train ECOS on Train families; freeze; evaluate on held-out Family-C with the full baseline suite; ≥5 training seeds; bootstrap CIs on success rate.

- **GO** iff **all** hold:  
  (1) ECOS mean success on Family-C > B3 (bandit) and > B2 (adaptive rule) with 95% bootstrap CI excluding 0 (paired across tasks);  
  (2) ECOS ≥ B5 (FM-rewrite) or is strictly cheaper at matched success;  
  (3) ablation A1 (no execution features) is significantly worse than full ECOS — i.e. execution feedback carries the gain;  
  (4) effect holds on ≥2 of 3 held-out family settings if multiple families are available.
- **NO-GO (→ REVISE or STOP):** if B3 matches ECOS within CI, or A1 ≈ full ECOS (gain is not from execution feedback), or gains vanish on held-out families (overfitting).

---

## Candidate M2 — Failure-Mode-Conditioned Parent Selection (FMPS)

**One-sentence claim to be tested:** *Choosing which parents to combine (and with which partner) using a PPO policy conditioned on the population's execution failure-mode profile yields better LLM agents on held-out task families than fitness-proportional, tournament, random, and bandit parent selection.*

### Why this second candidate

- Parent selection is the charter's third decision family and is cleanly separable from M1 (operator choice).
- Specific hypothesis: in LLM agents, **failure modes** (tool errors vs format errors vs wrong reasoning) are more informative for *who should mate with whom* than scalar success rate alone — e.g. pair a format-robust agent with a reasoning-strong but fragile one.
- This is harder to dismiss as "GLEET with a new action" because the state is failure-structured and the action is combinatorial pairing, not a continuous knob.

### State

1. **Failure-mode profile per individual:** histogram of failure types over recent episodes; per-type success rates; recovery rate after previous edits.
2. **Pairwise compatibility proxies:** behavioral distance between two agents (trajectory embeddings or tool-usage vectors); historical improvement when this pair (or similar pairs) was crossed.
3. **Population context:** diversity indices, stagnation, generation counter, best-so-far gap.

### Action

Discrete parent-pair selection from a shortlist (e.g. choose index pair from top-M candidates, or select partner for a fixed first parent). One decision family only. M1's operator is held **fixed** (default operator library used by all baselines) so effects are separable.

### Reward

`r = succ(crossover offspring) − max(succ(parent1), succ(parent2))` on the training-task eval subset; validity bonus as in M1.  
Negative reward when crossover produces invalid or strictly worse agents (encourages avoiding destructive pairs).

### Training / test

Same shared protocol as M1 (Train families → freeze → held-out Family-C). Seeds and leakage rules identical.

### Strong baselines

- B0 random pair; B1 fitness-proportional pairing; B2 tournament pairing; **B3 bandit over pair-shortlist features** (contextual bandit if state features used); B5 skip (no FM operator in this candidate — operator fixed).

### Novelty risks

| Risk | Severity | Mitigation |
|---|---|---|
| Parent selection is classic EA; RL-for-selection exists in RL-EA | High | Contribution must be the **failure-mode state** for LLM agents; ablate failure features vs fitness-only |
| State engineering may dominate the policy (hand-crafted features do the work) | Medium | Report linear probe / bandit-with-same-features control (B3) |
| Combinatorial action may make PPO sample-inefficient | Medium | Shortlist size M ≤ 8; if training fails, that is a REVISE, not a reason to claim success on M1-style storytelling |
| Overlaps with M1 if both combine later | Low (protocol forbids combining in v1) | Run M1 and M2 as separate experiments |

### Falsifiable GO / NO-GO

- **GO** iff FMPS > B2 and B3 on held-out Family-C (95% CI), and an ablation without failure-mode features is significantly worse, and offspring validity is not lower than baselines.
- **NO-GO:** bandit with the same features matches FMPS; or failure-mode ablation ≈ full model; or no transfer to Family-C.

---

## Cross-candidate decision rule (how GLEPPO picks after Phase 3)

1. If **both** GO → prefer the one with lower evaluation cost and cleaner ablation; the other becomes a secondary experiment or is dropped.
2. If **exactly one** GO → that becomes the paper's mechanism; the other is documented as a negative result.
3. If **neither** GO → **STOP** the "PPO evolution controller" hypothesis as scoped. Do not add a third decision family to rescue it. Allowed REVISE directions (still not automatic GO): change genotype/environment scale, or re-scope to a purely empirical study of when bandits suffice.

---

## Explicit non-claims

- We have **not** run any of these experiments. GO/NO-GO thresholds are prospective rules.
- We do **not** claim the gap in the literature is empty; the ledger lists pending works (DRL-PSO primary source, Meta-GA, EoH/ReEvo, FunSearch) that could shrink it. A Phase 0.2 deeper pass must re-check the gap statement before Phase 3 results are interpreted.
- We do **not** claim novelty from "PPO for agent evolution", "evolving prompts", or "execution feedback as fitness" individually — all three exist in the literature already.
