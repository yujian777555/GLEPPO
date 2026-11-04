# GLEPPO R26 Stage 1F — Exact Test Evidence Reconstruction and Disposition Correction

**Role:** Executor under Planner review  
**Project:** GLEPPO only  
**Repository:** yujian777555/GLEPPO  
**Required branch:** r25-handoff  
**Stage 1E Executor commit:** 65f83dfc7334d674ad1d96539872f71f1ae44303  
**Stage 1E source snapshot / parent:** da3dfefee9a86ff3833a6fa4f9cf0f71fd0b1375  
**Stage 1E Planner review:** research/R26_STAGE1E_PLANNER_REVIEW.md  
**R25 base:** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**Stage:** R26_STAGE1F_EXACT_TEST_EVIDENCE_AND_DISPOSITION_RECONCILIATION  
**Task type:** read-only source/test audit and report correction  
**Authorization:** no production source changes; no test-code changes; no registered experiment.

---

## 1. Planner decision — Stage 1E bookkeeping accepted, evidence map rejected

Read the complete Planner review first:

research/R26_STAGE1E_PLANNER_REVIEW.md

Stage 1E correctly fixed:
- all 42 formal Finding IDs R12–R53 are present exactly once;
- R18 is restored separately from R24;
- category counts sum to 42;
- disposition arithmetic 30 + 10 + 1 + 1 = 42;
- R46 appears only once as UNVERIFIABLE;
- 218 declared test functions across the seven PC1-related suites is the correct count;
- 450/450 is honestly marked EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED;
- no production source or test code changed.

Stage 1E is not accepted as a completed finding-level audit because its 42-row test map contains class/function names that do not match actual test declarations.

Planner checked the 42 rows against the seven PC1-related suites:
- 42 map rows;
- only 3 row class names match an actual class declaration;
- only 1 function name matches a declared function (test_init_evaluation), but it belongs to TestR12BudgetLedger, not the claimed TestR12Budget;
- 0 of 42 class/function pairs match an actual declaration pair.

The assertion column contains descriptions, not exact assertions. The map lacks test file paths, line ranges, source symbols, source line ranges and call-path/branch analysis.

Current state:

**R26_STAGE1E_REPORT_RECEIVED_REQUEST_CHANGES; EXACT_TEST_MAP_AND_DISPOSITION_REVIEW_REQUIRED; PC1_BLOCKED.**

## 2. Repository recovery and provenance

Before editing:
1. Verify branch r25-handoff and current HEAD.
2. Verify ancestry includes R25 base a8ff1827434a88b2fef02a89aaf3e120e0a017a7 and Stage 1E commit 65f83dfc7334d674ad1d96539872f71f1ae44303.
3. Record current branch HEAD, main SHA, ahead/behind counts, latest commit and worktree state.
4. Record Stage 1E source snapshot, Stage 1E report commit and current Stage 1F report commit separately.
5. If refs differ unexpectedly, stop and report the exact mismatch.
6. Continue only on r25-handoff. Do not merge or update main.

Planner last verified:
- r25-handoff = 65f83dfc7334d674ad1d96539872f71f1ae44303;
- Stage 1E parent/source snapshot = da3dfefee9a86ff3833a6fa4f9cf0f71fd0b1375;
- main = 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e;
- main → Stage 1E: 140 ahead, 0 behind;
- R25 base → Stage 1E: 59 ahead, 0 behind.

## 3. Work Package A — rebuild the 42-row test map from actual declarations

Inspect the seven PC1-related suites at the exact current HEAD:
- tests/test_r8_r9_r11_pc1.py
- tests/test_r12_r17.py
- tests/test_r19_r25.py
- tests/test_r26_r32.py
- tests/test_r33_r38.py
- tests/test_r39_r42.py
- tests/test_r54_r59.py

Do not copy any Stage 1E class/function names unless they are verified against source declarations.

For every R12–R53 Finding, record:
1. exact original Finding heading and original review file;
2. original failure mode and full acceptance criterion;
3. exact test file path, or NONE;
4. exact test class declaration, or NONE;
5. exact test function declaration, or NONE;
6. exact line range for the test;
7. source symbol/function called by the test;
8. source line range for that symbol;
9. actual assertion expression(s) and line range;
10. whether the test reaches the intended branch or fails earlier for another reason;
11. which part of the original acceptance criterion it proves;
12. uncovered acceptance conditions;
13. disposition and rationale.

A test name that sounds relevant is not evidence. Read the body and trace the call path. A generic assertRaises that rejects earlier because a prerequisite object is absent does not prove the intended field/branch validation.

If no direct test exists, write NONE. Do not invent a class, function, assertion or line range. If a later remediation test supports an earlier Finding, state the relationship and why it covers the earlier failure mode.

## 4. Work Package B — correct the test inventory coverage labels

The seven-suite declared function counts are already independently confirmed:

| File | Declared test functions |
|---|---:|
| test_r8_r9_r11_pc1.py | 25 |
| test_r12_r17.py | 35 |
| test_r19_r25.py | 38 |
| test_r26_r32.py | 34 |
| test_r33_r38.py | 37 |
| test_r39_r42.py | 26 |
| test_r54_r59.py | 23 |
| **Total** | **218** |

