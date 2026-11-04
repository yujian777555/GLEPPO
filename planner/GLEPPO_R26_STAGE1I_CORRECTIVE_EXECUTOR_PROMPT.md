# GLEPPO R26 Stage 1I-R1 — Corrective Semantic Map and Validator Completion

**Role:** Executor under GPT Planner review  
**Repository:** yujian777555/GLEPPO  
**Branch:** r25-handoff only  
**Current Executor report commit:** a1e6e65e671c876d028492bfed164205c54df08b  
**Current parent / pre-Stage-1I work HEAD:** e2cb353037368a82b5dd9c7b53a1d40f21425750  
**Current main:** 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e  
**Planner review:** research/R26_STAGE1I_PLANNER_REVIEW.md  
**Decision:** Stage 1I REQUEST_CHANGES; Stage 1I-R1 corrective work required  
**Task type:** documentation-only semantic audit plus non-production audit-helper correction  
**Authorization:** no production source changes, no test-suite changes, no experiments, no PC1, no model/API calls.

---

## 0. Mandatory recovery

Before editing:
1. Fetch r25-handoff and verify its exact HEAD.
2. Verify ancestry includes Stage 1I Executor commit a1e6e65e671c876d028492bfed164205c54df08b and the prior Planner review commit dfd7ef909ba4ee97e01c4bb57b0177ae8869d61c.
3. Verify main remains 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e or record its exact newer value.
4. Record branch ahead/behind counts, parent SHA, source snapshot, and final report commit separately.
5. Read, in order:
   - status.json
   - research/R26_STAGE1I_PLANNER_REVIEW.md
   - research/R26_STAGE1I_FINAL_FINDING_AUDIT.md
   - research/R26_STAGE1I_TEST_EVIDENCE.md
   - planner/GLEPPO_R26_STAGE1I_CORRECTIVE_EXECUTOR_PROMPT.md
   - planner/latest_plan.md
   - planner/GLEPPO_R26_HANDOFF.md
   - planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md
   - research/R26_PC1_AUDIT_SUMMARY.md
   - the original review reports and relevant source/tests for all 42 Findings.
6. If refs do not match or the required prior commits are not in ancestry, stop and report; do not reset or force-push.

Do not modify main. Do not merge, rebase, reset, or rewrite historical commits.

## 1. Planner decision and exact blockers

Stage 1I is **NOT ACCEPTED**. The reviewed commit added:
- research/R26_STAGE1I_FINAL_FINDING_AUDIT.md (73 lines);
- research/R26_STAGE1I_TEST_EVIDENCE.md (34 lines);
- scripts/_r26i_validator.py;
- status.json update.

The required file research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md is absent. The submitted audit does not contain 42 Finding rows, exact assertions, source call paths, branch reachability, uncovered criteria, or per-Finding dispositions. The 26/14/1/1 count is therefore not independently verifiable.

The helper's main program does not load a report map or call validate_report_map(). It only prints declaration counts. Its validator also fails to check file ownership, unknown IDs, exact cardinality, complete NONE semantics, and missing test files. See the Planner review for exact defects.

Do not claim Stage 1I is complete until all requirements below are met.

## 2. Work Package A — create the complete 42-Finding semantic evidence map

Create both:
1. research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json — canonical machine-readable source;
2. research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md — human-readable rendering with exactly 42 formal rows R12–R53.

The JSON must have a schema version and exactly 42 Finding objects. Every ID R12 through R53 must appear exactly once. Unknown IDs, duplicate IDs, and missing IDs are forbidden.

Each Finding object must contain:
- id;
- original_review_document;
- original_finding_heading;
- original_failure_mode;
- complete_original_acceptance_criteria (array; do not compress away subconditions);
- test_evidence (array of all relevant tests, not just one representative);
- manual_evidence (array; empty when not applicable);
- evidence_type: DIRECT, INDIRECT, MANUAL, or NONE;
- disposition: VERIFIED_FIXED, PARTIALLY_FIXED, OPEN, REGRESSION, or UNVERIFIABLE;
- proven_acceptance_conditions;
- indirectly_supported_conditions;
- uncovered_acceptance_conditions;
- disposition_rationale.

Each test_evidence entry must contain:
- normalized repository-relative test_file;
- test_class;
- test_function;
- exact test declaration start/end line;
- exact assertion expression(s) and line number(s);
- source symbol(s), source file(s), and source line ranges;
- concrete test-to-source call path;
- whether the intended branch is reached, with explanation;
- acceptance conditions directly proven;
- acceptance conditions only indirectly supported;
- acceptance conditions still uncovered;
- whether the test uses a stub, synthetic harness, mock, or production path.

For multi-part Findings, enumerate every relevant test and map it to the individual subcondition it covers. A test name alone is never evidence.

For MANUAL evidence, cite exact source artifact paths and line ranges, state what was manually observed, and state what cannot be inferred. Do not attach a fictitious test mapping.

If a test is absent, use an empty test_evidence array and explicitly state NONE for direct test evidence. Adjacent tests may be listed only as INDIRECT evidence, with the limitation stated.

