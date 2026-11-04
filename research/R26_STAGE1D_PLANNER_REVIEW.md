# GLEPPO R26 Stage 1D — Planner Independent Review

**Review date:** 2026-11-04  
**Repository:** yujian777555/GLEPPO  
**Branch:** r25-handoff  
**Stage 1D report commit:** ca0c9098b83a44229bbedaf5f478ae09d7c16db1  
**Stage 1D source snapshot / parent:** 8f77b361491cc2ab202bf7261425a03b08f903e5  
**R25 base:** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**main at review:** 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e  
**Planner decision:** REQUEST_CHANGES — Stage 1D evidence and disposition ledger remain inconsistent  
**PC1:** BLOCKED

---

## 1. Executive decision

Planner does **not** accept the Stage 1D result as a completed 42-finding audit.

Stage 1D made meaningful improvements over Stage 1C:
- it selected the correct PC1-related test suites rather than mapping PC1 findings to test_c7.py;
- it correctly identified R15 as OPEN;
- it recognized the lack of independent approval-key provenance for R46;
- it identified R36 as only partially fixed;
- it retained the no-PC1/no-Family-C/no-training boundary.

However, the submitted audit still fails its own 42-row accounting, repeats R46 across dispositions, omits formal finding R18, has a provenance category count mismatch, and does not provide the promised exact test-function/assertion map for all findings. The 450/450 result is still not independently evidenced by a saved log or CI run on the Stage 1D commit.

Correct state:

**R26_STAGE1D_REPORT_RECEIVED_REQUEST_CHANGES; FINDING_LEDGER_AND_TEST_EVIDENCE_RECONCILIATION_REQUIRED; PC1_BLOCKED.**

This is not a rejection of all 30+ source remediations. It is a rejection of the submitted aggregate counts and of the claim that the required finding-level evidence package is complete.

## 2. Repository provenance

Verified remote refs:
- r25-handoff HEAD = ca0c9098b83a44229bbedaf5f478ae09d7c16db1;
- Stage 1D commit parent = 8f77b361491cc2ab202bf7261425a03b08f903e5;
- main HEAD = 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e;
- main → Stage 1D: 124 commits ahead, 0 behind;
- R25 base → Stage 1D: 43 commits ahead, 0 behind.

Stage 1D commit changed only:
1. research/R26_STAGE1D_CORRECTED_FINDING_AUDIT.md;
2. research/R26_STAGE1D_TEST_EVIDENCE.md;
3. scripts/_r26d_test_inspect.py;
4. status.json.

The audit report says HEAD: 8f77b36, which is the Stage 1D commit's parent/source snapshot. The current branch HEAD is ca0c909.... The report must label these separately as source snapshot, report commit and current branch HEAD.

No production source or test code was changed in Stage 1D. No planner handoff, latest_plan, next-session prompt, R26_PC1_AUDIT_SUMMARY, historical Stage 1C correction, or raw test log was updated in the Stage 1D commit, despite the prior Stage 1D Executor prompt requiring those outputs.

Continue only on r25-handoff. Do not merge or update main.

## 3. Critical defect: formal Finding R18 is missing

R18 is a formal finding in research/THIRD_REVIEW_FINDINGS.md:

**R18 — Cost baseline still contains contradictory old values.**

It is also present in research/R26_PC1_FINDING_REGISTER.md as a formal Finding in the R12–R53 set.

The Stage 1D corrected category table omits R18 and says:

> R18 was previously listed under Cost but is actually a Cost baseline issue. R24 is the primary Cost finding.

That is not a valid reason to remove a formal Finding from the 42-row register. R18 remains a numbered, formal issue even if its remediation overlaps with R24.

