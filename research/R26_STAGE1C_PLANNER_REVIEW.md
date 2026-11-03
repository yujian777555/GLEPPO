# GLEPPO R26 Stage 1C — Planner Independent Review

**Review date:** 2026-11-03  
**Repository:** yujian777555/GLEPPO  
**Branch:** r25-handoff  
**Stage 1C Executor commit:** 021380c6a3879e13d87cca014537e71dc882a085  
**Stage 1C source snapshot stated by Executor:** 2a2cd1f2126aa14c5edeca71c79dc2f488f827b4  
**Stage 1C report commit:** 021380c6a3879e13d87cca014537e71dc882a085  
**Parent of report commit:** 2a2cd1f2126aa14c5edeca71c79dc2f488f827b4  
**main HEAD at review:** 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e  
**R25 base:** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**Planner decision:** REQUEST_CHANGES — Stage 1C's 42/42 VERIFIED_FIXED claim is not supported  
**Next task:** R26 Stage 1D — Corrected semantic audit and evidence reconciliation

---

## 1. Executive decision

Planner does **not** accept the Stage 1C conclusion that all 42 formal findings are VERIFIED_FIXED.

The Stage 1C commit is accepted as a documentation and preliminary inventory artifact only. The reported per-finding dispositions are not supported by the submitted verifier or test evidence.

Correct state:

**R26_STAGE1C_REPORT_RECEIVED; 42_VERIFIED_FIXED_CLAIM_REJECTED_PENDING_EVIDENCE; PC1_BLOCKED.**

This is not a claim that every underlying implementation is broken. Some source-level remediations are real and may be correct. It means the Stage 1C evidence does not establish that all 42 historical findings meet their original acceptance criteria.

## 2. Repository provenance

Remote references verified:
- r25-handoff HEAD = 021380c6a3879e13d87cca014537e71dc882a085;
- main HEAD = 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e;
- Stage 1C commit parent/source snapshot = 2a2cd1f2126aa14c5edeca71c79dc2f488f827b4;
- Stage 1C report commit = 021380c6a3879e13d87cca014537e71dc882a085;
- main → Stage 1C: 114 commits ahead, 0 behind;
- R25 base → Stage 1C: 33 commits ahead, 0 behind.

Stage 1C changed only:
1. research/R26_PC1_FINDING_LEVEL_VERIFICATION.md (added);
2. research/R26_PC1_TEST_EVIDENCE.md (added);
3. scripts/_r26c_finding_verify.py (added);
4. status.json (modified).

No production source or test source was changed in the Stage 1C commit. Continue only on r25-handoff; do not merge or update main.

The verification report's HEAD: 2a2cd1f is the source snapshot it claims to have inspected. It is not the report commit or the current branch HEAD. Preserve these as separate provenance fields.

## 3. Critical defect: the Stage 1C verifier does not verify findings

The committed scripts/_r26c_finding_verify.py was inspected in full.

For each R12–R53 record it:
- assigns a category;
- assigns one source path;
- assigns one test path;
- calls Path(...).exists() for source and test;
- counts occurrences of the literal string def test_ in the test file;
- prints a summary.

It does **not**:
- inspect the source function or call path;
- resolve line ranges or symbols;
- inspect test assertions;
- determine whether a test exercises the historical failure mode;
- execute tests;
- verify test output or exit codes;
- derive a disposition from evidence.

The script itself ends with:

    Status: NEEDS_DETAILED_VERIFICATION

Therefore its output cannot substantiate 42/42 source files verified, 42/42 VERIFIED_FIXED, or the per-finding dispositions.

## 4. Critical defect: the test-to-finding mapping is demonstrably invalid

The Stage 1C report maps almost every non-protocol finding to tests/test_c7.py and protocol findings to tests/test_c7r1c2_protocol.py.

Planner inspected both files.

### 4.1 tests/test_c7.py

This file imports:
- gleppo.genotype;
- gleppo.operators;
- gleppo.interpreter;
- gleppo.llm;
- gleppo.tasks;
- gleppo.tools.

