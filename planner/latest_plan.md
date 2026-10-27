# Planner Latest Plan — GLEPPO Phase 2A-R5 (OUTCOME: REQUEST CHANGES)

**Status:** REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED  
**Repository:** `yujian777555/GLEPPO` only  
**Reviewed implementation commit:** `5486f0f762f0a00fd155e5649d6d089f4ffa550a`  
**Fifth review:** `research/FIFTH_REVIEW_FINDINGS.md`  
**Production backend:** PENDING_DEPLOYMENT

## Planner decision

R4 fixed several genuine issues, including seed tuple composition and cost-report alignment. The fifth read-only source audit found R26–R32. In particular, negative ledger deltas can bypass the cap, registered analysis does not reconcile the full 45,440 slots, episode provenance is not checked against a plan, registered provenance fields are not required, the cache key collides for absent versus empty seed override, and the “runner” is only an accounting harness. The active protocol document still describes the older v2 sampling plan while code labels a proposed R4 design as canonical.

Do not execute registered PC1. This plan is an implementation-correctness task only.

## Executor instructions

Work only in `yujian777555/GLEPPO`, branch `main`. Fetch the newest remote HEAD first; the reviewed commit may no longer be latest. Read `research/FIFTH_REVIEW_FINDINGS.md`, `planner/latest_plan.md`, `gleppo/pc1.py`, `gleppo/evaluator.py`, `tests/test_r19_r25.py`, `research/PHASE2_PREFLIGHT.md`, `research/PC1_INDEPENDENT_REVIEW.md`, `research/SMOKE_RAW.json`, `research/COST_BASELINE.md`, and `status.json`.

Implement R26–R32 below. Do not merely update docs or write a new review. Every fix needs a regression test that asserts the intended invariant or specific rejection cause.

### R27 — Reject negative budget inputs and make ledger updates atomic

- Validate all planned-slot, actual-replica, cache-bundle, invalid/valid offspring, LLM-call and turn deltas as non-negative integers before mutating any state.
- Reject negative planned slots in both runner unit and collection methods before cap checks.
- If a unit is invalid or would exceed the cap, no ledger field and no executed-unit list may change.
- Remove the duplicate `check_cap` definition and ensure `check_cap`/reconcile check non-negative values, component totals and the hard cap.
- Add tests for negative planned slots, negative replica/cache deltas, negative counters, atomic failure and attempts to lower the ledger before exceeding the cap.

### R28 — Reconcile registered analysis against the full plan

- Registered analysis must not trust `planned_slots_total` alone or accept record-derived planned slots merely because they are below it.
- Use a verified plan artifact or explicit typed budget components for collection, Q and extra sampling.
- Reconcile exactly: collection=5,440; Q=36,000; extra=4,000; total=45,440; cap=50,000.
- In registered mode require exactly 100 states and exactly 40 registered source episodes/clusters, with exactly 5 actions × 3 Q rollouts × 1 extra sample per state-action. Reject surplus or missing states, clusters, and samples.
- Require per-record slot contribution to match sample role and reconcile the complete total, including collection slots, to 45,440.
- Evidence fields `budget.planned_slots`, `budget_components.total_planned`, and `planned_slots_total` must agree exactly.
- Add tests for missing collection slots, zero/missing record slots, low caller total, surplus states/clusters, and component-total mismatch.

### R29 — Validate state/task/episode/cluster provenance against the registered plan

- Generate a stable, hashed mapping from each state to its assigned source episode, task and family.
- Registered records must match the mapping exactly; non-empty strings alone are not sufficient.
- Validate `episode_id`, `cluster_id`, `task_id`, family and state ID as a consistent tuple.
- Replace the current false-positive unknown-episode test: use a full 40-episode fixture, mutate one episode, and assert the specific unknown-provenance rejection.
- Add tests for known episode with wrong cluster, wrong task, wrong family, and state assigned to a different episode.
- Keep Family C excluded at every boundary.

### R30 — Require registered provenance before computing statistics

- For registered analysis, require nonempty well-formed manifest hash, canonical protocol hash, runtime revision, evaluator version and plan/input artifact hash.
- Validate provenance before estimators or bootstrap run.
- Synthetic analysis must use an explicit test-only mode and be marked `is_synthetic=true`.
- Replace `test_registered_requires_provenance`, which currently fails early due to its two-state fixture, with a focused validator test or a complete structurally valid fixture. Assert the error is specifically about each missing provenance field.
- Verify the raw input-record hash during replay; reject corrupted/mismatched artifacts rather than silently recomputing under different input.

