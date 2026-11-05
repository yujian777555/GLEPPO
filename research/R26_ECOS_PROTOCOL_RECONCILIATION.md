# R26 ECOS Protocol Reconciliation

**Date:** 2026-11-05
**Status:** DOCUMENTATION-ONLY — NO EXPERIMENT OR TRAINING AUTHORIZED
**Branch:** r25-handoff
**Base:** R2.1.1 accepted commit 362f343f43befc7f43c00ba5edd1059b01d523d1
**Deliverables:** This document, ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.md, ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.json

## 1. Executive Decision

Protocol drift exists across Phase 1 design, R24 preregistration, PC1 R4 proposal, and shared implementation. This reconciliation identifies every discrepancy and proposes one canonical ECOS contract. **No historical document is modified.** The proposed contract is PROPOSED / NOT APPROVED.

## 2. Source Inventory

| Source | Path | Status |
|---|---|---|
| Phase 1 design | research/PHASE1_DESIGN.md | FROZEN (design) |
| R24 preregistration | research/R24_ECOS_CONTROLLER_PREREGISTRATION.md | PREREGISTERED / NOT AUTHORIZED |
| PC1 R4 protocol | research/PC1_PROTOCOL_R4_PROPOSED.md | PROPOSED / NOT APPROVED |
| Shared reward | gleppo/reward.py | ACTIVE IMPLEMENTATION |
| Evolution loop | gleppo/evolution.py | ACTIVE IMPLEMENTATION |
| Evaluator | gleppo/evaluator.py | ACTIVE IMPLEMENTATION |
| Features | gleppo/features.py | ACTIVE IMPLEMENTATION |
| PC1 module | gleppo/pc1.py | ACTIVE IMPLEMENTATION |
| Scientific integrity | research/R26_ECOS_SCIENTIFIC_INTEGRITY_REVIEW.md | PLANNER REVIEW |

## 3. Discrepancy Matrix

### A. Decision and Execution Units

| Dimension | Phase 1 | R24 | PC1 R4 | Implementation | Conflict | Proposed Canonical |
|---|---|---|---|---|---|---|
| Operator decision | One operator per generation | Not explicitly defined | N/A | evolution.py selects one op per gen | COMPATIBLE | One operator per generation |
| Generation | Apply operator to λ=4 offspring, evaluate, select | Not defined | N/A | evolution.py GenerationLog | COMPATIBLE | Generation = one operator application + evaluation + selection |
| Evolution episode | T=15 generations on one task | "1000 episodes" | N/A | evolution.py episode loop | R24 "episode" ambiguous | Episode = one T-generation evolution run on one task |
| Task instance | {task_id, family, template, seed, input, gold} | 4 train + 4 val + 4 confirm | Training-family only | tasks.py manifest | R24 sizes vs Phase 1 400/100/100 | See Section F |
| Evaluation replica | n_eval repeats per genotype | Not defined | N_eval=2 (PC1 only) | evaluator.py n_eval | PC1 uses n_eval=2, Phase 1 uses n_eval=3 | Phase 1: n_eval=3; PC1 diagnostic: n_eval=2 |
| Rollout / horizon | Not explicitly defined | Not defined | Horizon=3 for Q-rollouts | PC1 HORIZON=3 | Terminology conflict | Rollout = one trajectory of H=3 steps under fixed policy |
| PC1 state-action record | N/A | N/A | (state, action, reward trace) | StateActionRecord in pc1.py | COMPATIBLE | One (state, action) pair with reward trace |
| CTX slot / budget | T×λ×n_eval per task | Episodes/GPU/calls/tokens/wall | 45,440 planned slots | BudgetLedger | Different units | See Section I |
| Model call / token / wall / GPU | Not quantified in Phase 1 | 5000 calls, 1M tokens, 24h, 10 GPU-h | N/A | Not tracked | R24 limits only | R24 limits are controller-training compute; PC1 has separate slot budget |

**Nesting:** Operator decision → Generation → Episode (T generations) → Task instance (one episode per task). Evaluation replica is nested within generation (n_eval per offspring). PC1 state-action record is a diagnostic sample, not a controller unit.

### B. State Contract