It does **not** import gleppo.pc1 or gleppo.evaluator.

Its 17 tests cover C7 genotype/operator behavior, crossover, answer-format checking and evidence-presence checks. They do not test BudgetLedger, evaluator CRN/cache behavior, PC1 statistics, PC1 provenance, ApprovalGate, TrustedApprovalArtifact or PC1 runner semantics.

Consequently, assigning this test file to R12, R13, R14, R15, R16, R17, R20–R25, R27–R35, R37–R39, R41–R47, R50–R51 is not evidence of coverage.

### 4.2 tests/test_c7r1c2_protocol.py

This file imports compute_protocol_hash, update_protocol_hash, verify_protocol_hash and normalize_text from scripts/protocol_hash.py.

Its 10 tests cover text normalization, LF/CRLF/CR equivalence, updating and verifying a textual hash, content mutation and UTF-8 failure. It does not test gleppo.pc1.parse_protocol_document(), protocol_consistency_check(), structured protocol semantics, reward/estimator/seed schema, or registered protocol gates.

It therefore cannot establish that R19, R26, R36, R40, R45, R48, R49, R52 or R53 are fixed.

### 4.3 Relevant existing tests that must be inspected instead

The repository contains 24 test Python files. Relevant candidate suites include:
- tests/test_r8_r9_r11_pc1.py;
- tests/test_r12_r17.py;
- tests/test_r19_r25.py;
- tests/test_r26_r32.py;
- tests/test_r33_r38.py;
- tests/test_r39_r42.py;
- tests/test_r54_r59.py.

These filenames are leads, not proof. Stage 1D must inspect actual test bodies and call paths before using them as evidence.

## 5. Reported 450/450 result is not sufficient evidence

Stage 1C records:

    python -m unittest discover -s tests
    450/450 PASS
    exit code 0

The report contains no raw stdout/stderr, saved test log, per-test output, CI workflow URL, or exact mapping of test functions to all 42 findings. Planner has not independently reproduced this result.

The Stage 1C verifier does not execute this command. It only checks file existence and counts test-function declarations.

The 450/450 figure therefore remains EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED. It may be a genuine suite result, but it cannot be used as blanket evidence for 42 findings.

## 6. Category arithmetic is inconsistent

The category table in research/R26_PC1_FINDING_LEVEL_VERIFICATION.md contains these mismatches:

- Protocol lists 9 IDs (R19, R26, R36, R40, R45, R48, R49, R52, R53) but reports count 8.
- Approval lists 5 IDs (R38, R42, R43, R46, R50) but reports count 6.
- Provenance lists 9 IDs (R22, R29, R30, R35, R37, R41, R44, R47, R51) but reports count 7.
- R24 is listed in both Budget/CTX and Cost.
- The reported category counts sum to 41, not 42.

Stage 1D must establish one canonical primary category per formal finding, or explicitly declare multi-label categories and separately count unique IDs. The unique formal ID set must equal R12–R53 exactly once.

## 7. Concrete source-level distinctions

### 7.1 Runner findings R15, R25 and R31

Historical requirements:
- R15 (THIRD): implement a separate, non-launched data-collection/rollout orchestration entry point with guarded A/B-only inputs, Family-C guard, paired CRN metadata, budget cap and dry-run plan.
- R25 (FOURTH): either implement a genuinely gated collection/rollout runner or accurately downgrade all status/report wording to “dry-run planner + analysis only; collection runner not implemented,” keeping PC1 blocked.
- R31 (FIFTH): explicitly distinguish a synthetic gate/accounting harness from an actual collection/rollout runner; do not claim full implementation.

Current source:
- gleppo/pc1.py:1111–1117: execute_registered_pc1() unconditionally raises PC1ExecutionRefused.
- gleppo/pc1.py:1400–1411: SyntheticGateHarness explicitly states that it does not load tasks, invoke evaluators, execute rollouts or write raw artifacts; full runner is not implemented.

