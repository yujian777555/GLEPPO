# GLEPPO R26 Stage 1E — Planner Independent Review

**Review date:** 2026-11-04  
**Repository:** yujian777555/GLEPPO  
**Branch:** r25-handoff  
**Stage 1E report commit:** 65f83dfc7334d674ad1d96539872f71f1ae44303  
**Stage 1E source snapshot / parent:** da3dfefee9a86ff3833a6fa4f9cf0f71fd0b1375  
**R25 base:** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**main at review:** 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e  
**Planner decision:** REQUEST_CHANGES — 42-row accounting accepted; exact test evidence and several dispositions are not accepted  
**PC1:** BLOCKED

---

## 1. Executive decision

Stage 1E fixes the Stage 1D bookkeeping defects:
- all 42 formal IDs R12–R53 are present exactly once;
- R18 is restored as a separate Cost Finding from R24;
- the category table sums to 42 and its listed IDs match the 42-row register;
- the disposition arithmetic 30 + 10 + 1 + 1 = 42 is correct;
- R46 appears only once, as UNVERIFIABLE;
- the 218 declared test-function count across the seven PC1-related test suites is correct;
- the 450/450 result is honestly labelled EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED;
- Stage 1E changed only two reports and status.json; no production source or test code changed.

These are accepted as real improvements.

However, Stage 1E is **not accepted as a completed finding-level audit**. The central deliverable — the 42-row exact test class/function/assertion map — is not accurate. The names in the map do not correspond to the actual test declarations. The map also omits test file paths, line ranges, source symbols/call paths and actual assertion expressions. It is therefore a 42-row table, but not a valid 42-Finding evidence map.

Planner's independent name check against the seven PC1-related suites found:
- 42 map rows;
- only 3 row class names match an actual class declaration (TestR17Evidence once and TestR24CostConsistency twice);
- only 1 of the 42 function names exists in the seven suites (test_init_evaluation), but it belongs to TestR12BudgetLedger, not the claimed TestR12Budget class;
- **0 of 42 class/function pairs match an actual class/function pair**.

The exact map is not a minor formatting defect. It means the report still does not demonstrate which test exercises each Finding's original failure mode.

Correct state:

**R26_STAGE1E_REPORT_RECEIVED_REQUEST_CHANGES; EXACT_TEST_MAP_AND_DISPOSITION_REVIEW_REQUIRED; PC1_BLOCKED.**

## 2. Repository provenance

Verified remote refs:
- r25-handoff HEAD = 65f83dfc7334d674ad1d96539872f71f1ae44303;
- Stage 1E commit parent/source snapshot = da3dfefee9a86ff3833a6fa4f9cf0f71fd0b1375;
- main HEAD = 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e;
- main → Stage 1E: 140 ahead, 0 behind;
- R25 base → Stage 1E: 59 ahead, 0 behind.

Stage 1E commit changed only:
1. research/R26_STAGE1E_FINAL_FINDING_AUDIT.md;
2. research/R26_STAGE1E_TEST_EVIDENCE.md;
3. status.json.

No production source or test file changed.

The Stage 1E audit header says HEAD: da3dfef. That is the source snapshot/parent, not the report commit or current branch HEAD. The next report must distinguish SOURCE_SNAPSHOT, REPORT_COMMIT, and CURRENT_BRANCH_HEAD explicitly.

For Stage 1E commit 65f83df:
- GitHub commit status: pending, zero status entries;
- check runs: zero;
- Actions runs whose head_sha is 65f83df: zero.

This is consistent with the report's claim that the 450/450 result was not independently reproduced. Do not describe the result as CI-verified.

## 3. Accepted Stage 1E bookkeeping corrections

### 3.1 Formal Finding register

The final audit contains 42 rows, R12 through R53 inclusive, with no duplicate IDs in the table. R18 is present and separate from R24.

### 3.2 Category arithmetic

The category counts are internally consistent:

| Category | Count |
|---|---:|
| Budget/CTX | 5 |
| Seed/CRN | 5 |
| Protocol | 9 |
| Approval | 5 |
| Provenance | 9 |
| Runner | 3 |
| Statistics | 2 |
| Evidence | 2 |
| Cost | 2 |
| **Total** | **42** |

The category ID lists correspond to the 42 rows. This corrects the Stage 1D R18 omission and Provenance count error.

### 3.3 Disposition arithmetic

The submitted dispositions sum correctly:

