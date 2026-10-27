# Planner Latest Plan — GLEPPO Phase 2A-R4 Protocol and PC1 Auditability

**Status:** REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED  
**Repository:** `yujian777555/GLEPPO` only  
**Reviewed commit:** `4c727997a71d4eb1cd34c1612fe1d275009d859f`  
**Fourth review:** `research/FOURTH_REVIEW_FINDINGS.md`  
**Production backend:** PENDING_DEPLOYMENT

## Planner decision

Phase 2A-R3 improved the code and tests, but the fourth source audit found R19–R25. The protocol amendment is not formally approved, the CRN override does not preserve task/replicate uniqueness, the hard-budget guard does not reconcile caller totals with records, collection-cluster provenance is missing, raw evidence is not replayable end-to-end, cost documentation disagrees with the raw smoke artifact, and the registered collection/rollout runner is not implemented.

This is a remediation task only. Do not execute PC1 or production-model experiments.

## Executor prompt — follow exactly

You are the Executor for GLEPPO. Work only in `yujian777555/GLEPPO`, branch `main`. First fetch the newest remote HEAD and inspect `research/FOURTH_REVIEW_FINDINGS.md`, this plan, `research/PHASE2_PREFLIGHT.md`, `research/PC1_INDEPENDENT_REVIEW.md`, `gleppo/pc1.py`, `gleppo/evaluator.py`, `research/SMOKE_RAW.json`, `research/COST_BASELINE.md`, and `status.json`. Do not assume the reported tests prove correctness. Implement code changes, run allowed tests, inspect the diff, commit and push, and report exact evidence.

### R19 — Freeze the protocol and estimator correctly

- Create one canonical, versioned active protocol revision that agrees with `gleppo/pc1.py:PROTOCOL_VERSION` and `ESTIMATOR_VERSION`.
- Explicitly mark historical v1 sampling sections as superseded/archival; remove ambiguity from the active protocol text.
- The 100-state / 3 Q-rollout / horizon-3 / 1 extra-immediate design and `r_hat = Q-rollout first rewards + extra immediate` currently appear in a proposed amendment in `research/PC1_INDEPENDENT_REVIEW.md`, which explicitly says it is not an approved protocol. Do not claim it is approved until the Planner records an explicit decision.
- Add a protocol consistency test for version, state count, action count, rollout count, horizon, extra sample count, gamma, thresholds and 45,440 planned-slot arithmetic.
- Do not collect registered PC1 data during this task.

### R20 — Make CRN override semantics unique and testable

Current override behavior returns only `("SEED_OVERRIDE", eval_seed_override, replica_index)`; the current helper derives an override from state and rollout only. Fix the contract so paired actions share random inputs but distinct tasks and outer replicates cannot accidentally reuse them.

- Add task ID and outer replicate ID to the authoritative CRN-key derivation, while excluding action and genotype.
- Define whether `eval_seed` is a fully qualified key or a base key. Document one meaning and use it consistently in the evaluator, dry-run plan, runtime lock and records.
- Ensure task/state/rollout/replicate/inner-replica identities affecting randomness also participate in the cache key.
- Instrument the actual evaluator and test: same state/task/rollout/replicate across actions → identical seed parts; different task, rollout or replicate under the override path → distinct seed parts; repeated identical evaluation → cache hit only for the identical key.
- The PC1 schedule must use the exact tested CRN API.

### R21 — Make the budget guard fail closed

- Reject invalid/negative planned totals and totals over 50,000.
- For registered analysis, reconcile the caller-supplied total with the registered plan and per-record/component accounting; do not trust a caller-supplied number alone.
- The analysis ledger currently sums `StateActionRecord` entries for Q/extra samples but cannot represent the 5,440 state-collection slots. Add explicit state-collection planned/actual counters or an equivalent typed budget component; reconcile them to the total.
- Registered PC1 must enforce the exact registered sample counts (100 states × 5 actions × 3 Q rollouts × horizon 3, plus one extra immediate draw per state-action), unless a formally approved protocol revision says otherwise. Do not silently accept surplus samples.
- Check sample-role slot formulas and counter deltas. Add negative tests showing that an understated total, surplus samples, missing collection slots or inconsistent record counters cannot yield a decision.

### R22 — Preserve cluster/task provenance