| Dimension | Phase 1 | R24 | PC1 R4 | Implementation | Conflict | Proposed Canonical |
|---|---|---|---|---|---|---|
| State dimension | 32-dim (3 blocks: 12+12+8) | High-level description | Diagnostic projection | features.py STATE_DIM=32 | R24 not exact schema | 32-dim per Phase 1 §3.1 + features.py |
| Feature names | 12+12+8 described | Not enumerated | Not enumerated | features.py FEATURE_NAMES | R24 incomplete | Use features.py FEATURE_NAMES as canonical |
| Block A: execution outcomes | 12 dims (best, mean, gap, fail rates, valid_rate, turns, tool_calls, parent_delta) | "performance metrics" | N/A | features.py state_vector() | COMPATIBLE | Phase 1 §3.1 block A |
| Block B: population/operator history | 12 dims (diversity, op counts, op deltas, entropy, best/mean/age) | "operator history" | N/A | features.py | COMPATIBLE | Phase 1 §3.1 block B |
| Block C: progress | 8 dims (gen/T, stagnation, budget, recency, improve) | Not specified | N/A | features.py | COMPATIBLE | Phase 1 §3.1 block C |
| Normalization | Not specified | Not specified | N/A | _clip01() | Unresolved | Minimum: clip to [0,1]; exact normalization constants UNRESOLVED |
| PC1 state vs controller state | Controller state | Controller state | Diagnostic projection | pc1.py StateActionRecord | Different schemas | PC1 state is diagnostic projection; controller uses 32-dim |
| Gold label exclusion | Explicit | Implicit | Implicit | No gold in features.py | COMPATIBLE | Gold never in state |

**Unresolved dimensions:** Exact normalization constants for all 32 features. Phase 1 says "exact feature list frozen in Phase 2 code constants" — features.py implements this but fitting source for normalization is undocumented.

### C. Action Contract

| Dimension | Phase 1 | R24 | PC1 R4 | Implementation | Conflict | Proposed Canonical |
|---|---|---|---|---|---|---|
| Action set | 5 operators | 5 operators | 5 actions | operators.py K=5 | COMPATIBLE | Exactly 5: prompt_local_edit, prompt_critique_rewrite, tool_subset_edit, workflow_step_edit, crossover |
| Selection frequency | One per generation | Not specified | One per (state, action) | evolution.py | COMPATIBLE | One operator per generation |
| Application scope | All λ offspring | Not specified | N/A | evolution.py | COMPATIBLE | Applied to all λ=4 offspring |
| Fallback | Invalid → drop | Not specified | N/A | operators.py | COMPATIBLE | Invalid offspring dropped, counted in valid_rate |
| Operator RNG | hash(operator, parent_id, gen, draw) | Not specified | operator_rng_seed() | pc1.py operator_rng_seed | COMPATIBLE | Separate from evaluation RNG |
| Action/genotype in eval seed | Excluded | Not specified | Excluded | evaluator.py effective_seed_parts | COMPATIBLE | Excluded from paired evaluation seed |

### D. Reward Contract (MATERIAL CONFLICT)

| Dimension | Phase 1 | R24 | PC1 R4 | Implementation | Conflict | Proposed Canonical |
|---|---|---|---|---|---|---|
| Formula | clip(Δbest + 0.1×valid_rate + 0.25×Δmean, [-0.5, 1.0]) | effective_success(child) − effective_success(parent) | generation_reward from reward.py | reward.py: generation_reward() | **MATERIAL CONFLICT** | See decision below |
| Weights | w1=1.0, w2=0.1×w2, w3=0.25×w3 | N/A | w_best=1.0, w_valid=0.1, w_mean=0.25 | W_BEST=1.0, W_VALID=0.1, W_MEAN=0.25 | Phase 1 and implementation agree | clip(Δbest + 0.1×valid_rate + 0.25×Δmean, -0.5, 1.0) |
| Clip | [-0.5, 1.0] | Not specified | [-0.5, 1.0] | REWARD_CLIP_LO/HI | COMPATIBLE | [-0.5, 1.0] |
| Attribution | Per generation | "Immediate per episode" | Per (state, action) | evolution.py per-gen | R24 "per episode" ambiguous | Per generation (controller); per (state, action) (PC1 diagnostic) |

**Decision: ONE shared reward function.** R24's `effective_success(child) − effective_success(parent)` is a simplified description of the same objective. The implementation's `generation_reward` is the canonical formula. R24's immediate attribution is compatible — it describes the per-generation reward that the shared function computes. PC1 correctly imports the shared function.

**Rationale:** Changing the reward would invalidate all existing pilot data and create two competing objectives. The shared reward captures both best-improvement and population-lift. R24's simpler formula is a description error, not a different objective.

### E. Discounting and PPO/Return

| Dimension | Phase 1 | R24 | PC1 R4 | Implementation | Conflict | Proposed Canonical |
|---|---|---|---|---|---|---|
| Gamma | 0.95 | 0.99 | 0.95 | GAMMA=0.95 (reward.py, features.py) | **R24 CONFLICT** | 0.95 |
| GAE lambda | Not specified | 0.95 | N/A | Not implemented | R24 only | 0.95 (from R24, compatible with γ=0.95) |
| PPO config | Not specified | lr=3e-4, clip=0.2, entropy=0.01, value=0.5, max_grad=0.5 | N/A | Not implemented | R24 only | Adopt R24 PPO config (no conflicting source) |
| PC1 Q-hat | N/A | N/A | r₀ + γr₁ + γ²r₂ | pc1.py compute_q_hat | COMPATIBLE | Horizon=3, γ=0.95 |
| Rollout length | Not specified | Not specified | Horizon=3 | pc1.py HORIZON=3 | COMPATIBLE | H=3 for PC1; controller episode T=15 |

