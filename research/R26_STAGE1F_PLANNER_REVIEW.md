# GLEPPO R26 Stage 1F — Planner Independent Review

**Review date:** 2026-11-04  
**Repository:** yujian777555/GLEPPO  
**Branch:** r25-handoff  
**Stage 1F report commit:** 1a29d1cc722d3cc20491310c896d204b8290c625  
**Stage 1F commit parent / source snapshot candidate:** 29325cfa16441154c833f381f208747b57627a79  
**R25 base:** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**main at review:** 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e  
**Planner decision:** REQUEST_CHANGES  
**PC1:** BLOCKED

---

## 1. Executive decision

Stage 1F makes useful progress over Stage 1E:
- the formal register contains all 42 IDs R12–R53 exactly once;
- the category counts sum to 42;
- R18 is separated from R24 and is represented as NONE for a behavioral test, with a manual documentation-evidence claim;
- R24, R45, R52 and R53 are downgraded to PARTIALLY_FIXED;
- R15 remains OPEN and R46 remains UNVERIFIABLE;
- the seven-suite inventory count of 218 declared test functions is independently confirmed;
- 450/450 remains correctly labelled EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED;
- no production source or test file changed in the Stage 1F commit.

However, Stage 1F is **not accepted as a completed exact test-evidence audit**.

Two blocking defects remain:

1. **Disposition summary arithmetic is inconsistent.** The 42-row detailed table actually contains 27 VERIFIED_FIXED, 13 PARTIALLY_FIXED, 1 OPEN and 1 UNVERIFIABLE. The report's count summary, status.json and commit message say 22/15/1/1, which sums to only 39. The ID lists in the summary contain 27 VERIFIED_FIXED IDs and 13 PARTIALLY_FIXED IDs, not 22 and 15.
2. **The claimed 42-row actual test map is still not exact.** Planner independently parsed the declarations in all seven named test suites and compared the Stage 1F audit table's class/function pairs. Of the 39 rows that claim a test, 39 class names exist in their stated files, but only **5 of 39 function names exist in the stated class and file**. The other 34 function names are not declared there. The three NONE rows are R18, R45 and R46.

Therefore the 42-row table is not yet a valid actual-declaration map. The extractor script inventories declarations but does not validate the map.

Correct Planner state:

**R26_STAGE1F_REPORT_RECEIVED_REQUEST_CHANGES; DISPOSITION_COUNT_AND_EXACT_TEST_MAP_RECONCILIATION_REQUIRED; PC1_BLOCKED.**

## 2. Repository provenance

Verified remote refs:
- r25-handoff HEAD = 1a29d1cc722d3cc20491310c896d204b8290c625;
- Stage 1F report commit parent = 29325cfa16441154c833f381f208747b57627a79;
- main HEAD = 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e;
- main → Stage 1F: 154 ahead, 0 behind;
- R25 base → Stage 1F: 73 ahead, 0 behind.

Stage 1F commit changed only:
1. research/R26_STAGE1F_FINAL_FINDING_AUDIT.md;
2. research/R26_STAGE1F_TEST_EVIDENCE.md;
3. scripts/_r26f_extract_tests.py;
4. status.json.

No production source or test file changed.

The Stage 1F audit header says HEAD = 29325cf. That is the Stage 1F commit's parent, not the Stage 1F report commit/current branch HEAD. The report must distinguish SOURCE_SNAPSHOT_OR_PARENT, REPORT_COMMIT and CURRENT_BRANCH_HEAD explicitly.

For Stage 1F commit 1a29d1c:
- GitHub commit status: pending, zero status entries;
- check runs: zero;
- Actions runs targeting this exact head SHA: zero.

The 450/450 result must remain executor-reported and not independently reproduced.

## 3. Accepted corrections

### 3.1 Formal Finding IDs and category counts

The detailed table has 42 rows, 42 unique IDs, no duplicates, and no missing IDs in R12–R53.

The category counts are internally correct:

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

### 3.2 R18 / R24 distinction

R18 is represented as NONE for a behavioral test and VERIFIED_FIXED based on manual documentation evidence. This is conceptually acceptable: R18 is a documentation reconciliation finding, not a requirement to invent a test.

