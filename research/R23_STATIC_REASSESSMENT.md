# GLEPPO R23 — Independent Static Reassessment

**Repository:** `yujian777555/GLEPPO`  
**Branch:** `c7-g3-diag-v2-r1-fastpath`  
**Reviewed commit:** `2c66291ea896246a4f90b1f713c81a7ce931682c`  
**Date:** 2026-11-02  
**Review type:** Read-only static review of the R23 commit, reports, verifier, tamper-test script, DAC audit script, PC1 matrix script, preregistration and related protocol documents.  
**Not performed:** This review did not execute repository tests, run model calls, execute PC1, run formal G3, train the controller, or access Family C.

## 1. Decision

**R23 is useful progress, but its Stage A/B/C completion claims are not fully supported by the committed scripts. The correct state is `R23_REAUDIT_PARTIAL_REQUIRES_CORRECTION_AND_INDEPENDENT_REVIEW`.**

The R23 commit message reports 450/450 tests passed. That number is treated as executor-reported, not independently reproduced here. No combined commit status checks were returned for the exact R23 SHA, and the branch is not protected. This does not prove that local tests were not run; it means the exact commit does not currently have independently retrievable CI evidence in the reviewed artifacts.

## 2. Findings

### R23-F1 — The ten tamper scenarios are not actually executed against the verifier

**Evidence:** `scripts/_r23_tamper_tests.py`.

- `run_verifier()` is defined but never called.
- Each scenario creates and mutates a temporary copy, then appends `LOGIC_OK`.
- The verifier is never pointed at the temporary copy.
- The script itself says that the verifier reads the fixed `BASE` path and that full tamper tests would require modifying BASE.

**Consequence:** The reported “10 tamper tests: fail-closed” is not established by this script. The current test demonstrates that ten mutations can be prepared, not that the verifier rejects them.

**Required correction:** Make the verifier accept an explicit base-directory argument (or expose a pure verification function), run it against each temporary copy, and assert a non-zero exit code for each corrupted fixture. Never mutate the frozen original BASE.

### R23-F2 — The R21 verifier still leaves important integrity and coverage checks incomplete

**Evidence:** `scripts/verify_r21_c1_independent.py`.

- It compares raw and ledger hashes, and checks listed frozen-file hashes.
- It does not compare the actual frozen-manifest file hash with `R21_RESULT_MANIFEST.json:frozen_manifest_sha256`.
- It does not check the frozen file sizes recorded in the manifest.
- `EXPECTED_SEEDS` is declared but never used.
- It does not validate that every `unit_key` is exactly derived from its `task_id/seed_id`, nor that each task has exactly the registered seed set.
- It does not cross-check raw `dev_tasks/confirm_tasks` fields and per-unit group membership against the frozen split.
- It checks row count, call-ID uniqueness/order and token sum, but does not fully reconcile each ledger row with unit/request provenance or all runtime request/failure/retry counters.
- C4 is counted from `source_valid`, not an independently recomputed `effective_success` outcome.

**Consequence:** R21-C1's reported paired statistic can be reproduced conditional on the C4 proxy, but the verifier does not establish all the stronger claims in the R23 summary.

### R23-F3 — The R21 review report itself records limitations

**Evidence:** `research/R21_C1_INDEPENDENT_REVIEW_R23.md`.

The report verdict is `ACCEPT_WITH_LIMITATIONS`, not unconditional `ACCEPT`. It explicitly records:
1. `source_valid` is used as a proxy for `effective_success`;
2. full tamper tests require modifying BASE;
3. per-unit DEV/CONFIRM group assignment is not fully cross-validated.

The report identifies commit `89d0752`, while the R23 verifier and audit scripts are committed at `2c66291`. The review artifact therefore needs a precise reviewed-code commit and provenance binding.

**Consequence:** Retain the R21 result as promising evidence, but do not promote it to a fully unrestricted independent-review ACCEPT until these limitations are resolved.

### R23-F4 — The DAC AST audit is a narrow one-file scan, not a dependency-closure audit

