# R26 Stage 1I-R1 Planner Independent Review

**Date:** 2026-11-04  
**Repository:** yujian777555/GLEPPO  
**Branch:** r25-handoff  
**Reviewed R1 final HEAD:** 4d2ff06ee01146533501589b264d33ddd30ffcbe  
**R1 parent:** 539f74d5c898abc144992fff4a413a30744c1cc9  
**Map source snapshot:** 29325cfa16441154c833f381f208747b57627a79  
**Prior Stage 1I Planner review:** dfd7ef909ba4ee97e01c4bb57b0177ae8869d61c  
**Main:** 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e  
**Branch relation:** 211 ahead / 0 behind main  
**Decision:** REQUEST_CHANGES — STAGE 1I-R1 NOT ACCEPTED  
**Next task:** Stage 1I-R2 corrective semantic evidence and validator hardening.

---

## 1. Executive decision

Stage 1I-R1 has made substantial structural progress:
- the JSON map contains exactly 42 unique IDs R12–R53;
- the Markdown rendering contains 42 unique headings;
- Markdown and JSON dispositions agree row by row;
- the reported arithmetic 26 VERIFIED_FIXED / 14 PARTIALLY_FIXED / 1 OPEN / 1 UNVERIFIABLE sums to 42;
- R53 remains PARTIALLY_FIXED;
- R18 has 13 manual references and explicit cost-unit distinctions;
- durable handoff documents were updated;
- the commit does not modify production source or tests/.

However, **Stage 1I-R1 is not accepted**. The semantic map is not yet a trustworthy 42-Finding evidence record. Several test-to-source call paths are factually wrong, multiple cited tests do not exercise the acceptance condition claimed, relevant tests are omitted, source symbols are missing or misidentified, and the validator accepts incomplete line metadata.

The arithmetic is mechanically correct. That does not make the semantic classifications correct. Do not advance to R26_ECOS_PROTOCOL_RECONCILIATION.

## 2. Repository and provenance verification

Verified remotely:
- r25-handoff points to 4d2ff06ee01146533501589b264d33ddd30ffcbe.
- The R1 commit parent is 539f74d5c898abc144992fff4a413a30744c1cc9.
- The R1 commit is a descendant of the prior Planner review/prompt history; the previous Planner review commit remains in ancestry.
- main remains 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e.
- r25-handoff is 211 commits ahead and 0 behind main.
- The R1 commit changes 11 files: map JSON/Markdown, corrective report, two Stage 1I evidence reports, validator, latest plan, handoff, next-session prompt, cumulative PC1 summary, and status.json.
- No gleppo/ production source or tests/ file is modified in the R1 commit.
- GitHub reports 0 check runs and 0 commit status entries for the R1 SHA.

The report records the R1 final commit as “(this commit)” instead of the exact SHA. status.json also omits the R1 final SHA and the map source snapshot from the R1 provenance object. Correct these in R2.

Verification scope: remote GitHub source/file inspection and static call-path review. The Planner did not independently execute the 450-test suite or the 15 helper self-tests. The 450/450 result remains EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED. Model/API call count and production-runtime count remain Executor attestations.

## 3. Accepted structural work

The following parts are accepted as accurate:
1. JSON contains 42 rows, unique IDs R12–R53, no missing or unknown IDs.
2. Markdown has 42 unique Finding headings and all Markdown dispositions match the JSON dispositions.
3. The arithmetic is 26 + 14 + 1 + 1 = 42.
4. R53 is PARTIALLY_FIXED and its cited status-consistency test is correctly described as indirect evidence only; it does not prove status-only hash invariance.
5. R18 is correctly MANUAL, with no behavioral test, and the manual references distinguish planned slots, actual uncached replicas, cached bundles, actual model CTX, and production tokens/latency.
6. The tautological test_action_genotype_excluded is not cited as evidence.
7. R21-C1 remains DAC evidence, not an operator-selection experiment.
8. PPO superiority over fixed/rule/LinUCB remains unproven.
9. The commit contains no production source/test changes and main is unchanged.

These accepted parts do not resolve the blockers below.

## 4. Blocking finding F1 — test evidence arrays omit relevant tests