Current artifacts show meaningful remediation:
- research/SMOKE_RAW.json totals report wall_clock_s = 0.0261, planned_init_slots = 32, planned_offspring_slots = 96, planned_total_slots = 128, actual_replicas_run = 112.
- research/COST_BASELINE.md currently reports 0.0261 seconds, 96 offspring planned slots, 128 total planned slots, 112 actual replicas, and 45,440 PC1 planned slots.
- tests/test_r19_r25.py::TestR24CostConsistency::test_smoke_raw_matches_cost_baseline checks the raw wall-clock value is present and asserts the 32/96/128/112 slot/counter values.

Planner's provisional assessment is that R18 appears remediated and should be restored as a separate row, likely VERIFIED_FIXED if the Executor confirms the entire historical contradiction is removed. R24 remains a separate cost consistency Finding. Do not merge or delete either ID.

## 4. Critical defect: category and disposition arithmetic do not reconcile

### 4.1 Category table

The Stage 1D table lists these unique ID memberships:

| Category | IDs actually listed | Listed count |
|---|---:|---:|
| Budget/CTX | 5 | 5 |
| Seed/CRN | 5 | 5 |
| Protocol | 9 | 9 |
| Approval | 5 | 5 |
| Provenance | 9 | 7 |
| Runner | 3 | 3 |
| Statistics | 2 | 2 |
| Evidence | 2 | 2 |
| Cost | 1 | 1 |

The Provenance row lists R22, R29, R30, R35, R37, R41, R44, R47 and R51: nine IDs, not seven.

The listed ID memberships total 41 unique IDs because R18 is missing. Once R18 is restored to Cost, the natural one-primary-category reconciliation is:

- Budget/CTX: 5
- Seed/CRN: 5
- Protocol: 9
- Approval: 5
- Provenance: 9
- Runner: 3
- Statistics: 2
- Evidence: 2
- Cost: 2 (R18 and R24)

Total = 42.

If the Executor believes a different primary category is correct, it must identify exactly which Finding IDs are moved and why. Do not change counts while leaving the ID list unchanged.

### 4.2 Disposition table versus summary

The Stage 1D summary claims:
- VERIFIED_FIXED 30
- PARTIALLY_FIXED 8
- OPEN 1
- UNVERIFIABLE 1
- total 42.

These values sum to 40, not 42.

Counting the actual per-Finding rows in the report as written yields:
- VERIFIED_FIXED: 32
- PARTIALLY_FIXED: 7
- OPEN: 1
- UNVERIFIABLE: 1
- unique IDs shown: 41

This is a row-level recount of the submitted category tables, not Planner acceptance of those dispositions.

R46 is also listed in the commit summary's PARTIALLY_FIXED list and in the audit table as UNVERIFIABLE. A formal Finding must have exactly one primary disposition. R46 must be UNVERIFIABLE only unless new independent trust-anchor provenance evidence is supplied; do not count it in both categories.

The final corrected disposition table must contain each integer ID R12 through R53 exactly once and have disposition counts that sum to 42.

## 5. Test evidence is improved but still incomplete

### 5.1 The seven-suite count is reproducible from source inspection

Planner independently counted the declared test functions in the seven named files:

| Test file | Test functions |
|---|---:|
| test_r8_r9_r11_pc1.py | 25 |
| test_r12_r17.py | 35 |
| test_r19_r25.py | 38 |
| test_r26_r32.py | 34 |
| test_r33_r38.py | 37 |
| test_r39_r42.py | 26 |
| test_r54_r59.py | 23 |
| **Total** | **218** |

The arithmetic 218 is correct as a count of declared test functions across these seven PC1-related suites. It should not be described as 218 individually proven PC1 Finding tests without a per-function mapping.

### 5.2 The submitted per-Finding map is not exact or complete

research/R26_STAGE1D_TEST_EVIDENCE.md gives a per-Finding map for only five findings (R12, R13, R16, R19 and R43), not all 42.

