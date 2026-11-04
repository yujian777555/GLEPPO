# GLEPPO R26 Stage 1G — Planner Independent Review

**Review date:** 2026-11-04  
**Repository:** yujian777555/GLEPPO  
**Branch:** r25-handoff  
**Stage 1G Executor commit:** 69781d1166f9e28e7535915aad00af859c1b2734  
**Stage 1G source snapshot claimed:** 29325cfa16441154c833f381f208747b57627a79  
**R25 base:** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**main at review:** 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e  
**Planner decision:** REQUEST_CHANGES  
**PC1:** BLOCKED

---

## 1. Executive decision

Stage 1G corrects the Stage 1F disposition arithmetic and substantially improves the test declaration map. The 42 detailed rows now add to 42, and the 218 declared test-function count is independently confirmed.

However, Stage 1G is **not accepted as a completed finding-level evidence audit**.

Blocking reasons:

1. **Two of the 39 mapped function names still do not match actual declarations.** Planner independently parsed the seven suites at the claimed source snapshot. Only 37/39 file/class/function/line tuples match.
2. **The evidence table does not contain actual assertion expressions or source call paths.** Its Assertion column contains generic labels such as "Budget counters", "Fail-closed", "Role separation", and "CRN correctness". It has no exact assertion lines, source symbols, call paths, or uncovered acceptance conditions.
3. **The extractor remains an inventory script, not a map validator.** It does not parse the 42-row report table, compare each mapping, inspect assertion bodies, or trace source calls.
4. **Some mapped tests do not prove the Finding criterion.** R39 is mapped to a tautological equality assertion; R53 is mapped to a seed-schema mutation test unrelated to lifecycle-status hash invariance. R49's actual related test only exercises the protocol consistency checker, not the required approval lifecycle transition.
5. **At least R19 is over-classified.** Its original acceptance criterion requires explicit Planner/protocol approval before registered PC1 collection. The canonical protocol remains explicitly PROPOSED / NOT APPROVED; the test suite itself asserts the status is proposed. Unless a valid approval artifact and Planner decision are produced, R19 cannot be VERIFIED_FIXED.
6. **R18 manual evidence is not fully recorded in the Stage 1G report.** Planner independently confirms the current raw/cost figures, but the Stage 1G artifact does not include the exact line references required by its task.
7. **Report provenance fields are unresolved placeholders.** The audit says REPORT_COMMIT: (this commit) and CURRENT_BRANCH_HEAD: (this commit) rather than recording the exact SHA.
8. **Durable handoff files were not advanced.** The Stage 1G commit changed only the audit, test-evidence file, extractor and status.json. planner/latest_plan.md, planner/GLEPPO_R26_HANDOFF.md and planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md still describe Stage 1F as the current Planner decision / Stage 1G as the next task. This conflicts with status.json saying Stage 1G is complete.

Current Planner state:

**R26_STAGE1G_REPORT_RECEIVED_REQUEST_CHANGES; EXACT_TEST_MAP_AND_SEMANTIC_EVIDENCE_RECONCILIATION_REQUIRED; PC1 BLOCKED.**

## 2. Repository provenance

Verified:
- r25-handoff HEAD = 69781d1166f9e28e7535915aad00af859c1b2734;
- main HEAD = 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e;
- main → r25-handoff = 168 ahead, 0 behind;
- R25 base → r25-handoff = 87 ahead, 0 behind;
- Stage 1G commit changes only:
  1. research/R26_STAGE1G_FINAL_FINDING_AUDIT.md;
  2. research/R26_STAGE1G_TEST_EVIDENCE.md;
  3. scripts/_r26g_extract_tests.py;
  4. status.json.

No production source or test file changed in the Stage 1G commit.

The Stage 1G report's SOURCE_SNAPSHOT is 29325cfa... Planner independently parsed all seven named test suites at this exact SHA. The report commit and current branch HEAD are both 69781d1166f9e28e7535915aad00af859c1b2734; replace the two "(this commit)" placeholders with that exact SHA in the corrective report metadata.

For commit 69781d1:
- GitHub commit status: pending, zero status entries;
- check runs: zero;
- Actions runs targeting this exact head SHA: zero.

Therefore 450/450 remains **EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED**. Planner did not independently run the test suite and no raw stdout/stderr or CI run for this exact commit was found.

