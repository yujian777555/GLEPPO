# Planner Latest Plan — GLEPPO Phase 2A-R2 Remediation

**Status:** EXECUTOR TASK READY — PC1 NOT APPROVED / NOT EXECUTED  
**Repository:** `yujian777555/GLEPPO` only  
**Base commit:** `94764f86481edb8abb674c66aea0221ede2b9219`  
**Prior implementation commit under review:** `a272a453c1147d9b2fd194c04806ba0a4dac8cdc`  
**Review findings:** `research/SECOND_REVIEW_FINDINGS.md`  
**Current gate:** Fix R8–R11 and test the PC1 runner scaffolding; request another independent review afterward.

## Planner decision

Do not run PC1. The second review identified that the CRN helper is not wired end-to-end, actual CTX/cache counters are inconsistent, runtime-lock seed documentation is stale, StubLLM is not verified against every generated template, and the full PC1 evidence runner is missing.

This task is remediation only. Do not add a new research mechanism or implement/train any controller.

## Executor prompt — copy verbatim

You are the Executor for the GLEPPO research project. Work only in `yujian777555/GLEPPO`, branch `main`. Do not mix in other projects or reuse GLEET code. You must inspect the actual repository code, implement the changes, run tests, commit and push, update `status.json`, and report exact evidence. Do not merely repeat this plan.

### A. R8 — wire paired common-random-number (CRN) seeds end-to-end

Current defect: `gleppo/evaluator.py:Evaluator.evaluate` includes `behavior_hash[:8]` in `seed_parts` even when `eval_seed` is provided. That causes different candidate genotypes to receive different effective random seeds despite the same declared CRN seed.

Required design:
1. Define a deterministic seed hierarchy. The effective evaluation seed for a paired comparison must depend on state ID, task ID, rollout ID, outer replicate ID and inner replica index, but **must not depend on action or genotype** when comparing actions under CRN.
2. Keep genotype/action identity in the cache key and sample metadata; do not put it into the shared RNG seed.
3. Distinct outer replicate IDs and distinct rollout IDs must produce distinct seeds. Different actions evaluated at the same state/rollout/replicate must use identical effective seed inputs.
4. Ensure the PC1 runner passes the CRN key into the actual evaluator path. A helper-only test is insufficient.
5. Keep the existing family access guard and evaluator gold-label isolation.

Required regression tests:
- Use an instrumented fake interpreter to record every `seed_parts` passed by `Evaluator.evaluate`.
- Evaluate two different genotypes under the same declared CRN tuple and assert identical per-replica seed inputs.
- Change the outer replicate ID and assert seed inputs differ.
- Change the rollout ID and assert seed inputs differ.
- Verify cache identity remains genotype-specific and distinct replicate entries do not collide.
- Verify cache hits do not increment independent-sample counts.

### B. R9 — repair actual CTX and cache accounting

Choose and document these units consistently:
- **planned slots:** conservative planned candidate-task replica slots, including initialization;
- **actual CTX:** uncached candidate-task replica executions that actually ran;
- **cache hits:** cached evaluation bundles (one bundle returns `n_eval` replicas), unless you deliberately choose replica-level hits and update all reports accordingly;
- **LLM calls/tokens:** separate counters; never infer them from CTX.

Required fixes:
1. Update `BudgetLedger`, `Evaluator` counters and `EpisodeResult` so actual CTX increments by the number of replica executions that really ran, and a cache hit adds zero actual CTX.
2. `EpisodeResult.cache_hits` must be a per-episode delta, not the evaluator's cumulative total.
3. For initialization, use actual evaluator counters/deltas; do not assume every `evaluate()` call ran `n_eval` replicas if it may hit cache.
4. For offspring, count actual executions using counter deltas or an explicit result field. Do not subtract one bundle hit from a replica count.
5. Invalid offspring consume no evaluator CTX unless code proves they were evaluated; report them separately.
6. Keep planned slots conservative and independent of caching so the hard cap cannot be evaded by cache hits.

Required regression tests:
- `n_eval=2`, uncached evaluation: actual CTX rises by 2.
- Repeating the same genotype/task/replicate/seed from cache: actual CTX rises by 0 and cache-hit bundles rise by 1.
- A different replicate ID: no accidental cache reuse.
- Reuse one Evaluator across two episodes: each EpisodeResult reports only its own cache-hit and CTX deltas.
- Initialization slots are included in planned-slot accounting.
- Invalid offspring do not get counted as evaluated candidates.

### C. Fix smoke slot reporting

For the current smoke configuration:
`n_tasks=4, mu=4, lambda=2, T=6, n_eval=2`.

Expected conservative planned-slot arithmetic:
- initialization slots: `4 × 4 × 2 = 32`;
- offspring slots: `4 × 6 × 2 × 2 = 96`;
- total planned slots: `32 + 96 = 128`.

