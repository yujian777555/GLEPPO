# Sixth Independent Review Findings — Phase 2A-R5

**Reviewed commit:** `1441882ab8cd12e26c4b0dc22626d34d18f8e0dd`  
**Review date:** 2026-10-27  
**Scope:** read-only source, protocol, and regression-test audit. Reviewer did not execute repository tests or experiments.  
**GitHub CI:** no combined status checks or workflow runs were returned for the reviewed commit. The reported 169/169 test result is therefore Executor-reported and was not independently reproduced here.  
**Decision:** **REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED.**

## Improvements acknowledged

- The protocol is now explicitly named `pc1-proposed-v1-r5` and the document states PROPOSED / NOT APPROVED.
- The cost report and `SMOKE_RAW.json` agree on the latest stub smoke duration of 0.0235 seconds, with 32 + 96 = 128 planned slots and 112 actual replica executions.
- The registered entry point `execute_registered_pc1()` still unconditionally refuses execution.
- `SyntheticGateHarness` is now truthfully described as a gate/accounting harness, not a complete collection/rollout runner.
- The `None` versus empty-string seed case is covered by tests.

The following issues remain based on the actual source and test contents.

## R33 — Q/extra budget-component updates are not atomic (BLOCKER)

**Evidence:** `gleppo/pc1.py:BudgetLedger.record_q_slot()` and `record_extra_slot()`.

Both methods increment their component before calling `record_evaluation()`:
- `record_q_slot`: `self.planned_q_slots += ps` precedes validation of replica/cache deltas and the cap check inside `record_evaluation`.
- `record_extra_slot`: `self.planned_extra_slots += ps` likewise occurs before downstream validation.

If a call uses a valid planned-slot amount but an invalid negative `replicas_run_delta`, negative cache delta, or a value that would exceed the cap, `record_evaluation` raises after the component counter has already changed. This violates the claimed all-or-nothing update guarantee.

**Required fix:**
1. Validate every argument and calculate all proposed counter values before mutating any field.
2. Commit component and total counters in one atomic update only after all checks pass.
3. Add regression tests for Q and extra-slot methods where the component increment would otherwise occur before an invalid delta or cap failure.
4. Assert every ledger field remains byte-for-byte/equality unchanged after each rejected call.

## R34 — Seed tags collide with literal override values (BLOCKER)

**Evidence:** `gleppo/evaluator.py:Evaluator.effective_seed_parts()` and `_cache_key()`.

The implementation maps `None` to base tag `"NONE"`, empty string to `"EMPTY"`, and non-empty overrides to their literal string. Therefore:
- `eval_seed=None` and `eval_seed="NONE"` produce the same effective seed tuple.
- `eval_seed=""` and `eval_seed="EMPTY"` produce the same effective seed tuple.

The cache key has the same problem: `None` becomes `TAG:NONE`, while the literal override `"NONE"` also becomes `TAG:NONE`; similarly empty string and literal `"EMPTY"` collide. The current tests check only `None` versus `""`, so they miss these collisions.

Additionally, `crn_seed()` constructs its hash input by joining arbitrary identifiers with `|`, which is not an unambiguous encoding if identifiers can contain that delimiter.

**Required fix:**
- Use a collision-free tagged structure, e.g. a typed JSON array such as `["none"]`, `["value","NONE"]`, `["empty"]`, then hash the canonical serialization.
- Use the exact same canonical encoding contract for effective seed derivation and cache identity.
- Serialize CRN tuple fields unambiguously before hashing.
- Add tests for `None`, `""`, literal `"NONE"`, literal `"EMPTY"`, and delimiter-containing identifiers. Distinct semantic inputs must either be rejected or yield distinct effective seeds/cache keys.

## R35 — Registered records are not validated against the actual state-to-episode plan (BLOCKER)

**Evidence:** `gleppo/pc1.py:validate_records()`, `generate_pc1_dry_run_plan()`, and `tests/test_r26_r32.py:TestR29ProvenanceMapping`.

The dry-run generator creates a local `state_episode_map`, but that mapping is not returned as an explicit hashed provenance contract and is not supplied to `validate_records()`. Registered validation checks only that `task_id` and `episode_id` are non-empty, that each state has one cluster, and that there are exactly 40 distinct clusters. It does not verify that a given state/task/episode/cluster/family tuple matches the generated plan.

The current unknown-episode test mutates both the episode and cluster of one record. The validator can reject it because one state now has conflicting cluster IDs, without proving that the episode is unknown to the plan. Its assertion uses `str(ctx.exception).lower() + "episode" + str(ctx.exception).lower()`, which always inserts the word “episode” and therefore cannot verify the intended error text. The wrong-cluster test can similarly pass due to state-cluster conflict rather than plan-mapping validation.

**Required fix:**
1. Produce a deterministic state/task/episode/cluster/family mapping as part of the plan artifact and hash it.
2. Pass the verified mapping into registered validation or load it from the verified plan artifact.
3. Require exact agreement for every record; non-empty strings and a count of 40 clusters are insufficient.
4. Rewrite tests to assert a specific provenance error with all other fields valid.
5. Add cases for unknown episode, known episode with wrong cluster, wrong task, wrong family, and a state mapped to a different valid episode.

## R36 — Protocol-document consistency test does not validate all decision-critical fields (BLOCKER)

**Evidence:** `research/PC1_PROTOCOL_R4_PROPOSED.md`, `tests/test_r26_r32.py:TestR26ProtocolDocument`, and `gleppo/pc1.py:protocol_consistency_check()`.

