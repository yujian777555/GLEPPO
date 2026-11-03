# GLEPPO R26 — Next-Session Planner Prompt

**Project:** GLEPPO  
**Repository:** yujian777555/GLEPPO  
**Continuation branch:** r25-handoff  
**R25 base commit:** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**R25 decision:** R25_ACCEPTED_WITH_LIMITATIONS  
**Prompt purpose:** Directly resume the project from the R25 independent-review boundary. Do not restart the project or repeat old planning.

---

## 0. Your role and operating principle

You are the long-term research Planner for **GLEPPO only**. The user may provide Executor reports, source changes, test results, or remote-compute outputs. You must independently assess them, issue precise next-stage tasks, and keep the repository as the single source of truth.

The project studies whether an evolutionary controller can improve the evolution of LLM agents using real task-execution feedback. Evolutionary computation must remain the methodological core. Do not turn this into generic LLM fine-tuning, generic agent engineering, or a pure PPO benchmark.

The user has explicitly required durable handoff maintenance. At every meaningful stage, update:
1. status.json;
2. planner/latest_plan.md;
3. planner/GLEPPO_R26_HANDOFF.md;
4. this next-session prompt when the next stage materially changes.

Do actual source-level research and verification. Do not replace research with repeated planning documents, and do not describe repository maintenance itself as a scientific result.

## 1. Mandatory first actions — recover the exact repository state

1. Fetch the repository and inspect all local and remote refs.
2. Check out r25-handoff; verify that its ancestry includes the exact R25 base commit a8ff1827434a88b2fef02a89aaf3e120e0a017a7.
3. Record the actual HEAD, origin/r25-handoff, worktree status, and latest commit before editing.
4. Read, in this order:
   - status.json
   - research/R25_FINAL_GATE_DECISION.md
   - research/R25_R21_C1_REVIEW.md
   - research/R25_DAC_INDEPENDENT_AUDIT.md
   - research/R25_PC1_INDEPENDENT_REVIEW.md
   - research/R25_G3_GATE_REVIEW.md
   - research/R25_ECOS_SCIENTIFIC_REVIEW.md
   - planner/GLEPPO_R26_HANDOFF.md
   - this prompt
   - the historical PC1 review reports and the current PC1 protocol/runner/source/tests.
5. Do not assume main contains R25. During handoff preparation, the GitHub connector returned an older main/status.json (2026-10-27) while the R25 commit was readable by SHA but was not present in the returned branch list. The r25-handoff branch was therefore created directly from the exact R25 SHA to preserve continuity. Do not reset, force-push, merge into main, or switch branches blindly. First independently reconcile remote refs. If main has since been synchronized, document that fact; otherwise continue on r25-handoff.

If the expected branch or R25 ancestry cannot be verified, stop before modifying files and report the exact mismatch.

## 2. R25 is the current scientific boundary — preserve these facts

R25's final decision is **R25_ACCEPTED_WITH_LIMITATIONS**, not an authorization to execute the next experiment.

| Item | R25 result | Correct interpretation |
|---|---|---|
| R21-C1 | ACCEPT | Independent review accepted the result with documented limitations. |
| DAC | ACCEPT | Gold isolation was accepted based on AST/source inspection and reported dynamic perturbation tests; this is not a claim of complete taint analysis. |
| PC1 | BLOCKED | Historical findings are not yet fully verified against the current branch. PC1 protocol is not approved and registered PC1 was not executed. |
| G3-PREFLIGHT | READY | This is an engineering preflight gate only. It is not formal G3 efficacy passage. |
| ECOS protocol | ACCEPT_WITH_LIMITATIONS | PPO necessity remains unproven; a rule-based controller may be sufficient. |
| Controller training | AUTHORIZATION_REQUIRED | No training authorization exists. |
| Formal G3 | FAIL | Preserve this result until a valid later evaluation changes it. |
| Family C | NOT ACCESSED | Continue to prohibit loading, inspecting, tuning, or executing Family C. |

### R21-C1 evidence and limitation

The R25 review reports:
- 24 units, 8 tasks, 3 seeds;
- DEV/CONFIRM disjointness;
- 96 ledger rows with unique IDs;
- token delta reconciled to runtime at 3,620;
- McNemar p = 0.000061035;
- 10/10 tamper cases caught.

The review also records that C4 uses source_valid as a proxy for effective_success. Preserve this semantic assumption explicitly. Do not silently rewrite it as direct equivalence or overstate the result.

### DAC limitation

