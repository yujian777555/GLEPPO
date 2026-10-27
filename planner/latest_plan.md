# Planner Latest Plan — GLEPPO Phase 2A-R6 (OUTCOME: REQUEST CHANGES)

**Status:** REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED  
**Repository:** `yujian777555/GLEPPO` only  
**Reviewed implementation commit:** `1441882ab8cd12e26c4b0dc22626d34d18f8e0dd`  
**Sixth review:** `research/SIXTH_REVIEW_FINDINGS.md`  
**Production backend:** PENDING_DEPLOYMENT

## Planner decision

R5 improved the protocol document, test coverage, cache encoding for the specific None-versus-empty case, and honest runner naming. The sixth read-only audit still found R33–R38 plus a budget-granularity gap. Do not execute registered PC1.

## Executor task: Phase 2A-R6

Work only in `yujian777555/GLEPPO`, branch `main`. Fetch the latest remote HEAD before modifying files; do not assume the reviewed SHA is still current. Read `research/SIXTH_REVIEW_FINDINGS.md`, this plan, `gleppo/pc1.py`, `gleppo/evaluator.py`, `tests/test_r26_r32.py`, `research/PC1_PROTOCOL_R4_PROPOSED.md`, `research/SMOKE_RAW.json`, `research/COST_BASELINE.md`, and `status.json`.

Implement actual source fixes and tests, not just another report.

### R33 — Atomic Q/extra budget updates and role-specific slots

- Fix `BudgetLedger.record_q_slot()` and `record_extra_slot()`: currently they increment `planned_q_slots` / `planned_extra_slots` before downstream validation/cap checks can raise.
- Validate all input deltas, calculate prospective component and total values, enforce the hard cap and invariants, then commit every counter atomically.
- For registered analysis, require each Q record to carry exactly 24 planned slots and each extra-immediate record exactly 8 slots under the current design; do not rely only on aggregate sums.
- Add tests where invalid replica/cache deltas or cap failure would occur after the component update, and assert the complete ledger is unchanged.
- Add offsetting-record tests (e.g. 23 + 25 Q slots) and require rejection even when the aggregate remains unchanged.

### R34 — Collision-free seed and cache identity

- Current tags collide for `None` versus literal override `"NONE"`, and empty string versus literal override `"EMPTY"`.
- Use a typed, canonical, collision-free encoding such as JSON arrays with distinct variants: `["none"]`, `["empty"]`, `["value","NONE"]`.
- Use the same semantic encoding in effective seed parts and cache-key generation.
- Replace delimiter-only `crn_seed` serialization with canonical structured serialization before hashing.
- Add tests for None, empty string, literal NONE/EMPTY, and delimiter-containing task/state IDs. Distinct semantic inputs must either be rejected or produce distinct seed/cache identities.

### R35 — Validate provenance against a verified plan

- Export a deterministic state→task→episode→cluster→family mapping in the PC1 plan artifact.
- Compute and record its hash.
- Registered analysis must load/receive this verified mapping and validate every record against the exact tuple; non-empty fields and a count of 40 clusters are not sufficient.
- Replace false-positive tests. The unknown-episode test must fail specifically for unknown provenance, not state-cluster conflict. Remove the assertion that concatenates the literal word `episode`.
- Add tests for wrong cluster/task/family and assigning a state to a different valid episode.

### R37 — Require protocol and plan hashes in registered evidence

- Add required `protocol_hash` and `plan_mapping_hash` (or equivalent verified plan hash) inputs to registered analysis.
- Verify each against the canonical protocol and plan artifacts before statistical computation.
- Include both in raw evidence and replay artifacts.
- Reject missing or mismatched hashes before calculating estimators or bootstrap intervals.
- Add tests for each missing/mismatched hash, with structurally valid records so failure is attributable to the hash check.

### R36 — Full protocol-document consistency and canonical hash

- Implement a canonical parser for the JSON field block in `research/PC1_PROTOCOL_R4_PROPOSED.md`.
- Compute a stable protocol hash from the canonicalized decision-critical fields and expose it to evidence/gates.
- Compare all fields against code, including code/protocol version, status, estimator definitions, reward function, gamma, thresholds/margins, cluster unit, seed contract and all budget components.
- `protocol_consistency_check()` must validate the independent document, not only a Python dictionary built from the same code constants.
- Add mutation tests for each decision-critical field.
- The protocol must remain `PROPOSED / NOT APPROVED`; do not approve it as part of this implementation task.

### R38 — Fail-closed approval/runtime gate bindings

- Require non-empty `protocol_hash` and `expected_protocol_hash`; reject if either is absent or they differ.
- Require non-empty `runtime_revision` and `required_revision`; reject if either is absent or they differ.
- Bind approval to the verified canonical protocol artifact and its actual status; a caller-supplied `protocol_status="APPROVED"` alone is not evidence of Planner approval.
- Require a verifiable approval ID and a valid ISO date (or the repository's explicitly documented approval schema).
- Add negative tests for empty hash, empty expected hash, missing runtime revision, missing required revision, incorrect approval ID/date, wrong document hash and proposed protocol status.
- Keep `execute_registered_pc1()` unconditionally refusing execution during this phase.

## Required verification

Run actual commands and report the exact output for:
- Focused R33–R38 tests.
- `python -m unittest discover -s tests`.
- `zero_cost_protocol_check()`.
- `protocol_consistency_check()` plus document mutation tests.
- `python scripts/build_manifest.py`.
- Dry-run plan: exact 45,440 total, 5,440 + 36,000 + 4,000, 100 states and 40 episodes.
- Budget atomicity and role-specific slot tests.
- Seed/cache tests including literal NONE/EMPTY and delimiter-containing IDs.
- Plan-backed provenance and hash validation.
- Approval/runtime gate negative tests.
- Smoke and cost consistency against `research/SMOKE_RAW.json`.

Do not claim tests pass unless they ran. If a test fails, fix the root cause or report the remaining blocker; do not weaken registered requirements.

## Delivery

Update `research/SIXTH_REVIEW_FINDINGS.md` with remediation status while preserving original findings, update this plan and `status.json`, inspect the full diff, commit and push to `main`, then fetch the remote HEAD and verify clean synchronization. Do not self-approve.

## Forbidden

- No registered PC1 execution.
- No Family C access, execution or tuning.
- No production-model smoke/G3 while the production backend is pending.
- No PPO, Q-learning or bandit controller implementation/training.
- No GLEET code reuse or cross-project artifacts.
- No fabricated tests, measurements, model calls, costs or approvals.

## Acceptance

R33–R38 are complete only when Q/extra ledger updates are atomic, per-record slots match role semantics, seeds and cache keys are collision-free, registered provenance is verified against the hashed plan, evidence binds to canonical protocol and plan hashes, the protocol document is fully checked against code, and all approval/runtime gates fail closed.

**PC1 remains NOT APPROVED / NOT EXECUTED.** After remediation, request a seventh independent review; Planner protocol approval and production-runtime deployment remain separate subsequent gates.
