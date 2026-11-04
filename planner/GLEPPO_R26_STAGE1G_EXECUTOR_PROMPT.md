# GLEPPO R26 Stage 1G — Disposition Count and Exact Test Map Reconciliation

**Role:** Executor under Planner review  
**Project:** GLEPPO only  
**Repository:** yujian777555/GLEPPO  
**Required branch:** r25-handoff  
**Stage 1F Executor commit:** 1a29d1cc722d3cc20491310c896d204b8290c625  
**Stage 1F commit parent / source snapshot candidate:** 29325cfa16441154c833f381f208747b57627a79  
**Stage 1F Planner review:** research/R26_STAGE1F_PLANNER_REVIEW.md  
**R25 base:** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**Stage:** R26_STAGE1G_DISPOSITION_AND_EXACT_TEST_MAP_RECONCILIATION  
**Task type:** documentation-only evidence correction  
**Authorization:** no production source changes; no test-code changes; no registered experiment.

---

## 1. Planner decision — Stage 1F REQUEST_CHANGES

Read the complete Planner review:

research/R26_STAGE1F_PLANNER_REVIEW.md

Stage 1F improved the audit, but did not complete the required evidence reconciliation.

Accepted:
- all 42 formal IDs R12–R53 are present exactly once;
- category counts sum to 42;
- R18 is NONE for a behavioral test and has manual documentation evidence;
- R24, R45, R52 and R53 are PARTIALLY_FIXED;
- R15 is OPEN and R46 is UNVERIFIABLE;
- 218 declared test-function count is correct;
- 450/450 is correctly marked not independently reproduced;
- no production source or test code changed.

Blocking defects:
1. Detailed Stage 1F rows actually count 27 VERIFIED_FIXED, 13 PARTIALLY_FIXED, 1 OPEN and 1 UNVERIFIABLE. The count summary, status.json and commit message say 22/15/1/1, which sums to 39. The ID lists in the summary contain 27 verified IDs and 13 partial IDs.
2. Of the 39 rows that claim a test, 39 class names exist in their stated files, but only 5 function names exist in the stated class/file. The other 34 claimed function names are not declared there. Only 5/42 rows are exact file/class/function matches.
3. scripts/_r26f_extract_tests.py inventories declarations but does not compare the 42-row table with those declarations, inspect assertions, or validate call paths.
4. R26_STAGE1F_TEST_EVIDENCE.md does not contain the requested 42-row evidence map with line numbers, assertions and source call paths.
5. Stage 1F report metadata labels the parent commit 29325cf as HEAD. Distinguish source snapshot/parent, report commit and current branch HEAD.

Current Planner state:

**R26_STAGE1F_REPORT_RECEIVED_REQUEST_CHANGES; DISPOSITION_COUNT_AND_EXACT_TEST_MAP_RECONCILIATION_REQUIRED; PC1 BLOCKED.**

## 2. Repository recovery and provenance

Before editing:
1. Verify branch r25-handoff and current HEAD.
2. Verify ancestry includes R25 base a8ff1827434a88b2fef02a89aaf3e120e0a017a7 and Stage 1F report commit 1a29d1cc722d3cc20491310c896d204b8290c625.
3. Record current branch HEAD, main SHA, ahead/behind counts and latest commit.
4. Distinguish SOURCE_SNAPSHOT_OR_PARENT, REPORT_COMMIT and CURRENT_BRANCH_HEAD.
5. If refs differ unexpectedly, stop and report the exact mismatch.
6. Continue only on r25-handoff. Do not merge/update main.

Planner last verified:
- r25-handoff = 1a29d1cc722d3cc20491310c896d204b8290c625;
- Stage 1F parent = 29325cfa16441154c833f381f208747b57627a79;
- main = 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e;
- main → Stage 1F: 154 ahead, 0 behind;
- R25 base → Stage 1F: 73 ahead, 0 behind.

## 3. Work Package A — reconcile all 42 dispositions

The Stage 1F detailed table has 42 unique IDs R12–R53. Recount the disposition directly from those 42 rows.

Current detailed-row recount:
- VERIFIED_FIXED = 27;
- PARTIALLY_FIXED = 13;
- OPEN = 1;
- UNVERIFIABLE = 1;
- total = 42.

Stage 1F summary/status/commit message says 22/15/1/1 = 39, which is wrong.

Do not mechanically change 22/15 to 27/13 without reviewing the evidence. For every Finding:
1. retain the exact original ID;
2. preserve one primary category;
3. use exactly one disposition;
4. cite the original failure mode and acceptance criterion;
5. assess whether the mapped test actually proves that criterion;
6. downgrade if only partial behavior is demonstrated;
7. use NONE if no direct test exists;
8. explain the rationale.

