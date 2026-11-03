# GLEPPO R26 Stage 1C — Finding-Level Source Verification and Safe Regression Audit

**Role:** Executor working under Planner review  
**Project:** GLEPPO only  
**Repository:** yujian777555/GLEPPO  
**Required branch:** r25-handoff  
**Last verified branch HEAD:** bcdc24f4d3c7bbaf390678670c54f642b9948a99  
**Stage 1B audited source snapshot:** a1940a220bc2b7cdc4e6ba4fe0c723fbfb33c4ec  
**R25 baseline:** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**Stage:** R26_STAGE1C_FINDING_LEVEL_VERIFICATION  
**Task type:** read-only semantic source audit + safe offline regression evidence  
**Authorization:** no production code changes; no registered experiment.

---

## 1. Planner decision and objective

Planner accepts R26 Stage 1B only as a historical taxonomy milestone:
- 42 formal numbered review-finding headings (R12–R53);
- 5–6 unnumbered SECOND blockers;
- 8 TENTH remediation records (R54–R61);
- one R60–R61 review-result heading, not a formal finding.

The count of distinct underlying actionable issue clusters is still unresolved. Do not repeat “42 unique actionable findings” as a proven count. Keep separate:
1. formal numbered review headings;
2. unnumbered SECOND blockers;
3. remediation records;
4. distinct underlying issue clusters after cross-round deduplication.

Stage 1B's seven-domain scan is not accepted as a source audit because scripts/_r26b_source_audit.py checks whether keywords occur in files. It does not validate call paths, invariants, test coverage, or real execution behavior. The reported 450/450 test result is not accompanied by raw stdout/stderr or a CI run URL and has not been independently reproduced by Planner.

**Your objective is now to verify each historical formal finding against actual current source and test behavior.** Do not repeat keyword scans or merely list modules that contain relevant terms.

## 2. Exact repository and provenance recovery

Before any edits:

1. Fetch repository refs and verify the current r25-handoff HEAD.
2. Verify current HEAD descends from bcdc24f4d3c7bbaf390678670c54f642b9948a99 and the R25 base a8ff1827434a88b2fef02a89aaf3e120e0a017a7.
3. Record current branch, HEAD, origin/r25-handoff SHA, origin/main SHA, merge-base, worktree status, and latest commit.
4. Previous Planner verification established:
   - r25-handoff was at bcdc24f4d3c7bbaf390678670c54f642b9948a99;
   - main was at 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e;
   - main was 104 commits behind r25-handoff and not ahead of it;
   - R25 base was an ancestor of bcdc24f (23 commits ahead, 0 behind).
5. Re-check these values; do not assume they remain unchanged.
6. Distinguish three provenance points in every report:
   - source snapshot actually inspected;
   - report/document commit;
   - current final branch HEAD.
7. If ancestry fails or unrelated worktree changes exist, stop before modifying anything.
8. Do not reset, clean, rebase, cherry-pick, merge, force-push, or update main.

## 3. Read the source materials in full

Read:
- status.json;
- research/R26_PC1_FINDING_REGISTER.md;
- research/R26_PC1_CURRENT_BRANCH_FINDING_AUDIT.md;
- research/R26_PC1_AUDIT_SUMMARY.md;
- research/R26_STAGE1_PLANNER_REVIEW.md;
- research/R26_STAGE1B_PLANNER_REVIEW.md;
- research/SECOND_REVIEW_FINDINGS.md through research/TENTH_REVIEW_FINDINGS.md;
- research/R25_PC1_INDEPENDENT_REVIEW.md;
- planner/latest_plan.md;
- planner/GLEPPO_R26_HANDOFF.md;
- planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md;
- planner/GLEPPO_R26_STAGE1B_EXECUTOR_PROMPT.md;
- this prompt.

Search all refs and Git history for a FIRST review artifact or equivalent. Stage 1B did not report an exhaustive search. If FIRST cannot be found, record the exact history/ref search scope and mark it MISSING_SOURCE. Do not invent its contents.

Do not list, open, load, inspect, tune, or execute Family C files, data, metadata, or manifests. If a broad tree listing shows a Family C path, do not open or traverse it.

## 4. Work Package A — finalize the historical issue crosswalk

The Stage 1B register currently lists R12–R53 as formal findings, SECOND as 5–6 unnumbered blockers, and R54–R61 as eight remediation records.

