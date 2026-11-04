# GLEPPO R26 Stage 1I — Finding-Level Semantic Evidence Completion

**Role:** Executor under Planner review  
**Project:** GLEPPO only  
**Repository:** yujian777555/GLEPPO  
**Required branch:** r25-handoff  
**Stage 1H Executor commit:** 532ee8adf498e83967016723d28cb1e7dc30bf5f  
**Stage 1H source snapshot:** 29325cfa16441154c833f381f208747b57627a79  
**Stage 1H parent:** 0b1d5cac084966040a2a1820675605cc428776fc  
**Stage 1H Planner review:** research/R26_STAGE1H_PLANNER_REVIEW.md  
**R25 base:** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**Stage:** R26_STAGE1I_FINDING_LEVEL_SEMANTIC_EVIDENCE_COMPLETION  
**Task type:** documentation-only semantic audit and non-production audit-helper correction  
**Authorization:** no production source changes; no test-code changes; no registered experiment.

---

## 1. Planner decision — Stage 1H REQUEST_CHANGES

Read the complete Planner review:

research/R26_STAGE1H_PLANNER_REVIEW.md

Accepted from Stage 1H:
- all 42 formal Finding IDs R12–R53 occur exactly once;
- disposition arithmetic is 26 VERIFIED_FIXED / 14 PARTIALLY_FIXED / 1 OPEN / 1 UNVERIFIABLE = 42;
- category counts sum to 42;
- all 39 direct test declaration tuples match actual file/class/function/line declarations at source snapshot 29325cfa...;
- R31 and R49 function names are corrected;
- R19 is correctly PARTIALLY_FIXED while the canonical protocol remains PROPOSED / NOT APPROVED;
- R39's selected test mapping uses a real delimiter-collision test;
- R18 has a partial manual evidence reconciliation;
- 218 test functions are independently confirmed;
- 450/450 remains EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED;
- no production source or test code changed.

Blocking defects:
1. The evidence file is still only a declaration inventory. It does not include exact assertions, source symbols/call paths, intended branch, acceptance conditions or uncovered conditions for each Finding.
2. R53 still maps to test_mutation_seed_contract_fails (line 130), an unrelated seed_schema mutation test. Map test_mutation_status_not_checked_by_consistency (line 118) as related/indirect evidence only, and explicitly state that no direct status-only hash invariance test exists.
3. R39's action/genotype-exclusion criterion is not cross-referenced to the stronger instrumented evaluator tests. The local test_action_genotype_excluded method compares the same call with itself and is not adequate independent variation evidence.
4. R18 omits critical token/units/production-cost references.
5. scripts/_r26h_extract.py only inventories declarations; it does not validate the 42-row report map.
6. Handoff, latest plan, next-session prompt and cumulative PC1 records were not updated.
7. Stage 1H report metadata omits the exact Stage 1H commit/final HEAD.
8. No CI/raw test log exists for the exact Stage 1H SHA.

Current Planner state:

**R26_STAGE1H_REPORT_RECEIVED_REQUEST_CHANGES; FINDING_LEVEL_SEMANTIC_EVIDENCE_AND_DURABLE_HANDOFF_RECONCILIATION_REQUIRED; PC1 BLOCKED.**

## 2. Repository recovery and provenance

Before editing:
1. Verify branch r25-handoff and current HEAD.
2. Verify ancestry includes R25 base a8ff1827434a88b2fef02a89aaf3e120e0a017a7 and Stage 1H commit 532ee8adf498e83967016723d28cb1e7dc30bf5f.
3. Record current branch HEAD, main SHA, ahead/behind counts and latest commit.
4. Distinguish SOURCE_SNAPSHOT, STAGE1H_REPORT_COMMIT, STAGE1H_PARENT and CURRENT_BRANCH_HEAD.
5. Add exact Stage 1H report commit/final HEAD 532ee8adf498e83967016723d28cb1e7dc30bf5 in a Planner correction/addendum; do not silently rewrite the historical Executor report.
6. If refs differ unexpectedly, stop and report exact mismatch.
7. Continue only on r25-handoff. Do not merge/update main.

Planner last verified:
- r25-handoff = 532ee8adf498e83967016723d28cb1e7dc30bf5;
- Stage 1H parent = 0b1d5cac084966040a2a1820675605cc428776fc;
- source snapshot = 29325cfa16441154c833f381f208747b57627a79;
- main = 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e;
- main → Stage 1H: 182 ahead, 0 behind;
- R25 base → Stage 1H: 101 ahead, 0 behind.

## 3. Work Package A — build the real 42-Finding semantic evidence map