### R32 — Fix seed/cache-key normalization

- The current seed contract treats `None` as base `AUTO` and `""` as an explicit empty base, but the cache key maps both to `""`.
- Either reject empty override strings at the API boundary or encode absent and explicit overrides with distinct tagged values.
- Use a collision-safe serialization of all key components rather than delimiter-only concatenation if IDs may contain delimiters.
- Add a test that uses identical genotype/task/state/rollout/replicate with `eval_seed=None` and `eval_seed=""`; prove explicit rejection or distinct cache keys/effective seeds.
- Preserve paired CRN across actions and separation across task/state/rollout/replicate.

### R26 — Create a canonical protocol artifact without falsely approving it

- Create `research/PC1_PROTOCOL_R4_PROPOSED.md` as a canonical proposed protocol document. It must explicitly say **PROPOSED / NOT APPROVED**.
- Define the estimator equations, sample roles, 100 states, 5 actions, 3 Q rollouts, horizon 3, 1 extra immediate sample, gamma, cluster unit, seed contract, thresholds, bootstrap procedure and exact budget arithmetic.
- Mark the conflicting v2 sections in `research/PHASE2_PREFLIGHT.md` as historical/superseded for the proposed R4 design, without deleting the original record.
- Give the code protocol version an unambiguous name that does not imply approval/freeze while its status remains proposed.
- Add a protocol hash and a test that parses the canonical document and compares its substantive fields with code constants. A dict constructed from the same constants is not independent protocol validation.
- Do not change status to approved. Planner approval is a separate explicit decision after review of the canonical artifact.

### R31 — Correct the runner claim and enforce approval semantics

- The current `GatedPC1Runner` only increments a ledger and appends unit IDs; it does not load tasks, collect states, invoke operators/evaluator, execute rollouts, record rewards or write per-unit artifacts.
- Do not claim this is a complete collection/rollout runner.
- Either implement a genuinely gated orchestration layer using fake/synthetic components only, including plan-driven task/state/action/rollout identity, evaluator callback, reward trace capture, per-unit artifacts and budget reconciliation; or explicitly rename/status it as a synthetic gate/accounting harness and defer the collector.
- Add an approval gate that requires the protocol status to be approved, canonical protocol hash to match, and a recorded Planner approval identifier/date. Boolean flags alone must not authorize a proposed protocol.
- Production runtime approval must bind to a concrete runtime-lock revision, not only `ready=True`.
- Default remains deny. `execute_registered_pc1()` must continue to refuse in this phase.
- Test that all booleans set true still cannot execute while protocol status is proposed or approval metadata is missing.

## Verification

Run actual commands and report raw outputs for:
- Focused R26–R32 tests.
- `python -m unittest discover -s tests`.
- `zero_cost_protocol_check()`.
- `protocol_consistency_check()` plus document/code consistency test.
- `python scripts/build_manifest.py`.
- Dry-run schedule, exact state-to-episode mapping and 45,440/50,000 accounting.
- CRN and cache-key normalization tests.
- Raw-evidence round-trip and input-hash integrity tests.
- Cost-report consistency against `research/SMOKE_RAW.json`.

Do not say tests pass unless the command ran. If a test fails, fix the implementation or report the blocker; do not weaken the registered design.

## Delivery

Inspect the full diff; update `research/FIFTH_REVIEW_FINDINGS.md` with remediation status, `planner/latest_plan.md`, and `status.json`. Commit/push to `main`, then fetch the remote HEAD and verify synchronization and a clean worktree. Do not self-approve.

## Forbidden

- No registered PC1 execution.
- No Family C loading, execution, or tuning.
- No production-model smoke/G3 while the production backend is pending.
- No PPO, Q-learning or bandit controller implementation/training.
- No GLEET code reuse or cross-project artifacts.
- No fabricated tests, measurements, costs or approval records.

## Acceptance

R26–R32 are complete only when the budget cannot be reduced by invalid inputs, registered sample/slot totals reconcile exactly, provenance is validated against the plan, registered provenance is mandatory, cache keys are unambiguous, the protocol document agrees with code while remaining explicitly proposed, and the runner claim matches its actual behavior.

**PC1 remains NOT APPROVED / NOT EXECUTED.** The protocol requires explicit Planner approval, then another independent review, then production-runtime deployment and real-model smoke/G3 before any registered PC1 run.