**Evidence:** `scripts/_r23_dac_audit.py`.

- It parses only `gleppo/answer_binding.py`.
- It prints that perturbation tests were tested in another file, but does not execute those tests or call the DAC on controlled perturbations.
- It prints `DAC Gold Isolation: PASS` unconditionally.
- It does not trace the R21 runner's complete call graph, tool outputs, contract construction, helper imports, or evaluator boundary.

**Consequence:** The available evidence supports a narrow static inspection, not a full runtime/taint isolation claim.

**Required correction:** Trace the actual runner-to-DAC dependency path; execute explicit metamorphic tests that perturb real tool outputs and gold/checker-only data; prove the DAC result changes with tool data and is invariant to gold/checker changes. Distinguish evaluator-side gold access from DAC-side access.

### R23-F5 — The PC1 blocker matrix is a summary, not the promised current-branch re-audit

**Evidence:** `research/R23_PC1_BLOCKER_MATRIX.md` and `scripts/_r23_pc1_matrix.py`.

- The matrix groups issue IDs by broad categories and marks many as “partially fixed”.
- It does not contain one row per historical finding with current source location, test, reproducer, evidence, and a disposition.
- The script mainly reads historical findings from `status.json` and prints status labels; it does not inspect the current implementation or execute targeted tests.
- Its hard-coded review-name list runs from `second_review` through `tenth_review` (nine named entries), while the report claims ten historical reviews. Reconcile the actual review count and include the missing/initial review if one exists.

**Consequence:** The honest current status remains `CURRENT_BRANCH_REAUDIT_NOT_COMPLETE`. No PC1 blocker should be marked fixed solely because a remediation log says it was fixed in an earlier round.

### R23-F6 — G3 and training prerequisites form a circular dependency

**Evidence:**
- `research/R23_G3_FAILURE_DECOMPOSITION.md` says a G3 rerun requires controller training.
- `research/R23_CONTROLLER_TRAINING_PREREGISTRATION.md` lists “Formal G3 passage” as a prerequisite for controller training.
- `status.json` and `planner/latest_plan.md` place formal G3 passage before PC1/training.
- `research/PC1_PROTOCOL_R4_PROPOSED.md` §10 instead defines PC1 gates as trusted Planner approval, independent review, production runtime lock and budget guard; it does not list final post-training G3 efficacy passage as a PC1 prerequisite.

**Consequence:** The present sequence can deadlock: training is needed to generate the evidence for final G3, while final G3 passage is demanded before training.

**Required correction:** Preserve the existing formal G3 FAIL. Define two distinct gates in a pre-registered amendment:
- **G3-PREFLIGHT (pre-training):** evaluator correctness, tool execution, output-format contract, action feasibility, runtime integrity and safety. It must not require learned controller improvement.
- **G3-EFFICACY (post-training):** the actual causal comparison of trained ECOS against frozen baselines on untouched confirmation tasks.

PC1 may proceed only after its own protocol approval, independent review, runtime lock and budget gate, plus the explicitly defined pre-training safety/preflight gate. PC1 PASS then informs whether controller training is scientifically justified. Controller training follows only after PC1 approval and successful execution. Final G3-EFFICACY is evaluated after training. Any such gate amendment must be independently reviewed and approved before execution; do not silently waive a gate.

### R23-F7 — PC1 diagnostic reward and controller-training reward are not aligned

**Evidence:**
- `research/PC1_PROTOCOL_R4_PROPOSED.md` defines the diagnostic reward through `gleppo.reward.generation_reward`, with `r_hat` and `Q_hat` based on that reward.
- `research/R23_CONTROLLER_TRAINING_PREREGISTRATION.md` defines PPO reward only as “effective_success improvement”.

**Consequence:** The link between the PC1 myopia diagnostic and the ECOS controller's optimization objective is underspecified. A positive PC1 disagreement/advantage result under one reward does not automatically justify training under another.