## 3. Accepted Stage 1G corrections

### 3.1 Disposition arithmetic

The 42-row Stage 1G table contains:
- VERIFIED_FIXED = 27;
- PARTIALLY_FIXED = 13;
- OPEN = 1;
- UNVERIFIABLE = 1;
- total = 42.

This corrects Stage 1F's erroneous 22/15/1/1 summary.

The Stage 1G category counts also sum to 42:
- Budget 5;
- Seed/CRN 5;
- Protocol 9;
- Approval 5;
- Provenance 9;
- Runner 3;
- Statistics 2;
- Evidence 2;
- Cost 2.

These are accepted as the arithmetic of the submitted table, not acceptance of all 27 VERIFIED_FIXED dispositions.

### 3.2 Test inventory

Planner independently parsed the seven suites at source snapshot 29325cfa...:

| Test file | Declared functions |
|---|---:|
| test_r8_r9_r11_pc1.py | 25 |
| test_r12_r17.py | 35 |
| test_r19_r25.py | 38 |
| test_r26_r32.py | 34 |
| test_r33_r38.py | 37 |
| test_r39_r42.py | 26 |
| test_r54_r59.py | 23 |
| **Total** | **218** |

There are 42 distinct test classes across these seven suites. Both inventory counts are accepted.

### 3.3 Three NONE rows

The Stage 1G register correctly records:
- R18: NONE (manual documentation evidence);
- R45: NONE (no direct duplicate-key parser test);
- R46: NONE (no independent trusted-authorization provenance).

R18's manual evidence is independently corroborated by the source artifacts, but the Stage 1G report still needs exact line references (see §7).

### 3.4 Dispositions that remain directionally correct

The following submitted dispositions are supported in principle and should remain unless new evidence changes the underlying criteria:
- R15 OPEN: registered collection/rollout runner is not implemented; execute_registered_pc1() refuses execution.
- R24 PARTIALLY_FIXED: the test only checks a wall-clock substring and fixed counters; it does not parse report labels/units.
- R38 PARTIALLY_FIXED: the mapped test constructs no trusted artifact/key, so the gate can reject before reaching the intended protocol-hash branch.
- R42 PARTIALLY_FIXED: the mapped test calls TrustedApprovalArtifact.verify() directly; it is not a gate-level integration proof.
- R43 PARTIALLY_FIXED: the test proves that canonical PROPOSED status denies execution, but does not establish a valid APPROVED-path integration.
- R45 PARTIALLY_FIXED: no direct duplicate-key protocol parser test.
- R46 UNVERIFIABLE: no independent trusted authorization-source provenance.
- R48 PARTIALLY_FIXED: existing tests cover only part of the structured schema/adversarial mutation requirements.
- R49 PARTIALLY_FIXED: lifecycle transition behavior remains unproven.
- R50 PARTIALLY_FIXED: artifact-level verification tests do not prove full gate-level trust integration.
- R52 PARTIALLY_FIXED: estimator/seed adversarial coverage is incomplete.
- R53 PARTIALLY_FIXED: no direct status-only content-hash invariance test.
- R18 VERIFIED_FIXED is supportable as manual documentation reconciliation, provided the exact evidence lines are added.

## 4. Blocking defect A — two test function names are still wrong

Planner parsed every class and def test_* declaration in all seven suites and compared the Stage 1G table's file/class/function/line tuples.

Result:
- 42 Finding rows;
- 39 rows claim a direct test;
- 37/39 exact file/class/function/line matches;
- 2/39 mapped function names are not declared in the stated class/file;
- 3 NONE rows: R18, R45, R46.

### R31

Stage 1G claims:
- file: test_r26_r32.py;
- class: TestR31GateSemantics;
- function: test_all_booleans_true_still_denied;
- line: 372.

Actual declaration:
- test_all_booleans_true_still_denied_for_proposed_protocol at line 372.

The row's disposition PARTIALLY_FIXED is directionally reasonable, but its function name is not exact. The test exercises SyntheticGateHarness.execute_unit() with a PROPOSED protocol and asserts PC1ExecutionRefused; it does not prove a complete collection/rollout runner exists.

### R49