Planner independently rechecked the current source artifacts:
- SMOKE_RAW totals.wall_clock_s = 0.0261;
- COST_BASELINE §2 and §5 report 0.0261 seconds;
- planned_init_slots = 32;
- planned_offspring_slots = 96;
- planned_total_slots = 128;
- actual_replicas_run = 112;
- PC1 planned slots = 45,440;
- production LLM tokens/latency/cost remain UNMEASURED;
- the raw units note explicitly distinguishes planned slots from actual CTX.

R18 may remain VERIFIED_FIXED, but Stage 1G must cite exact raw JSON and cost-document lines and state that the evidence is a manual artifact comparison, not a test.

### 3.3 Corrected dispositions

The following changes from Stage 1E are directionally correct:
- R24: PARTIALLY_FIXED;
- R45: PARTIALLY_FIXED;
- R52: PARTIALLY_FIXED;
- R53: PARTIALLY_FIXED;
- R15: OPEN;
- R46: UNVERIFIABLE.

These are accepted as the Executor's proposed classifications pending a complete evidence map and count reconciliation.

### 3.4 218 declared test functions

Planner independently counted the declared test methods in the seven PC1 suites:

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

This count is accepted only as an inventory count. It is not proof that the mapped Finding is tested.

## 4. Blocking defect A — disposition arithmetic

The 42 detailed audit rows produce:

| Disposition | Count computed from detailed rows |
|---|---:|
| VERIFIED_FIXED | 27 |
| PARTIALLY_FIXED | 13 |
| OPEN | 1 |
| UNVERIFIABLE | 1 |
| **Total** | **42** |

The report's disposition summary instead states:
- VERIFIED_FIXED = 22;
- PARTIALLY_FIXED = 15;
- OPEN = 1;
- UNVERIFIABLE = 1;
- Total = 42.

Those values sum to 39, not 42.

The summary's ID lists also contradict its numeric counts:
- the VERIFIED_FIXED list contains 27 IDs;
- the PARTIALLY_FIXED list contains 13 IDs.

The commit message and status.json repeat 22/15. This is not merely a summary typo in one document; three authoritative artifacts disagree with the detailed table.

For reconciliation, the current detailed row dispositions are the source of the 27/13 recount. Stage 1G must:
1. recount directly from the 42 detailed rows;
2. decide whether 27/13 are the intended classifications or whether some rows need disposition changes after evidence review;
3. update every summary, status field and handoff consistently;
4. ensure numeric counts, ID lists and the 42-row table all agree.

Do not simply change 22 to 27 and 15 to 13 without first completing the substantive evidence review below.

## 5. Blocking defect B — test function names are still not actual declarations

Planner parsed the declarations in the seven test files and compared the Stage 1F audit table's test file/class/function triplets.

Result:
- 42 Finding rows;
- 3 rows intentionally have NONE: R18, R45 and R46;
- 39 rows claim a direct test;
- 39/39 claimed class names exist in the stated file;
- only 5/39 function names exist in the stated class and file;
- **34/39 claimed test functions do not exist in the stated class/file**;
- only 5/42 rows are exact file/class/function matches.

The five exact pairs are:
1. R12 — test_r12_r17.py / TestR12BudgetLedger / test_init_evaluation (line 37);
2. R24 — test_r19_r25.py / TestR24CostConsistency / test_smoke_raw_matches_cost_baseline (line 343);
3. R38 — test_r33_r38.py / TestR38FailClosedGates / test_approval_empty_protocol_hash_denied (line 369);
4. R42 — test_r54_r59.py / TestR54ApprovalGate / test_no_signature_rejected (line 89);
5. R43 — test_r54_r59.py / TestR54ApprovalGate / test_proposed_rejects_all_flags_true (line 69).

