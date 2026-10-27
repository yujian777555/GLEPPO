# Seventh Independent Review Findings — Phase 2A-R6

**Reviewed commit:** `6f4adf30c673a06ed70bfbeb3df2415d89d6b0e6`  
**Review date:** 2026-10-27  
**Scope:** read-only source, protocol, and test audit. Reviewer did not execute repository tests or experiments.  
**GitHub CI:** the commit-status query returned no status entries and the workflow-run query returned no runs. Executor-reported 206/206 is therefore not independently reproduced.  
**Decision:** **REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED.**

## Improvements acknowledged

- `BudgetLedger.record_q_slot()` and `record_extra_slot()` validate their direct arguments before mutation and check the hard cap.
- Registered record validation now checks each Q record's 24-slot contribution and each extra-immediate record's 8-slot contribution.
- The evaluator's `effective_seed_parts()` and cache key now use typed JSON encoding to distinguish `None`, empty strings, and literal values.
- Registered analysis requires protocol and plan hash arguments and compares them to code-derived values.
- `execute_registered_pc1()` still unconditionally refuses execution.
- The runtime remains a stub; the reported smoke and cost artifacts agree at 0.0246 s, 128 planned slots, and 112 actual replicas.

The following source-level issues remain.

## R39 — The canonical CRN helper still uses ambiguous delimiter concatenation (BLOCKER)

**Evidence:** `gleppo/pc1.py:crn_seed()`.

The implementation still returns:

```python
hashlib.sha256(f"CRN|{task_id}|{state_id}|{rollout_id}|{replicate_id}".encode()).hexdigest()[:16]
```

This contradicts the R6 commit summary that CRN uses JSON serialization. It is ambiguous when identifiers contain the delimiter. For example, `task_id="a|b", state_id="c"` and `task_id="a", state_id="b|c"` produce the same pre-hash string when the remaining fields match. The new delimiter test only exercises `Evaluator.effective_seed_parts()`; it does not call `crn_seed()`.

**Required fix:**
1. Canonically JSON-serialize a typed tuple/list of all CRN fields before hashing.
2. Use an explicit schema/version tag in that serialization.
3. Add direct `crn_seed()` collision tests with delimiter-containing task/state IDs and verify the intended CRN invariants: same tuple gives same seed; changing any field gives a different seed; action/genotype remain excluded.
4. Confirm every call site uses the same canonical CRN helper contract.

## R40 — Protocol consistency checks still accept important semantic mismatches (BLOCKER)

**Evidence:** `gleppo/pc1.py:protocol_consistency_check()`, `research/PC1_PROTOCOL_R4_PROPOSED.md`, and `tests/test_r33_r38.py:TestR36ProtocolConsistency`.

The current consistency check does not compare several decision-critical fields:
- `doc.code_version` against `PROTOCOL_VERSION`;
- exact protocol status against `PROTOCOL_STATUS` (it only checks whether the text contains `PROPOSED`);
- the complete seed contract against the actual typed JSON seed encoding;
- the documented reward formula / `generation_reward` contract;
- the complete estimator semantics, including the exact first-step and discounted-return equations.

The protocol document still describes `base_tag` as string values `"NONE"` / `"EMPTY"`, while the code uses typed structures `["none"]`, `["empty"]`, and `["value", value]`. The test suite's delimiter test does not test `crn_seed()`, and the current document check only requires that the seed-contract string contain `"SEED"`; therefore this mismatch passes.

Additionally, `run_pc1_analysis()` compares the supplied hash to the hash of the current document, but does not require `protocol_consistency_check()` to pass. A changed document can have a matching hash while disagreeing with code.

**Required fix:**
1. Compare protocol version and exact proposed status against code.
2. Make the documented seed contract match the exact typed serialization and hash contract.
3. Compare the complete reward and estimator definitions, not loose substring checks.
4. Add mutation tests for version, status, seed contract, reward definition, estimator definition and each threshold/budget field.
5. Require protocol-document/code consistency to pass before registered analysis accepts a protocol hash.
6. Keep the protocol marked **PROPOSED / NOT APPROVED** until explicit Planner approval.

## R41 — The plan hash is code-derived rather than bound to a verified plan artifact (BLOCKER)

**Evidence:** `generate_plan_mapping()`, `get_plan_mapping()`, and `run_pc1_analysis()`.

`get_plan_mapping()` returns a module-level cached mutable mapping and its previously computed hash. The mapping can be mutated by a caller while the cached hash remains unchanged. Registered analysis then validates records against the returned mapping and compares `plan_hash` only to the stale cached hash. The hash therefore does not necessarily describe the mapping actually used for validation.

The current plan hash is also generated in memory from hard-coded mapping logic; there is no required persisted plan artifact whose bytes/hash are loaded and verified by registered analysis. This falls short of binding results to the exact sampling plan used.

**Required fix:**
1. Make the plan mapping immutable or return defensive copies; never expose a mutable mapping paired with a stale cached hash.
2. Serialize the complete plan mapping to a deterministic artifact and hash the canonical artifact content.
3. Registered analysis must load or receive the verified artifact and validate records against that exact mapping.
4. Recompute and compare the hash at the validation boundary; do not trust a cached hash disconnected from the mapping.
5. Add tests that attempt to mutate the returned mapping, mutate the serialized plan, mismatch the supplied hash, and substitute a different but structurally valid mapping.