The corrected detailed table, disposition counts and ID lists must agree exactly. Category counts must still sum to 42.

At minimum:
- R24 remains PARTIALLY_FIXED;
- R45 remains PARTIALLY_FIXED;
- R52 remains PARTIALLY_FIXED;
- R53 remains PARTIALLY_FIXED;
- R15 remains OPEN while execute_registered_pc1() refuses registered execution and no collection/rollout runner exists;
- R46 remains UNVERIFIABLE without independent trusted-key provenance;
- R18 may remain VERIFIED_FIXED on manual documentation evidence, with exact raw/document lines.

Re-evaluate every other VERIFIED_FIXED item rather than assuming the current classification is correct.

## 4. Work Package B — rebuild the 42-row test evidence map

Inspect these exact test files at the verified Stage 1G source snapshot:
- tests/test_r8_r9_r11_pc1.py
- tests/test_r12_r17.py
- tests/test_r19_r25.py
- tests/test_r26_r32.py
- tests/test_r33_r38.py
- tests/test_r39_r42.py
- tests/test_r54_r59.py

The Stage 1F audit lists 39 test mappings, but only these five file/class/function pairs currently match actual declarations:
1. R12 — test_r12_r17.py / TestR12BudgetLedger / test_init_evaluation (line 37);
2. R24 — test_r19_r25.py / TestR24CostConsistency / test_smoke_raw_matches_cost_baseline (line 343);
3. R38 — test_r33_r38.py / TestR38FailClosedGates / test_approval_empty_protocol_hash_denied (line 369);
4. R42 — test_r54_r59.py / TestR54ApprovalGate / test_no_signature_rejected (line 89);
5. R43 — test_r54_r59.py / TestR54ApprovalGate / test_proposed_rejects_all_flags_true (line 69).

The following 34 mapped function names in Stage 1F are not declared in the stated class/file:
R13, R14, R15, R16, R17, R19, R20, R21, R22, R23, R25, R26, R27, R28, R29, R30, R31, R32, R33, R34, R35, R36, R37, R39, R40, R41, R44, R47, R48, R49, R50, R51, R52, R53.

For every R12–R53 Finding, record:
1. exact original Finding heading and original review file;
2. original failure mode and full acceptance criterion;
3. exact test file path, or NONE;
4. exact test class declaration, or NONE;
5. exact test function declaration, or NONE;
6. exact start/end line range for the test;
7. exact assertion expression(s) and line range;
8. source symbol/function reached by the test;
9. source line range for the symbol;
10. call path from test to source;
11. whether the test reaches the intended validation/behavior branch or fails earlier;
12. which acceptance conditions are proven;
13. which acceptance conditions remain uncovered;
14. disposition and rationale.

A class name existing is not proof that the claimed function exists. A function name existing in another class or file is not a valid match. Do not use abbreviated names.

If a class contains several tests relevant to one Finding, list each exact test and explain the specific evidence it contributes. If a single test supports multiple Findings, justify the reuse against each original acceptance criterion. Do not duplicate one test indiscriminately across Findings.

If no direct test exists, write NONE. Do not invent function names or line numbers.

## 5. Work Package C — semantic review of exact matches

Even the five exact Stage 1F pairs do not automatically prove the full Finding:

### R12
test_init_evaluation asserts initial ledger counters. Inspect the other methods in TestR12BudgetLedger for cache bundle hits and planned-versus-actual counter separation. State which subcriteria each method covers.

### R24
test_smoke_raw_matches_cost_baseline checks that a wall-clock substring appears somewhere in the cost document and checks hard-coded raw counters. It does not parse cost-report labels/units. Keep PARTIALLY_FIXED.

### R38
test_approval_empty_protocol_hash_denied creates ApprovalGate without a TrustedApprovalArtifact or approval_key. ApprovalGate.check() rejects first because the trusted artifact is absent. This does not prove the intended protocol-hash validation branch. Keep PARTIALLY_FIXED.

### R42
test_no_signature_rejected calls TrustedApprovalArtifact.verify() directly. It is an artifact-level test, not proof of the full ApprovalGate integration or trusted-key provenance.

### R43
test_proposed_rejects_all_flags_true supplies a signed test artifact, but the gate rejects because canonical protocol status is PROPOSED before HMAC verification. It proves default-deny while PROPOSED, not a valid APPROVED-path integration.

## 6. Work Package D — R18 manual evidence