Examples of incorrect function mappings:
- R13 claims test_validate_records; actual methods include test_missing_action_rejected, test_wrong_horizon_rejected, test_nonfinite_reward_rejected and others.
- R14 claims test_sample_role; actual methods are test_q_hat_excludes_extra_immediate, test_r_hat_includes_extra_immediate and test_extra_immediate_does_not_pollute_q_hat.
- R15 claims test_registered_refuses; actual method is test_registered_execution_refused.
- R16 claims test_same_crn_tuple; actual method is test_same_crn_tuple_gives_identical_seeds_across_genotypes.
- R17 claims test_replayable; actual methods include test_evidence_contains_provenance and test_evidence_records_have_required_fields.
- R19 claims test_consistency_check; actual method is test_consistency_check_passes.
- R21 claims test_negative_rejected; actual method is test_negative_total_rejected.
- R23 claims test_round_trip; actual method is test_round_trip_serialize_replay.
- R25 claims test_downgrade_wording; actual methods include test_default_deny and test_registered_execution_still_refused.
- R26 claims test_canonical_doc; actual method is test_document_fields_match_code.
- R27 claims test_atomic_updates; actual methods include test_atomic_failure_on_over_budget and test_snapshot_unchanged_after_rejection.
- R28 claims test_reconciliation; actual method is test_ledger_components_sum_to_total.
- R29 claims test_cross_validation; actual methods include test_unknown_episode_rejected_specifically and test_wrong_cluster_rejected.
- R30 claims test_registered_required; actual methods include test_missing_manifest_hash_rejected and test_missing_runtime_rejected.
- R31 claims test_harness_label; actual method is test_runner_is_harness_not_collector.
- R32 claims test_tagged_encoding; actual methods include test_none_and_empty_seed_distinguished and test_cache_no_hit_for_different_eval_seed.
- R33 claims test_q_extra_atomic; actual method is test_extra_slot_negative_cache_no_mutation.
- R34 claims test_typed_json; actual methods include test_none_vs_literal_NONE_distinct and test_delimiter_ids_no_collision.
- R35 claims test_plan_hash; actual method is test_plan_mapping_deterministic.
- R36 claims test_field_validation; actual methods include test_mutation_n_states_fails and test_mutation_estimator_fails.
- R37 claims test_protocol_plan_hash; actual methods include test_missing_protocol_hash_rejected and test_wrong_plan_hash_rejected.
- R39 claims test_delimiter_safe; actual method is test_delimiter_no_collision.
- R40 claims test_structured_checks; actual method is test_full_consistency_passes.
- R41 claims test_plan_artifact; actual method is test_save_load_roundtrip.
- R44 claims test_artifact_required; actual methods in TestR55PlanBinding include test_missing_protocol_hash_rejected and test_canonical_roundtrip.
- R47 claims test_plan_identity; no such method exists in TestR55PlanBinding.
- R48 claims test_schema_exact; actual methods in TestR56StrictTypes include test_bool_true_rejected, test_missing_field_rejected and test_extra_field_rejected.
- R49 claims test_mutation_status_not_checked; actual method is test_mutation_status_not_checked_by_consistency.
- R50 claims test_artifact_connected; no such method exists in TestR54ApprovalGate.
- R51 claims test_plan_hash_pinned; actual method is test_registered_hash_matches_computed.
- R52 claims test_seed_schema; no such method exists in TestR56StrictTypes.
- R53 claims test_hash_excludes; no such method exists in TestR40ProtocolConsistency.

The three NONE rows are R18, R45 and R46, as the report states.

## 6. The extractor script does not validate the map

scripts/_r26f_extract_tests.py:
- scans class declarations;
- scans test function declarations;
- counts functions;
- prints only the first three function names from each file;
- does not parse the 42-row audit table;
- does not compare each claimed class/function pair with declarations;
- does not inspect test bodies or assertions;
- does not trace source calls or verify that a test reaches the intended branch.

The script therefore supports an inventory count, not the claim that the 42-row test map was rebuilt from actual declarations. No raw output from this script is committed either.

The Stage 1F test-evidence document contains only the file/class/function inventory, the 218 count, the 450/450 caveat and three NONE findings. It does not provide the required 42-row map with exact line numbers, assertion expressions and source call paths.

## 7. Exact declaration is not sufficient evidence of the original Finding

Even the five exact pairs need semantic review:

### R24
test_smoke_raw_matches_cost_baseline checks that the first five characters of wall_clock_s occur somewhere in COST_BASELINE.md and checks hard-coded raw counters. It does not parse the cost report's units/labels. PARTIALLY_FIXED is correct.

