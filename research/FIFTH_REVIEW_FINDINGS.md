# Fifth Independent Review Findings — Phase 2A-R4

**Reviewed commit:** `5486f0f762f0a00fd155e5649d6d089f4ffa550a`  
**Review date:** 2026-10-27  
**Review type:** read-only source/protocol/test audit. Reviewer did not execute repository tests or experiments.  
**Decision:** **REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED.**

## Improvements acknowledged

- The evaluator seed tuple now includes the base seed, task, state, rollout, replicate, and inner replica index; it excludes action/genotype.
- The cost report now agrees with `research/SMOKE_RAW.json` at 0.019 s, and distinguishes 32 + 96 = 128 planned smoke slots from 112 actual replica executions.
- The registered entry point `execute_registered_pc1()` still refuses execution.
- Evidence artifacts now contain the principal point estimates and confidence intervals, and a save/load/recompute path exists.
- The protocol is explicitly marked `PROPOSED_AWAITING_PLANNER_APPROVAL`; it has not been approved, and this review does not approve it.

The following source-level blockers remain.

## R26 — There is no canonical protocol document matching the code's “canonical” object (BLOCKER)

**Evidence:**
- `gleppo/pc1.py` declares `PROTOCOL_VERSION = "pc1-frozen-v1-r4"`, while `PROTOCOL_STATUS = "PROPOSED_AWAITING_PLANNER_APPROVAL"`.
- `CANONICAL_PROTOCOL` is assembled from the same Python constants it checks. `protocol_consistency_check()` therefore does not validate an independently versioned protocol document.
- The research directory contains no canonical protocol file. `research/PHASE2_PREFLIGHT.md` still contains the proposed v2 design (80 states, 4 rollouts, 2 extra immediate samples, 47,200 slots); `research/PC1_INDEPENDENT_REVIEW.md` still says the 100-state / 3-rollout / 1-extra estimator is a proposed amendment, not an approved protocol.
- The code's active estimator is `r_hat = Q-rollout first rewards + extra immediate`, which does not match the historical §3.4 description of the immediate-reward estimator.

**Required fix:**
1. Create a separate canonical protocol artifact that records the proposed R4 design and explicitly marks it **PROPOSED / NOT APPROVED** until Planner approval.
2. Preserve old protocol text as historical, clearly superseded/archival, rather than leaving it to appear active.
3. Add a protocol hash and a test that parses the canonical document and compares its version, estimator, sample counts, thresholds, seed contract and 45,440-slot arithmetic to the code.
4. Rename `pc1-frozen-v1-r4` if necessary so its name does not imply a frozen protocol while status remains proposed.
5. Do not collect registered PC1 data until Planner explicitly approves the canonical protocol and the approval is recorded.

## R27 — BudgetLedger and GatedPC1Runner accept negative accounting deltas (BLOCKER)

**Evidence:** `BudgetLedger.record_evaluation()`, `record_collection()`, `record_q_slot()`, `record_extra_slot()`, and `GatedPC1Runner.execute_unit()`.

The ledger methods directly add caller-supplied values without rejecting negative planned slots, replica deltas, cache bundle deltas, invalid counts or LLM counters. The runner only checks whether `current_planned + planned_slots > HARD_CAP_SLOTS`; a negative planned value passes that guard and can reduce the running total. This makes the claimed per-unit hard-cap guard non-fail-closed.

**Required fix:**
- Validate all accounting deltas as non-negative integers before mutating any ledger field.
- Reject negative planned slots in both unit and collection paths before the cap check.
- Make updates atomic: if any input is invalid or would exceed the cap, no counters or executed-unit list may change.
- Add regression tests proving negative planned slots, negative replica/cache deltas, negative counters and a sequence that attempts to lower the ledger are rejected without mutation.
- Add a post-update invariant check for component totals and hard-cap compliance.

## R28 — Registered budget is not reconciled to the full 45,440-slot plan (BLOCKER)

**Evidence:** `run_pc1_analysis()` and `validate_records()`.

- The analysis ledger is reconstructed from Q and extra records only. It does not add the 5,440 collection slots.
- The check only rejects when `record_planned > planned_slots_total`; it accepts a record-derived total far below the caller's total. The raw evidence can consequently report `planned_slots_total = 45,440` while `budget_components.total_planned` omits collection and may be zero if records retain their default `planned_slots=0`.
- Registered validation requires **at least** 100 states and **at least** 40 clusters, not exactly the registered 100 states and 40 source episodes. Surplus states/clusters can be accepted even though they alter the sampling design and may exceed the planned budget.
- `BudgetLedger.reconcile()` is not called by `run_pc1_analysis()`.

**Required fix:**
1. Represent collection, Q and extra sampling budgets as explicit inputs to registered analysis, or load a verified dry-run plan and reconcile records against it.
2. In registered mode, require exact registered counts: exactly 100 states, exactly 40 source collection episodes/clusters, and exactly the registered sample counts for each state-action pair.
3. Require each record's planned-slot contribution to match its sample role, and reconcile the exact sum to 45,440.
4. Ensure evidence reports the same complete total in `budget.planned_slots`, `budget_components.total_planned` and `planned_slots_total`.
5. Add tests for zero/missing record slot counts, omitted collection slots, excess states/clusters, and a mismatch between component and total accounting.

## R29 — Cluster provenance fields are present but not cross-validated (BLOCKER)

**Evidence:** `StateActionRecord`, `validate_records()`, `generate_pc1_dry_run_plan()`, and `tests/test_r19_r25.py:TestR22ClusterProvenance`.

Validation checks that `task_id` and `episode_id` are non-empty and that at least 40 distinct `cluster_id` values exist. It does not verify that:
- `episode_id` belongs to the registered dry-run plan;
- a state maps to the episode assigned to it by the plan;
- `cluster_id` is the cluster associated with that episode;
- `task_id` is valid for that episode/task family.