The R1 prompt required every relevant test for multi-part acceptance criteria, with exact declarations, assertions, source symbols and call paths. The map contains only 40 test_evidence entries across 39 mapped rows. Several rows omit direct tests that already exist in the repository.

### R12 — cache/replica separation

The map cites only TestR12BudgetLedger.test_init_evaluation (tests/test_r12_r17.py:37–42). That test passes cache_bundle_delta=0 and does not exercise a cache hit. It cannot prove “bundle-level cache hits must not inflate replica counts.”

Relevant direct tests omitted from the R12 evidence array include:
- test_cache_bundle_hit_adds_zero_replicas (tests/test_r12_r17.py:44–48);
- test_shared_evaluator_deltas (line 66 onward);
- test_multiple_generations;
- test_planned_independent_of_cache.

The R12 row is VERIFIED_FIXED while its own uncovered_acceptance_conditions still says “Full bundle/replica unit reconciliation.” Add all relevant direct tests and reconcile the uncovered condition before deciding disposition.

### R14 — r_hat evidence omitted

The map cites test_q_hat_excludes_extra_immediate (tests/test_r12_r17.py:185–189), but the criteria also require r_hat to include extra_immediate. The direct test test_r_hat_includes_extra_immediate starts at line 191 and is not in the evidence array. test_extra_immediate_does_not_pollute_q_hat starts at line 197 and is also omitted.

Do not label r_hat evidence as indirect when a direct test exists but is absent from the row.

### R17 — replayable evidence and counter breakdown

The map cites only test_evidence_contains_provenance (tests/test_r12_r17.py:312–327). It omits test_evidence_records_have_required_fields (line 329 onward). More importantly, the row says “Full counter breakdown” is uncovered but still marks VERIFIED_FIXED; its rationale claims counter breakdown is covered by R28. R28's mapped test does not test actual replica/cache counter breakdown.

The source symbols build_evidence and save_evidence do not exist in gleppo/pc1.py. Actual relevant source includes run_pc1_analysis, save_evidence_artifact, load_evidence_artifact and replay_from_artifact. Correct the symbols and line ranges.

### R20 — override-path tests omitted and CRN call path is wrong

The row cites only test_same_crn_identical_across_genotypes. It omits direct tests for task, rollout, replicate isolation and the override path, including test_override_path_preserves_task_replicate_isolation (tests/test_r19_r25.py:136 onward).

The row's call path says effective_seed_parts -> crn_seed. That call does not exist. Evaluator.effective_seed_parts is in gleppo/evaluator.py:57–76 and constructs its own typed seed tuple. The crn_seed function is separately defined in gleppo/pc1.py:230–239. The map also assigns pc1.crn_seed to the wrong file, gleppo/evaluator.py.

Separate the evaluator seed path from the standalone PC1 crn_seed helper. Do not claim one calls the other.

### R23 — direct round-trip test omitted

The row cites test_evidence_contains_D_adv_CIs (tests/test_r19_r25.py:295 onward), but omits test_round_trip_serialize_replay (line 310 onward), which directly saves, reloads and replays evidence. The row's build_evidence and replay_evidence source symbols do not exist. Use the actual source symbols and test path.

### R39 — direct CRN tests and R20 cross-reference incomplete

The narrative evidence_boundaries lists seven direct CRN tests, but test_evidence contains only test_delimiter_no_collision and the R16 cross-genotype evaluator test. It omits:
- test_same_params_reproducible (tests/test_r39_r42.py:65);
- test_task_change_changes_seed (line 74);
- test_state_change_changes_seed (line 77);
- test_rollout_change_changes_seed (line 80);
- test_replicate_change_changes_seed (line 83);
- test_none_empty_string_no_collision (line 86).

The R20 cross-genotype test test_same_crn_identical_across_genotypes (tests/test_r19_r25.py:99 onward) is described in evidence_boundaries but is not an actual test_evidence entry with exact assertions/source/call path.

The tautological test at line 96 remains correctly excluded. Keep the structural action-exclusion claim distinct from behaviorally tested genotype invariance and from the unimplemented action-varying PC1 collector integration.

### Other material omissions