Keep 218 only as a count of declared functions.

Correct the per-file coverage labels:
- R15 explicit dry-run/refusal tests are in test_r12_r17.py, not test_r8_r9_r11_pc1.py.
- R25 gated-runner tests are in test_r19_r25.py.
- R31 gate-semantics tests are in test_r26_r32.py.
- test_r54_r59.py contains R54–R59 remediation tests. Some of those tests may support earlier formal Findings, but it is not direct complete coverage of all R43–R53.
- Distinguish formal Findings R12–R53 from later remediation IDs R54–R61.

## 5. Work Package C — mandatory disposition corrections

Re-evaluate all 42 dispositions against the original acceptance criteria and actual tests. Do not preserve the 30 VERIFIED_FIXED count simply to retain Stage 1E's arithmetic.

At minimum, absent additional exact existing evidence, these must be PARTIALLY_FIXED:

### R24 — cost consistency test

Current COST_BASELINE prose and SMOKE_RAW figures are aligned, but the actual test only:
- checks that the first five characters of the raw wall-clock string appear somewhere in the cost document;
- checks hard-coded counters equal 32, 96, 128 and 112.

It does not parse the cost document and validate that each figure is correctly labelled with its units. Original R24 explicitly requires a test parsing the raw artifact and checking values and units. Keep PARTIALLY_FIXED unless another exact existing test proves this.

### R52 — exact protocol schema semantics

Source in gleppo/pc1.py implements exact key/type checks for reward, estimator and seed schema, including seed version and encoding.

However, current direct tests do not cover the full adversarial acceptance set:
- estimator extra/unknown keys and missing keys;
- seed schema version mutation;
- seed schema encoding mutation;
- all required exact semantic/schema mutation cases.

Existing tests include a wrong estimator horizon, a seed field-list mutation containing action/genotype, and reward strict-type/missing/extra-field mutations. These are not the complete R52 acceptance set. Keep PARTIALLY_FIXED until exact tests exist or an exact existing test is found and mapped.

### R53 — immutable protocol content hash

Source compute_protocol_hash() excludes lifecycle status and approval metadata.

But TestR40ProtocolConsistency.test_mutation_status_not_checked_by_consistency only tests the consistency predicate. It does not call compute_protocol_hash() before/after a status-only mutation. No direct status-only hash-invariance test was found. Keep PARTIALLY_FIXED until an exact direct test exists.

### R18 — manual documentation evidence

R18 may remain VERIFIED_FIXED based on a precise manual comparison:
- SMOKE_RAW totals wall_clock_s = 0.0261;
- COST_BASELINE §2 and §5 report 0.0261 seconds;
- 96 is offspring planned slots;
- 128 is total smoke planned slots;
- 112 is actual uncached replica executions;
- 45,440 is PC1 planned slots, not actual CTX;
- production token/latency/cost remains UNMEASURED.

The older 0.021 figure in the historical review is superseded by the current raw artifact. Record the current source snapshot and exact section/line evidence. The Stage 1E test map's test_smoke_raw_matches function name is wrong; actual function is TestR24CostConsistency.test_smoke_raw_matches_cost_baseline. Do not invent a separate R18 test.

## 6. Work Package D — required gate and parser call-path checks

### D1. R38

Actual tests are in TestR38FailClosedGates:
- test_approval_empty_protocol_hash_denied
- test_approval_empty_expected_hash_denied
- test_approval_empty_approver_denied
- test_approval_empty_date_denied

These instantiate ApprovalGate without TrustedApprovalArtifact and approval_key. ApprovalGate.check() rejects first because the trusted artifact is missing. They do not prove the intended missing-binding checks are reached.

ApprovalGate.expected_protocol_hash is not consumed by ApprovalGate.check(). Trace each test and cite the exact early rejection. Keep R38 PARTIALLY_FIXED.

### D2. R43

The actual gate-level negative test is:
tests/test_r54_r59.py::TestR54ApprovalGate.test_proposed_rejects_all_flags_true

It creates a signed test artifact and confirms rejection while the canonical protocol is PROPOSED. The call rejects at the canonical status check before HMAC verification. It is not a positive approved-path integration test. ApprovalGate.expected_protocol_hash remains unused. Keep R43 PARTIALLY_FIXED and correct its mapping/rationale.

### D3. R45

Source parse_protocol_document() uses _DuplicateKeyChecker. The existing TestR13FailClosed.test_duplicate_key_rejected tests duplicate StateActionRecord keys in validate_records(), not duplicate keys in canonical protocol JSON. If no direct protocol parser duplicate-key test exists, write NONE and keep R45 PARTIALLY_FIXED.

### D4. R49

TestR40ProtocolConsistency.test_mutation_status_not_checked_by_consistency proves status is ignored by protocol_consistency_check(), not that compute_protocol_hash() is invariant to status. Keep R49 PARTIALLY_FIXED.

### D5. R50 and R46

Artifact-level no-signature/wrong-signature tests call TrustedApprovalArtifact.verify() directly. The signed-artifact gate-level negative test rejects at PROPOSED status before HMAC verification. There is no positive approved-path test proving the gate consumes a valid signed artifact.