Update `scripts/run_smoke.py`, `research/SMOKE_RAW.json` (regenerate it only by running the corrected stub smoke), and `research/COST_BASELINE.md` if it repeats the old count. Use separate names for `planned_init_slots`, `planned_offspring_slots`, and `planned_total_slots`. Do not label planned slots as actual CTX. Keep Family C untouched.

### D. R10 — align runtime lock with seed code

Update `docs/RUNTIME_LOCK.md` with a dated revision note and exact deterministic seed derivation used by the code. Remove stale claims that the active seed rules use Python's built-in `hash(...)` if those paths have been replaced. Clearly separate:
- evolution/control RNG;
- action/operator proposal RNG;
- common paired evaluation RNG;
- inner evaluation replica seed;
- FM-rewrite baseline RNG.

Do not claim a production runtime is locked: the production backend remains pending deployment. Any code or seed-lock change must be versioned and reflected in tests.

### E. R11 — validate StubLLM against every generated template

Inspect `gleppo/tasks.py` template definitions and `gleppo/llm.py` parser behavior. Add parameterized tests covering every registered Family A and B train/validation template, and Family C checker/parser tests only as zero-execution unit tests if they do not load or run held-out data. Do not execute Family C tasks.

Either:
- make StubLLM deterministically compute correct answers for every declared template when the relevant strategy/tools are enabled, without exposing gold labels to controllers/operators; or
- explicitly quarantine all StubLLM success-rate metrics as non-evidence and remove broad claims that the stub computes true answers for every template.

Prefer a template-specific deterministic task oracle only if it does not leak gold labels through the observation interface. The evaluator remains the only owner of correctness labels.

### F. PC1 runner scaffolding — implement, but DO NOT EXECUTE PC1

Implement a deterministic/replayable runner and synthetic unit tests for the complete analysis path. It must be possible to validate the runner without performing the registered PC1 experiment.

Required runner properties:
1. Accept explicitly supplied training-family A/B state records only; enforce family allowlists and `FamilyCGuard`.
2. Carry immutable `state_id`, collection-episode cluster ID, action ID, rollout ID, outer replicate ID and CRN seed metadata.
3. Compute `r_hat` and horizon-3 `Q_hat` from the same frozen `generation_reward` definition.
4. Compute the registered diagnostic statistic `D` and advantage with the existing frozen thresholds: `D >= 0.15`, advantage `>= 0.02`; do not tune thresholds.
5. Implement cluster bootstrap confidence intervals by resampling the registered collection-episode clusters, not individual rows. Add tests proving rows from one cluster remain together.
6. Emit raw, replayable evidence: protocol version, input hashes, seeds, cluster IDs, per-action rewards, horizon-3 reward traces, D/advantage, confidence intervals, strata, planned-slot counts, actual CTX, cache bundles, invalids, and stopping decision.
7. Enforce the 50,000 planned-slot hard cap before any registered PC1 data execution. If results are inconclusive at the cap, apply SR1 STOP.
8. Unit tests must use synthetic fixtures and assert calculations; they must not run PC1 on the frozen task set, read Family C outcomes, or access production credentials.
9. Do not claim PC1 is passed or executed. The runner implementation is not authorization to launch it.

If the exact registered D/advantage estimator or bootstrap convention is not unambiguously recoverable from Phase 1 documents, stop and report the ambiguity; do not invent a statistical definition. Ask for a planner decision before implementing that estimator.

### G. Verification and repository hygiene

Run, as applicable:
- focused tests for R8/R9/R11;
- `python -m unittest discover -s tests`;
- `gleppo.pc1.zero_cost_protocol_check()`;
- manifest verification;
- corrected stub smoke (A/B only);
- synthetic PC1 runner tests.

Then:
1. Inspect test output; do not report tests that were not run.
2. Inspect `git diff`, status and the actual source changes.
3. Commit and push to `main`; confirm `HEAD == origin/main` and a clean worktree.
4. Update `research/SECOND_REVIEW_FINDINGS.md` with remediation evidence and remaining blockers.
5. Update `planner/latest_plan.md` and `status.json` so they match the actual result.
6. Report exact commit SHA, test counts, smoke slot arithmetic, actual CTX/cache units, any failures, and confirmation that PC1 was not executed.

### Forbidden actions

- Do not execute PC1 or tune on PC1 outcomes.
- Do not access or execute Family C tasks or inspect Family C results.
- Do not run production-model G3 or production smoke while the production runtime is pending.
- Do not implement/train PPO, Q-learning, bandit controllers or additional research mechanisms.
- Do not copy GLEET code or reuse artifacts/results from another project.
- Do not fabricate model calls, costs, tokens, test results, or approval.

### Acceptance gate

This task is complete only when R8/R9 are demonstrated by end-to-end tests, smoke accounting includes initialization, runtime lock agrees with the code, StubLLM claims are verified or quarantined, the PC1 runner is tested on synthetic data, all available tests pass, and repository state is clean and synchronized. PC1 remains NOT APPROVED / NOT EXECUTED pending another independent review and the production-runtime gate.