Several listed function names are abbreviations or do not exist:
- R12 lists test_cache_bundle_hit; actual function is test_cache_bundle_hit_adds_zero_replicas.
- R13 lists test_validate_records; no such test function exists. Relevant functions include test_missing_action_rejected, test_wrong_horizon_rejected, test_nonfinite_reward_rejected, test_cluster_conflict_rejected, test_duplicate_key_rejected, test_invalid_action_rejected, test_invalid_role_rejected, test_registered_shape_requires_100_states, test_extra_immediate_wrong_length_rejected, and test_no_default_zeros_for_missing_actions.
- R16 lists test_same_crn_tuple; actual function in test_r8_r9_r11_pc1.py is test_same_crn_tuple_gives_identical_seeds_across_genotypes.
- R19 lists test_consistency_check; actual function is test_consistency_check_passes.
- R43 lists test_proposed_rejects; actual function is test_proposed_rejects_all_flags_true.

Every mapping must use the exact test class/function name, line range, called source function, assertion and original failure mode. Test-file names or abbreviated function names are insufficient.

### 5.3 The inspection helper does not verify semantic coverage

scripts/_r26d_test_inspect.py:
- extracts def test_ names by regex;
- collects import lines;
- checks whether imports contain pc1 or evaluator;
- prints counts and the first five function names.

It does not inspect test bodies, assertions, actual calls, historical failure modes, or test execution. It cannot substantiate 42 finding-level dispositions.

### 5.4 Specific test-coverage gaps found

**R36:** The existing mutation tests cover n_states, gamma, budget total, threshold D and estimator horizon. They do not cover every historical decision-critical field listed in the original R36 acceptance criterion, such as all budget components, cluster unit, threshold margins, reward identity, seed contract and complete version/lifecycle semantics. PARTIALLY_FIXED is appropriate unless additional exact tests are cited.

**R43:** The report says a gate-level test is needed, but the actual gate-level test tests/test_r54_r59.py::TestR54ApprovalGate::test_proposed_rejects_all_flags_true exists. It constructs a signed test artifact using the exact current protocol hash and asserts that the gate refuses while the canonical protocol remains PROPOSED. The rationale must be corrected. However, ApprovalGate.expected_protocol_hash is still not used by ApprovalGate.check(), and no positive approved-path integration test is present. PARTIALLY_FIXED may remain, but not for the stated reason.

**R45:** The source parser uses _DuplicateKeyChecker, but the seven suites contain no direct test proving duplicate keys in the canonical protocol JSON block are rejected. A test_duplicate_key_rejected for state/action records is not the same failure mode. Source implementation exists; test-level proof is missing.

**R48/R52:** The source contains exact reward/estimator/seed schema checks. Existing tests cover some reward type/missing/extra-field cases, estimator horizon mutation and seed field-list mutation. The inspected suites do not provide the full required mutation coverage for extra estimator keys and seed schema version/encoding. Do not claim complete test-backed semantic validation without these exact cases.

**R49/R53:** compute_protocol_hash() now excludes lifecycle fields, including status, in source code. However, test_mutation_status_not_checked_by_consistency tests only that the consistency predicate ignores status; it does not prove that changing only status leaves the content hash unchanged. No direct status-only hash invariance test was found in the seven suites. The Stage 1D mapping of R49 to test_wrong_doc_id_rejected is not relevant to lifecycle hash separation.

**R38:** Several tests assert only that ApprovalGate.check() raises. They construct gates without a trusted artifact/key, so the call fails earlier on missing trusted_artifact; those tests do not prove that the intended missing hash/approver/date checks themselves reject. In addition, expected_protocol_hash is currently not consumed by the gate.

**R50:** Artifact-level tests prove missing/wrong HMAC signatures are rejected by TrustedApprovalArtifact.verify(). The gate-level test with a signed artifact exits at the canonical PROPOSED status check before reaching HMAC verification. No test demonstrates a successful, approved-path gate consuming a valid signed artifact. Keep R50 partial pending a safe test seam and independent trust-anchor proof.