Stage 1G claims:
- file: test_r39_r42.py;
- class: TestR40ProtocolConsistency;
- function: test_mutation_status_not_checked;
- line: 118.

Actual declaration:
- test_mutation_status_not_checked_by_consistency at line 118.

The actual test changes doc["status"] to "APPROVED", calls protocol_consistency_check(path), and asserts r["all_pass"]. It does not exercise ApprovalGate, a proposed→approved transition, a trusted approval artifact, or content-hash invariance. PARTIALLY_FIXED remains appropriate, but the function name must be corrected and the scope of proof stated accurately.

## 5. Blocking defect B — the map is not a semantic evidence map

research/R26_STAGE1G_TEST_EVIDENCE.md has columns:
ID | Test File | Test Class | Test Function | Line | Assertion.

The Assertion entries are short labels, not assertion expressions. The document has no columns or entries for:
- test start/end line ranges;
- actual assertion expressions and exact assertion line numbers;
- source symbol/function exercised;
- call path from test to source;
- whether the test reaches the intended validation branch;
- acceptance conditions proved;
- acceptance conditions still uncovered;
- rationale linking the test to the original Finding.

The final audit table is only a 42-row file/class/function/line/disposition list. It does not preserve each original Finding's failure mode and acceptance criteria.

This fails the Stage 1G prompt's explicit requirement to provide, for each Finding, the exact test body/assertions, source call path, intended branch and uncovered acceptance conditions.

Examples:

### R13

Mapped test test_missing_action_rejected covers one rejection case. The same class also contains tests for wrong horizon, nonfinite rewards, cluster conflicts, duplicate keys, invalid actions/roles, registered state shape, extra-immediate length, and missing-action default-zero behavior. The Stage 1G evidence map does not enumerate these tests or identify which parts of the original fail-closed criterion they prove.

### R14

Mapped test test_q_hat_excludes_extra_immediate proves one Q-hat exclusion property. The class also contains test_r_hat_includes_extra_immediate and test_extra_immediate_does_not_pollute_q_hat. The evidence map omits these additional relevant tests and their assertions.

### R16 / R20

The mapped same-CRN test alone does not show the full seed contract. Relevant tests also cover changed state/rollout/replicate/task, explicit override behavior, cache separation, and operator RNG independence. The exact tests and effective-seed call path must be documented.

### R17 / R23

One provenance-key test or one evidence-field-presence test does not establish the full replay contract. The maps must enumerate required record fields, gold-label isolation, serialization/replay equality, decision statistics, provenance and budget components.

### R21 / R22 / R29 / R30

The map selects one negative test per Finding but omits other relevant tests for budget over-cap/understatement/surplus samples/reconciliation, missing task/episode IDs, unknown episodes, wrong cluster/task/family mappings, and missing runtime/evaluator/input-hash provenance.

### R33 / R34 / R35 / R37

The maps omit important related adversarial tests:
- R33 has Q/extra atomicity, over-budget, compensating-slot and unchanged-snapshot cases;
- R34 has None/literal NONE, empty/literal EMPTY, delimiter, cache collision and identical-key cases;
- R35 has unknown episode, wrong cluster, wrong task and wrong family cases;
- R37 has missing/wrong protocol hash and missing/wrong plan hash cases.

### R40 / R41 / R44 / R47 / R51

The map must distinguish ordinary positive round-trip checks from tamper detection, defensive-copy checks, wrong-hash rejection, registered identity binding and noncanonical-but-self-hashed plan rejection. A single selected method does not establish all of those properties.

Stage 1H must enumerate all directly relevant tests per Finding. If one test is only indirect or reaches an earlier guard, label it as such; do not call it direct proof.

## 6. Semantic mismatch / disposition concerns

### 6.1 R39 — mapped test is tautological

Stage 1G maps R39 to test_same_params_reproducible at tests/test_r39_r42.py:65.

Its assertion at line 66 is:

self.assertEqual(crn_seed("T1", "s1", 0, 0), crn_seed("T1", "s1", 0, 0))

Both operands are the same call with identical arguments. This assertion is tautological and does not independently test the canonical CRN encoding.

Relevant actual tests in the same class include:
- test_delimiter_no_collision at line 68;
- test_task_change_changes_seed at line 74;
- test_state_change_changes_seed at line 77;
- test_rollout_change_changes_seed at line 80;
- test_replicate_change_changes_seed at line 83;
- test_none_empty_string_no_collision at line 86.

