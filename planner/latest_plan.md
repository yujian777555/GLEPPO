# Planner Latest Plan — GLEPPO Phase 2A-R10 (TENTH REVIEW: REQUEST CHANGES)

**Status:** REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED  
**Reviewed commit:** `dfa99f17281d185ed3a8421c26d8bcd54fcab5d7`  
**Tenth review:** `research/TENTH_REVIEW_FINDINGS.md`  
**Production backend:** PENDING_DEPLOYMENT  
**GitHub CI:** No combined status entries or workflow runs were returned for the reviewed commit. Reported 232/232 tests were not independently reproduced by this reviewer.

## Planner decision

R9 improves protocol lifecycle checking, plan artifact comparison, and structured contracts, but the tenth read-only audit found four remaining blockers:

- **R50 — Trusted approval is not wired into the gate:** `TrustedApprovalArtifact.verify()` is unused by `ApprovalGate.check()`; the active path still accepts caller-created `PlannerApprovalRecord` data. The trust check only compares a field with a caller-supplied hash and does not cryptographically authenticate the approval.
- **R51 — Plan hash is not independently pinned:** `get_registered_plan_hash()` computes the hash from `generate_plan_mapping()` at runtime; plan ID/version constants are not included in or verified against the artifact. No adversarial self-hashed alternate-plan test was found.
- **R52 — Structured semantic validation is incomplete:** seed version/encoding are not checked, unknown reward/estimator fields are not rejected, and the claimed extra-term/estimator mutation tests are absent from the inspected test source.
- **R53 — Lifecycle state remains part of the protocol hash:** `compute_protocol_hash()` hashes the entire JSON block including `status`. The content predicate ignores status, but the hash does not, so lifecycle state and immutable content identity are not fully separated.

Do not execute registered PC1. Phase 2A-R10 is a security/contract remediation phase, not controller training.

## Executor instructions

Work only in `yujian777555/GLEPPO`, branch `main`. Fetch latest `origin/main` before editing and preserve review history. Read this plan, `research/TENTH_REVIEW_FINDINGS.md`, `gleppo/pc1.py`, `gleppo/reward.py`, all relevant `tests/test_r39_r42.py` and earlier tests, `research/PC1_PROTOCOL_R4_PROPOSED.md`, `status.json`, and `docs/RUNTIME_LOCK.md`.

### R53 — Separate immutable content identity from lifecycle state

- Define canonical protocol content as a typed payload that excludes status and approval metadata.
- Hash the canonical content/version only; store status and approval evidence separately.
- Test: status-only mutation leaves the immutable content hash unchanged; any decision-critical content mutation changes it.
- Keep current status PROPOSED / NOT APPROVED. Do not approve as part of this remediation.

### R50 — Implement trusted approval and wire it into the actual gate

- Replace caller-populated record validation as the authorization path with a verifiable approval artifact.
- Use a real cryptographic signature over canonical fields, verified with a public key pinned through an independent trust configuration. Do not treat a matching hash field as proof.
- Bind artifact ID, approver identity, date, immutable content hash and protocol version into the signed payload.
- `ApprovalGate.check()` must invoke the trusted verifier; no fallback to legacy `PlannerApprovalRecord` may authorize execution.
- Add tests for absent/invalid signatures, forged artifacts with the exact protocol hash, copied trust-anchor hashes, changed approver/date/content hash, and a valid signature fixture whose private test key is only for tests.
- Do not create or commit a real approval, production private key, or approval artifact for the live protocol.

### R51 — Pin registered plan identity/version/hash independently

- Define a versioned canonical plan artifact with registered ID, version, canonical mapping hash and immutable protocol-content hash.
- Pin the expected canonical plan hash independently of the runtime plan generator; do not call a runtime-recomputed hash “independently pinned.”
- Validate ID/version/hash at the registered analysis boundary and include them in evidence.
- Add an end-to-end test that changes the mapping, recomputes the artifact's self-hash, and confirms rejection against the independently pinned registered plan.
- Test missing identity, wrong version, wrong protocol binding, missing artifact, and correct canonical artifact.

### R52 — Enforce exact structured semantic contracts

- Use typed exact-schema validation or explicit allow-lists; reject unknown and missing keys and incorrect types.
- Check seed schema version and encoding against the executable seed contract, plus the exact field list.
- Check all reward weights/clipping bounds and exact estimator semantics against executable implementations.
- Add adversarial tests for extra reward keys/terms, estimator additions/alterations, wrong seed version, wrong encoding, unknown fields, missing fields and wrong types.

## Fast validation sequence

Run actual commands and preserve output/exit status:
1. Focused R50–R53 tests.
2. `python -m unittest discover -s tests`.
3. Zero-cost protocol check and `protocol_consistency_check()`.
4. Protocol content-hash/status lifecycle tests.
5. Trusted approval signature tests, including forged exact-hash records.
6. Canonical plan identity/version/hash tests, including alternate self-hashed plan.
7. Structured reward/estimator/seed schema mutation tests.
8. `python scripts/build_manifest.py`.
9. Dry-run arithmetic: 45,440 = 5,440 + 36,000 + 4,000; hard cap 50,000.
10. `python scripts/run_smoke.py` and cost consistency against `research/SMOKE_RAW.json`.

Do not claim a command passed unless it actually ran. Do not weaken tests or change pre-registered thresholds to make them pass.

## Delivery

Update `research/TENTH_REVIEW_FINDINGS.md` with a remediation log while preserving the original findings; update this plan and `status.json`. Update cost/evidence files only if measurements actually changed. Inspect the full diff, commit and push to `main`, fetch remote HEAD and verify synchronization. Request an eleventh independent review; do not self-approve.

## Forbidden

- No registered PC1 execution.
- No Family C access, execution or tuning.
- No production-model smoke/G3 while production backend is pending.
- No PPO, Q-learning or bandit controller implementation/training.
- No cross-project code or artifacts.
- No fabricated tests, measurements, model calls, costs, tokens, signatures or approval records.

## Acceptance

R10 is complete only when:
1. lifecycle status is excluded from immutable protocol-content hash;
2. trusted approval is cryptographically verifiable and enforced by the actual gate;
3. registered plan ID/version/hash are independently pinned and validated;
4. unknown/missing semantic contract fields and adversarial mutations are rejected;
5. focused/full tests and zero-cost validation actually run and outputs are recorded.

**PC1 remains NOT APPROVED / NOT EXECUTED.** Successful R10 remediation enables an eleventh independent review, not registered experiments.