This is correct fail-closed behavior and accurate labeling of a synthetic harness. It is **not** proof that the full runner required by R15 has been implemented. Stage 1D must classify each finding against its own original acceptance criterion. Do not blanket-mark all three VERIFIED_FIXED.

### 7.2 Approval findings R43, R46 and R50

Current source gleppo/pc1.py:1320–1365 has made progress:
- ApprovalGate accepts a TrustedApprovalArtifact;
- it requires an approval_key;
- it checks canonical protocol status is APPROVED;
- it calls trusted_artifact.verify(...);
- the HMAC verifies canonical approval fields;
- the gate checks protocol hash consistency.

However:
- approval_key is injected into the gate by its caller;
- no independent production trust-anchor provisioning/loader is demonstrated in this source;
- tests use TEST_KEY = b"test-approval-key-not-for-production";
- tests demonstrate test-key HMAC mechanics, not the provenance or governance of a production trust anchor.

Do not create, load or provision a production key. Distinguish HMAC correctness from independent authorization provenance. The remaining risk is trusted key provenance and authorization-source assurance, not simply “artifact verification missing.”

### 7.3 Protocol findings R26, R40, R45, R48, R49, R52 and R53

gleppo/pc1.py:126–223 now performs several structured checks, including exact reward/estimator/seed key sets, strict numeric types, code version, status presence and seed schema fields.

This is meaningful implementation evidence, but the Stage 1C test mapping does not test it. Stage 1D must inspect the actual PC1 tests for:
- protocol field mutation;
- unknown/missing keys;
- wrong types and bool-as-int;
- reward/estimator schema mutations;
- seed schema version/encoding;
- lifecycle status/hash separation;
- direct call path from registered analysis into protocol_consistency_check().

Do not mark semantic protocol findings fixed merely because the source has structured checks.

### 7.4 Seed/CRN findings

Current Evaluator.effective_seed_parts() uses typed JSON serialization and includes task/state/rollout/replicate/replica index. pc1.crn_seed() uses a versioned JSON payload. These are promising code changes.

The Stage 1C evidence incorrectly maps CRN findings to tests/test_c7.py, which does not import the evaluator. Inspect:
- tests/test_r8_r9_r11_pc1.py;
- tests/test_r12_r17.py;
- tests/test_r19_r25.py;
- tests/test_r26_r32.py;
- tests/test_r33_r38.py;
- tests/test_r39_r42.py.

Verify end-to-end pairing, cache identity, explicit override behavior, replica isolation and delimiter collision using the actual assertions.

## 8. Planner disposition

Stage 1C is **not accepted as a completed finding-level verification**.

Accepted:
- report and source snapshot provenance can be reconstructed;
- a row exists for each formal ID R12–R53;
- current source contains real implementation work in several domains;
- current source keeps registered PC1 default-deny;
- no production source or test code was changed in the Stage 1C commit.

Not accepted:
- 42/42 VERIFIED_FIXED;
- 42/42 semantic source verification;
- test coverage mapping to tests/test_c7.py / tests/test_c7r1c2_protocol.py;
- 450/450 as independently reproduced evidence;
- category arithmetic.

**Planner status:** R26_STAGE1C_REPORT_RECEIVED_REQUEST_CHANGES; FINDING_LEVEL_EVIDENCE_RECONCILIATION_REQUIRED; PC1_BLOCKED.

Next task is R26 Stage 1D. It must correct dispositions and evidence without modifying production source or test code.

## 9. Hard boundaries

No registered PC1 execution. No Family C access. No ECOS/PPO training. No Formal G3 efficacy. No external model/API calls. No production runtime calls. No production source changes. No test code changes. No production signing-key access/provisioning. No changes to frozen R1–R25 raw evidence/manifests. No merge/reset/rebase/force-push or update of main.

**Final decision:** REQUEST CHANGES. The 42/42 claim is rejected pending a real per-finding semantic audit with correct test evidence.