**Decision:** γ=0.95 is canonical (Phase 1 + implementation agree). R24's γ=0.99 is a preregistration error. GAE λ=0.95 adopted from R24.

### F. Train/Validation/Confirm/Held-out Split

| Dimension | Phase 1 | R24 | PC1 R4 | Implementation | Conflict | Proposed Canonical |
|---|---|---|---|---|---|---|
| Train | A+B (400 tasks) | 4 tasks, 3 seeds | Training-family only | tasks.py manifest | R24 sizes much smaller | Phase 1 400 tasks (or re-declared in freeze) |
| Validation | A_val+B_val (100 tasks) | 4 tasks, 3 seeds | N/A | tasks.py | R24 smaller | Phase 1 100 tasks |
| Confirm | Family C (100 tasks, held-out) | 4 tasks, 3 seeds | N/A | Not loaded | **R24 "confirm" ≠ Family C** | Family C is held-out test; R24 "confirm" is additional validation |
| Seed ranges | A: [0,199], B: [0,199], A_val: [1000,1049], B_val: [1000,1049], C: [0,99] | 3 seeds each | Not specified | tasks.py | Incompatible sizes | Phase 1 seed ranges are canonical |
| Task identity table | Templates TA1-TA8, TB1-TB6, TC1-TC5 | Not specified | Not specified | tasks.py manifest | R24 no manifest | Use Phase 1 template IDs + tasks.py manifest |

**Blocker:** R24's "confirm" set (4 tasks × 3 seeds) is NOT equivalent to Phase 1 Family C (100 tasks, held-out). R24 "confirm" appears to be a third validation split. Family C remains the one-time held-out test. Exact task identity table requires committed manifest — if missing, record as blocker.

### G. Baselines and Ablations

| Dimension | Phase 1 | R24 | Implementation | Conflict | Proposed Canonical |
|---|---|---|---|---|---|
| Fixed operator | B0 (prompt_local_edit), B0b (prompt_critique_rewrite) | "Fixed: best single operator" | N/A | R24 weaker | B0 + B0b (Phase 1) |
| Random | B1 (uniform) | "Random" | N/A | COMPATIBLE | B1 |
| Rule-based | B2 (1/5-success rule) | "Rule-based" | N/A | COMPATIBLE | B2 |
| Contextual bandit | B3a UCB1, B3b EXP3, B3c LinUCB, B3d Neural | Not listed | N/A | R24 missing | B3a-B3d (Phase 1 mandatory) |
| Continuous knob | B4 (GLEET-style) | Not listed | N/A | R24 missing | B4 (Phase 1) |
| FM rewrite | B5 (external baseline) | Not listed | N/A | R24 missing | B5 (Phase 1) |
| Q-learning | B6 (DQN, γ=0.95) | Not listed | N/A | R24 missing | B6 (Phase 1) |
| PPO | ECOS (PPO) | "PPO: ECOS controller" | N/A | COMPATIBLE | ECOS |
| Ablations | A0-A3 (feature blocks, myopic reward) | Not listed | N/A | R24 missing | A0-A3 (Phase 1) |

**Proposed tiered plan:**
- **Mandatory core:** B0, B0b, B1, B2, B3c (LinUCB), ECOS (PPO)
- **Strong baselines:** B3a, B3b, B3d, B6 (Q-learning)
- **Optional/deferrable:** B4, B5, A0-A3 (if cost constrained)

**Note:** R21-C1 is DAC comparison, NOT operator/controller comparison. It must not be cited as evidence for adaptive selection.

### H. Outcomes and Statistical Analysis

| Endpoint | Phase 1 | R24 | PC1 R4 | Proposed Canonical |
|---|---|---|---|---|
| Primary | Succ_C(best) on Family C | effective_success_rate | N/A | Succ_C(best) on Family C (held-out) |
| Secondary | Succ_C(mean), final agent | answer/format/tool/constraint | N/A | Succ_C(mean), answer correctness, format compliance |
| PC1 diagnostic | N/A | N/A | D (disagreement), advantage | D ≥ 0.15 AND advantage ≥ 0.02 → PASS |
| Training reward | Discounted return Σ γ^t r_t | Immediate r_t | N/A | Discounted return (γ=0.95) |
| Safety/hard failures | Failure taxonomy | Not specified | N/A | format_error, tool_error, wrong_answer, timeout, invalid_genotype |
| Cost metrics | T×λ×n_eval per task | GPU/calls/tokens/wall | 45,440 slots | Separate ledgers (see I) |