The document includes a JSON field block, but the test compares only a subset of fields: state/action/rollout/horizon/extra counts, episode count and a few budget values. It does not assert consistency for all of:
- code/protocol version and status;
- estimator definitions and reward identity;
- gamma and thresholds/margins;
- cluster unit;
- seed contract;
- all component budget formulas.

The code's `protocol_consistency_check()` still compares code constants with a Python dictionary built from those same constants; it does not independently read the protocol document. The document says its protocol hash is computed at test time, but the reviewed implementation does not provide a canonical document-hash function or persist the resulting protocol hash in analysis evidence.

**Required fix:**
- Implement one canonical parser/hash routine for the JSON field block.
- Compare every decision-critical field against the actual code contract, including estimator strings, status, version, gamma, thresholds, seed contract, cluster unit and exact budget components.
- Add mutation tests: change one field in a temporary copy of the protocol document and prove the consistency check fails for each critical field.
- Compute and expose a stable protocol hash; do not label the protocol frozen or approved while status remains proposed.

## R37 — Registered analysis does not require protocol hash and verified plan hash (BLOCKER)

**Evidence:** `run_pc1_analysis()` and its `raw_evidence` construction in `gleppo/pc1.py`.

The registered analysis signature requires non-empty `manifest_hash`, `runtime_revision`, and `evaluator_version`, but it has no required `protocol_hash` or verified plan hash parameter. The raw evidence records protocol version/status but not the hash of the canonical protocol document or the state-to-episode plan. This contradicts §9 of `PC1_PROTOCOL_R4_PROPOSED.md`, which says `protocol_hash` must be non-empty, and prevents evidence from proving which exact protocol and mapping were used.

**Required fix:**
1. Require a non-empty canonical protocol hash and plan/mapping artifact hash in registered mode before computing statistics.
2. Verify these hashes against the actual artifacts loaded by the analysis/replay path.
3. Include both hashes in raw evidence and the replay artifact.
4. Add tests that independently remove or mismatch each hash and assert the specific rejection before statistical computation.

## R38 — Approval/runtime gates permit missing binding values (BLOCKER for gate semantics)

**Evidence:** `ApprovalGate.check()` and `ProductionRuntimeGate.check()` in `gleppo/pc1.py`.

- `ApprovalGate` compares protocol hashes only if `expected_protocol_hash` is truthy. If it is empty, an empty or arbitrary `protocol_hash` is not rejected.
- `ProductionRuntimeGate` compares revisions only if `required_revision` is truthy. If it is empty, any non-empty `runtime_revision` can pass once `ready=True`.
- The gate's `protocol_status` is caller-supplied and is not bound to a verified approved protocol artifact. The current registered entry point still refuses, so this does not enable registered PC1 today, but the harness gate does not enforce the contract it claims to represent.

**Required fix:**
- Require non-empty protocol hash and expected hash, and require exact equality; empty values must fail closed.
- Require non-empty runtime revision and required revision, and exact equality.
- Bind approval to a verified protocol artifact whose status is actually APPROVED and whose hash matches; caller-supplied booleans/strings alone must not suffice.
- Validate approval identifier and date format, and test missing values and mismatches.
- Keep `execute_registered_pc1()` refusing execution until Planner approval, independent review approval, and production runtime are separately recorded.

## Budget granularity note

Registered analysis checks aggregate Q and extra planned-slot sums, but does not check every record's role-specific planned-slot contribution (Q record = 24 slots; extra record = 8 slots under the current design). Two records could offset one another (e.g. 23 and 25) while preserving the aggregate. Add per-record role/slot validation as part of R33/R35 remediation and prove that compensating errors are rejected.

## Verification limitations

This was a source and test audit only. The reviewer did not execute the 169 tests. No GitHub combined status checks or workflow runs were returned for the reviewed commit. Therefore 169/169 is recorded as Executor-reported, not independently reproduced.

The reported smoke/cost numbers are internally consistent in the current source artifacts: `SMOKE_RAW.json` records 0.0235 seconds, 128 planned slots and 112 actual replicas; `COST_BASELINE.md` also states 0.0235 seconds.

## Required remediation order

1. Fix R33 atomic updates for Q/extra ledger methods and add role-specific slot validation.
2. Fix R34 seed/cache tag collisions and delimiter-safe CRN encoding.
3. Fix R35 plan-backed provenance validation and replace false-positive tests.
4. Fix R37 protocol/plan hash requirements in registered analysis and evidence.
5. Fix R36 complete protocol-document consistency and canonical hashing.
6. Fix R38 fail-closed approval/runtime bindings.
7. Run focused and full tests, zero-cost protocol check, manifest verification, dry-run, smoke, cost consistency and document mutation tests; report actual outputs.
8. Update status and request a seventh independent review. Do not self-approve.

## Forbidden until further approval

- Do not execute registered PC1.
- Do not load, execute, or tune on Family C.
- Do not run production-model smoke or G3 while production backend is pending.
- Do not implement/train PPO, Q-learning or bandit controllers.
- Do not fabricate tests, measurements, model calls, costs or approvals.

## Final decision

**REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED.** R5 improves the implementation and correctly downgrades the runner to a synthetic harness, but atomic budget updates, collision-free seed identity, plan-backed provenance, complete protocol hashing, registered evidence hashes and fail-closed gate bindings remain unresolved.
