# GLEPPO R24 — Corrective Audit, Gate-Sequence Repair and Executable ECOS Preregistration

**Repository:** `yujian777555/GLEPPO`  
**Branch:** `c7-g3-diag-v2-r1-fastpath`  
**Exact starting HEAD:** `2c66291ea896246a4f90b1f713c81a7ce931682c`  
**Primary objective:** Correct the unsupported R23 audit claims, complete a real current-branch PC1 blocker re-audit, remove the G3/training circular dependency through an independently reviewable gate amendment, and make the ECOS experiment protocol executable.

## 0. Current truth — do not overstate R23

Read first:
- `research/R23_STATIC_REASSESSMENT.md`
- `research/R21_C1_INDEPENDENT_REVIEW_R23.md`
- `research/R23_PC1_BLOCKER_MATRIX.md`
- `research/R23_G3_FAILURE_DECOMPOSITION.md`
- `research/R23_CONTROLLER_TRAINING_PREREGISTRATION.md`
- `research/PC1_PROTOCOL_R4_PROPOSED.md`
- `status.json`

R23 reports 450/450 tests, but the committed tamper-test script does not actually run the verifier against its temporary tampered copies. The verifier has incomplete seed/split/manifest checks and counts C4 `source_valid` as a proxy for `effective_success`. The DAC audit parses one file and prints PASS without executing the claimed perturbation tests. The PC1 matrix is a summary, not a finding-by-finding current-code audit.

Current status:
- R21-C1 review: `ACCEPT_WITH_LIMITATIONS`, not unrestricted ACCEPT.
- PC1: `PROPOSED_NOT_APPROVED`, not executed.
- Current-branch PC1 blocker audit: NOT COMPLETE.
- Formal G3: FAIL.
- Controller training: NOT AUTHORIZED.
- Family C: prohibited.
- No new model/API calls in R24.

Do not delete or rewrite historical R1–R23 raw evidence.

## 1. Git discipline

Before editing:
- fetch origin;
- verify branch is exactly `c7-g3-diag-v2-r1-fastpath`;
- verify HEAD is `2c66291ea896246a4f90b1f713c81a7ce931682c` or a descendant;
- inspect clean/dirty worktree and remote HEAD;
- do not switch to main;
- do not reset, force-push or overwrite uncommitted user work.

All new artifacts and code stay in this repository and branch.

## 2. Stage A — make the R21 verifier genuinely fail-closed

Modify `scripts/verify_r21_c1_independent.py` so its input base directory is injectable (CLI `--base-dir` or a pure verification function). Preserve a default pointing to the frozen R21 evidence.

Required checks:
1. Compare raw, ledger and frozen-manifest actual hashes against every corresponding field in `R21_RESULT_MANIFEST.json`.
2. Check byte sizes and hashes for every file in `R21_FROZEN_MANIFEST.json`; reject missing, unexpected, unsafe-path and extra files according to the frozen manifest policy.
3. Validate exact run ID, protocol ID, model ID/revision and required provenance.
4. Validate exactly 24 unique units, exact eight task IDs, exact three seed IDs per task, exact unit_key composition, and the frozen DEV/CONFIRM split.
5. Check raw `dev_tasks` and `confirm_tasks` against the frozen task lists and validate every unit's group assignment.
6. Reconcile every ledger row with its unit/request provenance; validate unique monotonic call IDs, exact row count, request/failure/retry/generation counters and token deltas.
7. Do not silently map missing/null outcomes to false or success. Missing required fields must fail.
8. Recompute paired counts and McNemar from validated unit-level outcomes.

### C4 outcome semantics

Do not call `source_valid` an `effective_success` unless the registered protocol and evaluator code prove equivalence.

Trace the frozen R21 execution path:
- task input and declared contract;
- tool invocation and actual tool output;
- DAC answer binding;
- final answer;
- evaluator/checker outcome.