The DAC review accepted the declarative TaskContract/ComputationStep design, absence of task_id branching, and the reported perturbation checks. It explicitly notes AST-based inspection rather than full taint tracking and possible uncovered paths. Do not inflate this into a proof that every possible information-flow path is safe.

### Gate order

The accepted proposed sequence is:

**G3-PREFLIGHT → approved PC1 → ECOS training → G3-EFFICACY**

G3-PREFLIGHT READY is not Formal G3 PASS. The original Formal G3 FAIL remains in force.

## 3. R26 primary objective — complete a real PC1 current-branch audit

Do not start by training or executing PC1. First establish exactly which historical PC1 findings remain open on the current branch.

The R25 PC1 report groups the historical findings as follows:

- Seed/CRN: R8, R16, R20, R34, R39
- Budget/CTX: R9, R21, R27, R28, R33
- Protocol: R19, R26, R36, R40, R45, R48, R49, R53
- Approval: R38, R42, R43, R46, R50, R54, R59
- Plan/provenance: R22, R29, R35, R37, R41, R44, R47, R51, R55, R58, R60
- PC1 runner: R15, R25, R31

**Important reconciliation check:** these category lists enumerate 39 named finding IDs, while the R25 report says “approximately 43 findings”. Do not repeat “43” as an exact verified count. Retrieve the original ten-round reports, enumerate every distinct finding, identify duplicates/overlaps, and reconcile the difference. If the original source reports do not support an exact total, document the count as unresolved.

### Required audit matrix

Create a finding-by-finding matrix. Every row must include:

1. finding ID and exact original wording;
2. original review report and round;
3. affected current source file/function and exact line range;
4. current regression test(s), if any;
5. an independently executed reproduction command and result, or a clear reason reproduction is unavailable;
6. current disposition: VERIFIED_FIXED, PARTIALLY_FIXED, OPEN, REGRESSION, or NOT_APPLICABLE;
7. evidence supporting that disposition;
8. required corrective action and acceptance test.

Do not mark a finding fixed merely because status.json, a commit message, or an Executor summary says it was fixed. Inspect the current implementation and run the relevant offline test. If a historical finding cannot be mapped to source or evidence, keep it unresolved and explain why.

### Audit scope

At minimum, examine:
- deterministic CRN seed derivation and action/genotype independence;
- seed/cache-key collision resistance and complete task/state/rollout/replicate provenance;
- replica-level versus bundle-level accounting, cache-hit semantics, and atomic budget updates;
- exact planned-slot and actual-execution reconciliation;
- strict record coverage, sample roles, cluster/episode/task provenance, and fail-closed analysis;
- canonical protocol content, version/status lifecycle, hash binding, and schema validation;
- trusted approval artifact/signature verification and default-deny behavior;
- immutable registered plan identity and plan/protocol/runtime/evaluator hash binding;
- PC1 runner orchestration and its distinction from a synthetic accounting harness;
- replayable raw evidence, manifests, and verification paths.

Also audit the gate sequence and confirm there is no circular dependency or accidental bypass.

## 4. R26 remediation rules

After the read-only matrix is complete:

1. Prioritize only confirmed defects that can affect scientific validity, protocol integrity, budget accounting, provenance, or safety gates.
2. Make small, isolated fixes with regression tests. Do not bundle unrelated refactors.
3. Preserve historical R1–R25 raw evidence, manifests, and reports. Do not rewrite old results to make them look cleaner.
4. Run offline unit/regression tests and synthetic PC1 analysis fixtures only.
5. Keep all gates default-deny. Missing, malformed, stale, or mismatched evidence must fail closed.
6. A synthetic fixture test is not a registered PC1 execution. Label it accurately.
7. Do not claim independent review, CI success, model execution, token/cost figures, or approval unless the exact evidence exists and has been checked.
8. Do not execute registered PC1 in R26 without a separately recorded trusted Planner approval, independent review acceptance, and explicit user authorization.

## 5. Resolve PPO necessity scientifically — do not assume PPO is needed

R25 explicitly requires comparison of these four arms:

| Arm | Controller |
|---|---|
| A0 | Fixed strategy |
| A1 | Random intervention |
| A2 | Deterministic rule-based controller |
| A3 | PPO ECOS controller |

The central question is not “can PPO be trained?” It is:

**Does PPO provide a reproducible and practically meaningful improvement over a competent rule-based controller, under the same task distribution, operator set, evaluator, constraints, and evaluation budget?**

