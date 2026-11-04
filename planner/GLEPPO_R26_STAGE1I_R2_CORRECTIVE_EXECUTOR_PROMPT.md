# GLEPPO R26 Stage 1I-R2 — Semantic Evidence Correction and Validator Hardening

**Role:** Executor under GPT Planner review  
**Repository:** yujian777555/GLEPPO  
**Branch:** r25-handoff only  
**Reviewed R1 HEAD:** 4d2ff06ee01146533501589b264d33ddd30ffcbe  
**R1 parent:** 539f74d5c898abc144992fff4a413a30744c1cc9  
**R1 Planner review:** research/R26_STAGE1I_R1_PLANNER_REVIEW.md  
**Planner decision:** REQUEST_CHANGES — R1 NOT ACCEPTED  
**Task:** Stage 1I-R2 corrective completion  
**Authorization:** documentation, JSON/Markdown evidence map and non-production audit helper only. No production source changes, no tests/ changes, no experiments, no PC1, no model/API calls.

---

## 0. Mandatory recovery and provenance

Before editing:
1. Fetch r25-handoff and verify its exact current HEAD. It must include the R1 commit and this Planner review.
2. Verify the prior Planner review and R1 prompt remain in branch ancestry.
3. Verify main remains unchanged; record its exact current SHA and ahead/behind counts.
4. Record the R1 source snapshot separately from R1 parent, R1 final commit, R1 Planner review commit, R2 parent and R2 final commit.
5. Read:
   - status.json
   - research/R26_STAGE1I_R1_PLANNER_REVIEW.md
   - research/R26_STAGE1I_R1_CORRECTIVE_REPORT.md
   - research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json
   - research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md
   - scripts/_r26i_validator.py
   - all eight original review documents cited by the map
   - all test files cited by the map
   - relevant source symbols and source artifacts
   - latest_plan, handoff, next-session prompt and cumulative PC1 audit summary.
6. If refs differ, stop and report. Do not reset, rebase, force-push or modify main.

Exact R1 final commit is 4d2ff06ee01146533501589b264d33ddd30ffcbe. The R1 report currently says “(this commit)” and status.json omits the R1 final SHA/source snapshot from its provenance object. Correct both.

## 1. Planner decision and required scope

Stage 1I-R1 is NOT ACCEPTED. The JSON contains 42 unique IDs and the Markdown rendering is synchronized, but the semantic evidence is not trustworthy yet:
- many relevant tests are omitted;
- some call paths are factually false;
- some cited source symbols do not exist or are assigned to the wrong file;
- several source symbol line ranges are null;
- some VERIFIED_FIXED rows have uncovered acceptance conditions or cite tests that do not exercise the claimed criterion;
- the validator accepts null line values and its wrong-file self-test duplicates the missing-file case.

Read the full Planner findings in research/R26_STAGE1I_R1_PLANNER_REVIEW.md. R2 must correct the actual evidence, not merely rewrite the report language.

Remain in Stage 1I. Do not start R26_ECOS_PROTOCOL_RECONCILIATION.

## 2. Work Package A — correct the complete 42-Finding map

Update the canonical JSON and Markdown rendering:
- research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json
- research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md

Retain exactly 42 unique IDs R12–R53. Do not change the ID universe. Keep the Markdown rendering synchronized with the JSON. Recompute disposition counts mechanically after every correction.

### 2.1 Acceptance criteria must be complete

For every row, return to the cited original review document and preserve every independently testable acceptance subcondition. Do not compress multi-part requirements into vague phrases.

Examples that must be expanded:
- R39 must include the explicit version/schema tag requirement and confirmation that all CRN call sites use the same canonical contract, in addition to delimiter safety, tuple reproducibility, component isolation and action/genotype exclusion.
- R50 must preserve signed payload fields, independent trust-anchor requirements, gate consumption and the approved-path limitation.
- R51 must preserve plan ID, version, canonical mapping hash, protocol-content binding and the end-to-end registered-analysis requirements.
- R44 must distinguish artifact path requirement, actual artifact loading and record validation against that exact artifact.

For each criterion, map evidence to that specific subcondition. If it is not proven, list it as uncovered.

### 2.2 Enumerate all relevant tests, not one representative test

For every mapped Finding, include every relevant test that proves an acceptance subcondition. Each test_evidence entry must have exact declaration start/end lines, all relevant assertion expressions and line numbers, exact source symbols/ranges, concrete call path, intended branch reachability and harness type.

Correct at least these known omissions:

- **R12:** include test_cache_bundle_hit_adds_zero_replicas (tests/test_r12_r17.py:44–48), test_shared_evaluator_deltas (line 66 onward), and other relevant cache/planned-unit tests. test_init_evaluation alone does not exercise a cache hit.
- **R14:** include test_r_hat_includes_extra_immediate (tests/test_r12_r17.py:191 onward) and test_extra_immediate_does_not_pollute_q_hat (line 197 onward), in addition to the Q-hat exclusion test.
- **R17:** include test_evidence_records_have_required_fields (tests/test_r12_r17.py:329 onward). Reconcile the “full counter breakdown” criterion using actual evidence; do not claim R28 proves execution counters.
- **R20:** include test_different_task_isolated, test_different_rollout_isolated, test_different_replicate_isolated and test_override_path_preserves_task_replicate_isolation (tests/test_r19_r25.py:136 onward). Keep the evaluator seed path separate from the standalone crn_seed helper.
- **R23:** include test_round_trip_serialize_replay (tests/test_r19_r25.py:310 onward), not only test_evidence_contains_D_adv_CIs.
- **R26:** include test_document_fields_match_code (tests/test_r26_r32.py:346 onward), test_document_says_proposed, test_code_version_not_frozen and test_status_is_proposed as applicable.
- **R28:** cite test_ledger_components_sum_to_total (tests/test_r26_r32.py:122–133) for actual reconcile evidence. test_registered_budget_exact (lines 116–120) checks constants only and does not call reconcile. Include other registered-shape/component tests where relevant.
- **R30:** include missing manifest, runtime and evaluator-version tests. Correct the call path: the early guard is in run_pc1_analysis, not validate_records.
- **R37:** include missing protocol hash, missing plan hash, wrong protocol hash and wrong plan hash tests. Correct the call path to run_pc1_analysis for early guard failures.
- **R39:** include all seven direct CRN tests in tests/test_r39_r42.py: test_same_params_reproducible, test_delimiter_no_collision, test_task_change_changes_seed, test_state_change_changes_seed, test_rollout_change_changes_seed, test_replicate_change_changes_seed and test_none_empty_string_no_collision. Also include the R16 and R20 instrumented cross-genotype tests as separate evidence entries. Keep the tautological test_action_genotype_excluded excluded.
- **R40:** include mutation_version, mutation_status, mutation_seed_contract and mutation_reward tests (tests/test_r39_r42.py:108, 118, 130, 140), not only the happy-path consistency test.
- **R41:** include test_tampered_artifact_rejected, test_defensive_copy_prevents_mutation and test_wrong_hash_rejected, in addition to save/load round-trip.
- **R22, R29, R33, R35, R42:** re-audit each multi-part criterion and add every relevant test that exists. Do not leave relevant tests only in prose outside test_evidence.

Do not list irrelevant tests merely to increase counts. If a test does not reach the relevant code path, state that explicitly.

### 2.3 Correct false call paths and source symbols

These corrections are mandatory:

**R17 / R23**
- build_evidence, save_evidence and replay_evidence are not functions in gleppo/pc1.py.
- Use actual symbols: run_pc1_analysis, save_evidence_artifact, load_evidence_artifact and replay_from_artifact, with exact source ranges.
- The test path for evidence generation is test -> run_pc1_analysis -> raw_evidence; replay path is test -> save_evidence_artifact -> replay_from_artifact.

**R20**
- crn_seed is defined in gleppo/pc1.py:230–239, not gleppo/evaluator.py.
- Evaluator.effective_seed_parts (gleppo/evaluator.py:57–76) does not call crn_seed. Correct the call path.
- Map standalone crn_seed tests separately from evaluator seed tests.

**R28**
- test_registered_budget_exact checks constants only. It does not call BudgetLedger.reconcile.
- test_ledger_components_sum_to_total is the actual reconcile test.

**R30 / R37**
- The tests call run_pc1_analysis. Missing metadata/hash guards are evaluated before validate_records. Cite the exact early guard in run_pc1_analysis and do not claim validate_records was reached.

**R38**
- The test constructs ApprovalGate without trusted_artifact/approval_key and exits before the empty protocol hash branch. branch_reached must be false, with a specific explanation naming the earlier guard and exact source line.

**R44**
- test_missing_protocol_hash_rejected calls load_plan_artifact directly; it is not an end-to-end registered-analysis test.
- run_pc1_analysis at gleppo/pc1.py:636 onward requires plan_artifact_path, calls load_plan_artifact and validates records against the returned artifact mapping. Cite that source as MANUAL evidence.
- If no test proves end-to-end analysis binding, list that criterion as uncovered and re-evaluate disposition.

**R47**
- test_alternative_mapping_rejected fails at the registered mapping hash comparison before plan_id/version checks. Correct the call path to the actual registered-hash rejection branch. Do not say the ID/version branch was reached.
- Cite source-level ID/version checks separately and distinguish manual evidence from tested evidence.