## R42 — Approval metadata is still caller-supplied and is not verified against an approval record/artifact (BLOCKER for gate semantics)

**Evidence:** `ApprovalGate.check()` in `gleppo/pc1.py` and `tests/test_r33_r38.py:TestR38FailClosedGates`.

The gate checks that `approved=True`, `protocol_status="APPROVED"`, a nonempty approver/date, and matching nonempty hash strings were passed by the caller. It does not verify the canonical protocol artifact's status/hash or an actual Planner approval record. Any caller can construct the gate with arbitrary matching strings and a nonempty date such as `"not-a-date"` and make `check()` pass. The existing tests verify missing fields and a proposed status, but do not verify fake approval metadata or a malformed date.

The registered entry point still refuses, which prevents this gate weakness from authorizing registered PC1 through that entry point today. However, the gate itself does not satisfy its stated approval-binding contract.

**Required fix:**
1. Require a structured Planner approval record/artifact with a stable approval ID, valid ISO date, approved protocol hash, and exact protocol document hash.
2. Verify that record against the canonical protocol document; caller-supplied booleans and strings alone must not authorize.
3. Require exact protocol-document/code consistency and status `APPROVED` from the verified artifact.
4. Add tests for arbitrary matching hashes, forged approver/date strings, malformed dates, wrong approval IDs, changed protocol documents, and mismatched approved hashes.
5. Keep `execute_registered_pc1()` refusing execution until Planner approval, independent review approval, and production runtime readiness are separately recorded.

## Verification limitations

This was a read-only audit. The reviewer did not run the 206 tests or experiments. GitHub returned no combined status entries and no workflow runs for the reviewed commit, so 206/206 remains Executor-reported rather than independently reproduced.

The current stub smoke artifacts are internally consistent: `SMOKE_RAW.json` reports 0.0246 s, 128 planned slots, and 112 actual replicas; `COST_BASELINE.md` reports the same.

## Required remediation order

1. Fix R39: canonicalize `crn_seed()` and add direct delimiter-collision tests.
2. Fix R40: complete protocol/document semantic checks and require them before registered analysis.
3. Fix R41: bind plan hash to immutable/persisted plan artifact content.
4. Fix R42: bind approval to a verifiable Planner approval record and validate date/hash/status.
5. Run focused R39–R42 tests, full test suite, zero-cost protocol checks, protocol mutation tests, manifest, dry-run, smoke and cost consistency; report actual command outputs.
6. Update status and request an eighth independent review. Do not self-approve.

## Forbidden until further approval

- Do not execute registered PC1.
- Do not load, execute, or tune on Family C.
- Do not run production-model smoke/G3 while the production backend is pending.
- Do not implement/train PPO, Q-learning or bandit controllers.
- Do not fabricate tests, measurements, model calls, costs or approvals.

## Final decision

**REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED.** R6 fixed several reported issues, but the CRN helper remains delimiter-ambiguous, protocol consistency checks still miss semantic mismatches, the plan hash is not bound to an immutable verified artifact, and approval metadata is not verified against an actual approval record.

---

# Remediation Log (Executor, 2026-10-27 Phase 2A-R7)

**Base commit (seventh review):** `2474253`
**PC1 status:** NOT EXECUTED / NOT APPROVED.

| Finding | Fix | Tests |
|---|---|---|
| **R39** CRN delimiter ambiguity | `crn_seed()` uses typed JSON serialization `["crn-v2", task, state, rollout, replicate]` before SHA256; delimiter collision tests | `TestR39CRNSeed` (8) |
| **R40** protocol consistency incomplete | exact version/status comparison; seed contract/reward/estimator semantic checks; consistency required before registered analysis; mutation tests | `TestR40ProtocolConsistency` (5) |
| **R41** plan hash not bound to artifact | `save_plan_artifact`/`load_plan_artifact` with hash verification; defensive copies in `get_plan_mapping`; tamper detection | `TestR41PlanArtifact` (4) |
| **R42** approval metadata not verified | `PlannerApprovalRecord` with approval_id/ISO date/protocol_hash/version; `ApprovalGate.check()` validates record against canonical protocol; forged/malformed rejected | `TestR42ApprovalRecord` (9) |

## Experiment results

- **Experiment A (CRN):** all seed tests pass; delimiter collision prevented; field isolation verified
- **Experiment B (protocol/stats):** consistency PASS (doc_hash=af7e2138); plan artifact roundtrip OK; tampering rejected
- **Experiment C (regression):** 232/232 PASS; zero_cost PASS; dry-run 45,440/50,000; manifest OK; smoke 32+96=128/112

## Test evidence

- **Full unit suite: 232/232 PASS**
- **Zero-cost protocol check: PASS**
- **Protocol consistency check: PASS**
- **Dry-run: within_cap=True, total=45,440, schedule=2040**
- **Manifest: VERIFY OK**
- **Smoke: 32+96=128, actual=112, slot_arithmetic_ok=true**