R18 has no behavioral test. Keep test mapping NONE.

The current source artifact comparison is:
- SMOKE_RAW totals.wall_clock_s = 0.0261;
- COST_BASELINE §2 and §5 report 0.0261 seconds;
- planned_init_slots = 32;
- planned_offspring_slots = 96;
- planned_total_slots = 128;
- actual_replicas_run = 112;
- PC1 planned slots = 45,440;
- production LLM tokens/latency/cost remain UNMEASURED;
- raw units note distinguishes planned slots from actual CTX.

Record exact line references in SMOKE_RAW.json and COST_BASELINE.md. State clearly that this is manual artifact reconciliation, not test coverage. Do not claim measured production cost.

## 7. Work Package E — correct the extractor/evidence claims

scripts/_r26f_extract_tests.py is only an inventory helper:
- it scans class declarations;
- scans test method declarations;
- counts methods;
- prints only the first three methods per file;
- it does not parse or validate the 42-row table;
- it does not inspect assertion bodies or source calls.

Do not describe it as a test-map validator.

The 218 count is accepted as a declared-method inventory only. It is not 218 independent tests of the 42 findings.

The test-evidence document must include the complete 42-row evidence map, not only a file/class inventory. Preserve 450/450 as EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED. No fresh full test run is authorized or required in Stage 1G.

## 8. Required outputs

Create/update:
1. research/R26_STAGE1G_FINAL_FINDING_AUDIT.md — corrected 42-Finding table, original acceptance criteria, exact evidence and one disposition per Finding.
2. research/R26_STAGE1G_TEST_EVIDENCE.md — complete exact 42-row test map with file/class/function/line/assertion/source-call evidence and NONE where appropriate.
3. research/R26_STAGE1F_PLANNER_REVIEW.md — preserve Planner review.
4. research/R26_STAGE1F_FINAL_FINDING_AUDIT.md — append Planner corrections; preserve Executor report.
5. research/R26_STAGE1F_TEST_EVIDENCE.md — append Planner corrections; preserve Executor report.
6. research/R26_PC1_FINDING_REGISTER.md — reconcile current evidence-backed dispositions.
7. research/R26_PC1_FINDING_LEVEL_VERIFICATION.md — append Stage 1F Planner decision and Stage 1G status.
8. research/R26_PC1_TEST_EVIDENCE.md — append Stage 1F corrections and exact map status.
9. research/R26_PC1_AUDIT_SUMMARY.md — current disposition arithmetic and Planner state.
10. planner/latest_plan.md.
11. planner/GLEPPO_R26_HANDOFF.md.
12. planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md.
13. status.json.

Do not create empty placeholders. Preserve historical Executor reports and append Planner corrections rather than silently rewriting prior claims.

In status.json:
- Stage 1F Executor result remains historical;
- Stage 1F Planner decision is REQUEST_CHANGES;
- Stage 1G is current task;
- distinguish source snapshot/parent, Stage 1F report commit and current HEAD;
- disposition counts must be derived from the corrected 42-row table;
- PC1 remains BLOCKED;
- Family C remains NOT ACCESSED;
- controller training remains NOT STARTED;
- Formal G3 remains FAIL;
- model/API calls remain 0.

## 9. Hard prohibitions

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

## 10. Final report contract

Report:
- starting branch/HEAD and final branch/HEAD;
- Stage 1F parent/source snapshot, Stage 1F report commit and Stage 1G report commit;
- main SHA and ahead/behind;
- all 42 IDs and exactly one disposition each;
- category and disposition counts summing to 42;
- exact test path/class/function/line/assertion/source-call mapping;
- the 34 Stage 1F mismatches and their exact corrected mappings or NONE;
- missing tests and reasons for PARTIALLY_FIXED/UNVERIFIABLE;
- R18 manual documentation line references;
- 450/450 provenance or explicit lack of it;
- files changed;
- model/API calls = 0;
- registered PC1 = NOT EXECUTED;
- Family C = NOT ACCESSED;
- controller training = NOT STARTED;
- Formal G3 efficacy = NOT EXECUTED;
- production source/test changes = 0.

End with one status:
- R26_STAGE1G_AUDIT_COMPLETE_REQUIRES_PLANNER_REVIEW
- R26_STAGE1G_AUDIT_INCOMPLETE_BLOCKED
- R26_STAGE1G_REF_MISMATCH_STOPPED

**Immediate action:** verify refs; correct the disposition arithmetic; replace all 34 non-existent test names with exact declarations; provide assertions, line ranges and source call paths; update the repository handoff. Do not modify production source or tests.