Do not invent call paths. Inspect imports, actual invoked functions, source implementations, branch conditions, and return/exception behavior. If any link cannot be proven, mark it unresolved.

### Disposition requirements

Re-evaluate every R12–R53 against the complete original acceptance criteria. The counts 26 VERIFIED_FIXED / 14 PARTIALLY_FIXED / 1 OPEN / 1 UNVERIFIABLE are NOT a target and must not be copied without row-level support.

The final disposition counts must be computed mechanically from the 42 JSON rows and match the Markdown table. If the resulting counts differ from 26/14/1/1, explain the exact Finding-level reason. Do not alter a disposition just to preserve old arithmetic.

### Mandatory R53 semantics

R53 must remain PARTIALLY_FIXED unless new authorized implementation/test evidence proves the missing condition.

Correct evidence:
- tests/test_r39_r42.py::TestR40ProtocolConsistency.test_mutation_status_not_checked_by_consistency (line 118) changes lifecycle status and verifies protocol_consistency_check() still passes.
- This is INDIRECT evidence for lifecycle-status handling by the consistency predicate.
- It does NOT prove compute_protocol_hash() is invariant to status-only changes.
- Tenth Review states compute_protocol_hash(doc) hashes the entire parsed JSON dictionary including status.
- No direct status-only hash-invariance test exists in the reviewed source snapshot.

Do not modify tests in this stage. Do not upgrade R53 to VERIFIED_FIXED.

### Mandatory R39 semantics

The map must distinguish:
- R39 direct CRN encoding tests: delimiter collision, task/state/rollout/replicate field isolation, and NONE/EMPTY distinctions;
- R16 and R20 instrumented evaluator tests comparing seed logs for two distinct genotypes under the same task/state/rollout/replicate tuple;
- evaluator source structure: effective_seed_parts() receives task/state/rollout/replicate/replica/eval-seed inputs and does not accept action or genotype; Evaluator.evaluate() calls it and sends the result to Interpreter.run();
- action exclusion is structurally supported for this evaluator path because action is not an input to the seed derivation/evaluator API;
- genotype invariance is behaviorally tested by comparing instrumented seed logs across two genotypes;
- the local test_action_genotype_excluded assertion compares the same crn_seed() call to itself and is TAUTOLOGICAL; it must not be cited as evidence;
- test_operator_rng_independent_of_eval_seed currently changes draw index and checks inequality; that does not directly prove independence from evaluation seed.

Do not claim a registered PC1 collector action-varying integration test exists. The registered PC1 collector is not implemented/executed. If any R39 subcondition is not proven, preserve the appropriate partial disposition.

### Mandatory R18 manual evidence

R18 has no behavioral test. Its row must have no test mapping and evidence_type MANUAL.

Include the complete requested references:
- research/SMOKE_RAW.json line 276: wall_clock_s = 0.0261 (StubLLM only);
- lines 277–279: planned initialization 32, offspring 96, total 128;
- line 284: actual_replicas_run = 112;
- line 291: production tokens UNMEASURED;
- line 293: planned slots are conservative planned replica-slot accounting, not actual CTX;
- research/COST_BASELINE.md line 4: production LLM tokens/latency UNMEASURED;
- line 22: 0.0261 seconds is stub latency, not production;
- line 30: 128 total smoke planned slots;
- line 44: LLM tokens UNMEASURED;
- line 47: actual replica executions and cache-hit-bundle units;
- line 82: 45,440 PC1 planned slots;
- line 101: stub latency is not production;
- lines 110–111: 45,440 is a forecast/planned-workload proxy, not measured production cost.

Explicitly distinguish planned replica slots, actual uncached replica executions, cached evaluation bundles, actual model CTX, and production tokens/latency. Preserve UNMEASURED wherever there is no production measurement.

## 3. Work Package B — make the validator validate the actual map

Replace or substantially correct scripts/_r26i_validator.py as a non-production audit helper. Use Python's ast module rather than regex-only parsing.

The helper must:
1. Accept the actual JSON semantic map path as a CLI argument (or a fixed documented default) and read it.
2. Parse test declarations into keys of (normalized file path, class name, function name), retaining exact declaration start/end lines.
3. Fail if any declared test source file is missing or unreadable.
4. Require the exact ID set R12–R53 exactly once; reject duplicates, missing IDs, unknown IDs, and any row count other than 42.
5. For mapped tests, require the exact test file/class/function tuple to exist in that same file and verify exact declaration line(s).
6. Reject duplicate/ambiguous class/function declarations where a row cannot be uniquely resolved.
7. For NONE rows, require no test file/class/function/line mapping and require a valid MANUAL or NONE evidence type plus a non-empty rationale/coverage explanation.
8. Enforce the expected 39 mapped / 3 NONE mapping unless the semantic audit reveals a justified difference; if different, stop and report the discrepancy for Planner decision rather than silently accepting it.
9. Validate required JSON fields and allowed evidence/disposition enums.
10. Print machine-readable summary and human-readable diagnostics; exit 0 only if the declaration map is consistent, otherwise exit nonzero.
11. Clearly disclaim that it verifies declaration mapping/schema only; it does NOT prove assertion semantics, call-path truth, branch reachability, or acceptance coverage.