Keep gold/reference access evaluator-only. If the raw artifact lacks enough information to independently determine C4 answer correctness, say so and retain the narrower label `source_valid`; do not upgrade it to effective success. State exactly which metric the McNemar test compares.

### Tamper tests

Rewrite `scripts/_r23_tamper_tests.py` (or replace with a new R24 test) so every mutation is actually passed to the verifier via the temporary directory. Assert non-zero exit for at least:
- raw byte mutation;
- ledger token mutation;
- ledger row deletion;
- duplicate call ID;
- missing/duplicate unit;
- unexpected task/seed;
- DEV/CONFIRM assignment mutation;
- C4 outcome mutation;
- missing result manifest;
- frozen manifest hash/size mutation;
- frozen source mutation;
- missing provenance.

The original frozen BASE must never be modified. A test that only prepares a mutated copy or prints `LOGIC_OK` is not a passing test.

## 3. Stage B — complete DAC isolation audit

Replace the current one-file AST-only PASS claim with:
1. A dependency-path inventory from the actual R21 runner into DAC binding, task contracts, tools, interpreter and evaluator.
2. Static review of every DAC-reachable path for gold/checker/answer-key/task-ID/arm-label reads.
3. A clear trust-boundary map: evaluator may read gold; DAC execution may not.
4. Executed tests that call the real DAC path:
   - perturb tool output while holding all other inputs constant; result should change or abstain as specified;
   - perturb gold/checker-only values while holding tool output constant; DAC output must not change;
   - missing/invalid contracts and failed tools must abstain or fail closed;
   - answer must be traceable to the actual tool output.
5. Report uncovered paths and limitations.

Do not print PASS unconditionally. Exit non-zero on a failed audit assertion.

## 4. Stage C — PC1 blocker matrix, one finding at a time

Reconcile all historical review rounds and findings from `status.json` and the original review documents. First establish the exact number of reviews and unique finding IDs; do not assume “10 reviews / ~43 findings” without reconciling the list.

Create one row per finding in `research/R24_PC1_CURRENT_BRANCH_AUDIT.md`:
- finding ID and originating review/commit;
- severity and original statement;
- current implementation file/function/line;
- current regression test and exact assertion;
- targeted reproduction result on the current branch;
- disposition: `VERIFIED_FIXED`, `OPEN`, `PARTIAL`, `SUPERSEDED_BY_APPROVED_AMENDMENT`, or `NOT_APPLICABLE`;
- evidence and commit hash;
- whether it blocks PC1.

Audit actual source and tests, not remediation summaries. In particular cover:
- evaluator correctness and gold isolation;
- train/validation template separation;
- feature semantics;
- CRN seed and cross-process reproducibility;
- cache/replica/CTX accounting;
- Q-rollout versus extra-immediate sample roles;
- reward identity and estimator semantics;
- exact 100-state / 40-cluster provenance;
- replayable raw evidence and hashes;
- protocol-document/code/version/hash consistency;
- trusted approval artifact and default-deny behavior;
- actual collection/rollout orchestration, not just dry-run/accounting harness;
- complete budget reconciliation.

Fix offline defects that can be reproduced. Add targeted regression tests. Do not execute registered PC1.

## 5. Stage D — repair the G3 / PC1 / training gate sequence

The current documents create a circular dependency:
- preregistration says formal G3 must PASS before training;
- G3 decomposition says controller training is needed before the formal G3 efficacy rerun.

Do not silently delete the formal G3 requirement. Propose a protocol amendment that separates:

### G3-PREFLIGHT (pre-training safety/engineering gate)
Must test only prerequisites that can be established before learning:
- evaluator/checker correctness;
- tool-chain execution and path validity;
- output-format contract;
- feasible/valid operator definitions;
- stable seeds, trace integrity and runtime revision;
- safe execution, budgets and Family C exclusion.

It must NOT require learned controller improvement or post-training genotype-causality success.

