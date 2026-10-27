# Planner Latest Plan — GLEPPO Phase 2A-R3 Auditability Remediation

**Status:** REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED  
**Repository:** `yujian777555/GLEPPO` only  
**Reviewed commit:** `f329a45e91b8011a42e6cc3fee49817da940966b`  
**Third review:** `research/THIRD_REVIEW_FINDINGS.md`  
**Production backend:** PENDING_DEPLOYMENT

## Decision

R8 seed tests, the evolution-loop counter deltas, and smoke planned-slot arithmetic improved. However, the PC1 path is not yet auditable enough to approve. The new third review found R12–R18: stale bundle-level arithmetic in `BudgetLedger`, missing fail-closed input validation, unrepresented extra immediate draws, no full collection/rollout runner, inconsistent seed helper integration/cache identity, incomplete replay artifacts, and contradictory cost documentation.

This task fixes those issues only. Do not add a research mechanism, implement a controller, or run PC1.

## Executor prompt — copy verbatim

You are the Executor for GLEPPO. Work only in `yujian777555/GLEPPO`, branch `main`. Read `research/THIRD_REVIEW_FINDINGS.md` and this plan first. Do not assume a prior test report proves the current code correct. Inspect and modify the actual source, run the allowed tests, commit and push, and report exact outputs.

### Task 1 — R12: fix BudgetLedger units

Current `gleppo/pc1.py:BudgetLedger.record_generation` does `valid*n_eval - cache_hits`, while `cache_hits` means bundles, not replica executions. `record_init` similarly subtracts bundles from an actual-replica count.

- Prefer passing explicit `actual_replicas_run` deltas from evaluator counters into the ledger.
- Keep `planned_slots`, `actual_ctx` (uncached replica executions), `cache_hit_bundles`, invalid offspring, and model calls/tokens as distinct counters.
- Do not subtract a bundle count from a replica count.
- Add direct BudgetLedger tests for `n_eval=2`, one cached bundle, invalid offspring, initialization, and repeated generations.
- Ensure the PC1 ledger and Evolution/Evaluator use the same units.

### Task 2 — R13: make PC1 analysis fail closed

Update `StateActionRecord` validation and `run_pc1_analysis` so malformed or incomplete input raises a clear error rather than generating a statistic.

Required checks:
- Every included state has all actions 0–4.
- Every Q-rollout record has exactly `HORIZON=3` finite rewards.
- The analysis has at least `N_STATES=100` distinct states before a registered run can be eligible for a decision.
- Per-state/action Q rollout counts meet `Q_ROLLOUTS=3`; the extra immediate sample count is checked separately.
- A state ID cannot map to conflicting collection cluster IDs.
- Cluster IDs are nonempty and there are enough independent clusters for the registered bootstrap.
- Duplicate/conflicting rollout/replicate keys are rejected.
- Do not default missing action values to 0.0.
- Reject invalid action IDs, negative counters, non-finite reward values, or records with missing seed metadata.

Synthetic unit tests may use an explicit test-only validation mode for smaller fixtures, but that mode must not be available to registered PC1 execution and must be clearly named.

### Task 3 — R14: separate Q rollouts from extra immediate draws

The active v2 budget contains 4,000 extra immediate-reward slots. The current record schema does not distinguish these from Q-rollout records.

- Add a sample-role field with a closed set such as `q_rollout` and `extra_immediate`.
- `Q_hat` must consume only complete horizon-3 Q-rollout records.
- `r_hat` must use exactly the registered first-step samples (Q-rollout first rewards plus the declared extra immediate draws, if that is the registered estimator).
- Extra immediate records must not enter Q_hat as truncated trajectories.
- Preserve `generation_reward` as the only source of per-generation rewards.
- Add synthetic tests that prove extra immediate draws change r_hat as specified but cannot change Q_hat.
- If the current protocol does not unambiguously specify whether Q-rollout first rewards are included in r_hat in addition to extra draws, stop and report the ambiguity rather than silently choose a different estimator.

Reconcile the exact estimator and its slot accounting with `research/PHASE2_PREFLIGHT.md` amendment v2.

### Task 4 — R15: implement the guarded PC1 collection/rollout entry point, but do not launch it

`run_pc1_analysis` is currently an analyzer for preconstructed records, not a full registered experiment runner.