- R26 cites only test_protocol_document_exists (tests/test_r26_r32.py:336–338), omitting test_document_fields_match_code (line 346 onward), which directly checks document fields against code.
- R28 cites test_registered_budget_exact (tests/test_r26_r32.py:116–120). That test only checks constants. It does not call BudgetLedger.reconcile. The direct test_ledger_components_sum_to_total is at lines 122–133 and is omitted.
- R30 cites only test_missing_manifest_hash_rejected; the same class has direct missing-runtime and missing-evaluator-version tests. Its call path is also misidentified; run_pc1_analysis rejects the missing manifest before validate_records is reached.
- R37 cites only test_missing_protocol_hash_rejected and omits test_missing_plan_hash_rejected, test_wrong_protocol_hash_rejected and test_wrong_plan_hash_rejected. Its call path is incorrectly described as validate_records.
- R40 cites only test_full_consistency_passes, omitting mutation_version, mutation_status, mutation_seed_contract and mutation_reward tests in tests/test_r39_r42.py:108, 118, 130 and 140.
- R41 cites only test_save_load_roundtrip, omitting test_tampered_artifact_rejected, test_defensive_copy_prevents_mutation and test_wrong_hash_rejected.
- R22, R29, R33, R35 and R42 also cite only one representative test while their criteria contain multiple independently testable conditions. Re-evaluate their full relevant test sets.

This is not a request to inflate the map with irrelevant tests. Include every test that actually proves an acceptance subcondition and explicitly exclude tests that do not reach the claimed code path.

## 5. Blocking finding F2 — false test-to-source call paths and wrong source symbols

Several entries describe a test as exercising a function or branch that it does not reach.

### R28 — reconcile branch not reached

The mapped test test_registered_budget_exact only compares four constants at lines 117–120. It does not instantiate BudgetLedger, call reconcile, or exercise the reconcile branch. The call_path “test -> reconcile -> exact match” is false. Map test_ledger_components_sum_to_total at lines 122–133 for actual reconcile evidence.

### R30 and R37 — wrong source path

The tests call run_pc1_analysis. The missing metadata/hash checks occur in run_pc1_analysis before validate_records is called. The current call_path and source symbol validate_records are therefore inaccurate. Cite run_pc1_analysis and the exact early-guard lines, then separately map tests that actually reach later record validation.

### R38 — branch explanation contradicts branch flag

The R38 test constructs an ApprovalGate without trusted_artifact or approval_key. ApprovalGate.check exits on the missing TrustedApprovalArtifact before reaching the empty protocol_hash check. The map correctly sets branch_reached.reached=false, but its explanation still says the test exercises the intended path. Replace the generic explanation with the exact early-exit condition and line.

### R44 — loader test is not an end-to-end registered-analysis test

test_missing_protocol_hash_rejected calls load_plan_artifact directly. It does not call run_pc1_analysis and cannot by itself prove that registered analysis requires plan_artifact_path and validates records against the loaded artifact.

Source inspection shows run_pc1_analysis at gleppo/pc1.py:636 onward requires plan_artifact_path, calls load_plan_artifact, compares plan_hash and calls validate_provenance_against_plan. Cite that source path as MANUAL evidence. Do not describe the isolated loader test as end-to-end proof. If no end-to-end test exists, state that explicitly and re-evaluate disposition.

### R47 — alternative mapping test does not reach plan ID/version checks

load_plan_artifact compares the artifact's actual mapping hash with the registered hash before checking plan_id and plan_version. test_alternative_mapping_rejected changes the mapping and recomputes its self-hash, so it fails at the registered-hash comparison. It proves noncanonical mapping rejection, not that the later plan ID/version branches were reached. Correct the call_path and branch description; cite source-level ID/version checks separately.

### R50 — test calls artifact.verify(), not ApprovalGate.check()

tests/test_r54_r59.py:146–155 constructs a TrustedApprovalArtifact and calls art.verify(...) directly. It does not call ApprovalGate.check(). The map's source symbol ApprovalGate.check and call_path “test -> ApprovalGate.check -> hash mismatch” are false.

