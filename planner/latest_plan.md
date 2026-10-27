# Planner Latest Plan — GLEPPO Phase 2A-R9 (OUTCOME: REQUEST CHANGES)

**Status:** REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED  
**Reviewed commit:** `d4c58f03e57a5369864152f3a2bc5097589ace4e`  
**Ninth review:** `research/NINTH_REVIEW_FINDINGS.md`  
**Production backend:** PENDING_DEPLOYMENT  
**GitHub CI:** No combined status entries or workflow runs were returned for the reviewed commit; reported 232/232 tests were not independently reproduced.

## Planner decision

R8 added useful checks, but the ninth read-only source audit found four blockers:

- **R46 — Approval authenticity:** caller-supplied approval fields are not bound to a trusted/authenticated Planner approval artifact. An arbitrary record can be created if someone changes the document to APPROVED and computes its current hash.
- **R47 — Registered plan identity:** plan artifacts are self-hashed but not compared to an independently pinned registered plan identity/hash. A structurally valid alternate mapping with a recomputed self-hash is not explicitly rejected.
- **R48 — Semantic checks remain heuristic:** reward, estimator and seed semantics still use substring checks; materially changed contracts can preserve those strings and pass.
- **R49 — Lifecycle deadlock:** `protocol_consistency_check()` requires status `PROPOSED_NOT_APPROVED`, while `ApprovalGate` requires `APPROVED`. Registered analysis requires consistency to pass, so the status transition cannot satisfy both paths.

Do not execute registered PC1. The next phase is focused remediation plus zero-cost verification, not controller training.

## Executor instructions

Work only in `yujian777555/GLEPPO`, branch `main`. Fetch latest `origin/main` before edits and preserve all review history. Read this plan, `research/NINTH_REVIEW_FINDINGS.md`, `gleppo/pc1.py`, `gleppo/reward.py`, `tests/test_r39_r42.py`, `research/PC1_PROTOCOL_R4_PROPOSED.md`, `status.json`, and `docs/RUNTIME_LOCK.md`.

### R49 — Fix the protocol lifecycle model first

- Separate immutable protocol content/version/hash from lifecycle approval status.
- Consistency checks validate content/version and structured contract fields; they must not hardcode the protocol to remain PROPOSED forever.
- Approval checks consume a trusted approval artifact bound to the exact protocol hash.
- Add transition tests: proposed/unapproved denies; approved with valid trusted approval may pass the approval gate; changed content after approval denies.
- Do not approve the protocol as part of this implementation phase.

### R46 — Bind approval to a trusted authorization source

- A `PlannerApprovalRecord` populated by the caller is not proof of authorization.
- Use an authenticated/cryptographically verifiable approval artifact or another independently trusted approval event. Pin/verify its trust anchor separately from the mutable protocol document.
- Verify approval ID, approver identity, date, protocol version/hash and approved state.
- Add an adversarial test with invented metadata and the exact current protocol hash; it must fail without a valid trusted approval artifact.
- Remove or correctly enforce `expected_protocol_hash`; eliminate misleading unused gate fields.
- Keep default-deny behavior.

### R47 — Bind the plan artifact to the registered canonical plan

- Define a stable registered plan identity/version and pin its canonical hash independently (for example through a versioned manifest or protocol-bound plan identity).
- A matching self-hash is necessary but insufficient. Reject a different, structurally valid mapping even if its artifact hash is recomputed correctly.
- Registered analysis must load the artifact and verify both its internal hash and its registered identity/hash before validating records.
- Record plan identity/version/hash in raw evidence.
- Add end-to-end tests for alternate mapping + recomputed hash, missing artifact, changed artifact, wrong registered hash and correct canonical artifact.
- Keep Family C excluded.

### R48 — Replace substring checks with structured semantic contracts

- Define explicit structured fields for reward contract ID, all numeric reward weights, clipping bounds, estimator contract ID/semantics, sample roles, gamma/horizon and seed schema.
- Compare those values directly to executable constants/contracts in `gleppo/reward.py`, `gleppo/pc1.py` and the seed implementation.
- Include the best-reward coefficient `W_BEST`; do not leave imported constants unchecked.
- Add adversarial mutations that retain expected words/numbers while appending a reward term, changing estimator weighting/horizon, or adding action/genotype to the seed schema. Every mutation must fail.
- Continue rejecting duplicate JSON keys.

## Fast validation sequence

Run actual commands and preserve output/exit status:
1. Focused R46–R49 tests.
2. `python -m unittest discover -s tests`.
3. `zero_cost_protocol_check()` and `protocol_consistency_check()`.
4. Lifecycle transition tests and forged-approval tests.
5. Canonical plan identity, alternative-plan, hash and provenance tests.
6. Structured protocol mutation tests.
7. `python scripts/build_manifest.py`.
8. Dry-run arithmetic: 45,440 = 5,440 + 36,000 + 4,000; hard cap 50,000.
9. `python scripts/run_smoke.py` and cost consistency against `research/SMOKE_RAW.json`.

Do not claim a command passed unless it actually ran. Do not weaken tests or change pre-registered thresholds to make them pass.

## Delivery

Update `research/NINTH_REVIEW_FINDINGS.md` with a remediation log while preserving original findings. Update `planner/latest_plan.md` and `status.json`; update cost/evidence files only if measurements actually changed. Inspect the full diff, commit and push to `main`, fetch remote HEAD, and verify synchronization. Request a tenth independent review; do not self-approve.

## Forbidden

- No registered PC1 execution.
- No Family C access, execution or tuning.
- No production-model smoke/G3 while production backend is pending.
- No PPO, Q-learning or bandit controller implementation/training.
- No cross-project code or artifacts.
- No fabricated tests, measurements, model calls, costs or approval records.

## Acceptance

R9 is complete only when:
1. protocol status can transition without contradicting content consistency;
2. invented approval records cannot pass without trusted authorization;
3. registered analysis rejects alternate self-hashed plans;
4. semantic mutations are rejected structurally;
5. focused/full tests and zero-cost validation actually run and their outputs are recorded.

**PC1 remains NOT APPROVED / NOT EXECUTED.** Successful R9 remediation enables a tenth independent review, not registered experiments.