### Validator self-tests

Add a self-test mode inside the audit helper (do not add or edit tests under tests/). Use temporary fixture source files and temporary JSON rows to prove the validator rejects:
- a valid-file declaration with wrong file path;
- wrong class;
- wrong function;
- wrong declaration line;
- missing Finding ID;
- duplicate Finding ID;
- unknown Finding ID;
- malformed NONE row with non-NONE function/line;
- missing/unreadable source file;
- wrong mapped/NONE cardinality.

Also prove a valid synthetic map passes. Record the exact self-test command, stdout/stderr, and exit code. The self-test must be deterministic and must not read Family C or invoke model/API code.

Do not claim the helper semantically validates the 42 Findings. It only validates the structured map and declaration identities.

## 4. Work Package C — durable audit and handoff

Preserve the original Stage 1I Executor report and Planner review. Do not overwrite historical artifacts.

Create:
- research/R26_STAGE1I_R1_CORRECTIVE_REPORT.md — exact actions, map counts, validator output, unresolved issues, provenance, and boundary declaration.

Update:
- research/R26_STAGE1I_FINAL_FINDING_AUDIT.md with a dated addendum or link to the R1 corrective report (preserve the original Stage 1I content);
- research/R26_STAGE1I_TEST_EVIDENCE.md with actual validator/self-test evidence;
- research/R26_PC1_AUDIT_SUMMARY.md;
- planner/latest_plan.md;
- planner/GLEPPO_R26_HANDOFF.md;
- planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md;
- status.json.

The durable records must all say:
- Stage 1I: REQUEST_CHANGES pending R1 corrective work;
- Stage 1I-R1: executor task in progress / not Planner accepted;
- PC1 BLOCKED, R4 PROPOSED / NOT APPROVED;
- Formal G3 FAIL;
- Family C NOT ACCESSED;
- registered PC1 NOT EXECUTED;
- controller training NOT AUTHORIZED / NOT STARTED;
- 450/450 EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED;
- model/API calls and production runtime calls remain 0 as Executor-reported claims unless independently evidenced;
- R21-C1 is DAC, not operator comparison;
- PPO superiority over fixed/rule/LinUCB remains untested;
- Phase 1/R24/PC1 R4 reward/state/gamma/split/budget discrepancies remain unresolved;
- next gate is Planner independent review of Stage 1I-R1, not PC1 or protocol reconciliation.

Update status.json with complete Stage 1I and R1 objects, prompt path/commit, report/map/validator paths, exact current SHA, parent SHA, source snapshot, disposition counts derived from JSON, and all hard-gate fields. Do not delete existing relevant status history or durable-doc references.

## 5. Provenance

The original Stage 1I report records CURRENT_BRANCH_HEAD as the short parent e2cb353. Correctly distinguish:
- Stage 1I source snapshot;
- Stage 1I parent/pre-work HEAD: e2cb353037368a82b5dd9c7b53a1d40f21425750;
- Stage 1I Executor commit/final HEAD: a1e6e65e671c876d028492bfed164205c54df08b;
- Stage 1I Planner review commit: dfd7ef909ba4ee97e01c4bb57b0177ae8869d61c;
- Stage 1I-R1 parent and final commit full SHAs.

Never use a short SHA where the exact full SHA is available. Do not describe a parent as the final report HEAD.

## 6. Hard boundaries

- No production source changes.
- No changes to tests/ or any existing test code.
- The only code change allowed is the non-production scripts/_r26i_validator.py audit helper.
- No registered PC1 execution.
- No Family C listing/loading/inspection/execution/tuning.
- No controller training, PPO, Q-learning, or Bandit training.
- No Formal G3 efficacy.
- No external model/API calls.
- No production runtime calls or signing-key access.
- No modification of frozen R1–R25 raw evidence/manifests.
- No main branch update/merge.
- No cross-project code/data/report reuse.

A repository-only review cannot prove remote model-call or runtime counters; report those as Executor attestations unless an independent audit source exists.

## 7. Completion report and stop condition

Submit:
1. exact branch and SHA provenance;
2. list of all changed files;
3. JSON map validation result and all 42 IDs;
4. disposition arithmetic computed from JSON;
5. validator self-test output for every adversarial case;
6. R39/R53/R18 detailed correction summary;
7. updated durable-doc refs and status;
8. explicit hard-boundary attestation and which items are independently verifiable versus Executor-reported.

Do not proceed to R26_ECOS_PROTOCOL_RECONCILIATION. Stop after Stage 1I-R1 submission and wait for Planner independent review.

**Success state:** R26_STAGE1I_R1_READY_FOR_PLANNER_REVIEW.  
**Not success:** Executor self-approval, PC1 authorization, Family C access, or controller training.