Implement a separate collection/rollout orchestration entry point with:
- a deterministic dry-run mode that emits the planned state/action/rollout/replicate schedule and planned-slot total;
- explicit input family metadata and an A/B-only allowlist;
- a `FamilyCGuard` or equivalent guard at every data-load and task-evaluation boundary;
- the registered 100 states, 5 actions, 3 Q rollouts per state-action, horizon 3, extra immediate draws, and collection episodes;
- pre-execution hard-cap checks, including initialization/state-collection costs;
- a single action-independent CRN evaluation seed path for paired action comparisons;
- a separately derived action/operator-generation RNG stream;
- actual execution and cache counters passed into BudgetLedger;
- a default mode that refuses to execute registered PC1 unless a separate explicit approval gate and production-runtime gate are satisfied.

Do not execute registered PC1 or load the frozen Family C task split. Unit tests must use synthetic fixtures and the dry-run plan only. No production-model calls.

### Task 5 — R16: unify CRN, evaluator seed and cache-key semantics

Current concerns:
- `Evaluator.evaluate` uses `eval_seed` in the cache key but does not use it in `effective_seed_parts`.
- `crn_seed` and `replicate_seed` helpers are not wired into the collector.
- `replicate_seed` includes action ID, which must not be used as the paired evaluation seed across actions.
- If an explicit `eval_seed` is reused across different state/rollout tuples, the current cache key can collide even though the effective seed tuple differs.

Define one authoritative contract:
- **evaluation RNG:** shared across actions for a given state/task/rollout/replicate/inner replica;
- **operator-generation RNG:** action-specific where appropriate, separate from evaluation RNG;
- **cache key:** includes every field affecting the effective evaluation seed plus genotype, task, runtime, evaluator version and replica identity.

Either use `eval_seed` as the actual evaluation seed consistently or remove/rename it and update every caller/document. Add end-to-end tests for action pairing, state/rollout separation, replicate separation, explicit seed behavior and cache non-collision.

### Task 6 — R17: emit replayable PC1 raw evidence

The current `raw_evidence` omits source records and key provenance.

Write an artifact that contains, at minimum:
- protocol and estimator version;
- manifest/input hashes;
- runtime and evaluator revisions;
- sanitized per-record family, state ID, cluster ID, action, sample role, rollout/replicate IDs, CRN/effective seed metadata and horizon-3 rewards;
- planned slots, actual replica executions, cache bundles, invalid counts, model calls/tokens (UNMEASURED until production);
- r_hat/Q_hat, D/advantage, confidence intervals, strata, bootstrap seed/resample count and decision;
- a deterministic replay command and input artifact hash.

Do not leak gold labels to controllers/operators. Do not include or load Family C records.

### Task 7 — R18: reconcile COST_BASELINE.md

The current file contradicts itself:
- §2: actual replicas 112 and wall-clock 0.021 s;
- §5: CTX 96 and latency 0.012 s;
- §4/§6: PC1 47,200 despite active v2 planned slots = 45,440.

Edit the actual current file (do not rely on the failed exact-string replacement). Reconcile all sections with `research/SMOKE_RAW.json` and the active amendment:
- 96 = offspring planned slots only;
- 128 = total smoke planned slots including initialization;
- 112 = measured uncached replica executions in this recorded stub smoke;
- 0.021 s = recorded smoke wall-clock (not production latency);
- 45,440 = PC1 planned slots, not measured actual CTX or model cost;
- production tokens, turns, latency and cost remain UNMEASURED.
Fix any scale-factor labels that mix offspring-only slots with total planned slots.

### Verification

Run and report actual output for:
- focused tests for R12–R17;
- full `python -m unittest discover -s tests`;
- `zero_cost_protocol_check()`;
- manifest verification;
- synthetic PC1 analysis tests;
- PC1 dry-run plan validation only (no registered execution);
- documentation consistency checks for the numbers above.

Then inspect the diff, update `research/THIRD_REVIEW_FINDINGS.md` with remediation evidence, update `status.json` and this plan, commit/push to `main`, and confirm `HEAD == origin/main` and a clean worktree.

### Forbidden

- Do not execute registered PC1.
- Do not access or execute Family C tasks or outcomes.
- Do not deploy/run production-model smoke or G3 while the production backend remains pending.
- Do not implement/train PPO, Q-learning or bandit controllers.
- Do not copy GLEET code or add M2/another mechanism.
- Do not fabricate test outputs, costs, tokens or approvals.

### Acceptance

This phase is complete only when R12–R18 are fixed with tests, the PC1 dry-run plan is complete and capped, the raw artifact is replayable, the cost report is internally consistent, all allowed tests pass, and the changes are pushed. PC1 remains NOT APPROVED / NOT EXECUTED until a subsequent independent review and the production-runtime gate.
