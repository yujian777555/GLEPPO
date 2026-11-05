# GLEPPO R26 — Immediate Algorithm Pilot (User-Prioritized)

**Repository:** `yujian777555/GLEPPO`  
**Experiment branch:** `r26-algorithm-pilot`  
**Base commit:** `aa16c23101c1b387e8617910601da9a5d96231c1`  
**Main:** `6bad0b77835a2d00c62287c0c7d9d91d1d186d5e` (never modify)  
**User instruction:** "抓紧做算法实验"  
**Priority change:** Pause R1.2 documentation work. Run this bounded algorithm pilot first. R1.2 remains pending and is not silently accepted.

## 1. Research question

Does adaptive selection of the five frozen Agent-evolution operators improve task-solving performance over fixed, random and rule-based selection? Does a learned policy (LinUCB or Q-learning) add value beyond a hand-designed rule?

This is an **unregistered development pilot**, not PC1, not Formal G3, not a paper-confirmatory experiment, and not evidence of Family-C generalization. It is intended to identify whether a promising adaptive-selection effect exists before investing in PPO/A800 training.

## 2. Current code facts that must shape the experiment

At base commit:
- `gleppo/evolution.py:evolve` accepts `operator_schedule(t, pop, history)`.
- `EvolutionConfig` defaults to `mu=8, lam=4, T=15, n_eval=3`.
- `evolve_generation` currently sets offspring `replicate_id=stable_seed(episode_id,t,j,operator_name)`; this makes evaluation randomness action-dependent and invalidates cross-operator CRN pairing.
- The same RNG currently drives parent tournament selection and the extra mate draw for crossover. This can make future selection RNG streams differ by operator.
- `gleppo/features.py:state_vector` is not wired into `evolve` or a controller. Do not claim the 32-D vector is being used.
- `StubLLM` is deterministic and strategy-gated; it does not represent real Qwen/LLM performance.
- Formal G3 currently FAILS and the production Qwen task-solving path has not passed its gate.

## 3. Permitted scope and hard boundaries

The user has prioritized a bounded algorithm pilot, so work on this branch is authorized as follows:
- You MAY make an isolated experimental-branch correction to the evolution seed/RNG call path and add pilot-only code/tests.
- You MAY run a development pilot using Family A/B train and validation splits only.
- You MUST NOT modify or merge main.
- Do NOT access, read, load, execute or inspect any Family C task payload/gold. Do not load `test_C.jsonl`.
- Do NOT run registered PC1, PC1 R4, Formal G3, production Qwen runtime, local model inference, DeepSeek/API calls, or controller training on the real model.
- Do NOT run `scripts/_fix_gold.py`, `scripts/_check_tasks.py`, `scripts/_test_model.py`, or unrelated audit scripts.
- Do not alter data files, manifest, gold labels, historical protocols, or R1.2 documents.
- Use `StubLLM` only; report clearly that results are surrogate-only and non-confirmatory.
- A800 is NOT required for this pilot. Do not start PPO training. The point is to test whether adaptive operator selection has any signal before GPU investment.

## 4. Experimental arms

Use the five frozen actions from `OPERATOR_NAMES`:
1. `prompt_local_edit`
2. `prompt_critique_rewrite`
3. `tool_subset_edit`
4. `workflow_step_edit`
5. `crossover`

Run these nine arms:
- F1–F5: each of the five operators fixed for every generation (five separate arms).
- RND: uniform random over the five operators.
- RULE: Phase 1 B2 hand rule.
- LINUCB: contextual LinUCB on the pilot observation below.
- QLEARN: tabular Q-learning on a discretization of the same pilot observation.

Do not run PPO in this pilot. The fixed arms are all reported. Select the best fixed operator using TRAIN results only and freeze it before validation. Validation is used to compare the frozen best-fixed choice and all other arms descriptively; do not use validation to retune controllers.

### RULE implementation