**Primary estimand:** Paired comparison of Succ_C(best) between ECOS and best baseline on Family C. Analysis unit = task instance. CI = 95% paired bootstrap. Multiplicity correction = Holm-Bonferroni for primary comparisons.

### I. Budget Ledgers

| Ledger | Source | Units | Value | Notes |
|---|---|---|---|---|
| Candidate-task evaluation | Phase 1 | Executions per task | T×λ×n_eval = 15×4×3 = 180 | Equalized across methods |
| Controller training | R24 | Episodes | 1000 | R24 limit |
| Controller training | R24 | GPU hours | 10 | R24 limit |
| Controller training | R24 | Model calls | 5000 | R24 limit |
| Controller training | R24 | Tokens | 1M | R24 limit |
| Controller training | R24 | Wall clock | 24 hours | R24 limit |
| PC1 planned slots | PC1 R4 | Evaluation slots | 45,440 | Q: 36,000 + Extra: 4,000 + Collection: 5,440 |
| PC1 hard cap | PC1 R4 | Evaluation slots | 50,000 | Fail-closed |
| Operator LLM calls | Phase 1 | Calls per operator | 0-2 (varies by operator) | Separate from evaluation |

**Never add incomparable units.** Planned slots ≠ actual CTX ≠ model calls ≠ tokens. Cache hits are bundle-level (1 bundle = n_eval replicas). Initialization slots (32) must be included in planned totals.

### J. Seeds and Reproducibility

| Dimension | crn_seed (pc1.py:230) | effective_seed_parts (evaluator.py:57) | Conflict | Proposed Canonical |
|---|---|---|---|---|
| Payload | ["crn-v2", task_id, state_id, rollout_id, replicate_id] | [base_tag, task_id, state_id, rollout_id, replicate_id, replica_index] + "SEED" prefix | **TWO SEPARATE PATHS** | See decision |
| Version tag | "crn-v2" | None | Missing in evaluator | Add version tag |
| Action/genotype | Excluded | Excluded | COMPATIBLE | Excluded |
| Base override | Not supported | None/EMPTY/value (typed) | Different semantics | Typed encoding (evaluator) |
| Output | SHA256 hex[:16] | ("SEED", JSON string) | Different formats | JSON string with version |
| Call sites | PC1 only | Evaluator | Not shared | Must unify |

**Decision: ONE canonical seed schema.** Two independent serialization paths exist. Proposed: typed JSON with explicit version tag, fields [version, base_tag, task_id, state_id, rollout_id, replicate_id, replica_index]. Both call sites must use this. Action/operator RNG remains separate (operator_rng_seed).

**Implementation gap:** Requires code change to unify. Deferred to later approved code phase.

### K. Stop Rules and Gates

| Rule | Phase 1 | R24 | PC1 R4 | Proposed Canonical |
|---|---|---|---|---|
| PPO hypothesis stop | SR1: myopia diagnostic FAIL | N/A | FAIL → SR1 STOP | PC1 FAIL → stop PPO hypothesis |
| Inconclusive | N/A | N/A | INCONCLUSIVE → SR1 STOP | One additional diagnostic permitted |
| Training stop | N/A | Budget / no-improvement-100 / validation-degradation | N/A | R24 stop rules |
| Validation degradation | Not defined | "Validation degradation" | N/A | Validation reward declining for ≥10 episodes |
| Protocol amendment | Not specified | Not specified | Not specified | Any threshold/gamma/reward change requires amendment |
| PC1 gate | PC1 pass before training | PC1 approval + execution | Default deny | PC1 PASS + Planner approval + independent review + production runtime |
| Training gate | PC1 PASS | R21-C1 accept + PC1 + G3 + Planner | N/A | All R24 prerequisites |
| Held-out gate | Controller frozen | Confirm set | N/A | Controller frozen → one-time Family C eval |

## 4. Unresolved Blockers

1. **Exact 32-feature normalization constants** — fitting source undocumented
2. **R24 "confirm" vs Family C** — R24 confirm is NOT Family C; exact task identity table requires committed manifest
3. **Two seed serialization paths** — requires code unification (deferred)
4. **No controller implementation exists** — PPO config is R24-only, no source to verify

## 5. Implementation Changes Deferred

- Unify seed schema across crn_seed and effective_seed_parts
- Implement controller (PPO) with canonical config
- Implement exact normalization constants for 32 features
- Create committed task manifest with exact identities

## 6. Authorization Statement

**AUTHORIZED:** Documentation, reconciliation, proposed contract creation.
**NOT AUTHORIZED:** PC1 execution, Family C access, controller training, Formal G3, model/API calls, production runtime, baseline experiments, any code/test changes.
