# GLEPPO R26 Stage 1E — Correct the 42-Finding Ledger and Complete Evidence Reconciliation

**Role:** Executor under Planner review  
**Project:** GLEPPO only  
**Repository:** yujian777555/GLEPPO  
**Required branch:** r25-handoff  
**Stage 1D Executor commit:** ca0c9098b83a44229bbedaf5f478ae09d7c16db1  
**Stage 1D source snapshot / parent:** 8f77b361491cc2ab202bf7261425a03b08f903e5  
**Stage 1D Planner review:** research/R26_STAGE1D_PLANNER_REVIEW.md  
**R25 base:** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**Stage:** R26_STAGE1E_FINDING_LEDGER_AND_TEST_EVIDENCE_RECONCILIATION  
**Task type:** read-only source/test audit, correction of audit reports, safe offline evidence capture only  
**Authorization:** no production source changes; no test-code changes; no registered experiment.

---

## 1. Planner decision — Stage 1D is not accepted as a completed 42-finding audit

Read the complete Planner review first:

research/R26_STAGE1D_PLANNER_REVIEW.md

Stage 1D corrected the Stage 1C test-file mapping and made useful progress. However, the audit still has critical accounting and evidence defects:

1. R18, a formal Finding in the R12–R53 register, is missing.
2. The Provenance category lists nine IDs but reports a count of seven.
3. The category membership table contains only 41 unique Finding IDs because R18 is omitted.
4. The claimed disposition counts 30 + 8 + 1 + 1 sum to 40, not 42.
5. R46 appears in the PARTIALLY_FIXED list and as UNVERIFIABLE in the detailed table. A Finding must have exactly one disposition.
6. The detailed rows as currently written count 32 VERIFIED_FIXED, 7 PARTIALLY_FIXED, 1 OPEN and 1 UNVERIFIABLE across 41 unique IDs. This is a recount of the submitted table, not an accepted disposition.
7. The per-Finding test map covers only five Findings and uses abbreviated/nonexistent function names.
8. The test inspection helper counts function names/imports; it does not inspect semantic assertions.
9. The 450/450 result has no raw output/log or CI run on the Stage 1D commit.

Correct current state:

**R26_STAGE1D_REPORT_RECEIVED_REQUEST_CHANGES; FINDING_LEDGER_AND_TEST_EVIDENCE_RECONCILIATION_REQUIRED; PC1_BLOCKED.**

Do not preserve the 30/8/1/1 aggregate as an accepted result.

## 2. Exact repository recovery

Before editing:
1. Verify branch r25-handoff and current HEAD.
2. Verify ancestry includes R25 base a8ff1827434a88b2fef02a89aaf3e120e0a017a7.
3. Verify Stage 1D report commit ca0c9098b83a44229bbedaf5f478ae09d7c16db1 is an ancestor.
4. Record source snapshot, Stage 1D report commit and current HEAD separately.
5. Record main SHA and ahead/behind counts.
6. Record worktree state and latest commit.
7. If refs differ, stop and report the exact mismatch.
8. Continue only on r25-handoff. Do not merge or update main.

Planner last verified:
- r25-handoff = ca0c9098b83a44229bbedaf5f478ae09d7c16db1;
- Stage 1D parent/source snapshot = 8f77b361491cc2ab202bf7261425a03b08f903e5;
- main = 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e;
- main → Stage 1D: 124 ahead, 0 behind;
- R25 base → Stage 1D: 43 ahead, 0 behind.

Recheck these values; do not assume they remain unchanged.

## 3. Work Package A — restore the complete formal Finding register

Formal findings are every integer ID R12 through R53 inclusive: exactly 42 rows.

R18 must not be removed. It is a formal THIRD review Finding:
**R18 — Cost baseline still contains contradictory old values.**

R18 and R24 are separate formal Findings even if they share cost evidence:
- R18: historical cost/units contradiction and repeated figures in COST_BASELINE.md;
- R24: consistency between raw smoke artifact and cost baseline.