For every formal ID R12–R53:
- retrieve the exact original review text and source section;
- identify the first appearance and subsequent cross-references;
- record the historical source commit if recoverable;
- distinguish the original issue from later remediation descriptions;
- identify duplicates, restatements, splits, merges, and superseding records.

For SECOND:
- inspect its five initial numbered blocker bullets;
- reconcile why status.json contains six blocker descriptions;
- determine whether one bullet combines two independently testable defects;
- document the exact split rule and acceptance criteria if split;
- map remediation labels R8–R11 to the relevant blocker(s) only where the source supports the mapping.

For TENTH:
- distinguish formal findings R50–R53;
- distinguish remediation records R54–R61;
- distinguish the R60–R61 review-result heading from both finding and remediation records;
- map remediation entries to the issue they addressed and the evidence used for acceptance.

Do not force a single aggregate total. Report the formal heading count, unnumbered blocker count, remediation record count, and distinct issue-cluster count separately. If issue-cluster deduplication is not supportable, keep that count unresolved.

## 5. Work Package B — complete the 42-row semantic source audit

Create a row for every formal finding ID R12–R53. Also create linked rows for the SECOND blockers and R54–R61 remediation records, but do not inflate the formal finding count with these records.

Each row must include:

1. canonical ID and record type;
2. exact original issue statement (brief excerpt only);
3. source review filename, section/line range, review round, and historical commit if known;
4. cross-reference / split / duplicate / supersession links;
5. current source path, function/class, and exact line range;
6. current behavior observed from source control flow, not keyword presence;
7. exact related test path and test function;
8. what the test actually asserts and whether it reproduces the original failure mode;
9. safe reproduction/test command;
10. actual output, exit code, and test count;
11. disposition:
    - VERIFIED_FIXED
    - PARTIALLY_FIXED
    - OPEN
    - REGRESSION
    - NOT_APPLICABLE
    - UNVERIFIABLE
12. evidence and reasoning;
13. residual risk;
14. smallest corrective action;
15. precise acceptance test for a future remediation.

Do not mark a finding VERIFIED_FIXED merely because a function exists or a test passes. Require a test that exercises the relevant behavior and an inspected implementation path that enforces the requirement. If the evidence is insufficient, use UNVERIFIABLE.

### Mandatory domain-specific checks

#### A. Seed / CRN
Inspect:
- gleppo/evaluator.py effective_seed_parts and _cache_key;
- gleppo/evaluator.py evaluate call path;
- gleppo/pc1.py crn_seed and operator_rng_seed;
- all call sites that construct StateActionRecord.crn_seed and effective_seed_parts;
- seed schema in research/PC1_PROTOCOL_R4_PROPOSED.md;
- tests/test_r8_r9_r11_pc1.py;
- tests/test_r39_r42.py;
- tests/test_r26_r32.py and any relevant R12–R17 tests.

Specifically determine:
- whether evaluation seeds are independent of action/genotype while operator-generation RNG remains action/operator-specific;
- whether task, state, rollout, replicate, and replica index are all represented at the effective RNG boundary;
- whether the standalone pc1.crn_seed helper is a base/summary key or is incorrectly used as the full effective seed;
- whether None, empty string, typed values, delimiters, and serialization edge cases can collide;
- whether cache identity includes genotype identity and all seed-affecting/runtime/evaluator fields;
- whether end-to-end tests actually compare different genotypes/actions through an instrumented interpreter.

Important known test-quality issue to verify rather than blindly repeat:
- tests/test_r39_r42.py lines 96–100 labels a test as action/genotype exclusion but compares the same crn_seed call with itself. This individual assertion is tautological.
- tests/test_r8_r9_r11_pc1.py lines 50–64 does compare two distinct genotypes under the same CRN tuple through an instrumented interpreter. Assess both together.

#### B. Budget / CTX / cache
Inspect:
- BudgetLedger methods in gleppo/pc1.py;
- evaluator replica and cache counters in gleppo/evaluator.py;
- all call sites that pass deltas into BudgetLedger;
- initialization, offspring, invalid-offspring, collection, Q and extra-slot accounting;
- tests/test_r8_r9_r11_pc1.py and tests/test_r26_r32.py, tests/test_r33_r38.py.

Verify logical planned slots, actual replica executions, cache-hit bundles, valid/invalid offspring, LLM calls, and episode-level deltas are never mixed. Test partial-mutation failure cases, cap boundary, invalid types including bool, negative values, reconciliation, and cache hit/miss behavior.

