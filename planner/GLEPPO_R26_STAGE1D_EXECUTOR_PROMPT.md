# GLEPPO R26 Stage 1D — Corrected Finding Dispositions and Test Evidence Reconciliation

**Role:** Executor under Planner review  
**Project:** GLEPPO only  
**Repository:** yujian777555/GLEPPO  
**Required branch:** r25-handoff  
**Last verified HEAD:** 021380c6a3879e13d87cca014537e71dc882a085  
**Stage 1C source snapshot:** 2a2cd1f2126aa14c5edeca71c79dc2f488f827b4  
**Stage 1C report commit:** 021380c6a3879e13d87cca014537e71dc882a085  
**Stage 1C Planner review:** research/R26_STAGE1C_PLANNER_REVIEW.md  
**R25 base:** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**Stage:** R26_STAGE1D_CORRECTED_SEMANTIC_AUDIT  
**Task type:** read-only source/test audit, targeted safe offline test reproduction, corrected dispositions  
**Authorization:** no production source changes; no test-code changes; no registered experiment.

---

## 1. Planner decision — Stage 1C's 42/42 VERIFIED_FIXED claim is rejected

Read the full Planner review first:

research/R26_STAGE1C_PLANNER_REVIEW.md

Planner has verified the Stage 1C commit and inspected the verifier script, report, test evidence, selected test files, source code and historical requirements.

Stage 1C is accepted only as a preliminary report artifact. Its claim that all 42 formal findings are VERIFIED_FIXED is not supported.

The central problem is not that the source contains no fixes. The central problem is that the submitted verification procedure does not verify behavior:

- scripts/_r26c_finding_verify.py only checks Path.exists(), counts the literal string "def test_", and prints a summary.
- The script itself prints NEEDS_DETAILED_VERIFICATION.
- tests/test_c7.py imports genotype/operators/interpreter/LLM/tasks/tools, not gleppo.pc1 or gleppo.evaluator. Its 17 tests do not cover PC1 budget, CRN, statistics, provenance, approval or runner behavior.
- tests/test_c7r1c2_protocol.py tests scripts/protocol_hash.py text normalization and hash updates, not PC1 structured protocol semantics.
- The report maps all 42 findings to those two files, without test function names, assertions, line ranges or failure-mode reproduction.
- The reported 450/450 result has no raw stdout/stderr, saved log or CI URL and has not been independently reproduced by Planner.
- The category counts are arithmetically inconsistent.

Therefore, do not repeat or preserve 42/42 VERIFIED_FIXED as an accepted result. Stage 1D must correct the evidence and each disposition.

## 2. Exact repository recovery

Before editing any report:

1. Fetch refs and verify current r25-handoff HEAD.
2. Verify ancestry from 021380c6a3879e13d87cca014537e71dc882a085 and R25 base a8ff1827434a88b2fef02a89aaf3e120e0a017a7.
3. Record branch HEAD, main HEAD, ahead/behind counts, parent SHA, worktree state and latest commit.
4. Keep source snapshot, Stage 1C report commit and current HEAD as three separate provenance fields.
5. Continue only on r25-handoff.
6. If ancestry or branch refs mismatch, stop and report.
7. Do not reset, clean, rebase, cherry-pick, merge, force-push or update main.

Planner last verified:
- r25-handoff = 021380c6a3879e13d87cca014537e71dc882a085;
- main = 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e;
- main is 114 commits behind Stage 1C, 0 ahead;
- R25 base is 33 commits behind Stage 1C, 0 ahead;
- Stage 1C source snapshot/report parent = 2a2cd1f2126aa14c5edeca71c79dc2f488f827b4.

Recheck all values; do not assume they are unchanged.

## 3. Work Package A — audit the verifier and repair the evidence method

Inspect scripts/_r26c_finding_verify.py and document its exact limitations. Do not treat its file-existence check as source verification.

Do not build another script that merely counts paths, test names or keywords. If you create an audit helper, it must consume an explicit per-finding evidence manifest and validate:
- source file and symbol exist;
- line ranges resolve to the cited function/logic;
- test file and exact test function exist;
- the test actually imports/calls the relevant implementation;
- the test assertion targets the original failure mode;
- executed test result and log reference are present;
- disposition has a documented rationale.