Current artifacts appear to show R18 remediation:
- SMOKE_RAW.json totals: wall_clock_s 0.0261, planned_init_slots 32, planned_offspring_slots 96, planned_total_slots 128, actual_replicas_run 112;
- COST_BASELINE.md: 0.0261 seconds, 96 offspring planned slots, 128 total planned slots, 112 actual replicas, 45,440 PC1 planned slots;
- test_r19_r25.py::TestR24CostConsistency::test_smoke_raw_matches_cost_baseline checks the raw wall-clock and slot/counter figures.

Verify the entire historical R18 acceptance criterion. If all old contradictory values and unit confusion are gone, add R18 as a separate VERIFIED_FIXED row with exact evidence. If any discrepancy remains, use the appropriate lower disposition. Do not drop R18 or merge it into R24.

## 4. Work Package B — reconcile category counts

Use one primary category per Finding. The IDs currently listed imply the following natural reconciliation:

| Category | IDs | Count |
|---|---|---:|
| Budget/CTX | R12, R21, R27, R28, R33 | 5 |
| Seed/CRN | R16, R20, R32, R34, R39 | 5 |
| Protocol | R19, R26, R36, R40, R45, R48, R49, R52, R53 | 9 |
| Approval | R38, R42, R43, R46, R50 | 5 |
| Provenance | R22, R29, R30, R35, R37, R41, R44, R47, R51 | 9 |
| Runner | R15, R25, R31 | 3 |
| Statistics | R13, R14 | 2 |
| Evidence | R17, R23 | 2 |
| Cost | R18, R24 | 2 |
| **Total** | **R12–R53, each exactly once** | **42** |

If a primary category should differ, document the reason and move the ID explicitly. The unique ID set must equal {R12, ..., R53}; no omissions, duplicates or unnumbered blockers mixed into this table.

## 5. Work Package C — one disposition per Finding

For each R12–R53, assign exactly one:
- VERIFIED_FIXED
- PARTIALLY_FIXED
- OPEN
- REGRESSION
- NOT_APPLICABLE
- UNVERIFIABLE

Disposition counts must sum to 42. Do not list one ID under two statuses. R46 is UNVERIFIABLE unless independent trust-anchor provenance is actually evidenced; do not also count it as PARTIALLY_FIXED.

For every Finding include:
1. exact original review file and Finding heading;
2. original failure mode and full acceptance criterion;
3. current source file, symbol and line range;
4. relevant call path/invariant;
5. exact test class and function name, or NONE;
6. exact assertion(s), not a paraphrase of the test-file purpose;
7. whether the test reaches the intended code branch;
8. safe test command and exact output/log reference, if run;
9. disposition and rationale;
10. remaining risk and next acceptance condition.

A source implementation without a relevant test may be PARTIALLY_FIXED or UNVERIFIABLE; it is not automatically VERIFIED_FIXED. A generic assertRaises that fails earlier for an unrelated reason does not test the intended failure mode.

## 6. Work Package D — mandatory finding-specific corrections

### D1. R18 and R24 cost

Inspect current COST_BASELINE.md and SMOKE_RAW.json. Check every historical R18 value/unit, not only the current wall-clock substring. R18 and R24 each need a separate row. The exact relevant test is:

tests/test_r19_r25.py::TestR24CostConsistency::test_smoke_raw_matches_cost_baseline

The test checks raw wall-clock presence and the 32/96/128/112 values. State what it does and does not prove.

### D2. R43 approval

Stage 1D says a gate-level test is needed. That statement is inaccurate. The existing gate-level test is:

tests/test_r54_r59.py::TestR54ApprovalGate::test_proposed_rejects_all_flags_true

It constructs a signed test artifact with the exact current protocol hash and asserts that ApprovalGate refuses while the canonical document is PROPOSED.

Correct the rationale. Remaining limitations include:
- ApprovalGate.expected_protocol_hash is stored but not consumed by ApprovalGate.check();
- no positive approved-path integration test is present;
- a test key is not independent production trust-anchor evidence.