#### C. Statistical analysis / sample integrity
Inspect:
- StateActionRecord schema;
- validate_records;
- compute_r_hat, compute_q_hat, bootstrap and run_pc1_analysis;
- sample-role coverage, duplicate detection, cluster/episode/task mapping;
- all R13/R14/R17/R18 and later related tests.

Verify missing, duplicate, unexpected, non-finite, malformed, incomplete, and cross-role records fail closed. Check that estimator and bootstrap code use the registered cluster/episode unit correctly.

#### D. Protocol identity / canonical hash
Inspect:
- parse_protocol_document;
- duplicate-key rejection;
- strict schema and numeric validation;
- compute_protocol_hash and protocol_consistency_check;
- lifecycle status exclusion/inclusion rules;
- registered protocol hash constants;
- plan artifact three-way hash binding;
- tests/test_r19_r25.py, tests/test_r26_r32.py, tests/test_r33_r38.py, tests/test_r39_r42.py, tests/test_r54_r59.py and relevant C7 protocol tests.

Test actual document-byte mutations, semantic field changes, duplicate keys, wrong version, lifecycle-only changes, malformed fields, and stale registered constants. A test that only monkey-patches a function is not proof that real file changes are caught unless it exercises the actual loader path.

#### E. Approval and trusted authorization
Inspect:
- TrustedApprovalArtifact.sign and verify;
- PlannerApprovalRecord.validate;
- ApprovalGate.check;
- where approval_key is sourced and how its provenance is validated;
- whether a mutable caller can choose both the signing key and verifier key;
- replay, expiry, branch/commit binding, protocol document ID, action, status, protocol hash/version and runtime lock binding;
- tests/test_r54_r59.py and tests/test_r39_r42.py.

Separate these claims:
1. HMAC implementation correctly rejects malformed/incorrect signatures;
2. a valid HMAC artifact exists;
3. the key is controlled by an independent trusted authority;
4. the approval is tied to the exact reviewed branch/commit and action.

Do not create, request, load, or provision any production signing key. The static test key is test-only and must not be treated as a production trust anchor. The canonical protocol remains PROPOSED_NOT_APPROVED; do not change it.

#### F. Plan / provenance / evidence
Inspect:
- generate_plan_mapping and canonical plan hash;
- save_plan_artifact and load_plan_artifact;
- validate_provenance_against_plan;
- manifest verifier and raw evidence replay;
- path traversal, symlink and file mutation handling;
- binding of plan ID/version/hash, protocol hash, runtime revision, evaluator version, runner version, branch/commit and sample provenance;
- tests/test_r39_r42.py, tests/test_r54_r59.py, evidence tests and all relevant provenance tests.

Test self-consistent but noncanonical plans, stale artifacts, mutated mapping, missing fields, path traversal, symlink substitution, manifest tampering and record-to-plan mismatch. Do not read or alter frozen R1–R25 evidence.

#### G. PC1 runner and gate sequence
Inspect:
- execute_registered_pc1;
- SyntheticGateHarness;
- ApprovalGate, ProductionRuntimeGate and ProtocolVersionGate;
- all runner entry points and CLI/script call paths;
- whether a registered collection/rollout runner actually exists.

Planner has already observed:
- gleppo/pc1.py lines 1111–1117: execute_registered_pc1 unconditionally raises PC1ExecutionRefused;
- gleppo/pc1.py lines 1400–1411: SyntheticGateHarness explicitly says it does not load tasks, invoke evaluators, execute rollouts, or write raw artifacts, and that the full runner is not yet implemented.

Verify this against the current branch and historical R15/R25/R31 requirements. Do not relabel a synthetic accounting harness as a registered runner. Keep the gate sequence:
G3-PREFLIGHT → approved PC1 → ECOS training → G3-EFFICACY.

G3-PREFLIGHT READY is not Formal G3 PASS. Registered PC1 execution must remain refused.

## 6. Work Package C — test evidence and the 450/450 claim

Stage 1B reports the command:

python -m unittest discover -s tests

with 450/450 PASS and exit code 0, but it did not attach raw output or a CI run URL. Planner has not independently reproduced that result.

Before running tests:
1. Inspect each relevant test file, imports, fixtures and subprocess behavior.
2. Confirm no test loads, lists, reads, or executes Family C.
3. Confirm no test makes network/API calls, starts production runtime, loads/trains a controller, or invokes registered PC1.
4. If a test's side effects are uncertain, do not run it.
5. Prefer targeted offline tests for the finding under review.
6. Run the full suite only if the complete suite has been inspected and demonstrated safe under all prohibitions.

