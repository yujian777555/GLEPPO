# GLEPPO R26 Stage 1I-R2.1 — Narrow Disposition and Validator Correction

**Role:** Executor under GPT Planner review  
**Repository:** yujian777555/GLEPPO  
**Branch:** r25-handoff only  
**Reviewed R2 work commit:** 34ba848c4b8cf4fa07c9583e049b0bb7b0635aab  
**Current provenance follow-up HEAD:** da7a6c7bbd09f1ebca5bf6080dffc78e15615115  
**Planner review:** research/R26_STAGE1I_R2_PLANNER_REVIEW.md  
**Planner decision:** REQUEST_CHANGES — R2 not yet accepted  
**Task:** R2.1, a narrowly scoped correction. Do not repeat the complete R1/R2 audit.

## 1. Mandatory recovery

Before editing:
1. Fetch r25-handoff and confirm current HEAD is da7a6c7bbd09f1ebca5bf6080dffc78e15615115 or a descendant containing the Planner review/prompt.
2. Confirm main remains 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e and do not modify it.
3. Read the Planner review, current map JSON/Markdown, validator, R2 report, status, latest_plan, handoff, next-session prompt and cumulative PC1 summary.
4. Preserve R2 work commit 34ba848 and provenance follow-up da7a6c7 as distinct historical refs.

## 2. Correct exactly the overclaimed rows

Update `research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json` and regenerate/update Markdown.

### R39 -> PARTIALLY_FIXED

There are two different executable seed paths:
- `gleppo/pc1.py::crn_seed`: versioned JSON payload [`crn-v2`, task_id, state_id, rollout_id, replicate_id].
- `gleppo/evaluator.py::Evaluator.effective_seed_parts`: separate JSON payload [base_tag, task_id, state_id, rollout_id, replicate_id, replica_index], returned with `"SEED"`; it does not call crn_seed and its payload lacks the explicit crn-v2 version tag.

Keep all seven direct crn_seed tests and the R16/R20 cross-genotype tests as separate evidence. Do not claim these establish one canonical helper contract across call sites.

Add uncovered conditions:
- one shared canonical CRN helper/schema/version across evaluator and PC1 call sites;
- registered collector action-varying integration test.

Do not alter production source or tests/.

### R41 -> PARTIALLY_FIXED

Keep the four existing artifact lifecycle tests. The row's own uncovered condition says registered analysis end-to-end consumption of the verified artifact is not behaviorally tested. Do not transfer or erase this criterion merely because R44 discusses the same path. Preserve the R44 partial limitation and accurately distinguish source inspection from behavioral test evidence.

### R48 -> PARTIALLY_FIXED

Keep the six existing reward strict-type tests. Cross-reference R40's `test_mutation_seed_contract_fails` as evidence for action/genotype field mutation only. It does not test seed version or encoding mutation.

Add explicit uncovered conditions:
- adversarial seed version mutation test;
- adversarial seed encoding mutation test;
- implementation-to-document comparison for both executable seed derivation paths.

Do not claim the protocol check's hard-coded expected schema is automatically derived from the runtime implementation.

### Counts

Recompute from JSON. Expected after these three downgrades:
- VERIFIED_FIXED 25
- PARTIALLY_FIXED 15
- OPEN 1
- UNVERIFIABLE 1
- Total 42

If new evidence changes this, explain it and cite the exact source; do not target a preferred count.

## 3. Validator fix

In `scripts/_r26i_validator.py::validate_source_symbols`, add a fail-closed check that rejects `end_line > source_file_line_count`, with a distinct diagnostic such as `SRC_RANGE_END_OUT_OF_FILE`.

Add an adversarial self-test where:
- source file exists;
- start_line is valid and within the file;
- end_line is greater than the file length.

The new case must fail specifically for the end-of-file bound, not because the range is reversed or the start line is invalid. Preserve the existing 20 cases. Target 21/21 self-tests.

The validator remains a structural validator only. Do not claim it proves assertion semantics, source-symbol identity, call-path truth or branch reachability.

## 4. Repair UTF-8 durable records

The R2 additions to `planner/latest_plan.md` and `planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md` contain mojibake. Restore the affected tail sections from their R2 parent version 3d97847adf6f68dafe1f54855d27fe00e99e16ae, then append the R2.1 state using valid UTF-8. Fetch the committed files again and inspect their actual text. Do not append another malformed-encoding section.

## 5. Update all durable records

Update:
- `research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json`
- `research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md`
- `scripts/_r26i_validator.py`
- `research/R26_STAGE1I_R2_CORRECTIVE_REPORT.md`
- `research/R26_STAGE1I_FINAL_FINDING_AUDIT.md`
- `research/R26_STAGE1I_TEST_EVIDENCE.md`
- `research/R26_PC1_AUDIT_SUMMARY.md`
- `planner/latest_plan.md`
- `planner/GLEPPO_R26_HANDOFF.md`
- `planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md`
- `status.json`

Record R2 work commit 34ba848 and provenance follow-up da7a6c7 separately. Record the final R2.1 work commit and final provenance follow-up separately if another commit is needed to record its own SHA.

## 6. Verification and stop

Required:
- JSON has exactly 42 unique IDs R12-R53.
- Markdown has exactly 42 matching row dispositions.
- JSON/Markdown summary counts match.
- Disposition counts are mechanically derived.
- Validator 21/21 self-tests pass; include raw output and exit code.
- Map validator passes.
- No production source or tests/ changes.
- No model/API calls, production runtime, PC1, Family C or controller training.
- Main unchanged.
- Branch pushed; working tree clean.

Do not run registered PC1 or train any controller. Do not begin protocol reconciliation during this corrective task.

**Stop after R2.1 commit and durable-record update. Await Planner independent review. If accepted, the next task is R26_ECOS_PROTOCOL_RECONCILIATION, which should be narrowly scoped to resolving reward/state/gamma/split/budget/seed-contract drift and preparing the fastest safe path to the approved baseline experiment.**