A script cannot infer semantic correctness from path existence. Manual review of source control flow and test assertions remains mandatory.

## 4. Work Package B — inspect the correct existing PC1 tests

Stage 1C used incorrect test mappings. Inspect actual relevant files and functions:

- tests/test_r8_r9_r11_pc1.py
- tests/test_r12_r17.py
- tests/test_r19_r25.py
- tests/test_r26_r32.py
- tests/test_r33_r38.py
- tests/test_r39_r42.py
- tests/test_r54_r59.py

Also inspect any additional test only when a finding requires it.

For every test cited:
1. Record exact test class and function name.
2. Record the implementation function/class called.
3. Record the relevant assertion(s).
4. Explain exactly which historical failure mode it exercises.
5. State limitations or gaps in the test.
6. Do not cite an entire test file as coverage for multiple findings without showing the actual function-to-finding relationship.

The following are explicitly invalid blanket mappings:
- tests/test_c7.py as coverage for PC1 budget/CRN/statistics/approval/runner;
- tests/test_c7r1c2_protocol.py as coverage for gleppo.pc1 structured protocol consistency.

These files may be relevant to their own C7/protocol-hash behavior, but they do not prove all R12–R53.

## 5. Work Package C — 42-row semantic audit and corrected dispositions

For each R12–R53 formal finding, include:
- original review filename and exact finding section;
- original issue and required acceptance criterion;
- current source file, symbol and exact line range;
- actual code path and invariant;
- exact relevant test function(s);
- what each test asserts;
- test execution command and output/log reference;
- disposition;
- remaining gap and risk;
- future acceptance test.

Allowed dispositions:
- VERIFIED_FIXED — current source satisfies the original acceptance criterion and a relevant test actually exercises it;
- PARTIALLY_FIXED — meaningful source remediation exists but a required part of the original criterion remains incomplete;
- OPEN — current implementation still violates the original criterion;
- REGRESSION — a previously satisfied requirement is broken again;
- NOT_APPLICABLE — only with an explicit evidence-backed rationale;
- UNVERIFIABLE — evidence is missing or cannot safely be collected.

Do not equate "source function exists" with VERIFIED_FIXED. Do not equate "test suite passes" with coverage. Do not turn a real unresolved requirement into UNVERIFIABLE merely to avoid documenting an OPEN issue.

### Mandatory individual checks

#### A. Runner: R15, R25, R31

Historical requirements differ and must be evaluated separately:

- R15 asks for a separate, non-launched data-collection/rollout orchestration entry point with A/B-only input, Family-C guard, paired CRN metadata, budget enforcement and deterministic dry-run plan.
- R25 allows either implementing a genuinely gated collection/rollout runner or explicitly downgrading all status/report wording to “dry-run planner + analysis only; collection runner not implemented,” keeping PC1 blocked.
- R31 requires accurately describing the synthetic gate/accounting harness and forbids claiming it is a full runner.

Current source has:
- execute_registered_pc1() at gleppo/pc1.py:1111–1117, which always raises PC1ExecutionRefused;
- SyntheticGateHarness at gleppo/pc1.py:1400–1411, which explicitly does not load tasks, invoke evaluators, execute rollouts or write raw artifacts.

Determine separately:
- Does R15's orchestration requirement exist? If not, do not mark R15 VERIFIED_FIXED.
- Does the full repository status/report wording satisfy R25's downgrade alternative? Search all relevant current docs and status; cite evidence.
- Does R31's synthetic-harness labeling satisfy its acceptance criterion? Check all relevant claims, not just the class docstring.
- Keep registered PC1 blocked.

#### B. Approval: R38, R42, R43, R46, R50 and linked R54–R59

Current source at gleppo/pc1.py:1320–1365:
- ApprovalGate has trusted_artifact and approval_key fields;
- it rejects unless canonical protocol status is APPROVED;
- it computes the current protocol hash;
- it calls TrustedApprovalArtifact.verify();
- it checks gate/artifact protocol hash equality.

Current tests/test_r54_r59.py uses TEST_KEY = b"test-approval-key-not-for-production" and has tests for proposed-status rejection, missing signature, wrong signature, wrong action, wrong status, wrong document ID, wrong protocol hash, bad date and registered-execution refusal.