The current file research/R26_STAGE1H_TEST_EVIDENCE.md has only:
ID | Test File | Class | Function | Line | Evidence Type.

Create research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md with exactly 42 Finding rows R12–R53. For every Finding, include:

1. exact original Finding heading and source review document;
2. original failure mode and full acceptance criteria, not a paraphrase that drops conditions;
3. exact test file(s), class(es), all relevant test function(s), test start/end line range(s);
4. exact assertion expression(s), each with source line number(s);
5. source function/class/method called by the test, with source file and line range;
6. actual test-to-source call path (test → public API → validator/helper → state mutation, return value or exception);
7. whether the intended branch is reached, or whether an earlier guard/fixture condition exits first;
8. acceptance conditions directly proven;
9. acceptance conditions only indirectly supported;
10. acceptance conditions still uncovered;
11. evidence type: DIRECT, INDIRECT, MANUAL, or NONE;
12. disposition and concise evidence-based rationale.

For tests that call a test harness, synthetic gate or stub, state that explicitly. Do not imply a synthetic harness proves a production runner exists.

For multi-part criteria, enumerate all relevant tests and map each to the individual criterion it covers. One representative test is not enough when the original Finding requires multiple independent properties.

Do not invent call paths. Inspect the test imports, actual invoked symbols and source implementation. If a call path cannot be proven statically, mark it unresolved.

If there is no test for a criterion, write NONE for direct evidence even if an adjacent test exists. List adjacent tests separately as indirect evidence.

Do not automatically preserve the 26 VERIFIED_FIXED count. Re-evaluate every VERIFIED_FIXED Finding against the original review acceptance criteria. Change a disposition only when the evidence requires it; count arithmetic is a result, not a target.

## 4. Work Package B — mandatory R53 correction

Stage 1H maps R53 to test_mutation_seed_contract_fails at tests/test_r39_r42.py:130. This test changes seed_schema and is unrelated to lifecycle-status hash invariance.

Correct R53's evidence:
- related test: TestR40ProtocolConsistency.test_mutation_status_not_checked_by_consistency at line 118;
- evidence type: INDIRECT only;
- assertion: protocol_consistency_check() still reports all_pass after only the lifecycle status is changed;
- uncovered requirement: this does not prove compute_protocol_hash() excludes status.

The Tenth Review states that compute_protocol_hash(doc) serializes/hashes the entire parsed JSON dictionary, including status. No direct status-only hash invariance test is present in the frozen source snapshot.

Keep R53 PARTIALLY_FIXED. Do not claim the implementation or tests establish the required immutable-content-hash/lifecycle-status separation.

## 5. Work Package C — mandatory R39 cross-Finding evidence

The Seventh Review R39 acceptance includes:
- delimiter-containing task/state identifiers do not collide;
- same full tuple reproduces the same seed;
- changing task, state, rollout or replicate changes the seed;
- action/genotype remain excluded from the paired environment CRN key.

Stage 1H correctly lists these non-tautological direct tests:
- TestR39CRNSeed.test_delimiter_no_collision at line 68;
- test_task_change_changes_seed at line 74;
- test_state_change_changes_seed at line 77;
- test_rollout_change_changes_seed at line 80;
- test_replicate_change_changes_seed at line 83;
- test_none_empty_string_no_collision at line 86.

However, test_action_genotype_excluded at line 96 compares the same crn_seed() call to itself. Do not use it as proof of action/genotype exclusion.

Cross-reference the stronger instrumented tests:
- tests/test_r12_r17.py::TestR16SeedContract::test_same_crn_identical_across_genotypes at line 246;
- tests/test_r19_r25.py::TestR20CRNContract::test_same_crn_identical_across_genotypes at line 99.

These construct different genotypes, run them through Evaluator with identical task/state/rollout/replicate inputs, capture effective seeds from InstrumentedInterpreter and assert equal seed logs. Explain the call path and what the tests prove. Keep R39 disposition evidence-based.

## 6. Work Package D — complete R18 manual evidence

R18 has no behavioral test. Keep test mapping NONE and classify its evidence as MANUAL.

Include these exact references:
- research/SMOKE_RAW.json line 276: wall_clock_s = 0.0261;
- lines 277–279: planned init 32, offspring 96, total 128;
- line 284: actual_replicas_run = 112;
- line 291: LLM tokens UNMEASURED under StubLLM;
- line 293: units note; planned slots are conservative replica-slot accounting and explicitly NOT actual CTX;
- research/COST_BASELINE.md line 4: production LLM tokens/latency UNMEASURED;
- line 22: 0.0261 s is stub wall-clock, not production;
- line 30: 128 planned smoke slots;
- line 44: LLM tokens UNMEASURED;
- line 47: actual replica executions and cache-hit-bundle unit definitions;
- line 82: PC1 planned slots = 45,440;
- line 101: stub smoke latency, not production;
- lines 110–111: planned workload proxy and SR5 limitation, not measured production cost.

