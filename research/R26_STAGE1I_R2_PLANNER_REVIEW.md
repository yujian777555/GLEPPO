# R26 Stage 1I-R2 Planner Independent Review

**Date:** 2026-11-04  
**Repository:** yujian777555/GLEPPO  
**Branch:** r25-handoff  
**Reviewed work commit:** 34ba848c4b8cf4fa07c9583e049b0bb7b0635aab  
**Current provenance follow-up HEAD:** da7a6c7bbd09f1ebca5bf6080dffc78e15615115  
**R2 parent:** 3d97847adf6f68dafe1f54855d27fe00e99e16ae  
**Main:** 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e  
**Decision:** REQUEST_CHANGES — R2 NOT YET ACCEPTED  
**Next task:** Stage 1I-R2.1 narrow disposition/validator/handoff correction

## 1. Executive decision

R2 is a substantial improvement and its structural work is accepted:
- 42 unique Finding IDs R12-R53;
- 193 test-evidence entries across 39 mapped rows;
- no null source-symbol line ranges;
- major omissions and false call paths identified in R1 were corrected;
- JSON/Markdown disposition arithmetic is 28/12/1/1 = 42;
- R2 work commit changes documentation, the JSON/Markdown map, status and the non-production audit helper; no production source or tests/ changes;
- main remains unchanged.

However, three rows still overstate their disposition. R2 must not be accepted with 28 VERIFIED_FIXED until these are corrected. This is a narrow R2.1 task, not a restart of the 42-row audit.

## 2. Blocking semantic disposition corrections

### R39 — VERIFIED_FIXED is not supported

The two actual seed derivation paths are not one canonical versioned helper:

- `gleppo/pc1.py::crn_seed` serializes [`"crn-v2"`, task_id, state_id, rollout_id, replicate_id].
- `gleppo/evaluator.py::Evaluator.effective_seed_parts` independently serializes [base_tag, task_id, state_id, rollout_id, replicate_id, replica_index] and returns (`"SEED"`, encoded). The serialized evaluator payload itself does not carry the `crn-v2` version tag and it does not call `crn_seed`.

The seven direct tests prove the standalone helper's collision/reproducibility properties. R16/R20 tests prove cross-genotype invariance of the separate evaluator path. They do not prove both paths share one canonical versioned contract or that all call sites use the same helper.

Required disposition: **PARTIALLY_FIXED**. Explicitly list as uncovered:
- one shared canonical CRN contract/version across PC1 and evaluator call sites;
- registered collector action-varying integration (still unimplemented).

Do not modify production source or tests/ in R2.1.

### R41 — VERIFIED_FIXED conflicts with its own uncovered condition

R41's original criteria include registered analysis loading and validating against the verified artifact. The R41 test array covers save/load round-trip, tamper rejection, defensive copy and wrong hash, but the row still lists end-to-end registered analysis artifact consumption as uncovered. R44's partial/source-level evidence cannot silently erase R41's own uncovered condition.

Required disposition: **PARTIALLY_FIXED** unless the row explicitly supplies and verifies direct end-to-end evidence already present in the repository. Do not invent such a test. Preserve the R44 limitation.

### R48 — VERIFIED_FIXED conflicts with incomplete seed-schema evidence

R48 requires exact seed version/encoding comparison with implementation and adversarial mutation tests for version, encoding, extra/missing keys and wrong types.

The R48 test array currently maps six R56 strict-type tests, all focused on reward-contract types/keys. R40's `test_mutation_seed_contract_fails` covers a seed-field mutation (action/genotype inclusion), but there are no mapped direct version/encoding mutation tests.

Further, `protocol_consistency_check` compares document seed_schema to hard-coded expected fields/version/encoding; it does not derive those values from both executable seed paths. The evaluator path and `crn_seed` path currently use different serialized schemas.

Required disposition: **PARTIALLY_FIXED**. Explicitly list missing version/encoding adversarial tests and implementation-to-document cross-check as uncovered. Cross-reference the existing R40 seed-contract mutation test accurately; do not claim it tests version or encoding.

### Corrected disposition arithmetic

Downgrading R39, R41 and R48 changes the mechanically derived counts to:

| Disposition | Corrected count |
|---|---:|
| VERIFIED_FIXED | 25 |
| PARTIALLY_FIXED | 15 |
| OPEN | 1 |
| UNVERIFIABLE | 1 |
| **Total** | **42** |

This is the expected correction unless additional evidence is discovered. Do not preserve 28/12/1/1 for cosmetic reasons.

## 3. Validator defect

In `validate_source_symbols`, the file-length check verifies that start_line is not beyond EOF, but does not reject end_line greater than the source file's line count. The current wrong-range self-test uses start_line=999 and end_line=3; it exercises reversed-range handling, not the missing end-of-file bound.

R2.1 must:
- reject end_line > source-file line count with a distinct diagnostic;
- add an adversarial self-test where start_line is valid and end_line is beyond EOF;
- preserve all existing 20 self-tests and add the new test;
- do not claim the validator proves symbol semantics, call paths, assertion truth or branch reachability (its disclaimer correctly excludes these).

## 4. Durable-record encoding defect

The R2 commit appended mojibake/incorrectly decoded text to:
- `planner/latest_plan.md`
- `planner/GLEPPO_R26_NEXT_SESSION_PROMPT.md`

The parent versions at 3d97847 are correctly encoded. Restore these affected tail sections from the parent and re-append the R2.1 state as valid UTF-8. Check the actual fetched text after commit; no replacement characters or mojibake sequences are acceptable.

## 5. Provenance and independent-verification limits

- R2 work commit: 34ba848c4b8cf4fa07c9583e049b0bb7b0635aab.
- Provenance follow-up commit: da7a6c7bbd09f1ebca5bf6080dffc78e15615115.
- Current branch HEAD at review: da7a6c7bbd09f1ebca5bf6080dffc78e15615115.
- Main: 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e.
- GitHub check runs for current HEAD: 0; commit status entries: 0.
- 450/450 remains EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED.
- 20/20 validator self-tests remain Executor-reported; Planner has statically inspected the validator and identified the EOF upper-bound gap.

Record work commit and provenance follow-up HEAD as separate fields. Do not call 34ba848 the current branch HEAD.

## 6. R2.1 deliverables

1. Correct the JSON rows R39/R41/R48 and mechanically recompute counts.
2. Regenerate/update Markdown so all 42 row dispositions and summary match JSON.
3. Update the R2 corrective report with this Planner review and R2.1 corrections.
4. Fix validator end_line EOF bound and add the 21st adversarial self-test.
5. Repair UTF-8 tails in latest_plan and next-session prompt.
6. Update handoff, cumulative PC1 audit summary and status.json with exact provenance.
7. Confirm branch head, clean working tree, no production source/tests changes, main unchanged.

## 7. Hard gates remain unchanged

- PC1 BLOCKED; R4 PROPOSED / NOT APPROVED.
- Formal G3 FAIL.
- Family C NOT ACCESSED.
- Registered PC1 NOT EXECUTED.
- Controller training NOT AUTHORIZED / NOT STARTED.
- No model/API calls, production runtime or signing-key access.
- No production source or tests/ changes.
- No frozen R1-R25 evidence/manifest changes.
- No main merge/update/reset/rebase/force-push.
- No cross-project code/data/report reuse.

**Next:** R2.1 executor completion -> Planner independent review. If accepted, proceed directly to R26_ECOS_PROTOCOL_RECONCILIATION. Do not run PC1 or train the controller during R2.1.
