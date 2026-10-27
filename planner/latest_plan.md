# Planner Latest Plan — GLEPPO Phase 2A-R7 (OUTCOME: REQUEST CHANGES)

**Status:** REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED  
**Reviewed implementation commit:** `6f4adf30c673a06ed70bfbeb3df2415d89d6b0e6`  
**Seventh review:** `research/SEVENTH_REVIEW_FINDINGS.md`  
**Production backend:** PENDING_DEPLOYMENT  
**GitHub CI:** No combined status entries or workflow runs were returned for the reviewed commit; reported 206/206 tests were not independently reproduced by the reviewer.

## Planner decision

R6 improved the budget ledger, typed seed encoding in the evaluator, registered provenance checks, protocol document parsing, and gate defaults. The seventh read-only audit found R39–R42. In particular, `gleppo/pc1.py:crn_seed()` still joins arbitrary identifiers with a delimiter, the protocol consistency checker does not validate all semantic fields, the plan hash is paired with a mutable cached mapping rather than a verified immutable artifact, and approval metadata is not checked against an actual Planner approval record.

Do not execute registered PC1. This phase is limited to implementation correctness and zero-cost validation.

## Executor instructions

Work only in `yujian777555/GLEPPO`, branch `main`. Fetch the newest remote HEAD before editing; do not assume the reviewed SHA is still latest. Read `research/SEVENTH_REVIEW_FINDINGS.md`, this plan, `gleppo/pc1.py`, `gleppo/evaluator.py`, `tests/test_r33_r38.py`, `research/PC1_PROTOCOL_R4_PROPOSED.md`, `research/SMOKE_RAW.json`, `research/COST_BASELINE.md`, `status.json`, and `docs/RUNTIME_LOCK.md`.

Implement R39–R42 in code and tests; do not only update reports.

### R39 — Canonical CRN serialization

- Replace `crn_seed()` delimiter joining with canonical typed JSON serialization of a versioned field list, then hash it.
- Preserve common-random-number semantics: task/state/rollout/replicate define the shared evaluation stream; action/genotype remain excluded.
- Add direct tests for IDs containing `|`, proving distinct semantic tuples cannot collide; prove identical tuples are stable and changes to each key field change the seed.
- Inspect every call site and align it with the canonical helper.

### R40 — Complete protocol/document semantic consistency

- `protocol_consistency_check()` must compare `code_version` to `PROTOCOL_VERSION`, exact protocol status, estimator version/semantics, reward definition, gamma, thresholds, sample design, cluster unit, budget components, and the exact typed seed contract.
- Update the proposed protocol document so its seed contract describes the actual typed JSON encoding, not legacy string tags.
- Replace weak substring checks such as merely requiring `"SEED"` with exact schema/field checks.
- Require protocol/document consistency to pass before registered analysis accepts the protocol hash.
- Add mutation tests for version, status, seed contract, reward, estimator, threshold and budget fields.
- Protocol remains `PROPOSED / NOT APPROVED`.

### R41 — Bind plan hash to immutable verified plan content

- `get_plan_mapping()` currently exposes a mutable cached mapping alongside a hash computed earlier. Make the mapping immutable or return defensive copies.
- Serialize the complete state/task/episode/cluster/family mapping into a deterministic plan artifact and hash its canonical content.
- Registered analysis must validate records against the exact verified artifact, not a mutable module singleton.
- Recompute/verify the mapping hash at the analysis boundary.
- Add tests for caller mutation, artifact tampering, mismatched supplied hashes, and a different but structurally valid mapping.
- Keep Family C excluded.

### R42 — Bind gate approval to a verifiable Planner approval record

- A caller-supplied `approved=True`, `protocol_status="APPROVED"`, nonempty strings and matching arbitrary hashes are not sufficient evidence.
- Define a structured approval artifact/record with stable approval ID, valid ISO date, protocol hash and approved status.
- Validate that record against the canonical protocol document and its current hash.
- Reject malformed dates, arbitrary IDs, forged metadata, mismatched hashes and changed protocol documents.
- Keep `execute_registered_pc1()` refusing execution throughout this phase.

## Verification

Run actual commands and report raw output/exit status for:
- Focused R39–R42 regression tests.
- `python -m unittest discover -s tests`.
- `zero_cost_protocol_check()` and `protocol_consistency_check()`.
- Protocol mutation tests covering every decision-critical field.
- Plan artifact hash, immutability and tamper tests.
- CRN seed collision tests and paired-seed invariants.
- Approval-record validation and gate negative tests.
- `python scripts/build_manifest.py`.
- Dry-run plan arithmetic (45,440 = 5,440 + 36,000 + 4,000; hard cap 50,000).
- `python scripts/run_smoke.py` and `SMOKE_RAW.json` / `COST_BASELINE.md` consistency.

Do not claim tests pass unless the command actually ran. Do not weaken requirements to make tests green.

## Delivery

Update `research/SEVENTH_REVIEW_FINDINGS.md` with remediation status while preserving the original findings. Update `planner/latest_plan.md` and `status.json`. Inspect the full diff, commit and push to `main`, then fetch remote HEAD and verify synchronization and a clean worktree. Request an eighth independent review; do not self-approve.

## Forbidden

- No registered PC1 execution.
- No Family C loading, execution or tuning.
- No production-model smoke/G3 while production backend is pending.
- No PPO, Q-learning or bandit controller implementation/training.
- No cross-project code or artifacts.
- No fabricated test results, measurements, model calls, costs or approval records.

## Acceptance

R39–R42 are complete only when CRN serialization is collision-safe, the full protocol contract is independently validated against code, the plan hash binds to immutable verified artifact content, and approval gates verify a real approval record and exact protocol artifact.

**PC1 remains NOT APPROVED / NOT EXECUTED.** A successful R7 implementation pass enables an eighth independent review, not immediate registered experimentation.