The test_action_genotype_excluded assertion at line 96 is also a repeated identical function call; explain its structural limitation rather than presenting it as an independent context-invariance experiment.

The Stage 1G mapping must be rebuilt around the actual delimiter and component-isolation tests. Do not use the tautological same-call assertion as the evidence anchor.

### 6.2 R49 — related test is not a lifecycle-transition test

The actual method test_mutation_status_not_checked_by_consistency verifies only that changing status to APPROVED does not make protocol_consistency_check() fail. It does not verify:
- proposed/unapproved gate denies;
- approved state with a valid trusted approval artifact can pass;
- changed immutable content after approval is denied;
- status is separated from content hash.

Keep R49 PARTIALLY_FIXED unless these exact transition requirements are independently evidenced.

### 6.3 R53 — mapped test is unrelated to the Finding

Stage 1G maps R53 to test_mutation_seed_contract_fails at tests/test_r39_r42.py:130. That test mutates seed_schema and checks protocol_consistency_check() fails. It is not a status/hash test.

The related existing method is test_mutation_status_not_checked_by_consistency at line 118, but the Tenth Review explicitly says that test does not prove status is excluded from the content hash.

R53 must be mapped to the related test only as partial/indirect evidence, and the audit must state that no direct status-only hash invariance test exists. Keep PARTIALLY_FIXED.

### 6.4 R19 — VERIFIED_FIXED is not supported while protocol remains proposed

Original R19 (Fourth Review) requires:
1. one canonical versioned protocol revision agreeing with code;
2. estimator, sample roles, sample counts, cluster unit, seed contract and full budget arithmetic;
3. explicit Planner/protocol approval before registered data collection;
4. a protocol-consistency test that checks the decision-critical constants.

Current research/PC1_PROTOCOL_R4_PROPOSED.md states:
- line 3: Status: PROPOSED / NOT APPROVED;
- line 8: approval is NOT APPROVED and requires explicit Planner decision;
- line 14: document does not authorize data collection;
- line 110: Planner approval and independent review approval are prerequisites;
- canonical JSON line 129: status = PROPOSED_NOT_APPROVED.

TestR19ProtocolFreeze.test_protocol_status_not_approved also asserts that status is PROPOSED.

The canonical document and consistency checks are meaningful progress, but explicit protocol approval has not occurred. Unless a separately authorized and verifiable approval artifact exists, R19 must be downgraded to PARTIALLY_FIXED, not VERIFIED_FIXED. Recount dispositions after all semantic reviews; do not preserve 27/13 merely to keep the previous total.

## 7. R18 manual evidence — accepted with required citation repair

Planner independently rechecked the source snapshot:

research/SMOKE_RAW.json:
- line 276: wall_clock_s = 0.0261;
- lines 277–279: planned init 32, offspring 96, total 128;
- line 284: actual replicas 112;
- line 291: production LLM tokens UNMEASURED;
- line 293: explicit units note that planned slots are NOT actual CTX.

research/COST_BASELINE.md:
- line 4: production tokens/latency UNMEASURED;
- line 22: stub wall-clock 0.0261 s;
- line 30: total planned smoke slots 128;
- line 44: LLM tokens UNMEASURED;
- line 47: actual replicas mean uncached replica executions;
- line 82: PC1 planned slots 45,440;
- line 101: 0.0261 s is stub smoke latency, not production;
- lines 110–111: 45,440 is used as a planned workload proxy for forecasting, not a measured production cost.

The values reconcile. R18 may remain VERIFIED_FIXED as manual documentation evidence. Stage 1H must add these exact references to the R18 row and clearly distinguish planned slots from actual replica executions and actual model CTX.

## 8. Extractor limitations

scripts/_r26g_extract_tests.py:
- parses class declarations;
- parses test_* function names and declaration lines;
- prints an inventory;
- counts classes and functions.

It does not:
- parse R26_STAGE1G_FINAL_FINDING_AUDIT.md;
- compare each Finding row with a declared file/class/function;
- validate reported line numbers;
- extract assertion expressions;
- inspect source calls or intended branches;
- determine whether a test proves the original acceptance criterion.