**Required correction:** Either use one frozen reward contract throughout, or pre-register and justify the distinction, including the exact mapping from PC1 evidence to the controller's objective. Do not choose the reward after seeing PC1 results.

### R23-F8 — The controller preregistration is not yet executable

**Evidence:** `research/R23_CONTROLLER_TRAINING_PREREGISTRATION.md`.

Missing or underspecified items include:
- exact five operator/action names, parameters, preconditions and invalid-action handling;
- exact state-vector schema, normalization, missing-value behavior and timing;
- mathematical reward definition, attribution horizon and per-episode aggregation;
- PPO implementation/version, hyperparameters, update schedule, rollout length, entropy/value losses and seed hierarchy;
- exact task/template IDs and immutable train/validation/confirm manifest hashes;
- how the “best single operator” baseline is selected without validation/confirm leakage;
- exact rule-based baseline;
- sample-size/power rationale for four tasks per split;
- how the 1,000-episode budget reconciles with 10 GPU-hours, 5,000 model calls, 1M tokens and 24 hours;
- exact stopping/checkpoint rules and confirm-set access control.

**Consequence:** The document is a useful preregistration outline, not an executable locked protocol.

### R23-F9 — Project status and plan artifacts are stale or contradictory

**Evidence:** `status.json`, `planner/latest_plan.md`, `research/R21_C1_INDEPENDENT_REVIEW_R23.md`.

- `planner/latest_plan.md` still contains the R22 plan and says R21-C1 independent review is provisional pending R23.
- `status.json:training_readiness` still carries the pre-R23 R22 status.
- `status.json:reviewed_commit` points to an older commit, not the R23 reviewed commit.
- `r23_status` says the R21 verifier and DAC audit passed, while the review report says `ACCEPT_WITH_LIMITATIONS` and the committed scripts reveal the gaps above.

**Consequence:** The repository's current operational state cannot be inferred reliably from one status field. R24 must reconcile latest_plan, status, report verdicts and exact commit references.

## 3. What remains supported

- The R21 raw report records 24 paired units across eight tasks.
- The reported raw outcome is C0=9/24 and C4 source-valid=24/24.
- Conditional on treating C4 source-valid as the C4 success classification, the discordant-pair counts are 15 versus 0 and the exact two-sided McNemar value is (2/2^{15}=0.00006103515625).
- The R23 commit adds a verifier, DAC audit script, PC1 summary matrix, G3 decomposition and a controller-training outline.
- The project has not executed PC1, has not trained the controller and has not accessed Family C according to the supplied R23 record.

These points do not establish that the C4 proxy is identical to the registered effective-success outcome or that the R23 audit scripts prove all claimed properties.

## 4. Required R24 decision

R24 should be a bounded corrective pass, not another open-ended planning cycle:

1. Make the R21 verifier genuinely parameterized and fail-closed; execute all tamper fixtures against temporary copies.
2. Reconcile C4 outcome semantics and exact per-unit split/seed provenance.
3. Replace the one-file DAC grep/AST PASS with dependency-path and executed metamorphic tests.
4. Convert the PC1 matrix into a finding-by-finding current-branch evidence table; do not claim the re-audit complete until every finding has a disposition.
5. Resolve the G3 preflight / post-training efficacy cycle with a formally amended, independently reviewed gate sequence.
6. Align PC1 and ECOS rewards; finish the controller protocol with exact state/action/reward, operator validity, baselines, split hashes, PPO parameters and budget ledger.
7. Reconcile status and latest_plan against the exact R24 commit.
8. Obtain independent review of the final R24 commit before any registered PC1 execution or training authorization.

## 5. Hard boundaries

- Do not run registered PC1.
- Do not run formal G3 efficacy.
- Do not train the ECOS controller.
- Do not access, load or tune Family C.
- Do not make model/API calls in this corrective pass.
- Do not modify R1–R22 raw data, ledgers or frozen manifests.
- Do not fabricate independent approval, Planner approval, signatures, test results or CI evidence.
- Do not mark historical findings fixed without current-code evidence.