**R50**
- tests/test_r54_r59.py:146–155 calls art.verify() directly; it does not call ApprovalGate.check().
- Correct source symbol/call path to TrustedApprovalArtifact.verify.
- test_proposed_rejects_all_flags_true does call ApprovalGate.check, but exits at canonical PROPOSED status before HMAC verification. Record these as separate tests with separate reached branches.
- The positive approved-path gate integration remains untested because canonical protocol status is PROPOSED. Do not fabricate approval or change status.

**R51**
- test_registered_hash_matches_computed compares REGISTERED_PROTOCOL_CONTENT_HASH, not REGISTERED_PLAN_HASH.
- REGISTERED_PLAN_HASH is at gleppo/pc1.py:978.
- Use actual plan artifact tests and source evidence. Re-evaluate whether plan ID/version are tested or only source-inspected. Do not call the protocol hash test plan-hash evidence.

**R52**
- validate_reward_schema does not exist in gleppo/pc1.py.
- Actual implementation is protocol_consistency_check (lines 126–223), with nested _check_exact_keys (line 172) and _is_strict_number (line 176).
- Correct the source symbol and call path. Include existing bool/string/missing/extra field tests; preserve untested estimator/seed mutation conditions as uncovered.

**R25**
- GatedPC1Runner does not exist in gleppo/pc1.py. Inspect and cite the actual SyntheticGateHarness / create_default_gated_runner symbols where relevant.

**R24 / R26**
- Replace incomplete file paths such as “research/” with exact repository-relative artifact paths and exact line ranges.

**R45**
- The rationale mentions _DuplicateKeyChecker, but evidence_type is NONE and manual_evidence is empty. Either add MANUAL evidence with exact parser/source lines or remove the source claim. The absence of a direct duplicate-key parser test must remain explicit.

### 2.4 Disposition re-evaluation

The 26/14/1/1 result is not a target. Re-evaluate all 42 rows against complete original criteria after correcting test arrays and call paths.

Examples requiring special attention:
- R12: VERIFIED_FIXED is not supported by the currently mapped initialization-only test.
- R17: VERIFIED_FIXED conflicts with the uncovered full-counter-breakdown condition and nonexistent source symbols.
- R26: file-existence-only evidence does not prove document/code consistency.
- R28: constants-only test does not prove reconcile.
- R40: happy-path test does not prove adversarial mutations.
- R44: isolated loader test does not prove registered-analysis artifact binding.
- R51: cited test is for protocol hash, not plan hash.
- R47: identity/version branch was not reached by the alternative-mapping test.

A row may remain VERIFIED_FIXED if complete direct/manual evidence genuinely supports every criterion. If evidence is indirect, incomplete or branch-unreached, classify accordingly. Do not force the old counts.

Keep:
- R53 PARTIALLY_FIXED unless a direct status-only hash-invariance test already exists in the reviewed source snapshot. No tests may be added in this stage.
- R18 MANUAL with no behavioral test; production tokens/latency remain UNMEASURED.
- R46 UNVERIFIABLE unless independent trust-anchor provenance exists.

## 3. Work Package B — harden scripts/_r26i_validator.py

This remains a non-production audit helper. Use Python ast for test declarations.

### Required strict checks

1. Require schema_version exactly 1.0.
2. Require a JSON object with findings as a list.
3. Require exactly 42 rows and exact unique ID set R12–R53.
4. Validate required field types, not only key presence.
5. For every mapped test entry:
   - test_file/class/function are nonempty strings;
   - declaration_start_line and declaration_end_line are positive integers, not bool, null or strings;
   - declaration lines exactly match AST declarations in the same normalized file path;
   - no missing/unreadable test source;
   - reject ambiguous duplicate declarations.
6. For every source_symbols entry:
   - symbol and exact repository-relative file path are nonempty;
   - start_line/end_line are positive integers, not bool or null;
   - end_line >= start_line;
   - file exists and the line range is within the file;
   - for Python symbols, validate the named function/class/constant against AST or a clearly documented equivalent. If a symbol cannot be resolved, fail validation and correct the map rather than silently accepting it.
7. Validate assertion_expressions as an array of objects with positive integer line and nonempty expression.
8. Validate branch_reached as an object with boolean reached and a specific nonempty explanation. Reject the generic template explanation when it contradicts the call path.
9. Validate harness_type against an explicit enum.
10. Validate manual_evidence structure and require exact path + line/range + value + note.
11. Validate NONE rows and evidence_type semantics.
12. Print machine-readable summary and diagnostics; exit nonzero on any invalid row.
13. Preserve the disclaimer: declaration/schema validation does not prove semantic correctness, assertion meaning, call-path truth or acceptance coverage.

### Required self-tests

Keep deterministic self-tests in the helper; do not add/edit files under tests/.