Implement the Phase 1 B2 rule literally and document tie/fallback behavior:
- If stagnation is at least 4 generations, choose `tool_subset_edit`.
- Otherwise inspect the most recently used operator and its last five uses; if at least two of those uses had positive `op_delta_mean`, keep it.
- Otherwise choose `crossover`.
- If no operator history exists, use `prompt_critique_rewrite` as a deterministic initial fallback.
Record the exact rule in the run manifest.

### Pilot-only observation (NOT canonical 32-D state)

Build a deterministic `pilot_context_v1` from controller-visible data only:
- best_success, mean_success, best_minus_mean;
- generation progress t/T;
- stagnation fraction;
- four population failure-category rates (format/tool/wrong/timeout);
- last-generation valid rate and op_delta_mean;
- mean reward over the last three generations;
- tool-set and workflow-signature pairwise Jaccard diversity;
- operator-usage entropy.

Normalize/clip each component with explicitly documented formulas. No gold, task answer, hidden evaluator fields, or Family-C information may enter the context. If a required field is unavailable, mark it unavailable or use a documented neutral value; do not silently claim this is the registered 32-D state.

### LINUCB

- One linear model per action; ridge initialization A_a=I, b_a=0.
- Select argmax xᵀθ_a + α√(xᵀA_a⁻¹x), α=1.
- Update only after the generation reward is observed; at episode end, apply the final generation's reward to the final action.
- Train online across TRAIN episodes; freeze all A/b matrices for validation.

### QLEARN

- Tabular Q-learning over a documented discretization of `pilot_context_v1`.
- Five actions; γ=0.95, α=0.1, ε starts 0.20 and decays to 0.05 over TRAIN decisions.
- Update with r_t + γ max_a Q(s_{t+1},a); terminal transition has no bootstrap term. Call an explicit episode-finalization method so the last generation reward is not dropped.
- Train only on TRAIN episodes; freeze Q table and use greedy action on validation.
- Persist the controller across the ordered TRAIN tasks for each seed; use a separate controller instance per training seed.

## 5. Paired seed correction required before any comparison

In this experimental branch only, correct the call path in `gleppo/evolution.py`:

1. Change offspring evaluation replicate ID from
   `stable_seed(episode_id,t,j,operator_name)`
   to an action-independent value such as
   `stable_seed(episode_id,t,j)`.
2. Keep `task_id`, `state_id`, `rollout_id` and `replica_index` consistent across methods for the same task/seed/generation/offspring slot. Genotype remains part of cache identity, not the random seed.
3. Separate the parent-selection RNG stream from crossover's additional mate draw. Derive the mate RNG deterministically from (config seed, task, episode, generation, "mate") so crossover cannot consume draws from the parent-selection RNG stream.
4. Preserve deterministic reproducibility across processes.
5. Extend the in-memory generation history passed to the schedule with `op_delta_mean`, `valid_rate`, `valid_count` and `invalid_count`; retain the existing fields. These are controller-visible, post-generation observations only.
6. Add focused tests proving:
   - same task/episode/generation/offspring slot has identical effective evaluation seed parts across different operator arms;
   - initial population hashes match across methods for the same task/seed;
   - crossover mate selection does not shift the parent-selection RNG stream;
   - different task/replica/generation slots remain distinct;
   - Family C is rejected by the guard.

Do not alter the canonical PC1 seed schema or claim that the registered PC1 implementation is approved. This is an isolated experimental correction only.

## 6. Data and run configuration

Use only manifest-verified files:
- TRAIN: `data/train_A.jsonl`, `data/train_B.jsonl`.
- VALIDATION: `data/val_A.jsonl`, `data/val_B.jsonl`.
- Never open `data/test_C.jsonl`.

