# GLEPPO R26 Stage 1 — PC1 Historical Finding Audit (Executor Task Prompt)

**Role:** Executor (implementation/repository operator)  
**Project:** GLEPPO only  
**Repository:** yujian777555/GLEPPO  
**Required branch:** r25-handoff  
**Expected starting HEAD:** 3558c65b704efa05bf1f7ad85a2bebf89b1f4414  
**R25 scientific boundary:** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**Task type:** READ-ONLY SOURCE AUDIT + EVIDENCE INVENTORY  
**Stage result:** R26_STAGE1_PC1_AUDIT_DRAFT  
**Do not execute PC1, train a controller, or access Family C.**

---

## 1. Objective

Perform a complete, source-grounded, finding-by-finding audit of all historical PC1 blockers against the current GLEPPO continuation branch.

The purpose is to determine which historical findings are genuinely fixed, partially fixed, still open, regressed, or no longer applicable. Do not infer closure from old status files, commit messages, test names, or Executor summaries. Inspect the current implementation and independently run relevant offline tests.

A key reconciliation issue must be resolved: the R25 PC1 summary says approximately 43 findings across ten rounds, but the six category lists in the R25 report enumerate only 39 distinct named IDs. Retrieve the original reports and reconcile the difference. Do not silently call 39 or 43 the verified total until the source reports establish it.

This stage is strictly read-only with respect to implementation code and frozen evidence. You may add the audit report and update planning/status/handoff documents after the audit evidence is assembled. Do not make source-code fixes in Stage 1.

## 2. Exact repository recovery — stop if inconsistent

Before reading or changing anything:

1. Fetch origin and enumerate local/remote branches and tags.
2. Check out r25-handoff. Do not work on main or another project branch.
3. Verify that HEAD is exactly 3558c65b704efa05bf1f7ad85a2bebf89b1f4414, or document every intervening commit and verify that the branch still descends from R25 base a8ff1827434a88b2fef02a89aaf3e120e0a017a7.
4. Record:
   - current branch;
   - HEAD SHA;
   - origin/r25-handoff SHA;
   - origin/main SHA;
   - merge-base of main and r25-handoff;
   - worktree status;
   - latest commit subject.
5. If the branch does not contain the R25 base, the expected handoff commit is absent, or the worktree contains unrelated user changes, stop before writing and report the exact discrepancy.
6. Do not reset, clean, rebase, force-push, cherry-pick, merge, or discard changes. Do not synchronize main as part of this task.
7. The previous handoff found that GitHub's main/status.json was stale relative to R25. Verify the actual refs rather than assuming that remains true.

## 3. Read these materials first

Read complete contents, not just excerpts:

1. status.json
2. research/R25_FINAL_GATE_DECISION.md
3. research/R25_PC1_INDEPENDENT_REVIEW.md
4. research/R25_R21_C1_REVIEW.md
5. research/R25_DAC_INDEPENDENT_AUDIT.md
6. research/R25_G3_GATE_REVIEW.md
7. research/R25_ECOS_SCIENTIFIC_REVIEW.md
8. planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md
9. planner/GLEPPO_R26_HANDOFF.md
10. planner/latest_plan.md

Then locate and read the original ten PC1 review rounds, all original finding reports, corrective reports, protocol revisions, and runner reviews. Search repository history and all relevant branches/tags if a report is not present in the current tree. Use Git history to identify renamed, superseded, or deleted reports. Do not substitute the R25 summary for original finding text.

Also locate and inspect the current versions of:
- PC1 protocol and preregistration;
- protocol canonicalization/hash implementation;
- seed/CRN derivation;
- cache and replicate accounting;
- budget ledger and planned-slot accounting;
- sample/record/episode/task provenance;
- evidence manifest and verifier;
- approval gate/signature verification;
- registered plan and runtime/evaluator lock;
- PC1 runner and synthetic fixtures;
- related tests and CI configuration.

Do not access, list, load, inspect, tune, or execute Family C. Do not inspect its contents, metadata, manifests, or paths. If a general repository listing exposes a Family C filename, do not open or traverse it; report that the boundary was preserved.

## 4. Historical finding inventory

The R25 report currently groups the named findings as follows:

| Category | IDs in R25 summary | Count |
|---|---|---:|
| Seed/CRN | R8, R16, R20, R34, R39 | 5 |
| Budget/CTX | R9, R21, R27, R28, R33 | 5 |
| Protocol | R19, R26, R36, R40, R45, R48, R49, R53 | 8 |
| Approval | R38, R42, R43, R46, R50, R54, R59 | 7 |
| Plan/provenance | R22, R29, R35, R37, R41, R44, R47, R51, R55, R58, R60 | 11 |
| PC1 runner | R15, R25, R31 | 3 |
| **Total named IDs in this table** | | **39** |

The R25 report also says approximately 43 findings across ten rounds. Reconcile this by extracting all unique findings from original round reports. For every finding, record:
- canonical finding ID, if one exists;
- exact original wording;
- round and report filename;
- whether it is a new finding, duplicate, restatement, split finding, or merged finding;
- cross-references to other IDs;
- whether the R25 category table includes it;
- final unique count and counting rule.

If the original records do not support an exact reconciliation, state that the count remains unresolved and identify the missing records. Never invent four findings to force the total to 43.

## 5. Required current-source audit matrix

Create one row per canonical finding in research/R26_PC1_CURRENT_BRANCH_FINDING_AUDIT.md.

Every row must contain:

1. Finding ID.
2. Exact original wording (quote only the necessary short text).
3. Original report filename, round, and historical commit if recoverable.
4. Category.
5. Current source path, function/class, and line range.
6. Relevant current test path and test name.
7. Independent reproduction command.
8. Actual reproduction result, exit code, and relevant output.
9. Current disposition:
   - VERIFIED_FIXED
   - PARTIALLY_FIXED
   - OPEN
   - REGRESSION
   - NOT_APPLICABLE
   - UNVERIFIABLE
10. Evidence and reasoning.
11. Remaining risk.
12. Required corrective action.
13. A precise acceptance test for a future remediation.

Use UNVERIFIABLE when the source, historical wording, or reproducible evidence is missing. Do not silently map uncertainty to fixed or not applicable.

### Evidence standards

- A passing test is evidence only for the behavior it actually exercises.
- Inspect test bodies; do not infer coverage from test names.
- For a claimed verifier/tamper check, confirm that the test invokes the verifier on the tampered artifact and asserts rejection.
- For hash checks, verify the actual bytes and all relevant manifest fields are compared.
- For CRN, inspect all seed components, override paths, cache keys, task/rollout/replicate separation, and reproducibility behavior.
- For budget accounting, distinguish logical evaluations, replica executions, cache hits, planned slots, actual slots, and billable calls.
- For approvals, verify the actual trusted artifact/signature and all bound hashes; do not treat a boolean flag or unsigned JSON as trusted authorization.
- For protocol identity, inspect canonicalization, version/status lifecycle, content hash, runtime lock, evaluator lock, and plan binding.
- For provenance, verify complete row coverage and exact linkage across task, episode, state, rollout, replicate, seed, and sample role.
- For PC1 runner claims, distinguish a synthetic fixture/accounting harness from the registered experiment path. A dry-run or synthetic harness is not registered PC1.

## 6. Audit domains that must be covered

At minimum, independently inspect the following domains and map them to all relevant historical findings:

### A. Seed and CRN
- Deterministic seed derivation.
- Full seed tuple and override behavior.
- Independence/isolation across task, state, rollout, replicate, replica, action, and genotype as required by the registered design.
- Cache-key collision and accidental reuse.
- Reproducibility across processes/platforms if claimed.

### B. Budget, cost, and accounting
- Per-replica and per-bundle accounting semantics.
- Cache-hit accounting.
- Atomic reservation/debit/reconciliation.
- Negative, overflow, under-cap, and over-cap inputs.
- Planned-slot versus actual-execution distinction.
- Exact budget exhaustion and fail-closed behavior.
- Token/call/runtime counters and provenance.

### C. Protocol and statistical analysis
- Canonical protocol dictionary and schema.
- Protocol status transitions and approval state.
- Exact constants and hash verification.
- Registered sample counts and coverage.
- DEV/CONFIRM separation and role integrity.
- Unit/task/episode/cluster assignment.
- Missing, duplicate, unexpected, or malformed records.
- Analysis recomputation and fail-closed semantics.

### D. Approval and authorization
- Trusted Planner approval provenance.
- Signature or authenticated approval verification.
- Approval expiry, replay, branch/commit binding, and revocation if applicable.
- Default-deny behavior.
- Separation of engineering preflight from experiment authorization.
- No implicit training authorization.