### PC1 diagnostic
Only after its own protocol is independently reviewed and approved, G3-PREFLIGHT passes, the trusted Planner approves, production runtime is locked and budget guard passes:
- run the registered A/B-only PC1 diagnostic;
- Family C remains forbidden;
- obey PC1's existing 45,440 planned-slot / 50,000 hard-cap contract unless an amendment is independently approved before execution;
- if PC1 is FAIL/INCONCLUSIVE under its registered stopping rules, stop and do not train.

### ECOS controller training
Only after PC1 is approved and executed with a valid PASS, plus all required approvals:
- train the controller, not Qwen;
- DAC stays fixed and identical across all arms;
- preserve the preregistered confirm set.

### G3-EFFICACY (post-training outcome)
After training, evaluate whether ECOS improves the evolutionary system against frozen baselines on untouched confirm tasks. This is the final causal efficacy gate. A failure remains a valid research result; do not tune on confirm.

The amendment must explicitly state which gate authorizes which action, who approves it, and which evidence is required. Obtain independent review and trusted Planner approval before any gate execution.

## 6. Stage E — make the ECOS preregistration executable

Complete `research/R24_ECOS_CONTROLLER_PREREGISTRATION.md` and a machine-readable JSON protocol.

Specify:
- exact operator names, parameters, preconditions and invalid-action handling;
- exact state vector, feature meanings, normalization and observation timing;
- exact reward equation, horizon, attribution and aggregation;
- alignment with PC1's `generation_reward` or a pre-registered rationale for using a different objective;
- PPO library/version and all hyperparameters, rollout/update schedule and seed hierarchy;
- exact task/template/seed IDs and immutable split manifest hashes;
- baseline definitions and how “best single operator” is selected without validation/confirm leakage;
- exact rule-based policy;
- statistical estimand, sample-size rationale, paired analysis and confidence intervals;
- 1,000-episode / 10-GPU-hour / 5,000-call / 1M-token / 24-hour budget reconciliation;
- stopping rules and checkpoint selection;
- explicit confirmation-set access control.

Do not start training. If any specification is not grounded in current code/evidence, mark it OPEN instead of inventing a value.

## 7. Stage F — test and independent review

- Run focused tests and the full test suite on the exact R24 candidate commit.
- Ensure GitHub Actions/CI runs are associated with the exact commit; report the run URL and conclusion. If CI is unavailable, state that tests are executor-reported only.
- Clean-clone verification must reproduce the results.
- Request independent read-only review of the exact final R24 SHA and protocol hashes.
- Do not self-approve.
- No PC1, formal G3 efficacy, controller training, Family C access or model/API calls in R24.

## 8. Deliverables and final state

Required:
- `research/R23_STATIC_REASSESSMENT.md` (preserve);
- corrected R21 verifier and actual tamper tests;
- complete DAC dependency and dynamic isolation audit;
- `research/R24_PC1_CURRENT_BRANCH_AUDIT.md`;
- `research/R24_G3_GATE_AMENDMENT_PROPOSAL.md`;
- `research/R24_ECOS_CONTROLLER_PREREGISTRATION.md` and JSON;
- updated `planner/latest_plan.md`, `status.json`, handoff prompt;
- test logs, exact commit, CI URL, clean-clone evidence.

Allowed terminal states:
- `R24_CORRECTIONS_COMPLETE_REQUIRES_INDEPENDENT_REVIEW`
- `BLOCKED_R21_C1_SEMANTICS`
- `BLOCKED_PC1_CURRENT_BRANCH_AUDIT`
- `BLOCKED_GATE_AMENDMENT`
- `BLOCKED_ECOS_PREREGISTRATION`

No terminal state authorizes PC1 or training. Those require a separate trusted approval after independent review.

## 9. Execute now

Do not respond with another plan only. Start by verifying Git state, then fix the tamper harness and verifier. Continue the current-branch blocker audit and gate amendment. Run only offline tests. Update the repository and handoff at each completed boundary.
