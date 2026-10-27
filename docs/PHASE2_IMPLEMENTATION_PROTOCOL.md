# Phase 2 Implementation Protocol — GLEPPO

**Status:** READY FOR EXECUTION, with PC1 cost/schema preflight gates.  
**Repository:** `yujian777555/GLEPPO` only.  
**Active candidate:** M1 ECOS. M2 FMPS remains frozen.  
**Scope:** implement the minimal environment and verify causality/reproducibility; PPO training is forbidden until the corrected PC1 diagnostic passes.

## 0. Binding rules carried forward

- P0.1 C1: do not copy or transliterate GLEET code; its repository has no license.
- P0.1 C2: M1 only; no FMPS implementation or third decision family.
- P0.1 C3: bandit and FM-rewrite baselines remain mandatory for effectiveness experiments.
- P0.1 C4: deeper literature collision check is required before publication-level novelty claims.
- P0.1 C5 / Phase 1 SR2: if PPO does not beat identical-state contextual-bandit baselines on held-out Family C, STOP the scoped PPO hypothesis.
- Phase 1 PC1 / SR1: no PPO training until the myopia diagnostic passes; if it fails, STOP.
- No cross-project code, data, results, plans, or status.
- No fabricated results or costs. Keep measured, estimated, and unknown values separate.

## 1. Preflight design-consistency audit — mandatory before expensive runs

The Phase 1 document is the design source of truth, but several implementation details need a transparent consistency pass before freezing code.

### 1.1 PC1 cost arithmetic

The Phase 1 PC1 prescription currently says:
- at least 200 sampled states;
- 5 actions per state;
- at least 20 rollouts per state-action;
- horizon h=5;
- population offspring count λ=4;
- n_eval=3 repeated evaluations per offspring.

A direct full-generation implementation implies up to:
`200 × 5 × 20 × 5 × 4 × 3 = 1,200,000`
candidate-task executions, excluding state-collection overhead and operator-generation model calls. This conflicts with the Phase 1 cost guard of 50,000 episodes if “episode” means candidate-task execution.

Before running PC1, create an append-only amendment in `research/PHASE2_PREFLIGHT.md` that:
1. explicitly defines the counting unit (candidate-task execution, generation transition, controller rollout, and model call are different units);
2. recalculates the original protocol's upper bound;
3. proposes a statistically defensible, budget-capped diagnostic or justifies a different explicit cap;
4. accounts for state collection, λ offspring, repeated evaluation, operator LLM calls, cache hits/misses, and invalid offspring;
5. specifies uncertainty estimates, paired/common random-number treatment, and an inconclusive-result rule;
6. preserves the original PC1 values and explains every proposed change; never silently edit the registered values.

**Do not execute PC1 until the amended protocol is committed and independently reviewed.** If a feasible diagnostic cannot distinguish myopic from delayed-reward decisions under the declared cap, recommend STOP or a documented design revision; do not run an unbounded diagnostic.

### 1.2 Observation-vector schema

Phase 1 declares d=32 with blocks of 12+12+8, but the enumerated execution and progress features do not unambiguously sum to those block sizes, and the population block mixes operator counts, means, entropy, diversity, and aggregate features without a fully specified packing table.

Before implementation:
- write one canonical feature schema table with feature name, source, dimension, normalization, update time, missing-value rule, and whether it uses execution feedback;
- show an explicit dimension sum equal to the chosen d;
- distinguish operator counts from operator reward/improvement means;
- define how unobserved operators and first-generation features are encoded;
- add a test asserting exact vector shape, dtype, finite values, and feature order.

Any deviation from Phase 1 must be recorded as an amendment, not silently resolved in code.

### 1.3 Operator and runtime ambiguity

- Freeze whether `prompt_local_edit` is deterministic/template-based (0 LLM calls) or uses a paraphrase call (1 call); no per-run ambiguity.
- Pin the exact base-model checkpoint/revision, tokenizer, inference backend/version, decoding settings, seed behavior, hardware/quantization, tool versions, and timeout rules in `docs/RUNTIME_LOCK.md`.
- All methods must use the same frozen base model, tool interfaces, and execution conditions.
- Define canonical JSON serialization and SHA256 genotype hash; do not treat hash uniqueness as proof of behavior change.
- Failure traces passed to operators must exclude gold answers, reference outputs, hidden test labels, and evaluator internals.
- Specify exact cache keys and ensure cache cannot leak test results or cross-contaminate stochastic evaluation.