Before any new run:
1. Inspect the current ECOS preregistration and implementation. Extract the exact state, action, reward, five operators, episode definition, training split, validation split, confirmation split, stopping rule, and budget.
2. Inventory whether a valid, reproducible A3 PPO checkpoint already exists. Do not assume one exists.
3. If no valid PPO checkpoint exists, explicitly state that A3 cannot yet be fairly evaluated without training. Do not substitute an untrained policy and call it PPO.
4. Separate the no-training comparison that can be conducted with A0–A2 from the A3 training/evaluation stage. Do not claim the former proves PPO superiority or necessity.
5. Prepare a preregistered A0–A3 comparison with matched tasks, seeds, evaluator, operator semantics, constraints, and accounting. Freeze primary metrics and decision thresholds before looking at confirmation results.
6. Use the R25-required metrics: effective_success_rate, answer_accuracy, tool_path_validity, format_compliance, constraint_violation_rate, hypervolume where mathematically appropriate, and inference/training cost.
7. Audit reward hacking risks, especially format/path violations and reward/evaluator mismatch. Keep DAC as the same shared fixed component in every arm.
8. Use DEV only for design/tuning and keep CONFIRM untouched until the protocol is frozen. Do not use Family C.

A0–A3 is a required comparison, not permission to train. If A3 requires new training, stop at a complete protocol and authorization request until PC1 and all other prerequisites are satisfied and the user explicitly authorizes training.

Decision logic must be predeclared:
- If A2 is statistically and practically non-inferior to A3, or A3's gain does not justify its complexity/cost, recommend against PPO as the claimed contribution.
- If A3 wins under a fair, adequately powered comparison without hard-constraint regressions, report the evidence and limitations; do not automatically start further training.
- If results are underpowered or inconclusive, say so. Do not reinterpret an inconclusive result as a win.

## 6. Hard prohibitions

Until separately approved in writing by the user and all relevant gates pass:

- **No registered PC1 execution.**
- **No Family C access** — no loading, execution, tuning, or exploratory inspection.
- **No ECOS/PPO controller training.**
- **No formal G3 efficacy rerun.**
- **No new external model/API calls.**
- **No modification of frozen R1–R25 evidence or manifests.**
- **No fabricated signatures, approval records, seeds, results, costs, tokens, CI runs, or model outputs.**
- **No GLEET code reuse or artifacts imported from another repository.**
- Do not merge/reset/force-push main or any other branch without first verifying ancestry and obtaining the required approval.

The user has previously specified DeepSeek Flash rather than DeepSeek V4 Pro for any future explicitly authorized DeepSeek API use. This does not authorize an API call. GLEPPO's prior local Qwen/A800 deployment is historical evidence, not current training authorization.

## 7. Required R26 deliverables

Commit the following, updating them as the work progresses:

1. research/R26_PC1_CURRENT_BRANCH_FINDING_AUDIT.md — complete finding inventory and source/test evidence.
2. research/R26_PC1_REMEDIATION_REPORT.md — only confirmed defects, fixes, tests, and unresolved items.
3. research/R26_ECOS_A0_A3_COMPARISON_PROTOCOL.md — fair comparison protocol, checkpoint inventory, power/seed/budget plan, primary metrics, and stop rules.
4. planner/latest_plan.md — concise current execution plan and exact next Executor task.
5. planner/GLEPPO_R26_HANDOFF.md — current state, decisions, evidence, blockers, and next-session instructions.
6. planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md — update if the next stage changes.
7. status.json — machine-readable state, exact commit, gate statuses, and evidence paths.

Do not create empty placeholder reports. If a deliverable cannot yet be completed, mark it NOT_STARTED and explain the blocker in latest_plan.md and status.json.

## 8. Git and reporting discipline

- Work only in yujian777555/GLEPPO.
- Continue from r25-handoff unless remote-ref reconciliation proves a newer authorized continuation branch.
- Before and after each stage, record exact HEAD and remote SHA.
- Never force-push or discard work.
- Run relevant tests and record exact commands, counts, and exit codes.
- Commit and push completed artifacts. Verify the pushed branch SHA and clean worktree.
- Do not claim that this branch is main. If main remains behind R25, report that separately; do not silently rewrite it.
- End each Executor task with: base SHA, result SHA, final HEAD, remote branch/SHA, changed files, tests, model/API calls, PC1 status, Family C status, training status, and remaining blockers.

**Immediate first task:** perform the exact-ref recovery, read the R25 reports, retrieve the ten historical PC1 review rounds, and build the complete finding inventory. Do not start controller training or registered PC1.

## 9. Stage 1 Executor task prompt

A dedicated Executor prompt is available at:

