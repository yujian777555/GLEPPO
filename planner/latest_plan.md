# Planner Latest Plan — GLEPPO Phase 2A-R8 (OUTCOME: REQUEST CHANGES)

**Status:** REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED  
**Reviewed implementation commit:** `e7355a7c0c6eb1d9e66d3f66fba3a9ac6b1e8e03`  
**Eighth review:** `research/EIGHTH_REVIEW_FINDINGS.md`  
**Production backend:** PENDING_DEPLOYMENT  
**GitHub CI:** No combined status entries or workflow runs were returned for the reviewed commit; the reported 232/232 tests were not independently reproduced by the reviewer.

## Planner decision

R7 improved CRN serialization, introduced plan artifact helpers, and added structured approval-record fields. The eighth read-only audit found R43–R45:

- **R43:** ApprovalGate can accept a caller-invented APPROVED record matching the hash of the canonical document even while the document itself remains PROPOSED. The gate does not use `expected_protocol_hash`; date validation checks only the string shape.
- **R44:** Registered analysis still uses `get_plan_mapping()` rather than a verified persisted plan artifact. Save/load tests do not prove that analysis consumes the artifact.
- **R45:** Protocol consistency uses loose substring checks for seed, reward and estimator semantics; the JSON field block repeats `code_version` and `status`, and duplicate keys are silently accepted by the default parser.

Do not execute registered PC1.

## Executor task: Phase 2A-R8

Work only in `yujian777555/GLEPPO`, branch `main`. Fetch latest `origin/main` before edits and preserve all existing review history. Read the eighth-review report, this plan, `gleppo/pc1.py`, `gleppo/reward.py`, `tests/test_r39_r42.py`, `research/PC1_PROTOCOL_R4_PROPOSED.md`, `status.json`, and `docs/RUNTIME_LOCK.md`.

### R43 — Real approval binding

- Reject gate approval unless the canonical protocol document itself is approved.
- Require a trusted, verifiable Planner approval artifact/record; caller-supplied status, ID, approver, date and hash strings alone are not proof.
- Validate actual calendar dates, not only YYYY-MM-DD regex shape.
- Enforce `expected_protocol_hash` or remove it and document one authoritative source.
- Add a test using the exact hash of the current PROPOSED document and an invented APPROVED record; it must fail.
- Keep `execute_registered_pc1()` refusing execution.

### R44 — Bind registered analysis to persisted plan artifact

- Require registered analysis to receive/load a verified plan artifact or a typed verified-plan object created by `load_plan_artifact()`.
- Validate all registered records against the exact mapping loaded from that artifact.
- Recompute the hash at the analysis boundary and store the artifact hash and identity in evidence.
- Do not silently replace a missing artifact with the generated in-memory mapping.
- Test missing artifact, tampering, mismatched hash, external mutation and a structurally valid alternative mapping.

### R45 — Exact protocol semantic validation

- Replace substring heuristics with exact structured fields/versioned contract IDs for the seed schema, reward function and estimator.
- Verify reward semantics against `gleppo/reward.py:generation_reward`, including coefficients, inputs and clipping bounds.
- Verify the estimator and seed schema against executable contracts.
- Reject duplicate JSON keys in the canonical protocol field block.
- Remove duplicate `code_version` and `status` keys from `research/PC1_PROTOCOL_R4_PROPOSED.md`.
- Add mutation tests for reward coefficients, estimator semantics, seed schema, and duplicate critical keys.

## Fast validation sequence

Run actual commands and preserve output/exit status:
1. Focused R43–R45 tests after each fix.
2. `python -m unittest discover -s tests`.
3. `zero_cost_protocol_check()` and `protocol_consistency_check()`.
4. Protocol mutation and duplicate-key tests.
5. Plan artifact binding, tamper and provenance tests.
6. Approval-gate tests including the current-proposed-document forgery case and invalid calendar dates.
7. `python scripts/build_manifest.py`.
8. Dry-run plan arithmetic: 45,440 = 5,440 + 36,000 + 4,000; hard cap 50,000.
9. `python scripts/run_smoke.py` and cost consistency against `research/SMOKE_RAW.json`.

Do not claim a command passed unless it actually ran. Do not weaken the tests.

## Delivery

Update `research/EIGHTH_REVIEW_FINDINGS.md` with remediation status while preserving original findings; update `planner/latest_plan.md`, `status.json`, and cost/evidence artifacts only when the underlying measurements changed. Inspect the full diff, commit and push to `main`, then fetch remote HEAD and verify synchronization. Request a ninth independent review; do not self-approve.

## Forbidden

- No registered PC1 execution.
- No Family C access, execution or tuning.
- No production-model smoke/G3 while production backend is pending.
- No PPO, Q-learning or bandit controller implementation/training.
- No cross-project code/artifacts.
- No fabricated tests, measurements, model calls, costs or approval records.

## Acceptance

R43–R45 are complete only when a fabricated approval cannot pass, registered analysis is bound to the exact verified plan artifact, and protocol semantics are checked exactly against executable contracts with duplicate keys rejected.

**PC1 remains NOT APPROVED / NOT EXECUTED.** A successful R8 remediation pass enables a ninth independent review; it does not authorize registered experiments.
