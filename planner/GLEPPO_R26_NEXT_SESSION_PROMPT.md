# GLEPPO R26 — Next-Session Planner Prompt

**Project:** GLEPPO only  
**Repository:** yujian777555/GLEPPO  
**Branch:** r25-handoff  
**Current stage:** R26 Stage 1I-R2 corrective work  
**Current Planner decision:** Stage 1I-R1 REQUEST_CHANGES; not accepted  
**Main:** 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e

---

## 1. Role and project boundaries

You are the Planner for GLEPPO. The Executor is a separate agent/operator who implements the written task. The Planner must independently inspect the resulting repository state and evidence; never accept an Executor completion report without verification.

This repository is separate from openissue, agentfotagent, EvoPareto-Agent, CausalEvo-DSH, ResearchCI, NeuroEvoScientist and all other projects. Do not reuse their code, data, reports or status.

## 2. Read these files first

1. status.json
2. research/R26_STAGE1I_R1_PLANNER_REVIEW.md
3. planner/GLEPPO_R26_STAGE1I_R2_CORRECTIVE_EXECUTOR_PROMPT.md
4. planner/latest_plan.md
5. planner/GLEPPO_R26_HANDOFF.md
6. research/R26_PC1_AUDIT_SUMMARY.md
7. research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json
8. research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md
9. scripts/_r26i_validator.py
10. research/R26_STAGE1I_R1_CORRECTIVE_REPORT.md
11. research/R26_STAGE1I_FINAL_FINDING_AUDIT.md
12. research/R26_STAGE1I_TEST_EVIDENCE.md
13. The original THIRD through TENTH review findings and every cited source/test file.

## 3. Exact repository state at the latest Planner review

- R1 final HEAD: 4d2ff06ee01146533501589b264d33ddd30ffcbe
- R1 parent: 539f74d5c898abc144992fff4a413a30744c1cc9
- R1 source snapshot: 29325cfa16441154c833f381f208747b57627a79
- R1 Planner review: dcdcef5b2e7e68a6590d95c90c4caf453399c127
- R2 prompt: planner/GLEPPO_R26_STAGE1I_R2_CORRECTIVE_EXECUTOR_PROMPT.md
- Main: 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e
- Branch relation after Planner documentation updates: 220 ahead / 0 behind main.
- Main has not been modified.

Always re-fetch the remote branch and verify current HEAD before work. Do not assume these SHAs remain the latest after a new Executor submission.

## 4. Current Planner decision

**REQUEST_CHANGES — R26_STAGE1I_R1_SEMANTIC_EVIDENCE_AND_VALIDATOR_NOT_YET_AUDITABLE.**

R1 has structural progress:
- 42 unique JSON IDs R12-R53;
- 42 unique Markdown headings;
- Markdown/JSON dispositions agree;
- 26/14/1/1 arithmetic is mechanically correct;
- R53 remains PARTIALLY_FIXED;
- R18 is MANUAL with 13 references;
- no production source or tests/ changes in R1.

But the evidence map is not yet semantically reliable. Key defects:
- relevant direct tests are omitted for R12, R14, R17, R20, R23, R39, R40, R41 and other multi-part findings;
- R28 maps a constants-only test to BudgetLedger.reconcile;
- R30/R37 claim validate_records call paths although run_pc1_analysis rejects missing values earlier;
- R44 maps an isolated loader test as evidence for registered-analysis binding;
- R47 fails at registered hash comparison before plan ID/version checks;
- R50 maps a direct art.verify test as ApprovalGate.check;
- R51 maps a protocol-content hash test to REGISTERED_PLAN_HASH;
- R17/R23/R25/R48/R52 cite nonexistent source symbols;
- R20 places crn_seed in the wrong file and claims a nonexistent call path;
- 12 source-symbol ranges are null and the validator does not inspect them;
- wrong_file_path self-test duplicates missing-file test;
- null declaration line values can bypass checks;
- several VERIFIED_FIXED dispositions are overclaimed.

See research/R26_STAGE1I_R1_PLANNER_REVIEW.md for the full line-level review.

## 5. Current Executor task — Stage 1I-R2

Execute planner/GLEPPO_R26_STAGE1I_R2_CORRECTIVE_EXECUTOR_PROMPT.md exactly.

Required:
1. Correct the full 42-row JSON/Markdown semantic map.
2. Preserve every independently testable acceptance subcondition from the original reviews.
3. Enumerate every relevant direct/indirect test for each multi-part Finding.
4. Correct all call paths, source symbols, file paths and branch-reachability claims.
5. Provide exact non-null source line ranges.
6. Re-evaluate all 42 dispositions; do not force 26/14/1/1.
7. Harden the AST validator for strict schema/types, positive declaration/source line ranges and source symbol resolution.
8. Add targeted adversarial self-tests, including an existing-file/wrong-owner case and null declaration/source line cases.
9. Correct provenance: R1 final SHA and source snapshot must be explicit.
10. Update all durable records and status.json.