The current wrong_file_path case at line 418 points to a nonexistent file and duplicates missing_source_file at line 480. The second fixture file exists but is not used for an existing-file/wrong-owner case.

Add a test where the map points to an existing fixture file that does not contain the declared class/function. Assert the specific wrong-owner/declaration error, not merely “some issue exists”.

Add tests for:
- null declaration_start_line rejected;
- null declaration_end_line rejected;
- null source-symbol start/end rejected;
- wrong source symbol/file/range rejected;
- wrong existing-file ownership;
- wrong class/function/line;
- missing/duplicate/unknown ID;
- malformed NONE row;
- missing/unreadable file;
- wrong mapped/NONE cardinality;
- invalid schema_version;
- malformed required field types;
- invalid branch_reached/harness_type/manual evidence;
- valid synthetic map passes.

For each negative case, assert the expected diagnostic category/message. A test must not pass because of an unrelated cardinality or missing-file error.

The existing 15/15 result is Executor-reported; after changes, record exact new output and exit code. The actual repository map validation must also pass.

## 4. Work Package C — provenance and durable records

Create:
- research/R26_STAGE1I_R2_CORRECTIVE_REPORT.md

Update:
- research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json
- research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md
- scripts/_r26i_validator.py
- research/R26_STAGE1I_FINAL_FINDING_AUDIT.md (dated addendum; preserve historical text)
- research/R26_STAGE1I_TEST_EVIDENCE.md
- research/R26_PC1_AUDIT_SUMMARY.md
- planner/latest_plan.md
- planner/GLEPPO_R26_HANDOFF.md
- planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md
- status.json

Record exact:
- R1 source snapshot: 29325cfa16441154c833f381f208747b57627a79;
- R1 parent: 539f74d5c898abc144992fff4a413a30744c1cc9;
- R1 final commit: 4d2ff06ee01146533501589b264d33ddd30ffcbe;
- R1 Planner review commit: dcdcef5b2e7e68a6590d95c90c4caf453399c127;
- R2 parent and final full SHAs;
- main SHA and branch ahead/behind.

Do not write “(this commit)” when the exact final SHA is available.

All durable records must say:
- Stage 1I: REQUEST_CHANGES, not accepted;
- Stage 1I-R1: REQUEST_CHANGES, not accepted;
- Stage 1I-R2: Executor complete / awaiting Planner independent review only after the actual commit;
- PC1 BLOCKED; R4 PROPOSED / NOT APPROVED;
- Formal G3 FAIL;
- Family C NOT ACCESSED;
- Registered PC1 NOT EXECUTED;
- controller training NOT AUTHORIZED / NOT STARTED;
- 450/450 EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED;
- model/API calls and production runtime calls remain Executor attestations unless independently evidenced;
- R21-C1 is DAC, not operator comparison;
- PPO superiority over fixed/rule/LinUCB remains untested;
- Phase 1/R24/PC1 R4 reward/state/gamma/split/budget discrepancies remain unresolved;
- next gate is Planner independent review of R2, not PC1 or protocol reconciliation.

Do not delete status history or prior Planner decisions.

## 5. Hard boundaries

- No production source changes.
- No tests/ changes.
- Only documentation, JSON/Markdown evidence map and non-production scripts/_r26i_validator.py may change.
- No registered PC1 execution.
- No Family C listing/loading/inspection/execution/tuning.
- No controller training, PPO, Q-learning or Bandit training.
- No Formal G3 efficacy.
- No model/API calls.
- No production runtime calls or signing-key access.
- No frozen R1–R25 evidence/manifest changes.
- No main update/merge.
- No reset/rebase/force-push.
- No cross-project code/data/report reuse.

Report model/API and production-runtime counts as Executor attestations; repository-only inspection cannot prove remote runtime counters.

## 6. Completion report and stop condition

Submit:
1. exact branch, parent, source snapshot and final SHA provenance;
2. list of changed files;
3. exact 42 IDs and JSON/Markdown consistency;
4. all relevant tests per Finding and exact source ranges;
5. corrected call paths and branch reachability;
6. disposition counts mechanically derived from JSON;
7. validator positive/adversarial self-test output with targeted diagnostics and exit codes;
8. actual map validation output;
9. R12/R14/R17/R20/R23/R28/R39/R40/R41/R44/R47/R50/R51/R52 corrections;
10. updated durable records and hard-boundary attestations.

After R2 is committed and all durable records are updated, stop and wait for Planner independent review. Do not proceed to R26_ECOS_PROTOCOL_RECONCILIATION, PC1, Family C, controller training or Formal G3.

**Success state:** R26_STAGE1I_R2_READY_FOR_PLANNER_REVIEW.  
**Not success:** Executor self-approval, protocol reconciliation, PC1 authorization, Family C access or controller training.