### E. Plan and evidence provenance
- Immutable plan identity.
- Protocol/runtime/evaluator/runner hash binding.
- Manifest completeness and path safety.
- Raw evidence read-only verification.
- Reproducible replay and audit trail.
- Exact branch/commit and environment provenance.

### F. PC1 runner
- Actual registered execution entry point.
- ApprovalGate, ProductionRuntimeGate, ProtocolVersionGate behavior.
- Per-unit budget enforcement.
- Refusal paths and bypass resistance.
- Clear separation of dry-run, synthetic fixture, smoke, and registered PC1.
- No Family C or controller-training access.

### G. Gate sequence
Confirm that the sequence remains:
G3-PREFLIGHT → approved PC1 → ECOS training → G3-EFFICACY.

Check that no gate is bypassed, that G3-PREFLIGHT is not mislabeled as Formal G3 PASS, and that training cannot start before all prerequisites and explicit user authorization.

## 7. Commands and reproducibility

Use read-only Git commands first. Examples:

- git status --short --branch
- git rev-parse HEAD
- git rev-parse origin/r25-handoff
- git rev-parse origin/main
- git merge-base origin/main origin/r25-handoff
- git log --all --oneline --decorate
- git log --all --name-status -- research
- git grep -n "PC1" <verified-branch>
- pytest <specific-test-path> -q

Adapt commands to the actual repository. Record exact commands and results. Do not run a broad command that might access Family C. Do not run tests that execute production, make external API calls, start training, or trigger registered PC1.

If a test's safety is uncertain, inspect its implementation before running it. Use offline-only test subsets and explicitly record the selection rationale.

## 8. Stage 1 outputs

Produce:
1. research/R26_PC1_CURRENT_BRANCH_FINDING_AUDIT.md — full historical inventory, count reconciliation, source/test evidence, reproduction commands, dispositions, and residual risks.
2. research/R26_PC1_AUDIT_SUMMARY.md — concise summary of verified fixed/open/partial/unverifiable findings and whether remediation is justified.
3. planner/latest_plan.md — update with the audit result and exact next stage.
4. planner/GLEPPO_R26_HANDOFF.md — record the exact state and next-session continuation.
5. planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md — update only if the next task materially changes.
6. status.json — machine-readable R26 Stage 1 status and evidence references.

Do not create an empty or speculative audit report. If the original ten rounds cannot all be found, report exactly which reports were recovered and which are missing. Keep the matrix incomplete and the gate BLOCKED/UNVERIFIABLE rather than fabricating closure.

## 9. What is explicitly out of scope

This stage does NOT authorize:
- source-code remediation or refactoring;
- registered PC1 execution;
- Family C access of any kind;
- ECOS/PPO controller training;
- formal G3 efficacy execution;
- new external model/API calls;
- new production runtime calls;
- changing frozen R1–R25 raw evidence or manifests;
- modifying main or merging branches.

Only audit documentation and project-state/handoff updates are allowed after evidence collection. If a real defect is found, document it with reproduction evidence and propose the smallest fix for a separately authorized Stage 2. Do not implement it now.

## 10. Required final report

Return a structured report with:

- Starting branch and exact base SHA.
- Final branch and exact result SHA.
- Remote branch SHA and whether it matches local HEAD.
- Worktree clean/dirty state.
- Historical review reports found / expected / missing.
- Exact unique finding count and reconciliation explanation.
- Counts by disposition.
- Five highest-risk unresolved findings and why they matter.
- Tests run: exact command, count, pass/fail, exit code.
- Tests deliberately not run and why.
- Files added/updated.
- Model/API calls: must be 0.
- Registered PC1: NOT EXECUTED.
- Family C: NOT ACCESSED.
- ECOS/PPO training: NOT STARTED.
- Formal G3 efficacy: NOT EXECUTED.
- Exact next recommended task and its acceptance criteria.

Do not report success if the audit is incomplete. End with one of:
- R26_STAGE1_AUDIT_COMPLETE_REQUIRES_PLANNER_REVIEW
- R26_STAGE1_AUDIT_INCOMPLETE_BLOCKED
- R26_STAGE1_REF_MISMATCH_STOPPED

**Start now with repository/ref recovery and historical report retrieval. Do not edit source code and do not execute any gated experiment.**