| Disposition | Executor count |
|---|---:|
| VERIFIED_FIXED | 30 |
| PARTIALLY_FIXED | 10 |
| OPEN | 1 |
| UNVERIFIABLE | 1 |
| **Total** | **42** |

R46 appears only as UNVERIFIABLE. R15 remains OPEN. The arithmetic is accepted; the substantive basis for every disposition is not.

### 3.4 Cost documentation / R18

Planner independently inspected the current COST_BASELINE.md and SMOKE_RAW.json:
- raw smoke wall_clock_s = 0.0261;
- cost baseline §2 and §5 report 0.0261 seconds;
- 96 is labelled offspring planned slots, not actual CTX;
- 128 is total smoke planned slots including initialization;
- 112 is actual uncached replica executions;
- 45,440 is labelled PC1 planned slots, not measured actual CTX;
- production token/latency/cost values remain UNMEASURED.

The current 0.0261 raw artifact supersedes the older 0.021 value quoted in the historical R18 review. On the current files, R18's documentation-level correction appears sound and may remain VERIFIED_FIXED if Stage 1F records the exact section/value comparison. The Stage 1E test map is still wrong for R18: the actual test is TestR24CostConsistency.test_smoke_raw_matches_cost_baseline, not test_smoke_raw_matches. R18 is a documentation Finding; do not invent a separate test that does not exist.

R24 is different. Its original acceptance criterion explicitly requires a consistency test that parses the raw artifact and checks the report's values and units. The actual test:
- asserts the first five characters of the raw wall-clock string appear somewhere in COST_BASELINE.md;
- asserts hard-coded raw counters equal 32, 96, 128 and 112.

It does not parse the cost report's units or prove that each number is used under the correct label. The prose currently appears reconciled, but the required semantic consistency test is not demonstrated. R24 must be PARTIALLY_FIXED unless a separate exact test satisfying the original criterion is identified.

## 4. Critical defect: the 42-row test map does not match test declarations

Stage 1E's map contains 42 rows but lists abbreviated or invented test class/function names.

Examples verified against the actual seven PC1-related test files:

| Finding | Stage 1E claim | Actual source evidence |
|---|---|---|
| R12 | TestR12Budget.test_init_evaluation | TestR12BudgetLedger.test_init_evaluation |
| R13 | TestR13Stats.test_validate_records | No such function/class; actual class TestR13FailClosed has test_missing_action_rejected, test_wrong_horizon_rejected, test_nonfinite_reward_rejected, etc. |
| R14 | TestR14Stats.test_sample_role | No such pair; actual class TestR14SampleRoles |
| R15 | TestR15Runner.test_registered_refuses | No such pair; actual class TestR15DryRunPlan.test_registered_execution_refused |
| R16 | TestR16CRN.test_same_crn_tuple | No such pair; actual TestR16SeedContract.test_same_crn_identical_across_genotypes |
| R17 | TestR17Evidence.test_replayable | Class exists, function does not; actual tests include test_evidence_contains_provenance and test_evidence_records_have_required_fields |
| R18/R24 | TestR24CostConsistency.test_smoke_raw_matches | Actual function is test_smoke_raw_matches_cost_baseline |
| R19 | TestR19Protocol.test_consistency_check | Actual TestR19ProtocolFreeze.test_consistency_check_passes |
| R21 | TestR21Budget.test_negative_rejected | Actual TestR21BudgetFailClosed.test_negative_total_rejected and other specific rejection tests |
| R26 | TestR26Protocol.test_canonical_doc | Actual TestR26ProtocolDocument.test_protocol_document_exists and test_document_fields_match_code |
| R36 | TestR36Protocol.test_field_validation | Actual TestR36ProtocolConsistency has explicit mutation tests |
| R38 | TestR38Approval.test_missing_binding | Actual TestR38FailClosedGates has test_approval_empty_protocol_hash_denied etc. |
| R43 | TestR43Approval.test_proposed_rejects | Actual TestR54ApprovalGate.test_proposed_rejects_all_flags_true and TestR31GateSemantics.test_all_booleans_true_still_denied_for_proposed_protocol |
| R45 | TestR45Protocol.test_duplicate_keys | No direct duplicate-canonical-protocol-JSON-key test exists in the seven suites |
| R49 | TestR49Protocol.test_lifecycle_separate | Actual TestR40ProtocolConsistency.test_mutation_status_not_checked_by_consistency; this tests consistency, not hash invariance |
| R52 | TestR52Protocol.test_seed_schema | No such test; current tests cover only selected reward/estimator/seed mutations |
| R53 | TestR53Protocol.test_hash_excludes | No such test; no direct status-only protocol-hash invariance test exists |

