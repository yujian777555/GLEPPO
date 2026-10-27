# Eighth Independent Review Findings — Phase 2A-R7

**Reviewed commit:** `e7355a7c0c6eb1d9e66d3f66fba3a9ac6b1e8e03`  
**Review date:** 2026-10-27  
**Scope:** read-only source, protocol, and test audit. Reviewer did not execute repository tests or experiments.  
**GitHub CI:** the combined-status query returned no status entries and the workflow-run query returned no runs for the reviewed commit. Executor-reported 232/232 tests are not independently reproduced.  
**Decision:** **REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED.**

## Improvements acknowledged

- `crn_seed()` now uses versioned JSON serialization and direct delimiter-collision tests.
- Protocol consistency checks compare exact code version and proposed status fields and are called from registered analysis.
- Plan save/load helpers verify an embedded mapping hash and `get_plan_mapping()` returns defensive copies.
- An approval-record dataclass and gate-level validation have been added.
- The entry point `execute_registered_pc1()` still unconditionally refuses registered execution.
- The reported smoke artifacts agree on 0.0263 s, 128 planned slots, 112 actual replicas, and zero cache-hit bundles.

The following gaps remain.

## R43 — ApprovalGate can accept an invented approval while the canonical protocol remains PROPOSED (BLOCKER)

**Evidence:**
- `research/PC1_PROTOCOL_R4_PROPOSED.md` declares **Status: PROPOSED / NOT APPROVED** and its canonical JSON status is `PROPOSED_NOT_APPROVED`.
- `PlannerApprovalRecord.validate()` checks caller-supplied `protocol_status == "APPROVED"`, a nonempty ID/approver, date string format, protocol hash and version. It does not verify that the canonical protocol document itself is approved or that the approval ID resolves to a trusted Planner approval artifact.
- `ApprovalGate.check()` computes the hash of the current protocol document, then validates the caller-provided record against that hash. It does not reject the canonical document's still-proposed status. The gate-level `expected_protocol_hash` field is not used.
- `tests/test_r39_r42.py:test_valid_record_passes` validates a record labelled APPROVED against the hash of the current protocol document, even though that document remains PROPOSED. The forged-record test only uses a wrong hash, so it does not exercise a forged record with the correct current hash.
- The date check uses a regular expression only; a calendar-invalid value such as `2026-99-99` satisfies the shape check.

**Required fix:**
1. Require the canonical protocol artifact itself to contain an approved status before the gate can pass.
2. Bind authorization to a trusted, verifiable Planner approval artifact/record; do not treat caller-provided status, ID, approver, date and matching hash as proof of authorization.
3. Validate the real calendar date, not only the YYYY-MM-DD character pattern.
4. Either enforce `expected_protocol_hash` or remove it and document the single authoritative hash source.
5. Add a negative test using the exact current protocol hash and an invented APPROVED record. It must fail while the canonical document remains PROPOSED.
6. Keep `execute_registered_pc1()` refusing execution.

## R44 — Registered analysis does not consume the verified plan artifact (BLOCKER)

**Evidence:**
- `save_plan_artifact()` and `load_plan_artifact()` exist and their isolated tests check round-trip and tampering.
- However, `run_pc1_analysis()` compares the caller's `plan_hash` against `get_plan_mapping()`'s in-memory generated hash.
- `validate_records()` likewise calls `get_plan_mapping()` and validates against that generated mapping.
- Neither registered analysis nor provenance validation requires the saved plan artifact path/content or validates records against the mapping loaded from that artifact.

Thus, passing artifact round-trip/tamper tests does not establish that the analysis used the persisted plan artifact identified by the evidence hash.

**Required fix:**
1. Make registered analysis require a verified plan artifact or an explicitly typed verified-plan object created by `load_plan_artifact()`.
2. Validate every record against that exact loaded mapping.
3. Recompute/verify the plan hash at the analysis boundary and record the artifact hash/path/identity in raw evidence.
4. Do not substitute the generated in-memory mapping when a registered artifact is required.
5. Add an end-to-end test where a different but structurally valid mapping is saved, then prove analysis either uses that exact mapping or rejects it against the registered canonical plan. Also test missing artifact, altered artifact and mismatched supplied hash.

## R45 — Protocol consistency is still a heuristic rather than a complete semantic contract (BLOCKER)

**Evidence:** `protocol_consistency_check()` checks the seed contract by accepting substrings such as `crn-v2`, `typed`, or `json`; reward consistency by checking only for `clip` and `valid_rate`; and estimator completeness by checking words such as `first` and `discounted`. These checks do not compare the full formula/equations to the implementation. For example, changing a reward coefficient while retaining those words could pass.

The canonical JSON block in `PC1_PROTOCOL_R4_PROPOSED.md` also repeats the `code_version` and `status` keys. Python's default JSON parser silently accepts duplicate keys, leaving ambiguous source material that mutation tests should not normalize away.

**Required fix:**
1. Replace substring checks with exact structured fields or versioned semantic identifiers tied to the implementation.
2. Verify the actual reward formula against `gleppo/reward.py:generation_reward`, including coefficients, clipping bounds and inputs.
3. Verify the estimator definition and seed schema against executable contracts, not just prose fragments.
4. Reject duplicate JSON object keys when parsing the canonical protocol block.
5. Remove duplicate `code_version` and `status` keys from the protocol document.
6. Add mutation tests that change one reward coefficient, estimator equation, seed schema or duplicate a critical key while retaining other expected substrings. Every mutation must fail closed.

## Verification limitations

This was a read-only source audit. The reviewer did not run the reported 232 tests or experiments. GitHub returned no combined status entries and no workflow runs for the reviewed commit, so 232/232 remains Executor-reported rather than independently reproduced.

The protocol document remains PROPOSED / NOT APPROVED; production backend remains PENDING_DEPLOYMENT; registered PC1 has not been executed; Family C has not been accessed.

## Required remediation order

1. Fix R43: a fabricated approval must not pass while the canonical protocol remains proposed.
2. Fix R44: bind registered analysis to the exact verified plan artifact.
3. Fix R45: enforce exact protocol semantics and reject duplicate JSON keys.
4. Run focused R43–R45 tests, full suite, zero-cost protocol checks, manifest verification, dry-run and smoke/cost consistency. Report actual outputs.
5. Update status and request a ninth independent review. Do not self-approve.

## Forbidden until all gates are satisfied

- Do not execute registered PC1.
- Do not load, execute, or tune on Family C.
- Do not run production-model smoke/G3 while the production backend is pending.
- Do not implement/train PPO, Q-learning or bandit controllers.
- Do not fabricate tests, measurements, model calls, costs or approval records.

## Final decision

**REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED.** R7 adds useful safeguards, but the approval gate can accept a caller-invented approval record against the hash of a still-proposed protocol; registered analysis does not consume the saved plan artifact; and protocol semantic checks remain heuristic.