Therefore it is an inventory extractor, not an exact test-map validator. The Stage 1G claim that all 42 mappings are exact is disproven by the two mismatches above.

## 9. Handoff and status consistency

Stage 1G commit changed only four files. It did not update:
- planner/latest_plan.md;
- planner/GLEPPO_R26_HANDOFF.md;
- planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md;
- the cumulative PC1 audit/register/evidence documents.

These still carry the Stage 1F REQUEST_CHANGES state and Stage 1G as the next task, while status.json says Stage 1G is complete. This is a long-session continuity defect.

The Stage 1G report also leaves:
- REPORT_COMMIT: (this commit);
- CURRENT_BRANCH_HEAD: (this commit).

Replace both with the exact report/current HEAD SHA, 69781d1166f9e28e7535915aad00af859c1b2734.

## 10. Planner disposition

**Stage 1G is partially accepted, but not accepted as a complete audit.**

Accepted:
- 42 detailed IDs and arithmetic: 27/13/1/1 = 42;
- category arithmetic = 42;
- 42 unique test classes and 218 declared test functions independently confirmed;
- 37/39 mapped function names and line numbers are exact;
- R18/R45/R46 are correctly represented as no direct behavioral test;
- 450/450 remains not independently reproduced;
- no production source/test code changed;
- PC1, Family C, training and Formal G3 boundaries remain unchanged.

Not accepted:
- R31 and R49 function names;
- claim that all 42 mappings are exact;
- generic assertion descriptions in place of actual assertion expressions;
- missing per-Finding source symbols/call paths and uncovered acceptance conditions;
- R39's tautological mapped test;
- R53's unrelated seed-schema test mapping;
- R19 VERIFIED_FIXED while the canonical protocol is still PROPOSED / NOT APPROVED;
- missing exact R18 manual-evidence references in Stage 1G;
- unresolved report SHA placeholders;
- stale latest_plan/handoff/next-session prompt.

**Current Planner status:**
R26_STAGE1G_REPORT_RECEIVED_REQUEST_CHANGES; EXACT_TEST_MAP_AND_SEMANTIC_EVIDENCE_RECONCILIATION_REQUIRED; PC1 BLOCKED.

## 11. Next task — R26 Stage 1H

Read planner/GLEPPO_R26_STAGE1H_EXECUTOR_PROMPT.md.

Stage 1H is documentation and audit-helper correction only:
1. Correct R31 and R49 function names and verify all 39 mapped declaration tuples.
2. Replace the generic assertion labels with exact assertion expressions and exact line ranges.
3. Add source symbols, test-to-source call paths, intended-branch analysis, acceptance coverage and uncovered conditions for all 42 Findings.
4. List all relevant tests for a Finding where the class contains multiple tests; do not select one arbitrary method as the sole evidence.
5. Correct R39's tautological evidence anchor and map the actual delimiter/component-isolation tests.
6. Correct R49/R53 mappings and explain their remaining lifecycle/hash gaps.
7. Re-evaluate all 27 VERIFIED_FIXED items against the original review acceptance criteria. At minimum, R19 must become PARTIALLY_FIXED unless explicit Planner/protocol approval is actually evidenced.
8. Add exact R18 manual evidence lines.
9. Replace (this commit) provenance placeholders with exact SHAs.
10. Update status.json, latest_plan, handoff, next-session prompt and cumulative PC1 audit/register/evidence files.
11. Preserve the 450/450 caveat; do not claim independent reproduction.

Do not modify production source or test code in Stage 1H. Missing tests remain partial/open/unverifiable as appropriate. Any test implementation requires a separate Planner authorization after the documentation review.

## 12. Hard boundaries

No registered PC1 execution. No Family C access. No ECOS/PPO training. No Formal G3 efficacy. No external model/API calls. No production runtime calls. No production source changes. No test-code changes. No production signing-key access/provisioning. No changes to frozen R1–R25 raw evidence/manifests. No merge/reset/rebase/force-push or update of main. No cross-project artifact reuse.

**Final decision:** REQUEST CHANGES. Stage 1G corrected the arithmetic and most declaration names, but 2 mappings remain wrong, the evidence map still lacks actual assertions/call paths, R39 is anchored to a tautology, R53 is mapped to an unrelated test, and R19 is over-classified while the protocol remains explicitly unapproved.