**R46:** UNVERIFIABLE is correct absent an independently provisioned/pinned trust anchor and evidence of approval-source provenance. The static test key proves HMAC mechanics only.

### 5.5 450/450 is not independently reproduced by Planner

The Stage 1D evidence file states python -m unittest discover -s tests = 450/450 PASS, exit code 0, but contains no raw stdout/stderr, saved log, environment details or CI run URL.

For Stage 1D commit ca0c909..., GitHub returned:
- commit status state pending, total statuses 0;
- check runs total 0;
- no Actions workflow run with head_sha == ca0c909....

The latest listed Actions runs are from 2026-11-02 and do not target the Stage 1D commit; the newest listed run at SHA 90f964a... concluded failure. This does not prove the Executor did not run tests locally. It means Planner cannot independently reproduce or audit the claimed result from committed evidence.

Correct label:

450/450 — EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED.

Do not state reproducible without the exact raw output and a saved, attributable run log.

## 6. Other source-level corrections

### 6.1 R18 and R24 are separate formal findings

R18 concerns contradictory historical cost figures/units. R24 concerns consistency between raw smoke artifact and cost baseline. The current test_smoke_raw_matches_cost_baseline test is relevant to both, but each Finding needs its own row and acceptance rationale.

### 6.2 R43 rationale must reflect the test that exists

The exact test test_proposed_rejects_all_flags_true is a gate-level test. The remaining limitation is not absence of a gate-level test; it is lack of a positive approved-path test and the unused gate-level expected_protocol_hash field. Do not erase the real test.

### 6.3 Keep the runner distinction

- execute_registered_pc1() still refuses.
- SyntheticGateHarness is a gate/accounting harness, not a collection/rollout runner.
- R15 remains OPEN.
- R25 and R31 must remain separate and be assessed against their own wording/downgrade alternatives.
- PC1 remains BLOCKED.

## 7. Planner disposition

Stage 1D is accepted as a meaningful correction over Stage 1C, but **not accepted as a complete 42-finding audit**.

Accepted:
- correct PC1-related test suites were identified;
- the 218 declared test-function count is arithmetically correct;
- R15 remains OPEN;
- R46 lacks independent trust-anchor provenance;
- R36 is not fully fixed;
- registered PC1 remains fail-closed;
- no production source/test code changed.

Not accepted:
- 30/8/1/1 disposition totals;
- omission of R18;
- Provenance count 7 while nine IDs are listed;
- R46 counted as both partial and unverifiable;
- incomplete and inexact five-row test map as proof for all 42 findings;
- claim that the helper verifies semantic coverage;
- 450/450 as independently reproduced;
- R45/R48/R49/R52/R53 as fully test-verified without the missing direct mutation tests.

**Planner status:** R26_STAGE1D_REPORT_RECEIVED_REQUEST_CHANGES; FINDING_LEDGER_AND_TEST_EVIDENCE_RECONCILIATION_REQUIRED; PC1_BLOCKED.

## 8. Next task — R26 Stage 1E

Read planner/GLEPPO_R26_STAGE1E_EXECUTOR_PROMPT.md.

Stage 1E is a documentation/evidence reconciliation stage. Do not modify production source or test code. Restore all 42 formal rows, provide exact test function/assertion mapping, correct dispositions, and attach the actual 450-test run output/log if it exists. Where a required test does not exist, record the gap and keep the Finding PARTIALLY_FIXED or UNVERIFIABLE; do not invent evidence.

## 9. Hard boundaries

No registered PC1 execution. No Family C access. No ECOS/PPO training. No Formal G3 efficacy. No external model/API calls. No production runtime calls. No production source changes. No test-code changes. No production signing-key access/provisioning. No changes to frozen R1–R25 raw evidence/manifests. No merge/reset/rebase/force-push or update of main.

**Final decision:** REQUEST CHANGES. Stage 1D materially improves the audit but its formal Finding ledger and evidence package are still incomplete.