R43 may remain PARTIALLY_FIXED, but not because a gate-level negative test is absent.

### D3. R45 duplicate JSON keys

Source parse_protocol_document() uses _DuplicateKeyChecker. Search all seven PC1-related suites for a direct test that creates a canonical protocol JSON block with duplicate critical keys and proves parsing fails.

A test named test_duplicate_key_rejected for duplicate state/action records is not the same test. If no direct duplicate-protocol-key test exists, do not call the entire R45 acceptance criterion VERIFIED_FIXED.

### D4. R48 and R52 exact schema semantics

Current source has structured reward, estimator and seed schema checks. Existing tests include:
- reward bool/string/missing/extra-field mutations in test_r54_r59.py;
- estimator horizon mutation in test_r33_r38.py;
- seed field-list mutation in test_r39_r42.py.

Check whether there are direct mutations for:
- extra estimator keys/semantics;
- missing estimator keys;
- seed schema version;
- seed schema encoding;
- extra/missing seed keys;
- reward formula identity and exact typed fields.

Do not claim full adversarial coverage when these direct tests are absent. Distinguish source-level validation from test-backed validation.

### D5. R49 and R53 lifecycle/content hash

Current compute_protocol_hash() filters out lifecycle fields, including status. The existing test test_mutation_status_not_checked_by_consistency proves only that protocol_consistency_check() ignores status; it does not prove the content hash remains invariant when status changes.

No direct status-only hash invariance test was found in the Stage 1D test suites. Map the exact test for each Finding. If absent, state the gap. Do not map R49 to test_wrong_doc_id_rejected.

### D6. R38 gate tests

Inspect whether the tests actually reach the intended validation branch. Several current tests instantiate ApprovalGate without trusted_artifact/approval_key, so gate.check() rejects earlier because the artifact is missing. Such tests do not prove that missing expected hash, approver or date is rejected at the intended check.

Also note expected_protocol_hash is not used by ApprovalGate.check(). Do not call that field's validation fixed without evidence.

### D7. R50 HMAC integration and R46 trust anchor

Separate:
1. TrustedApprovalArtifact.verify() correctly validates HMAC with a supplied key;
2. ApprovalGate.check() actually consumes the artifact;
3. a positive approved-path test reaches the HMAC verification call;
4. the key comes from an independently trusted source;
5. the approval event/approver is authenticated outside caller-controlled fields.

The existing gate-level test with the signed artifact rejects at the canonical PROPOSED status check before HMAC verification. Artifact-level wrong-signature tests do not prove a successful gate integration path.

Do not provision or request a production key. Keep R46 UNVERIFIABLE absent independent provenance evidence.

### D8. Runner R15/R25/R31

Assess separately:
- R15 requires an actual guarded collection/rollout orchestration entry point. It remains OPEN while execute_registered_pc1() refuses and no real collector exists.
- R25 permits an accurately documented downgrade to dry-run planner + analysis only, provided all current status/report wording agrees.
- R31 requires the synthetic gate/accounting harness to be accurately labeled, with no claims that it collects tasks, invokes Evaluator, executes rollouts or writes raw artifacts.

Do not conflate the three Findings.

## 7. Work Package E — exact test evidence and 450/450

The seven relevant suites contain the following declared test-function counts, independently confirmed by Planner:

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

This is a count of test functions in seven PC1-related suites. It is not proof that all 218 individually cover formal Findings.

The Stage 1D evidence maps only five Findings and uses abbreviated names. Replace that with all 42 exact mappings. Use exact class/function names, source calls, assertions and failure modes. If no suitable test exists, write NONE and retain the gap.

### 450/450 evidence

Stage 1D claims:
python -m unittest discover -s tests
450/450 PASS
exit code 0

Planner found no raw log and no GitHub check/workflow run for commit ca0c909. The result must remain:

450/450 — EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED

unless an attributable raw run log or CI artifact is provided.