The actual direct test path is test -> TrustedApprovalArtifact.verify -> protocol_hash mismatch. ApprovalGate.check at gleppo/pc1.py:1320–1365 does call trusted_artifact.verify, but the current canonical protocol is PROPOSED, so test_proposed_rejects_all_flags_true exits at the proposed-status guard before the HMAC verification call. State this distinction. There is no positive approved-path gate integration evidence.

### R51 — protocol hash test is not plan hash test

tests/test_r54_r59.py:284–287 compares compute_protocol_hash(doc) with REGISTERED_PROTOCOL_CONTENT_HASH. It does not test REGISTERED_PLAN_HASH. The actual REGISTERED_PLAN_HASH constant is gleppo/pc1.py:978. Do not use the protocol-content hash test as evidence for the registered plan hash.

The source does contain plan identity/version checks in load_plan_artifact, but the cited test does not reach those branches. Add exact source-level evidence and correct the disposition if required.

### R52 — nonexistent source symbol

There is no validate_reward_schema function in gleppo/pc1.py. The actual implementation is in protocol_consistency_check (lines 126–223), with nested helpers _check_exact_keys (line 172) and _is_strict_number (line 176). Correct the symbol and call path.

### Other nonexistent/mislocated symbols

- R17: build_evidence and save_evidence are not defined in gleppo/pc1.py.
- R23: build_evidence and replay_evidence are not defined; use the actual analysis/serialization/replay functions.
- R25: GatedPC1Runner is not defined in gleppo/pc1.py; the source has SyntheticGateHarness and create_default_gated_runner.
- R20: crn_seed is in gleppo/pc1.py, not gleppo/evaluator.py.
- R24 and R26 use the incomplete source file path “research/” rather than exact artifact paths.

## 6. Blocking finding F3 — unresolved source-symbol line ranges

The JSON map contains source_symbols with null start_line/end_line for:
- R17: build_evidence, save_evidence;
- R20: pc1.crn_seed;
- R23: build_evidence, replay_evidence;
- R24: SMOKE_RAW.json, COST_BASELINE.md;
- R25: GatedPC1Runner;
- R26: PC1_PROTOCOL_R4_PROPOSED.md;
- R48: validate_reward_schema;
- R51: REGISTERED_PLAN_HASH;
- R52: validate_reward_schema.

The R1 prompt required exact source symbol/file/line ranges. These null ranges violate that requirement. Some symbols also do not exist or are assigned to the wrong file, as described above.

The validator does not inspect source_symbols at all, so the reported VALIDATION PASSED result cannot detect these missing or false source references.

## 7. Blocking finding F4 — validator self-test and schema checks are incomplete

The AST rewrite is an improvement, and the validator does check the map's ID set, declaration tuples and declaration line values. However, its own adversarial suite does not establish all claimed behavior.

### Wrong-file self-test duplicates missing-file test

- The wrong_file_path case at scripts/_r26i_validator.py:418 changes the map path to tests/wrong_file.py, which does not exist.
- The missing_source_file case at line 480 also uses a nonexistent file.
- The second valid fixture file is created at line 292 but is not used to test an existing-file/wrong-owner mismatch.

Add a case that points a mapped declaration at an existing fixture file that does not contain the declared class/function. Assert that it fails specifically because the declaration tuple is absent from that file, not merely because the file is missing.

### Null declaration line values pass

At lines 243 and 247, declaration_start_line and declaration_end_line are compared only when the supplied value is not None. A map row with null start/end values therefore bypasses exact line validation. Require positive integer line values and reject null, bool, string or non-positive values.

### Source-symbol metadata is not validated

The helper checks that source_symbols is present, but does not validate each symbol's name, exact file path, positive integer start/end lines, or source-range ordering. The current map's null source ranges pass. Add strict structure checks and reject unresolved ranges for every mapped source symbol.

### Other schema gaps

- schema_version is not checked against the supported version 1.0;
- required fields are checked for presence but not all field types;
- assertion_expressions item structure and line/expression types are not checked;
- branch_reached must be an object with a boolean reached field and a nonempty, specific explanation;
- harness_type needs an explicit allowed enum;
- manual_evidence entries need source, line/range, value and note validation;
- the helper does not compare the Markdown rendering's IDs/dispositions with the canonical JSON map. The current rendering happens to match, but that consistency should be checked or explicitly designated as a manual-only check.