## 2. Phase 2A — Minimal environment implementation

Implement only in GLEPPO, with independent code:

1. Declarative genotype schema: `system_prompt + tools + workflow`; no arbitrary free-form code execution.
2. Fixed interpreter and deterministic tool interfaces as designed.
3. Five operators with frozen I/O schemas, exact proposal-call counts, validity checks, and failure handling.
4. Task generators for train A/B, validation A′/B′, and held-out C, with templates and IDs separated by construction.
5. Gold-label isolation: evaluator owns references; controller/operator processes receive only allowed observations and failure categories.
6. Hash-frozen `data/manifest.json` (or a documented equivalent) containing split IDs, generator/template versions, seeds, schemas, and SHA256 digests. Held-out C must not be read or executed during development/tuning.
7. Frozen evolution loop: μ=8, λ=4, T=15, tournament k=2 parent selection, (μ+λ) elitist survivor selection, one operator per generation.
8. Deterministic unit tests for serialization, manifest verification, no leakage, invalid offspring accounting, reward arithmetic, and reproducible seeds.
9. Update status and record exact runtime/environment versions.

Do not implement the PPO trainer yet. Do not start baseline training yet.

## 3. G3 genotype-causality gate

For every operator, run controlled parent-vs-offspring checks on training-family tasks only:
- record genotype diff and SHA256 hashes;
- record actual execution trace and task outcome;
- confirm edits affect allowed fields only;
- test for at least one reproducible observable behavior change per operator;
- measure valid-offspring rate and no-op rate.

If any operator has no demonstrated behavioral effect, revise that operator once and rerun the gate. Do not retain a known no-op operator merely to keep K=5. If the library cannot yield a valid five-operator set under the declared constraints, stop and ask for a design decision rather than silently changing the action space.

## 4. Smoke test and measured cost

Run a small, predeclared smoke test on training-family tasks only. The smoke test is for runtime correctness and cost measurement, not controller effectiveness.

Record in `research/COST_BASELINE.md`:
- exact number of task episodes, agent turns, tool calls, operator proposals, retries, invalid offspring, cache hits/misses;
- input/output tokens if exposed, wall-clock latency, hardware, peak memory, and failure rate;
- costs by operator and by execution-vs-proposal call;
- projected cost for the frozen PC1 protocol and later baseline suite, clearly separating measured values from extrapolation.

Do not use Family C in smoke tests. Do not start PPO training.

## 5. PC1 myopia diagnostic gate

Only after the preflight amendment is reviewed, genotype causality passes, manifests are frozen, and the smoke-test cost is known:
- sample states from random and hand-designed heuristic rollouts on A/B training tasks only;
- estimate immediate reward and h-step return under the pre-registered action protocol;
- use paired seeds/common random numbers where valid to reduce variance;
- report disagreement D, non-myopic action return advantage, uncertainty intervals, stratification by stagnation, exact execution counts, and all failed/invalid branches;
- do not tune thresholds after seeing results.

**PC1 pass/fail rule:** use the amended, committed protocol. If the registered thresholds fail, or uncertainty remains inconclusive at the hard cap, do not start PPO; follow SR1 (STOP) unless the protocol explicitly preregistered one bounded extension.

## 6. Only after PC1 passes

A later plan may authorize:
- independent PPO implementation;
- B0/B1/B2/B3a/B3b/B3c/B3d/B4/B5/B6 implementations and controlled training;
- multi-seed effectiveness experiments on validation tasks;
- final frozen evaluation on Family C.

The existence of an implementation or a successful smoke test is not permission to claim efficacy. Full effectiveness testing must use identical-state LinUCB and neural contextual-bandit controls, FM-rewrite, and Q-learning as pre-registered.

## Acceptance criteria for this phase

- `research/PHASE2_PREFLIGHT.md` resolves the PC1 counting-unit/budget contradiction and state-vector dimension ambiguity.
- `docs/RUNTIME_LOCK.md` pins the runtime before any real model execution.
- Minimal environment, operators, task split, evaluator, and evolution loop are implemented independently.
- G3 behavior-causality gate is reported with evidence.
- Manifests are frozen and verified; held-out C is untouched.
- Smoke-test costs are measured and written to `research/COST_BASELINE.md`.
- PC1 is either run under an approved, budget-consistent protocol or explicitly held pending review.
- No PPO training or effectiveness claim before PC1 passes.
- All code/tests/docs are pushed to `main`; status.json reflects actual state.