Small, fast pilot subset:
- TRAIN: first 7 train_A tasks (covers TA1–TA7) + first 5 train_B tasks (covers TB1–TB5): 12 tasks.
- VALIDATION: first 3 val_A tasks + first 3 val_B tasks: 6 tasks.
- Evolution seeds: 11 and 22 for the initial screen.
- Config: `mu=8, lam=4, T=15, n_eval=2`; all arms identical.
- Expected planned slots per episode: 16 initialization + 120 offspring = 136 candidate-replica slots.
- Nine arms × 12 TRAIN tasks × 2 seeds = 216 TRAIN episodes.
- Nine arms × 6 VALIDATION tasks × 2 seeds = 108 VALIDATION episodes.
- Total initial pilot: 324 episodes, 44,064 planned candidate-replica slots.
- Use a fresh Evaluator/cache per arm-task-episode; preserve cache within an episode only.
- Same ordered task IDs, seeds, initial genotypes, μ/λ/T/n_eval and stopping semantics for every arm.
- No early stopping in this pilot; every episode runs T=15 generations.

The LinUCB/Q-learning controller is trained across the 12 TRAIN tasks for each seed, then frozen and evaluated on the six validation tasks for that same seed. Validation must never update controller parameters.

## 7. Outputs and analysis

Create a new isolated directory:
`experiments/r26_operator_pilot/`

Required:
- `run_pilot.py`: deterministic orchestration of all arms.
- `controllers.py`: pilot context, RULE, LINUCB, QLEARN implementations.
- `paired_seed_tests.py`: focused pairing/RNG tests (or add tests under `tests/` if needed).
- `RUN_MANIFEST.json`: source commit, config, task IDs, seeds, arm definitions, split hashes, code revision, explicit Family-C denial, StubLLM identity, and all deviations.
- `RAW_EPISODES.jsonl`: one row per episode, including per-generation operator/reward/best/mean/validity, final metrics, actual replicas, cache bundles and wall time.
- `SUMMARY.md` and `SUMMARY.json`: aggregate train/validation results and paired comparisons.
- Do not overwrite previous run artifacts.

Report for each arm:
- validation best_success (primary pilot metric);
- final population mean success;
- best-so-far area under learning curve;
- discounted return with γ=0.95;
- valid/invalid offspring rate;
- per-family A/B results;
- actual replicas, cache bundles and wall time.

Compare LINUCB and QLEARN against RND, RULE and the best-fixed operator selected on TRAIN. Use paired bootstrap over validation task × seed pairs (10,000 resamples) and report mean difference and 95% interval. The validation sample is only 12 paired units: label intervals exploratory and do not claim statistical confirmation or publication-ready significance. Report per-task results to expose heterogeneity.

## 8. Decision rules after the pilot

- If LINUCB/QLEARN do not beat both RND and RULE on validation, do NOT proceed to PPO. Inspect operator-effect heterogeneity and whether the current operator library produces measurable improvements.
- If one adaptive policy shows a consistent positive validation effect across A and B, expand to ≥5 seeds and a larger TRAIN/VALIDATION subset before any PPO.
- If adaptive policies improve only one family, report the interaction; do not claim general Agent improvement.
- If all five fixed operators are statistically/ practically indistinguishable in this surrogate, the current benchmark/operator library cannot identify adaptive-selection value. Revise the task/operator mechanism before training.
- No outcome from this pilot unlocks PC1, Family C, Formal G3, production runtime, or PPO automatically. Those require separate gates.

## 9. Git and reporting

- Work only on `r26-algorithm-pilot`.
- Commit experimental source, tests, run artifacts, and a concise handoff.
- Do not merge or cherry-pick to main or `r25-handoff`.
- Keep R1.2 documentation task paused; do not alter its prompt or review report.
- Record any failed run and preserve raw outputs. Do not tune hyperparameters on validation.
- After the pilot, stop and report the actual results, including negative results and any execution blockers. Do not continue into PPO automatically.

**Immediate priority: implement the paired-seed correction, run the 324-episode StubLLM pilot, and return measured results.**