For every command record exact invocation, working directory, exit code, stdout/stderr or a stable log artifact, test count, pass/fail/skip counts, and the specific findings it supports. A 450/450 aggregate result does not verify a finding unless the corresponding test body exercises that behavior.

Do not change test files in this stage. If a test is tautological or insufficient, record the missing test and propose a precise acceptance test for Stage 2.

## 7. Work Package D — reconcile status.json provenance

Stage 1B status.json top-level fields include reviewed_commit=e6ae41... and R3 implementation/experimental status fields. These may be historical R3 facts.

Inspect the status schema and Git history. Preserve historical R3 values, but add clearly scoped R26 fields identifying:
- audited source snapshot;
- Stage 1B report commit;
- Stage 1C final report commit;
- current branch HEAD;
- main SHA and branch comparison;
- formal heading count;
- unnumbered blocker count and split uncertainty;
- remediation record count;
- distinct actionable issue cluster count or unresolved status;
- per-finding disposition counts;
- test evidence references;
- all safety gates.

Do not silently replace historical status fields or mislabel the current source commit.

## 8. Required outputs

Create/update:

1. research/R26_PC1_FINDING_LEVEL_VERIFICATION.md — complete 42-row formal finding matrix plus linked SECOND/remediation crosswalk.
2. research/R26_PC1_TEST_EVIDENCE.md — safe test inventory, exact commands, raw results, coverage mapping, and skipped tests with reasons.
3. research/R26_PC1_FINDING_REGISTER.md — update only where crosswalk/deduplication is evidenced; preserve the 42 formal-heading count and distinguish issue clusters.
4. research/R26_PC1_CURRENT_BRANCH_FINDING_AUDIT.md — replace the misleading seven-domain lexical-scan conclusion with a clearly labeled Stage 1B preliminary record plus the actual Stage 1C finding-level matrix or a pointer to it.
5. research/R26_PC1_AUDIT_SUMMARY.md — summarize actual dispositions and remaining blockers.
6. planner/latest_plan.md — exact next task and gate.
7. planner/GLEPPO_R26_HANDOFF.md — exact refs, evidence and blockers.
8. planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md — next-stage continuation.
9. status.json — scoped R26 provenance and status.

Do not create empty placeholders. If all 42 findings cannot be verified, state exactly which are complete and which remain UNVERIFIABLE. Do not call Stage 1C complete unless every formal finding has a defensible disposition and the unnumbered blockers/remediation crosswalk is documented.

## 9. Strict prohibitions

- No registered PC1 execution.
- No Family C access of any kind: no listing, loading, reading, inspecting, tuning or executing.
- No ECOS/PPO controller training.
- No Formal G3 efficacy rerun.
- No new model/API calls.
- No production runtime calls.
- No production source-code fixes or refactors.
- No test-code changes.
- No modification of frozen R1–R25 raw evidence or manifests.
- No new approval artifact or signature.
- No production signing-key access or provisioning.
- No merge/reset/rebase/force-push or update of main.
- No cross-project code or artifact reuse.

The user's preference for DeepSeek Flash applies only to a future explicitly authorized API call. It does not authorize one now.

## 10. Final report contract

Report:
- starting branch and exact HEAD;
- source snapshot inspected;
- current remote branch SHA and final report SHA;
- main SHA and ahead/behind comparison;
- worktree status;
- FIRST review search scope/result;
- formal heading count, blocker count, remediation count and deduplicated issue-cluster count;
- a disposition table for all R12–R53;
- five highest-risk unresolved findings and exact evidence;
- test inventory, commands, raw outputs, counts and skips;
- why each test supports each finding;
- files changed;
- model/API calls = 0;
- registered PC1 = NOT EXECUTED;
- Family C = NOT ACCESSED;
- controller training = NOT STARTED;
- Formal G3 efficacy = NOT EXECUTED;
- production source changes = 0.

End with one status:
- R26_STAGE1C_FINDING_LEVEL_AUDIT_COMPLETE_REQUIRES_PLANNER_REVIEW
- R26_STAGE1C_AUDIT_INCOMPLETE_BLOCKED
- R26_STAGE1C_REF_MISMATCH_STOPPED

**Immediate action:** verify refs, inspect exact source and test paths, complete the finding-level evidence matrix, and run only safe offline tests. Do not implement fixes or execute gated experiments.