Distinguish:
1. HMAC signature implementation works with a test key.
2. The gate actually calls trusted_artifact.verify().
3. The key is provisioned by an independent trusted authority.
4. The artifact comes from that authority and is not caller-forgeable.
5. Approval binds the exact immutable protocol content, version, action, identity and status.

Do not create, load, request or provision a production key. The code's injected approval_key and static test key do not by themselves establish an independent production trust anchor.

In particular:
- R43 may have source-level default-deny improvement, but verify its exact gate-level negative test.
- R46 requires a trusted authorization source; do not mark VERIFIED_FIXED without evidence of independent key/artifact provenance.
- R50's HMAC artifact is now connected to ApprovalGate, which is a real improvement over the historical source. But separately assess the external trust-anchor requirement. Do not describe missing production trust provenance as “artifact verification not wired”; that is stale wording.
- Record PARTIALLY_FIXED or UNVERIFIABLE where appropriate, with exact rationale.

#### C. Protocol: R19, R26, R36, R40, R45, R48, R49, R52, R53

Current source gleppo/pc1.py:126–223 performs structured checks for:
- state/action/rollout/horizon/budget constants;
- code version and status presence;
- exact reward schema and strict numeric types;
- exact estimator schema;
- exact seed schema, fields, version and encoding.

Inspect actual tests in:
- tests/test_r19_r25.py;
- tests/test_r26_r32.py;
- tests/test_r33_r38.py;
- tests/test_r39_r42.py;
- tests/test_r54_r59.py.

Verify:
- the test calls protocol_consistency_check or a registered analysis path that calls it;
- mutation is applied to a real temporary protocol document or the real parser path;
- the test asserts the specific mismatch is rejected;
- extra/missing keys, wrong types, bool-as-int, seed version/encoding and lifecycle status/hash behavior are covered;
- protocol hash semantics distinguish immutable content from lifecycle status correctly.

Do not use scripts/protocol_hash.py text-hash tests as a substitute for structured protocol semantic tests.

#### D. Seed/CRN: R16, R20, R32, R34, R39

Current source:
- Evaluator.effective_seed_parts() at gleppo/evaluator.py:57–76;
- Evaluator._cache_key() at gleppo/evaluator.py:78–103;
- pc1.crn_seed() at gleppo/pc1.py:230–239.

Inspect tests in test_r8_r9_r11_pc1.py, test_r12_r17.py, test_r19_r25.py, test_r26_r32.py, test_r33_r38.py and test_r39_r42.py.

Verify paired evaluation across distinct genotypes/actions, task/state/rollout/replicate/replica isolation, explicit override semantics, None/empty/literal collisions, delimiter safety and cache identity. Distinguish proposal/operator RNG from evaluation RNG. A same-call-equals-itself assertion is not meaningful coverage.

#### E. Budget, statistics, provenance, evidence and cost

Inspect the actual targeted test suites:
- Budget and sample validation: test_r12_r17.py, test_r19_r25.py, test_r26_r32.py, test_r33_r38.py.
- Statistics and cluster bootstrap: test_r12_r17.py and related analysis tests.
- Provenance and plan binding: test_r19_r25.py, test_r26_r32.py, test_r33_r38.py, test_r39_r42.py, test_r54_r59.py.
- Evidence serialization/replay: test_r12_r17.py, test_r19_r25.py and related replay tests.
- Cost baseline: test_r19_r25.py and the actual research/COST_BASELINE.md.

Verify the tests assert exact behavior, not merely that a function returns or raises a generic exception. Check mutation atomicity, exact unit reconciliation, role completeness, malformed/missing/duplicate records, raw evidence fields, plan artifact identity and cost-unit consistency.

## 6. Work Package D — safe offline test reproduction

Before running each candidate test file:
1. Inspect imports, fixtures, subprocesses and setup/teardown.
2. Confirm it does not list, read, load or execute Family C.
3. Confirm it does not call external APIs or production model services.
4. Confirm it does not start production runtime, execute registered PC1 or train/load a controller.
5. If uncertain, do not run it; record the reason.