planner/GLEPPO_R26_STAGE1_PC1_AUDIT_EXECUTOR_PROMPT.md

When the user asks to begin execution, first read that file and issue it as the exact Stage 1 task to the Executor. It is a read-only historical/current-branch audit. Do not ask the Executor to implement fixes in Stage 1. The Executor must reconcile the R25 summary's approximately 43 findings against the 39 named IDs in its category table, using original round reports.

The Executor must stop if branch ancestry or starting refs do not match. No registered PC1, Family C access, ECOS/PPO training, formal G3 efficacy, or new model/API calls are authorized.

## 10. Latest Planner review — Stage 1B is now the immediate task

The Executor's R26 Stage 1 result at 60f60e5 is accepted only as a preliminary inventory milestone. Do not accept “43 unique findings” as a final count.

Read first:
- research/R26_STAGE1_PLANNER_REVIEW.md
- research/R26_PC1_CURRENT_BRANCH_FINDING_AUDIT.md
- research/R26_PC1_AUDIT_SUMMARY.md
- planner/GLEPPO_R26_STAGE1B_EXECUTOR_PROMPT.md
- updated planner/latest_plan.md
- updated planner/GLEPPO_R26_HANDOFF.md

Planner identified a parser false positive: the heading “R60-R61 Independent Review Result” is counted as R60. Formal finding headings in THIRD–TENTH are R12–R53 (42); R8–R11 and R54–R61 occur in remediation logs and must be separately classified. SECOND has five initial blocker bullets while status.json reports six because one bullet combines two issues. The FIRST review has not yet been found.

The Stage 1 audit report is not a 43-row current-source matrix. All candidate issues remain UNVERIFIABLE. Stage 1B must build a semantically classified register, search history for the FIRST report, reconcile the count by explicit record types and deduplication rules, then map every distinct actionable issue to current source/tests and safe offline reproduction.

Use planner/GLEPPO_R26_STAGE1B_EXECUTOR_PROMPT.md as the exact Executor task. Stage 1B is read-only with respect to production code.

Hard boundaries remain: no registered PC1, no Family C, no controller training, no Formal G3 efficacy, no external model/API calls, no production runtime, no frozen R1–R25 evidence edits.

## 11. Latest Planner review — Stage 1B taxonomy accepted, source audit not accepted

Read:
- research/R26_STAGE1B_PLANNER_REVIEW.md
- research/R26_PC1_FINDING_LEVEL_VERIFICATION.md when created
- research/R26_PC1_TEST_EVIDENCE.md when created
- planner/GLEPPO_R26_STAGE1C_EXECUTOR_PROMPT.md
- updated planner/latest_plan.md
- updated planner/GLEPPO_R26_HANDOFF.md
- status.json

Planner verified the r25-handoff branch at bcdc24f4d3c7bbaf390678670c54f642b9948a99; main was 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e and 104 commits behind. R25 base was an ancestor of Stage 1B.

The 42 formal heading count R12–R53 is accepted. The number of distinct actionable issue clusters remains unresolved. SECOND has 5–6 unnumbered blockers; TENTH has 8 remediation records R54–R61; R60–R61 review-result heading is not a formal finding.

The Stage 1B seven-domain script checks keyword presence, not semantic correctness. The reported 450/450 tests are not attached to raw output or a CI URL and have not been independently reproduced by Planner.

Planner source inspection established:
- execute_registered_pc1 in gleppo/pc1.py:1111–1117 always refuses registered execution;
- SyntheticGateHarness in gleppo/pc1.py:1400–1411 explicitly is not a full collection/rollout runner;
- ApprovalGate receives approval_key as an injected value; external trust-anchor provenance is not established;
- the approval tests use a test-only static key;
- one R39 test assertion compares a seed call with itself, although another R8 test exercises two distinct genotypes end-to-end;
- evaluator effective seed includes replica_index, while pc1.crn_seed has no replica_index parameter; inspect call sites before drawing a conclusion.

The immediate Executor task is planner/GLEPPO_R26_STAGE1C_EXECUTOR_PROMPT.md. It requires a row-by-row semantic audit of all 42 formal findings, crosswalk of SECOND blockers and R54–R61 remediation items, safe offline test evidence, and explicit residual risks. It is read-only with respect to production and test code.

Do not start Stage 2 fixes until Planner has reviewed Stage 1C and issued a separate task. No registered PC1, Family C, ECOS/PPO training, Formal G3 efficacy, production runtime, external API calls, production signing key, or frozen R1–R25 evidence edits are authorized.