The disclaimer about not proving semantic assertion truth remains correct. Do not overstate the helper as a semantic validator.

## 8. Blocking finding F5 — acceptance criteria are compressed and some VERIFIED_FIXED dispositions are unsupported

The JSON's complete_original_acceptance_criteria arrays still compress several original review requirements into broad phrases.

Examples:
- R39 omits the explicit schema/version tag requirement and confirmation that every CRN call site uses the same canonical contract from the Seventh Review.
- R50 omits several required signed-payload fields and the independent trust-anchor/gate-consumption requirements from the Tenth Review.
- R51 omits protocol-content binding and the full registered plan artifact identity/hash requirements from the Tenth Review.

Preserve every independently testable subcondition from the original review. Do not collapse multiple required fixes into one vague criterion.

Several rows are VERIFIED_FIXED even though their only mapped test does not exercise the claimed criterion, or their own uncovered list is nonempty:
- R12: cache-hit behavior is not tested by the cited initialization test.
- R17: full counter breakdown remains uncovered; the cited R28 test does not prove it.
- R26: the cited test checks file existence only; the document/code comparison test is omitted.
- R28: the cited test checks constants only, not reconciliation.
- R40: the cited test is a happy-path consistency check; mutation tests are omitted.
- R44: the cited test is an isolated artifact-loader test, not registered analysis integration.
- R51: the cited test checks protocol content hash, not plan hash or plan identity.

The 26/14/1/1 arithmetic is accepted as mechanically computed. The semantic classifications are not accepted. Re-evaluate every row against every original acceptance subcondition. The previous counts are not a target.

R45 also needs clarification: its rationale says the source has _DuplicateKeyChecker, but evidence_type is NONE and manual_evidence is empty. Either cite the actual parser implementation as MANUAL evidence and retain the missing direct parser test as uncovered, or remove the source claim.

## 9. Provenance and evidence status

- Exact R1 final commit is 4d2ff06ee01146533501589b264d33ddd30ffcbe.
- The corrective report currently says “(this commit)” rather than the exact SHA.
- The JSON map source_snapshot is 29325cfa16441154c833f381f208747b57627a79, but the R1 report/status provenance does not consistently record it.
- status.json lacks stage_1i_r1_final_commit in the R1 provenance object.
- The map/Markdown content and source declarations are inspectable from the repository.
- The 15 self-test results and map validation result are Executor-reported; the Planner has not executed the helper.
- GitHub has zero check runs and zero commit statuses for the exact R1 SHA.
- 450/450 remains EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED.
- Model/API calls = 0 and production runtime calls = 0 remain Executor attestations, not independently verified by this repository-only review.

## 10. Hard boundaries

The reviewed R1 commit changes documentation, JSON evidence, status and the non-production validator only. No production source or tests/ changes are present in the commit diff.

The following gates remain unchanged:
- PC1 BLOCKED; R4 PROPOSED / NOT APPROVED.
- Formal G3 FAIL.
- Family C NOT ACCESSED.
- Registered PC1 NOT EXECUTED.
- Controller training NOT AUTHORIZED / NOT STARTED.
- No model/API calls or production runtime are authorized.
- No R1–R25 frozen evidence/manifest modifications.
- No main merge/update/reset/rebase/force-push.
- No cross-project artifacts.

## 11. Planner decision

**REQUEST_CHANGES — R26_STAGE1I_R1_SEMANTIC_EVIDENCE_AND_VALIDATOR_NOT_YET_AUDITABLE.**

Stage 1I-R1 is not accepted. Remain in Stage 1I. The next task is Stage 1I-R2 corrective completion. After R2 is submitted, Planner must independently inspect the corrected map, exact call paths, source ranges, adversarial validator cases and disposition rationale.

Only after Stage 1I is formally accepted may a separate R26_ECOS_PROTOCOL_RECONCILIATION stage begin.

## 12. R2 stop condition

Submit the corrected map and validator, update the durable records and status, and stop for Planner review. Do not proceed to protocol reconciliation, PC1, Family C, controller training or Formal G3.

**Final status:** R1 received; Planner REQUEST_CHANGES; R2 required.