The Stage 1E assertion column contains descriptions such as "Budget accounting", "Seed correctness", "Lifecycle separate" and "Hash excludes status". These are not actual assertion expressions or assertion line references.

The Stage 1E test map also omits:
- test file path for each Finding;
- exact line range;
- exact source function/symbol and line range;
- original failure mode and full acceptance criterion;
- the call path from the test into the intended source branch;
- the actual assertion expression and whether the test reaches that branch.

A row count of 42 does not make this a valid test map.

## 5. Test-file inventory is arithmetically correct but its coverage labels are imprecise

The declared test-function counts are correct:

| File | Functions |
|---|---:|
| test_r8_r9_r11_pc1.py | 25 |
| test_r12_r17.py | 35 |
| test_r19_r25.py | 38 |
| test_r26_r32.py | 34 |
| test_r33_r38.py | 37 |
| test_r39_r42.py | 26 |
| test_r54_r59.py | 23 |
| **Total** | **218** |

But the coverage column overstates or misattributes some files:
- test_r8_r9_r11_pc1.py contains R8/R9/R11 suites and TestPC1RunnerSynthetic; the explicit R15 tests are in test_r12_r17.py, R25 tests in test_r19_r25.py, and R31 tests in test_r26_r32.py.
- test_r54_r59.py is organized around R54–R59 remediation tests. It contains useful tests relevant to some older findings, such as the R43 proposed-status rejection and R50 artifact verification, but it does not provide one direct test for every R43–R53 Finding. Do not label the whole file as complete coverage of R43–R53.
- A later remediation test may support an earlier formal Finding, but the evidence map must explain the exact link to that Finding's original failure mode.

The number 218 is accepted only as the count of declared functions in these seven files, not as 218 independent Finding-level proofs.

## 6. Substantive disposition corrections required

### 6.1 R24 — downgrade from VERIFIED_FIXED

The prose is currently aligned with SMOKE_RAW, but the actual test does not parse/validate units and labels as required by the original R24 acceptance criterion. No other exact test was identified. Set R24 to PARTIALLY_FIXED unless new existing evidence satisfies the full criterion. Stage 1F is documentation-only; do not add tests in that stage.

### 6.2 R52 — downgrade from VERIFIED_FIXED

Current source in pc1.py implements exact key/type checks for reward, estimator and seed schema, including seed version and encoding. This is a meaningful source remediation.

However, existing direct tests in the seven suites do not cover the full original adversarial acceptance set:
- estimator extra/unknown keys and missing keys;
- seed schema version mutation;
- seed schema encoding mutation;
- all required exact semantic/schema mutation cases.

The current estimator mutation test changes horizon; the current seed mutation test changes fields to include action/genotype; the strict-type tests focus on reward fields. The Stage 1E map's test_seed_schema does not exist.

R52 must be PARTIALLY_FIXED until the missing direct tests are implemented and verified, or a previously existing exact test is found and mapped.

### 6.3 R53 — downgrade from VERIFIED_FIXED

Current compute_protocol_hash() filters lifecycle fields, including status, from the hashed payload. This is a source-level implementation change.

But no direct test proves that changing only status leaves compute_protocol_hash() unchanged. TestR40ProtocolConsistency.test_mutation_status_not_checked_by_consistency checks only protocol_consistency_check(), not the hash. The Stage 1E map's test_hash_excludes does not exist.

R53 must be PARTIALLY_FIXED until a direct hash-invariance test exists and passes, or an exact existing test is identified.

### 6.4 R43 — correct the map and rationale

A real gate-level negative test exists:
tests/test_r54_r59.py::TestR54ApprovalGate.test_proposed_rejects_all_flags_true

It creates a signed test artifact and confirms the gate rejects while the canonical protocol is PROPOSED. The rejection occurs at the canonical PROPOSED status check before the HMAC verification call. It is evidence for default-deny while PROPOSED, not a positive approved-path integration test.

ApprovalGate.expected_protocol_hash is still stored but not consumed by ApprovalGate.check(). Keep R43 PARTIALLY_FIXED, but cite the actual test and explain the path it exercises.

### 6.5 R38 — current negative tests do not prove all intended binding checks