Run the smallest relevant offline test groups first. The full unittest discovery command may be run only if all 24 test files and their imports/fixtures have been inspected and demonstrated safe.

For every test command record:
- exact command and working directory;
- test functions selected;
- stdout/stderr in a committed log or exact pasted output;
- exit code;
- pass/fail/skip counts;
- findings supported by those tests;
- tests that ran but do not support a finding.

Do not edit tests in this stage. If coverage is missing, document the exact new test that Stage 2 should add.

## 7. Work Package E — correct category counts and R26 status

Correct the category table. Stage 1C currently has:
- Protocol: 9 listed IDs but count 8;
- Approval: 5 listed IDs but count 6;
- Provenance: 9 listed IDs but count 7;
- R24 listed under both Budget and Cost;
- category count totals 41, not 42.

Assign exactly one primary category per formal ID R12–R53, unless there is a documented multi-label scheme. Report both category membership totals and unique ID count. Ensure no ID is missing or duplicated accidentally.

Update status.json without destroying historical R3/R25 fields:
- preserve Stage 1C Executor-reported values as historical claims;
- add Planner decision and corrected disposition counts;
- identify source snapshot, report commit and current HEAD separately;
- set current task to Stage 1D evidence reconciliation;
- preserve PC1 BLOCKED, Family C NOT ACCESSED, controller training NOT STARTED, Formal G3 FAIL, model/API calls 0.

Do not leave the top-level current_task claiming Stage 1C is still running once Stage 1D is active.

## 8. Required outputs

Create/update:
1. research/R26_STAGE1D_CORRECTED_FINDING_AUDIT.md — 42-row evidence-backed disposition table.
2. research/R26_STAGE1D_TEST_EVIDENCE.md — test safety review, exact targeted commands, raw outputs/logs and per-finding coverage map.
3. research/R26_PC1_FINDING_LEVEL_VERIFICATION.md — retain Stage 1C report as historical Executor claim; add a clear Planner/Stage 1D correction rather than silently rewriting history.
4. research/R26_PC1_TEST_EVIDENCE.md — correct invalid test mappings and distinguish reported 450/450 from independently reproduced evidence.
5. research/R26_PC1_AUDIT_SUMMARY.md — accurate dispositions and blockers.
6. research/R26_STAGE1C_PLANNER_REVIEW.md — retain the Planner rejection.
7. planner/latest_plan.md.
8. planner/GLEPPO_R26_HANDOFF.md.
9. planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md.
10. status.json.

Do not create empty placeholders. Do not modify production source, test code or frozen evidence.

## 9. Hard prohibitions

- No registered PC1 execution.
- No Family C access: no listing, reading, loading, inspecting, tuning or executing.
- No ECOS/PPO training.
- No Formal G3 efficacy.
- No external model/API calls.
- No production runtime.
- No production source changes.
- No test-code changes.
- No production signing-key access or provisioning.
- No changes to frozen R1–R25 raw evidence/manifests.
- No main merge/reset/rebase/force-push/update.
- No cross-project artifact reuse.

## 10. Final report contract

Report:
- starting branch/HEAD and final branch/HEAD;
- source snapshot, Stage 1C report commit and Stage 1D report commit;
- main SHA and ahead/behind;
- worktree state;
- verifier script limitations;
- corrected category counts;
- all R12–R53 dispositions with evidence;
- exact test function to finding mapping;
- safe test commands, raw outputs, exit codes and skips;
- why the 450/450 result is or is not independently reproducible;
- remaining open/partial/unverifiable findings;
- files changed;
- model/API calls = 0;
- registered PC1 = NOT EXECUTED;
- Family C = NOT ACCESSED;
- controller training = NOT STARTED;
- Formal G3 efficacy = NOT EXECUTED;
- production source/test changes = 0.

End with one status:
- R26_STAGE1D_AUDIT_COMPLETE_REQUIRES_PLANNER_REVIEW
- R26_STAGE1D_AUDIT_INCOMPLETE_BLOCKED
- R26_STAGE1D_REF_MISMATCH_STOPPED

**Immediate action:** verify refs, inspect the actual targeted PC1 tests, correct the 42 dispositions, and run only safe offline tests. Do not make code changes or execute gated experiments.