If the Executor has the original stdout/stderr:
- preserve it exactly;
- record Python version, OS, working directory, command, start/end time, exit code and test summary;
- save it as a committed text log;
- state whether it is an original local run or a later reproduction.

If no original log exists, say so. Do not recreate output or claim the previous run is independently reproduced.

Do not rerun full unittest discovery until all 24 test files, imports, fixtures and side effects have been inspected and shown safe. The prior safety review covered the seven PC1-related suites, not automatically all tests in the repository. Run only safe targeted tests if a full-suite safety review is incomplete.

## 8. Work Package F — audit scripts and evidence method

scripts/_r26d_test_inspect.py only extracts test names and checks imports. It is not a semantic verifier. Label it as a test inventory helper, not a finding verifier.

Do not replace it with another path/count/keyword-only verifier. Any future helper must validate an explicit evidence manifest, exact test function existence, line references and saved test result references. Manual assertion/call-path review remains mandatory.

## 9. Required outputs

Create/update:
1. research/R26_STAGE1E_FINAL_FINDING_AUDIT.md — exactly 42 rows, R12–R53.
2. research/R26_STAGE1E_TEST_EVIDENCE.md — exact 42-row test map, safety review, raw logs if available, and unsupported claims clearly labeled.
3. research/R26_STAGE1D_CORRECTED_FINDING_AUDIT.md — preserve original Executor report and append the Stage 1E correction/Planner decision.
4. research/R26_STAGE1D_TEST_EVIDENCE.md — preserve historical Stage 1D claim and append exact corrections.
5. research/R26_PC1_FINDING_REGISTER.md — restore R18 and reconcile all categories.
6. research/R26_PC1_FINDING_LEVEL_VERIFICATION.md — preserve Stage 1C history, add Stage 1D/1E correction.
7. research/R26_PC1_TEST_EVIDENCE.md — correct invalid Stage 1C mapping and document current evidence state.
8. research/R26_PC1_AUDIT_SUMMARY.md — accurate current counts and blockers.
9. research/R26_STAGE1D_PLANNER_REVIEW.md — retain Planner review.
10. planner/latest_plan.md.
11. planner/GLEPPO_R26_HANDOFF.md.
12. planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md.
13. status.json.

Do not create empty placeholders. Preserve historical Executor claims as historical claims; append corrections rather than silently rewriting history.

Update status.json:
- retain Stage 1C and Stage 1D Executor claims as historical;
- record Planner REQUEST_CHANGES separately;
- set Stage 1E as current_task;
- separate source snapshot, Stage 1D report commit, Stage 1E report commit and current HEAD;
- preserve PC1 BLOCKED, Family C NOT ACCESSED, controller training NOT STARTED, Formal G3 FAIL, model/API calls 0.

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
- source snapshot, Stage 1D report commit and Stage 1E report commit;
- main SHA and ahead/behind;
- worktree state;
- all 42 IDs and exactly one disposition each;
- category counts and disposition counts summing to 42;
- R18 and R24 as separate Findings;
- exact test function/assertion/source-call mapping for all 42;
- missing tests and reasons for PARTIALLY_FIXED/UNVERIFIABLE;
- exact 450/450 log provenance or explicit lack of it;
- safe commands, output, exit codes and skips;
- files changed;
- model/API calls = 0;
- registered PC1 = NOT EXECUTED;
- Family C = NOT ACCESSED;
- controller training = NOT STARTED;
- Formal G3 efficacy = NOT EXECUTED;
- production source/test changes = 0.

End with one status:
- R26_STAGE1E_AUDIT_COMPLETE_REQUIRES_PLANNER_REVIEW
- R26_STAGE1E_AUDIT_INCOMPLETE_BLOCKED
- R26_STAGE1E_REF_MISMATCH_STOPPED

**Immediate action:** verify refs, restore R18, reconcile all 42 IDs and dispositions, provide exact test mappings, and preserve honest evidence boundaries. Do not modify production source or tests.