- Add explicit task ID and source collection-episode ID to the state/record provenance.
- The dry-run plan must map every sampled state to one of the 40 registered collection episodes/task clusters; do not list collection episodes and state IDs as disconnected schedules.
- Enforce the registered independent-cluster requirement. At minimum, validate the planned 40-episode design and ensure every state maps to a known cluster; no arbitrary two-cluster substitute.
- Reject missing, unknown, conflicting or duplicated state/episode mappings.
- Test that bootstrap resamples complete episode clusters and rejects insufficient or untraceable clusters.
- Keep Family C protected at all data-loading and evaluation boundaries.

### R23 — Make raw evidence genuinely replayable

- Include `D`, advantage, `D_ci`, `adv_ci`, decision, exact sample counts, full budget-component breakdown, bootstrap seed/method/resample count, protocol hash, input-record hash, manifest hash, runtime revision and evaluator version.
- Registered analysis must reject missing/empty provenance. Synthetic tests must be explicitly marked synthetic and must not be mistaken for registered evidence.
- The current replay command references the placeholder `records_from_raw`; replace it with an actual serialization/deserialization and replay entry point.
- Add a round-trip test: serialize raw records to an artifact, reload them, rerun analysis, and compare point estimates, confidence intervals, sample counts, decision and budget counters.
- Do not expose gold labels or answer keys to controllers/operators.

### R24 — Reconcile costs to source artifacts

- `research/SMOKE_RAW.json` reports total `wall_clock_s = 0.0188`; `research/COST_BASELINE.md` reports 0.021 s. Use the source artifact's value unless a separate raw artifact documents a different run and measurement ID.
- Fix the cost table headings: 45,440 is a planned-slot budget, not measured actual CTX. 96 is offspring-only planned slots, not actual CTX. 128 is total smoke planned slots. 112 is the recorded actual uncached replica count.
- Fix §6 wording that currently calls 45,440 “CTX” and treats it as a measured execution count.
- Add a consistency test that parses the JSON raw artifact and verifies the report's values and units, rather than searching for expected strings only.
- Keep production model calls, tokens, latency and costs marked UNMEASURED.

### R25 — Clarify and implement the collection/rollout runner

The current `generate_pc1_dry_run_plan()` is a plan generator and `execute_registered_pc1()` always raises. Do not describe this as a complete collection/rollout runner.

- Implement the gated collection/rollout orchestration behind explicit independent-review and production-runtime gate objects, with default-deny behavior.
- It must construct per-generation/per-replica unit IDs, run state collection and action rollouts, invoke the evaluator, pass the actual CRN key, update budget counters, enforce the cap before every unit, and write raw artifacts.
- This task must remain unable to launch a real registered run because review approval and the production backend are absent. Unit-test gate behavior and orchestration only with fake/synthetic components.
- If a safe gated collector cannot be implemented without an approved protocol, stop and state that clearly; downgrade all status claims to “dry-run planner + analysis only; collection runner not implemented.”
- Do not access or execute Family C.

### Verification and delivery

Run and report actual command output for:
- R19–R25 focused tests.
- `python -m unittest discover -s tests`.
- `zero_cost_protocol_check()`.
- Manifest verification.
- Dry-run schedule, cluster mapping and hard-cap checks.
- CRN override tests for task/replicate separation.
- Raw-evidence serialize/reload/replay comparison.
- Cost-report consistency against `SMOKE_RAW.json`.

Inspect the full diff. Update `research/FOURTH_REVIEW_FINDINGS.md` with remediation status without deleting the original findings, update this plan and `status.json`, commit/push to `main`, then verify the final remote HEAD and clean worktree. Do not self-approve.

### Forbidden

- Do not execute registered PC1 or tune against its results.
- Do not load, execute, or tune on Family C.
- Do not deploy/run production-model smoke or G3 while production backend is pending.
- Do not implement/train PPO, Q-learning or bandit controllers.
- Do not copy GLEET code or reuse other project artifacts.
- Do not fabricate tests, costs, tokens, measurements or approval.
- Do not weaken sample counts, thresholds, or budget rules to make the checks pass.

## Acceptance criteria

R19–R25 are complete only when code and tests prove protocol/version consistency, paired CRN uniqueness, fail-closed budget accounting, traceable 40-episode cluster provenance, evidence round-trip replay, raw-source cost consistency, and a genuinely gated collector (or an explicit truthful deferral). PC1 remains **NOT APPROVED / NOT EXECUTED** pending another independent review and the production-runtime gate.