Explicitly distinguish:
- planned candidate-task replica slots;
- actual uncached replica executions;
- cached evaluation bundles;
- actual model CTX;
- production token/latency measurements.

R18 may remain VERIFIED_FIXED only as manual documentation reconciliation with the above limits explicit.

## 7. Work Package E — upgrade the audit helper into a declaration-map validator

scripts/_r26h_extract.py currently prints class/function declarations and selected test classes. It is not a report validator.

Update or replace it as a non-production helper so it:
1. parses the 42-row Finding table/evidence map;
2. requires each ID R12–R53 exactly once;
3. checks the expected set of 42 IDs and reports missing/duplicate/unknown IDs;
4. checks that exactly 39 rows have a test and exactly 3 rows are NONE, unless the semantic audit justifies a changed mapping;
5. validates file/class/function/declaration line for each mapped test;
6. reports exact mismatches and exits nonzero on map inconsistency;
7. reports inventory counts separately: 218 test functions, 48 class declarations, 42 unique class names including the shared InstrumentedInterpreter helper, and 41 unique test classes;
8. explicitly states that the helper does not prove assertion semantics, source call paths or acceptance coverage.

Do not make the helper claim semantic verification. Semantic review must remain in the evidence map.

No production source or test code may be changed.

## 8. Work Package F — update durable handoff and cumulative records

Preserve Stage 1H Executor artifacts and append Planner corrections where appropriate.

Create/update:
1. research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md;
2. research/R26_STAGE1I_FINAL_FINDING_AUDIT.md;
3. research/R26_STAGE1H_PLANNER_REVIEW.md remains the Planner decision and must not be overwritten;
4. research/R26_STAGE1H_FINAL_FINDING_AUDIT.md — append Stage 1H Planner correction/provenance;
5. research/R26_STAGE1H_TEST_EVIDENCE.md — append R53/R39/R18 corrections;
6. research/R26_PC1_AUDIT_SUMMARY.md;
7. research/R26_PC1_FINDING_REGISTER.md;
8. research/R26_PC1_FINDING_LEVEL_VERIFICATION.md;
9. research/R26_PC1_TEST_EVIDENCE.md;
10. planner/latest_plan.md;
11. planner/GLEPPO_R26_HANDOFF.md;
12. planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md;
13. status.json.

In status.json:
- Stage 1H Executor result remains historical;
- Stage 1H Planner decision is REQUEST_CHANGES;
- Stage 1I is current task;
- Stage 1I counts are derived from the corrected final table;
- source snapshot, Stage 1H report commit, Stage 1H parent and current HEAD are distinct;
- PC1 remains BLOCKED;
- Family C remains NOT ACCESSED;
- controller training remains NOT STARTED;
- Formal G3 remains FAIL;
- model/API calls remain 0.

Do not create empty placeholders. Keep historical Executor reports and append Planner corrections instead of silently rewriting prior claims.

## 9. Test and experiment boundary

Do not run registered PC1. Do not access Family C. Do not train a controller. Do not make external model/API calls or production runtime calls.

No fresh full test run is authorized or required in Stage 1I. Keep 450/450 as EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED. If prior raw stdout/stderr and exact source SHA exist, record them; do not infer a run from a status label.

## 10. Hard prohibitions

- No registered PC1 execution.
- No Family C listing, reading, loading, inspecting, tuning or execution.
- No ECOS/PPO training.
- No Formal G3 efficacy.
- No external model/API calls.
- No production runtime calls.
- No production source changes.
- No test-code changes.
- No production signing-key access/provisioning.
- No changes to frozen R1–R25 raw evidence/manifests.
- No main merge/reset/rebase/force-push/update.
- No cross-project artifact reuse.

## 11. Final report contract

Report:
- starting branch/HEAD and final branch/HEAD;
- Stage 1H commit/source/parent and Stage 1I report/final HEAD;
- main SHA and ahead/behind;
- all 42 IDs and exactly one final disposition each;
- category and disposition counts summing to 42;
- all 39 declaration mappings validated by the helper;
- test-body start/end, exact assertions, source symbols and call paths for every Finding;
- intended-branch/early-guard analysis;
- original acceptance criteria proven, indirect and uncovered;
- R53 corrected indirect mapping and missing direct hash invariance;
- R39 cross-genotype evidence from R16/R20;
- R18 complete manual references and unit caveats;
- all VERIFIED_FIXED dispositions re-evaluated;
- 450/450 provenance or explicit lack of it;
- files changed;
- model/API calls = 0;
- registered PC1 = NOT EXECUTED;
- Family C = NOT ACCESSED;
- controller training = NOT STARTED;
- Formal G3 efficacy = NOT EXECUTED;
- production source/test changes = 0.