### R38
test_approval_empty_protocol_hash_denied creates an ApprovalGate without a TrustedApprovalArtifact or approval_key. ApprovalGate.check() rejects first because the trusted artifact is absent. This does not demonstrate that the intended missing protocol-hash validation branch is reached. PARTIALLY_FIXED is correct.

### R42
test_no_signature_rejected calls TrustedApprovalArtifact.verify() directly. It is an artifact-level test, not a positive/negative integration proof that ApprovalGate.check() consumes the artifact correctly.

### R43
test_proposed_rejects_all_flags_true supplies a signed test artifact, but the gate rejects because the canonical protocol status is PROPOSED before HMAC verification. This proves default-deny while PROPOSED, not a valid APPROVED-path integration.

### R12
test_init_evaluation checks initial ledger counters. The complete R12 acceptance criterion must still be compared with the other methods in TestR12BudgetLedger, including cache bundle hits and planned-vs-actual counter separation. Do not claim more than the assertions prove.

## 8. Test execution evidence

Stage 1F correctly states:

**450/450 — EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED**

For commit 1a29d1cc:
- GitHub status entries = 0;
- check runs = 0;
- Actions runs targeting this exact SHA = 0.

No raw stdout/stderr log was added. Planner has not independently reproduced the 450/450 run. Keep the caveat.

## 9. Planner disposition

**Stage 1F is partially accepted but not accepted as a completed finding-level audit.**

Accepted:
- 42 formal IDs R12–R53 present exactly once;
- category counts sum to 42;
- R18 has no behavioral test and is treated as manual documentation evidence;
- R24/R45/R52/R53 are downgraded to PARTIALLY_FIXED;
- R15 remains OPEN;
- R46 remains UNVERIFIABLE;
- 218 declared test-function count is correct;
- 450/450 is not misrepresented as independently reproduced;
- no production source or test code changed.

Not accepted:
- the 22/15 disposition summary;
- the 42-row actual test map;
- 34 of 39 claimed test function names;
- the claim that the extractor validates the map;
- the absence of per-Finding test line ranges, assertion expressions and source call paths;
- the claim that all mapped test declarations substantiate their original Finding acceptance criteria.

Current detailed-row arithmetic is 27 VERIFIED_FIXED / 13 PARTIALLY_FIXED / 1 OPEN / 1 UNVERIFIABLE. This is a recount of the submitted rows, not acceptance of all 27 VERIFIED_FIXED claims.

**Planner status:** R26_STAGE1F_REPORT_RECEIVED_REQUEST_CHANGES; DISPOSITION_COUNT_AND_EXACT_TEST_MAP_RECONCILIATION_REQUIRED; PC1 BLOCKED.

## 10. Next task — R26 Stage 1G

Read planner/GLEPPO_R26_STAGE1G_EXECUTOR_PROMPT.md.

Stage 1G is a documentation-only correction:
1. Reconcile detailed row dispositions, numeric counts and ID lists.
2. Replace every non-existent test function name with exact declarations, or NONE.
3. For each Finding, include test file, class, function, line range, actual assertion expression, source symbol/call path and uncovered acceptance conditions.
4. Inspect the test body; do not treat a matching name as proof.
5. Correct the test-evidence document to contain the full 42-row map.
6. Correct report provenance fields and all handoff/status documents.
7. Re-evaluate dispositions if the exact test does not prove the original criterion.

Do not modify production source or test code in Stage 1G. Missing tests should remain PARTIALLY_FIXED; implement new tests only in a separately authorized remediation stage after Planner review.

## 11. Hard boundaries

No registered PC1 execution. No Family C access. No ECOS/PPO training. No Formal G3 efficacy. No external model/API calls. No production runtime calls. No production source changes. No test-code changes. No production signing-key access/provisioning. No changes to frozen R1–R25 raw evidence/manifests. No merge/reset/rebase/force-push or update of main.

**Final decision:** REQUEST CHANGES. Stage 1F corrected several dispositions and the category ledger, but the count summary is arithmetically wrong and the claimed actual test map still contains 34 non-existent function names.