The R38 tests in TestR38FailClosedGates instantiate ApprovalGate without a TrustedApprovalArtifact and approval_key. ApprovalGate.check() rejects first because the artifact is absent. These tests do not independently prove that the intended missing protocol-hash, expected-hash, approver or date checks reject at their intended validation branch.

In addition, ApprovalGate.check() does not consume expected_protocol_hash and does not directly validate the gate's approver/date fields. Keep R38 PARTIALLY_FIXED and correct the test map.

### 6.6 R45 — source implementation is not direct protocol duplicate-key test evidence

parse_protocol_document() uses _DuplicateKeyChecker, but test_r12_r17.py::TestR13FailClosed.test_duplicate_key_rejected tests duplicate StateActionRecord keys in validate_records(). It does not test duplicate keys in the canonical protocol JSON document. No direct protocol parser mutation test was found in the seven suites. Keep R45 PARTIALLY_FIXED.

### 6.7 R49 — consistency test is not content-hash invariance test

TestR40ProtocolConsistency.test_mutation_status_not_checked_by_consistency proves status is ignored by the consistency predicate. It does not prove compute_protocol_hash() is unchanged by a status-only mutation. Keep R49 PARTIALLY_FIXED.

### 6.8 R50 and R46 — artifact mechanics versus trusted approval

Artifact-level no-signature/wrong-signature tests call TrustedApprovalArtifact.verify() directly. The gate-level signed-artifact negative test rejects because the canonical status is PROPOSED before HMAC verification. No positive approved-path integration test demonstrates ApprovalGate.check() consuming a valid signed artifact.

R46 remains UNVERIFIABLE without independently provisioned/pinned trust-anchor provenance. Do not infer trust from the static test key.

## 7. Test execution evidence

Stage 1E correctly labels the 450/450 claim:

**450/450 — EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED**

For commit 65f83df:
- status entries = 0;
- check runs = 0;
- Actions runs targeting the commit = 0.

No raw stdout/stderr log was added. Do not claim independent reproduction. Stage 1F is a documentation/source-audit stage; it does not need to rerun the suite.

## 8. Planner disposition

**Stage 1E is partially accepted but not accepted as a completed finding-level audit.**

Accepted:
- 42 formal IDs R12–R53 present exactly once;
- category arithmetic correct;
- disposition arithmetic correct as submitted;
- R18 restored separately from R24;
- R46 has one disposition, UNVERIFIABLE;
- 218 declared test-function count correct;
- 450/450 honestly marked not independently reproduced;
- no production source/test code changed.

Not accepted:
- 42-row exact test map;
- test class/function names that do not exist;
- generic assertion descriptions presented as exact assertions;
- missing per-Finding test paths, line ranges, source symbols and call-path analysis;
- inaccurate test-file coverage labels;
- R24 VERIFIED_FIXED;
- R52 VERIFIED_FIXED;
- R53 VERIFIED_FIXED.

At minimum, R24, R52 and R53 must be PARTIALLY_FIXED absent new exact evidence. R18 may remain VERIFIED_FIXED if Stage 1F records the manual comparison to the current raw artifact and all relevant COST_BASELINE sections.

**Planner status:** R26_STAGE1E_REPORT_RECEIVED_REQUEST_CHANGES; EXACT_TEST_MAP_AND_DISPOSITION_REVIEW_REQUIRED; PC1_BLOCKED.

## 9. Next task — R26 Stage 1F

Read planner/GLEPPO_R26_STAGE1F_EXECUTOR_PROMPT.md.

Stage 1F is a read-only evidence reconstruction and report correction stage. Do not modify production source or test code. Replace invented/abbreviated class/function names with exact existing test declarations, or write NONE. Rebuild the evidence map for all 42 findings, inspect each test body and call path, correct test inventory coverage labels, and re-evaluate dispositions. Do not preserve 30 VERIFIED_FIXED merely to keep the old total.

## 10. Hard boundaries

No registered PC1 execution. No Family C access. No ECOS/PPO training. No Formal G3 efficacy. No external model/API calls. No production runtime calls. No production source changes. No test-code changes. No production signing-key access/provisioning. No changes to frozen R1–R25 raw evidence/manifests. No merge/reset/rebase/force-push or update of main.

**Final decision:** REQUEST CHANGES. Stage 1E fixes the 42-row bookkeeping, but the exact test evidence map and several dispositions remain unsupported.