End with one status:
- R26_STAGE1I_AUDIT_COMPLETE_REQUIRES_PLANNER_REVIEW
- R26_STAGE1I_AUDIT_INCOMPLETE_BLOCKED
- R26_STAGE1I_REF_MISMATCH_STOPPED

**Immediate action:** verify refs; correct R53 and R39 cross-evidence; complete all 42 semantic evidence rows; complete R18 manual evidence; upgrade the helper to validate the exact declaration map; update durable handoff and provenance. Do not modify production source or tests.

---

## 12. Planner addendum — ECOS scientific integrity and protocol drift (2026-11-04)

Read and preserve the separate Planner review:

`research/R26_ECOS_SCIENTIFIC_INTEGRITY_REVIEW.md`

This addendum does **not** replace or weaken Work Packages A–F. Stage 1I remains primarily the 42-Finding PC1 semantic-evidence audit. Do not start a new experiment or change production code to address the science questions.

### 12.1 Correct the R21-C1 evidence attribution

R25's statement “Fixed strategy enough? UNLIKELY — R21-C1 shows operator matters” is not supported by R21-C1.

R21-C1 compares C0 (LLM arithmetic execution) with C4 (DAC deterministic answer computation). It does not compare evolutionary operators or fixed/adaptive controllers. Do not cite R21-C1 as evidence that operator choice matters or that fixed-operator evolution is inadequate.

In Stage 1I handoff/status additions, preserve the corrected interpretation:
- R21-C1 supports the DAC/arithmetic-correctness result under its documented limitations.
- Fixed-vs-adaptive operator selection remains UNTESTED.
- PPO-vs-rule and PPO-vs-contextual-Bandit remain UNTESTED.
- Historical operator pilots may motivate heterogeneity, but behavior change or a local operator win is not proof that adaptive selection beats the best fixed operator.

Do not edit or rewrite the historical R25 report. Cite the Planner addendum instead.

### 12.2 Record protocol drift without silently resolving it

The following artifacts disagree materially and must not be treated as one already-frozen controller contract:
- `research/PHASE1_DESIGN.md`: 32-D state, one operator per generation, generation reward, γ=0.95, multi-step episode return, broad baseline suite;
- `research/R24_ECOS_CONTROLLER_PREREGISTRATION.md`: immediate child-parent effective_success reward, γ=0.99, a shorter state description, 4/4/4 task split, and a 1,000-episode training budget;
- `research/PC1_PROTOCOL_R4_PROPOSED.md` and `gleppo/reward.py`: PC1 myopia diagnostic uses the shared generation_reward and γ=0.95; R4 remains PROPOSED / NOT APPROVED;
- `gleppo/evolution.py`: actual generation reward calls the shared generation_reward implementation.

Do not choose a winner, amend frozen documents, change reward code, or mark these protocols reconciled in Stage 1I. Record that a separate Planner-reviewed protocol reconciliation is required **after Stage 1I acceptance and before any PC1 approval or controller training**.

### 12.3 Required durable-handoff update

When updating status/latest_plan/handoff/next-session records:
1. Link `research/R26_ECOS_SCIENTIFIC_INTEGRITY_REVIEW.md`.
2. State that the Idea is retained as a falsifiable hypothesis, not a validated method.
3. State that R21-C1 is DAC evidence, not operator-selection evidence.
4. State that the reward/state/gamma/split/baseline/metric contract still needs reconciliation.
5. Add `R26_ECOS_PROTOCOL_RECONCILIATION` as a later review gate after Stage 1I; do not bypass the current Stage 1I task.
6. Keep PC1 BLOCKED, Formal G3 FAIL, Family C NOT ACCESSED, controller training NOT AUTHORIZED/NOT STARTED, registered PC1 NOT EXECUTED, and model/API calls at zero.

### 12.4 Stage 1I final report addendum

The final Executor report must include a short “Scientific integrity handoff” section confirming:
- no R21-C1-to-operator-effect inference was used;
- the protocol discrepancies above were preserved as unresolved rather than silently patched;
- no experiment, model/API call, PC1 execution, Family-C access, training, source change, or test-code change occurred;
- the next gate is Planner review of Stage 1I, then a separate protocol reconciliation.

This is a documentation and handoff requirement only. It does not authorize the future protocol reconciliation or any experiment.