No production source or tests/ modifications are allowed.

## 6. Mandatory semantic boundaries

- R12: cite actual cache-hit accounting tests, not only initialization.
- R14: cite direct r_hat and Q_hat tests.
- R17: use real functions run_pc1_analysis, save_evidence_artifact, load_evidence_artifact and replay_from_artifact; no nonexistent build_evidence/save_evidence.
- R20: Evaluator.effective_seed_parts does not call pc1.crn_seed; crn_seed is in gleppo/pc1.py.
- R23: include test_round_trip_serialize_replay and real serialization/replay symbols.
- R28: test_ledger_components_sum_to_total actually calls reconcile; test_registered_budget_exact only checks constants.
- R30/R37: early guards are in run_pc1_analysis, before validate_records.
- R38: empty-hash test exits earlier at missing trusted_artifact; mark intended hash branch not reached.
- R39: enumerate seven direct CRN tests plus separate R16 and R20 instrumented evaluator tests; exclude tautological test_action_genotype_excluded.
- R40/R41: include mutation/tamper/defensive-copy/wrong-hash tests.
- R44: distinguish source-level registered artifact path from missing end-to-end test.
- R47: alternative mapping test reaches registered-hash rejection, not plan ID/version branch.
- R50: direct art.verify test is not gate integration; proposed-status gate test exits before HMAC verification.
- R51: REGISTERED_PROTOCOL_CONTENT_HASH is not REGISTERED_PLAN_HASH.
- R52: validate_reward_schema does not exist; use protocol_consistency_check and its nested helpers.
- R53 remains PARTIALLY_FIXED without a direct status-only hash-invariance test.
- R18 remains MANUAL; production tokens/latency are UNMEASURED.
- R45 must cite _DuplicateKeyChecker as MANUAL source evidence or remove the unsupported source claim.

## 7. Scientific status

GLEPPO's ECOS research hypothesis remains open, not demonstrated.

- R21-C1 is a DAC comparison, not an operator/controller comparison.
- Fixed vs adaptive operator selection remains UNTESTED.
- PPO vs rule controller remains UNTESTED.
- PPO vs LinUCB/Neural Bandit remains UNTESTED.
- Phase 1/R24/PC1 R4 reward/state/gamma/split/budget discrepancies remain unresolved.
- Do not silently choose one protocol version or claim PPO superiority.

## 8. Hard gates

- PC1 BLOCKED; R4 PROPOSED / NOT APPROVED.
- Formal G3 FAIL.
- Family C NOT ACCESSED.
- Registered PC1 NOT EXECUTED.
- Controller training NOT AUTHORIZED / NOT STARTED.
- No production source or tests/ changes in Stage 1I-R2.
- No model/API calls, production runtime calls or signing-key access.
- No frozen R1-R25 evidence/manifest changes.
- No main merge/update/reset/rebase/force-push.
- No cross-project code/data/report reuse.
- 450/450 remains EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED.
- Model/API and production-runtime zero counters remain Executor attestations unless independently evidenced.

## 9. Stop condition

After Stage 1I-R2 is committed and all durable records/status are updated, stop and wait for Planner independent review. Do not proceed to R26_ECOS_PROTOCOL_RECONCILIATION, PC1, Family C, controller training or Formal G3.

**Next gate:** Stage 1I-R2 Executor completion → Planner independent review.

---

## CURRENT SESSION OVERRIDE — R2.1 (2026-11-04)

The R2 Executor submission was independently reviewed. Decision: REQUEST_CHANGES, limited to three overclaimed dispositions and one validator boundary defect.

Read first:
1. `research/R26_STAGE1I_R2_PLANNER_REVIEW.md`
2. `planner/GLEPPO_R26_STAGE1I_R2_1_CORRECTIVE_EXECUTOR_PROMPT.md`
3. `status.json`
4. `research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json`

Do not restart R1/R2 or repeat the full 42-row audit. Correct only R39/R41/R48 dispositions, validator source end-line EOF bound, and UTF-8/provenance records. Expected corrected counts: 25/15/1/1.

The R2 work commit is `34ba848c4b8cf4fa07c9583e049b0bb7b0635aab`; its provenance follow-up is `da7a6c7bbd09f1ebca5bf6080dffc78e15615115`. The current branch must be re-fetched before work; never assume these are still HEAD.

Hard gates unchanged: PC1 BLOCKED, Formal G3 FAIL, Family C NOT ACCESSED, registered PC1 NOT EXECUTED, controller training NOT AUTHORIZED/NOT STARTED. No production source/tests changes, no model/API calls or production runtime.

After R2.1, stop for Planner review. If accepted, proceed directly to R26_ECOS_PROTOCOL_RECONCILIATION to resolve protocol drift and prepare the fastest safe baseline experiment. Do not run PC1 or train during R2.1.