The test named `test_unknown_episode_in_registered` changes one record to an unknown episode, but it has only two clusters; it passes by failing the separate “need at least 40 clusters” condition, not by proving that unknown episodes are rejected. This is a false-positive test for the intended invariant.

**Required fix:**
- Validate records against an explicit, hashed state-to-episode/task mapping from the registered plan.
- Require exact agreement among state ID, task ID, episode ID, cluster ID and family.
- Replace the current unknown-episode test with a fixture containing the full registered cluster count, mutate one episode to an unknown value, and assert the specific unknown-provenance error.
- Add tests for a known episode with the wrong cluster, wrong task, wrong family, and a state assigned to a different episode than the plan.

## R30 — Registered provenance validation is absent; the test does not prove it (BLOCKER)

**Evidence:** `run_pc1_analysis()` and `tests/test_r19_r25.py:TestR23EvidenceReplay.test_registered_requires_provenance`.

The analysis function accepts `manifest_hash`, `runtime_revision`, and `evaluator_version` as empty-string defaults and writes them to evidence without rejecting empty values. The test intended to prove missing provenance is rejected uses only two states, so registered validation fails earlier on the 100-state requirement. It therefore does not establish a provenance check.

**Required fix:**
- For registered analysis, require non-empty, well-formed manifest hash, protocol hash, runtime revision and evaluator version before statistical computation.
- Require a valid source-plan/input-record hash and ensure provenance matches the artifacts used.
- Keep a separate explicit synthetic mode for fixtures.
- Rewrite the test with a full structurally valid registered fixture (or isolate the provenance validator) and assert failure specifically due to each missing provenance field.

## R31 — The “gated collection/rollout runner” is still an accounting stub (BLOCKER for the R25 completion claim)

**Evidence:** `GatedPC1Runner.execute_unit()` and `execute_collection_episode()`.

These methods check booleans and increment counters/append unit IDs. They do not call an evaluator, construct a state, apply an action, execute a rollout, collect reward traces, enforce the plan's state-to-episode mapping, or write per-unit raw artifacts. Thus `GatedPC1Runner` is currently a gate/accounting harness, not an actual collection/rollout runner. This is not inherently unsafe while PC1 is blocked, but the implementation and status must not claim the full runner is implemented.

The gate also does not require `PROTOCOL_STATUS` to be approved, and `ApprovalGate` is just a boolean with optional unvalidated approver/date fields. `ProtocolVersionGate` only compares version strings. If these booleans are set true, a proposed protocol can pass the gate.

**Required fix:**
- Until the protocol is approved, accurately rename/describe this as a synthetic gate/accounting harness, not a collection/rollout runner.
- Add an explicit protocol-approval gate that requires the canonical protocol status to be approved, its hash to match, and a recorded Planner approval identifier/date. Default must remain deny.
- Do not treat caller-supplied booleans alone as evidence of review approval.
- If the real collector is implemented later, wire an explicit task loader, state collector, operator/evaluator, rollout/reward recorder, plan reconciliation and raw-artifact writer behind the gates; test with fake components only.
- Keep `execute_registered_pc1()` refusing execution until the independent review and production runtime gates are truly satisfied.

## R32 — Cache-key normalization collides for `eval_seed=None` and empty-string override (BLOCKER)

**Evidence:** `gleppo/evaluator.py:Evaluator.effective_seed_parts()` and `_cache_key()`.

The seed derivation distinguishes:
- `eval_seed=None` → base `"AUTO"`;
- `eval_seed=""` → an explicit empty base.

But the cache key uses `eval_seed_override or ""`, so both cases produce the same cache-key field. For the same genotype/task/state/rollout/replicate, the second call can return a result cached under a different effective seed.

**Required fix:**
- Use an unambiguous tagged representation for absent versus explicit override, or reject empty overrides at the API boundary.
- Add a regression test that evaluates with `None` and `""` under the same other inputs and proves either explicit rejection or distinct cache keys/effective seeds.
- Ensure serialization of seed components is collision-safe (avoid ambiguous delimiter-only concatenation if IDs can contain delimiters).

## Test evidence limitations

This review was read-only. The reviewer did not run the 135 tests. The Executor-reported 135/135 is therefore recorded as reported evidence, not independently reproduced. The repository's tests include several cases that can fail for a different earlier validation condition than the test name claims; add tests that assert the specific error/invariant, not merely any `ValueError`.

## Required remediation order

1. Fix R27 negative counter/slot rejection and atomic budget updates.
2. Fix R28 full-plan budget reconciliation and exact registered shape.
3. Fix R29 provenance mapping and false-positive tests.
4. Fix R30 registered provenance validation and its test.
5. Fix R32 seed/cache-key normalization.
6. Fix R26 canonical protocol artifact and version/document consistency, while keeping it proposed until Planner approval.
7. Fix R31 gate semantics and truthfully downgrade runner status unless a real fake-backend orchestration is implemented.
8. Run focused and full tests, protocol/document consistency, manifest, dry-run and cost checks; report exact command output.
9. Update status and request another independent review. Do not self-approve.

## Forbidden until further approval

- Do not execute registered PC1.
- Do not load, execute, or tune on Family C.
- Do not run production-model smoke or G3 while production is pending.
- Do not implement/train PPO, Q-learning or bandit controllers.
- Do not fabricate tests, measurements, model calls, costs or approvals.

## Final decision

**REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED.** R20/R23/R24 have improved, but R26–R32 remain blocking issues. The proposed protocol still needs explicit Planner approval, the budget and provenance checks need to fail closed, and the gate/accounting harness must not be represented as a complete collector.