R46 remains UNVERIFIABLE without independently provisioned/pinned trust-anchor provenance. Do not access or provision a production key.

## 7. Work Package E — correct R24/R52/R53 and all 42 dispositions

Re-evaluate all 42 dispositions against the original acceptance criteria and actual tests. Do not preserve the 30 VERIFIED_FIXED count simply to retain Stage 1E's arithmetic.

Create a corrected single-disposition table with every ID R12–R53 exactly once.

Requirements:
- one primary category per Finding;
- one disposition per Finding;
- disposition counts sum to 42;
- category counts sum to 42;
- no Finding is marked VERIFIED_FIXED merely because source code contains a plausible implementation;
- if original acceptance requires direct behavioral tests and no such test exists, use PARTIALLY_FIXED;
- R15 remains OPEN while execute_registered_pc1() refuses and no collection/rollout runner exists;
- R46 remains UNVERIFIABLE absent independent trust-anchor provenance.

Do not silently edit history. Preserve the Stage 1E Executor report and append the Planner correction. Any revised disposition must include a specific rationale.

## 8. Work Package F — 450/450 evidence and execution boundary

Stage 1E reports:

450/450 — EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED

This is the correct label. No raw stdout/stderr log was committed, and GitHub had no status entries, check runs or Actions run targeting Stage 1E commit 65f83df.

Do not invent a log or claim a fresh run occurred. Stage 1F is a documentation/source audit. No full test rerun is required.

## 9. Required outputs

Create/update:
1. research/R26_STAGE1F_FINAL_FINDING_AUDIT.md — all 42 formal Findings, exact original criteria, exact source symbols/lines, one category and one disposition each.
2. research/R26_STAGE1F_TEST_EVIDENCE.md — exact 42-row test map, file/class/function/line/assertion/call-path evidence, and explicit NONE where no direct test exists.
3. research/R26_STAGE1E_PLANNER_REVIEW.md — preserve Planner review.
4. research/R26_STAGE1E_FINAL_FINDING_AUDIT.md — append Planner corrections; preserve Executor claim.
5. research/R26_STAGE1E_TEST_EVIDENCE.md — append exact corrections; preserve Executor claim.
6. research/R26_PC1_FINDING_REGISTER.md — align disposition state with the corrected audit, preserving formal IDs R12–R53.
7. research/R26_PC1_FINDING_LEVEL_VERIFICATION.md — append Stage 1E Planner review and Stage 1F status.
8. research/R26_PC1_TEST_EVIDENCE.md — append Stage 1E mapping corrections.
9. research/R26_PC1_AUDIT_SUMMARY.md — current status and accurate disposition counts.
10. planner/latest_plan.md.
11. planner/GLEPPO_R26_HANDOFF.md.
12. planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md.
13. status.json.

Do not create empty placeholders. Preserve historical Executor reports and append corrections rather than silently rewriting them.

In status.json:
- Stage 1E Executor result remains historical;
- Stage 1E Planner decision is REQUEST_CHANGES;
- Stage 1F is current task;
- distinguish source snapshot, Stage 1E report commit and current HEAD;
- keep PC1 BLOCKED, Family C NOT ACCESSED, controller training NOT STARTED, Formal G3 FAIL, model/API calls 0.

## 10. Hard prohibitions

- No registered PC1 execution.
- No Family C access: no listing, reading, loading, inspecting, tuning or executing.
- No ECOS/PPO training.
- No Formal G3 efficacy.
- No external model/API calls.
- No production runtime calls.
- No production source changes.
- No test-code changes.
- No production signing-key access or provisioning.
- No changes to frozen R1–R25 raw evidence/manifests.
- No main merge/reset/rebase/force-push/update.
- No cross-project artifact reuse.

## 11. Final report contract

Report:
- starting branch/HEAD and final branch/HEAD;
- Stage 1E source snapshot, report commit and Stage 1F report commit;
- main SHA and ahead/behind;
- worktree state;
- all 42 IDs and exactly one disposition each;
- category and disposition counts summing to 42;
- exact test path/class/function/line/assertion/source-call mapping;
- missing tests and reason for PARTIALLY_FIXED/UNVERIFIABLE;
- corrected R24/R52/R53 dispositions;
- R18 manual documentation evidence;
- 450/450 provenance or explicit lack of it;
- files changed;
- model/API calls = 0;
- registered PC1 = NOT EXECUTED;
- Family C = NOT ACCESSED;
- controller training = NOT STARTED;
- Formal G3 efficacy = NOT EXECUTED;
- production source/test changes = 0.

End with one status:
- R26_STAGE1F_AUDIT_COMPLETE_REQUIRES_PLANNER_REVIEW
- R26_STAGE1F_AUDIT_INCOMPLETE_BLOCKED
- R26_STAGE1F_REF_MISMATCH_STOPPED

**Immediate action:** verify refs; rebuild the exact test map from actual test declarations; re-evaluate R24/R52/R53 and all other dispositions; preserve honest evidence boundaries. Do not modify production source or tests.
