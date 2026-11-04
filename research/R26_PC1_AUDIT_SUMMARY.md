# GLEPPO R26 PC1 Audit Summary

**Updated:** 2026-11-04  
**Repository:** yujian777555/GLEPPO  
**Branch:** r25-handoff  
**Current stage:** R26 Stage 1I-R2 — semantic evidence correction and validator hardening (Executor not yet started)  
**Latest Planner decision on Stage 1I:** REQUEST_CHANGES  
**PC1:** BLOCKED

## 1. Historical inventory

| Record type | Current count | Interpretation |
|---|---:|---|
| Formal review headings | 42 | R12–R53 |
| SECOND unnumbered blockers | 5–6 | split rule still needs documented reconciliation |
| TENTH remediation records | 8 | R54–R61 |
| R60–R61 review-result heading | 1 | not a formal Finding |
| Distinct actionable issue clusters | UNRESOLVED | requires cross-round deduplication |

## 2. Stage 1C Executor claim versus Planner decision

Executor reported:
- 42/42 source files verified;
- 42/42 formal findings VERIFIED_FIXED;
- two test files;
- 450/450 tests PASS, exit code 0.

Planner rejects the 42/42 VERIFIED_FIXED claim because the evidence method does not substantiate it.

### Verifier limitation

scripts/_r26c_finding_verify.py:
- assigns each Finding a source path and a test path;
- checks only Path.exists();
- counts literal "def test_" occurrences;
- does not inspect source symbols/call paths or test assertions;
- does not execute tests or capture output;
- ends with NEEDS_DETAILED_VERIFICATION.

### Test mapping limitation

- tests/test_c7.py imports genotype/operators/interpreter/LLM/tasks/tools, not gleppo.pc1 or gleppo.evaluator. Its 17 tests do not cover the claimed PC1 domains.
- tests/test_c7r1c2_protocol.py tests scripts/protocol_hash.py text normalization/hash updates, not PC1 structured protocol semantics.
- Relevant PC1 test suites exist: test_r8_r9_r11_pc1.py, test_r12_r17.py, test_r19_r25.py, test_r26_r32.py, test_r33_r38.py, test_r39_r42.py and test_r54_r59.py. Stage 1D must inspect exact functions and assertions.
- The reported 450/450 result has no raw stdout/stderr, saved log or CI URL and has not been independently reproduced by Planner.

## 3. Category arithmetic correction required

The Stage 1C category table is inconsistent:
- Protocol lists 9 IDs but reports 8;
- Approval lists 5 IDs but reports 6;
- Provenance lists 9 IDs but reports 7;
- R24 appears in both Budget and Cost;
- reported category counts sum to 41, not 42.

Stage 1D must provide one primary category per formal ID, or explicitly distinguish multi-label category memberships from unique ID counts.

## 4. Concrete implementation observations

### Runner

- gleppo/pc1.py:1111–1117: execute_registered_pc1() unconditionally refuses.
- gleppo/pc1.py:1400–1411: SyntheticGateHarness explicitly does not load tasks, invoke evaluators, execute rollouts or write raw artifacts.

This is fail-closed and correctly labels a synthetic accounting harness. It does not prove a full runner exists. Assess R15, R25 and R31 separately against their original criteria.

### Approval

- gleppo/pc1.py:1320–1365: ApprovalGate requires a TrustedApprovalArtifact and injected approval_key, checks canonical APPROVED status, calls artifact.verify(), and checks protocol hash.
- tests/test_r54_r59.py uses a static test-only key.

This is meaningful HMAC/gate integration progress. It does not establish independent production trust-anchor/key provenance. Assess R43, R46 and R50 separately.

### Protocol and CRN

- gleppo/pc1.py:126–223 has structured protocol checks.
- gleppo/pc1.py:230–239 has a versioned JSON CRN helper.
- gleppo/evaluator.py:57–103 has typed effective seed and cache-key logic.

These are source-level implementation elements, not blanket proof. They require the relevant PC1 tests and actual assertions.

## 5. Current Planner disposition

**R26_STAGE1C_REPORT_RECEIVED_REQUEST_CHANGES; FINDING_LEVEL_EVIDENCE_RECONCILIATION_REQUIRED; PC1 BLOCKED.**

No blanket VERIFIED_FIXED dispositions are accepted from Stage 1C. Stage 1D must establish each status using original acceptance criteria, actual source paths, exact test functions and safe reproduced results.

## 6. Next task

Execute planner/GLEPPO_R26_STAGE1D_EXECUTOR_PROMPT.md.

Stage 1D is read-only with respect to production source and test code. It must:
1. inspect the correct existing PC1 tests;
2. correct all 42 Finding dispositions;
3. reconcile category arithmetic;
4. reproduce safe targeted tests with raw output/logs;
5. distinguish HMAC mechanics from trusted-key provenance;
6. distinguish a synthetic harness from a real collection/rollout runner;
7. preserve all execution prohibitions.

## 7. Hard gates

| Gate | State |
|---|---|
| PC1 registered execution | BLOCKED / NOT EXECUTED |
| Family C | NOT ACCESSED |
| ECOS/PPO training | NOT STARTED / NOT AUTHORIZED |
| Formal G3 | FAIL |
| Model/API calls in Stage 1C | 0 reported |
| Production runtime | NOT EXECUTED |

---

## 8. Stage 1D Planner correction — 2026-11-04

**Planner decision:** REQUEST_CHANGES. Stage 1D materially improves Stage 1C but is not accepted as a completed 42-Finding audit.

- R18 is a formal Finding and is missing from the Stage 1D table; retain R18 separately from R24.
- Provenance lists nine IDs but reports seven.
- The stated 30/8/1/1 disposition counts sum to 40.
- R46 appears in the partial list and as unverifiable in the detailed table.
- Only five Findings have a test mapping, with abbreviated or nonexistent test names.
- The 218 figure is a correct count of test functions across seven PC1-related suites, not proof of 218 distinct Finding-level tests.
- _r26d_test_inspect.py only inventories function declarations/imports.
- No raw 450/450 log or CI run on Stage 1D commit ca0c909 was found. Keep the result EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED.
- R45/R48/R52/R49/R53 require more direct test evidence; R43's existing gate-level negative test must be acknowledged.

Full review: research/R26_STAGE1D_PLANNER_REVIEW.md.

Next: R26 Stage 1E, prompt planner/GLEPPO_R26_STAGE1E_EXECUTOR_PROMPT.md. PC1 remains BLOCKED.

---

## 9. Stage 1E Planner correction — 2026-11-04

**Planner decision:** REQUEST_CHANGES. Stage 1E bookkeeping is accepted, but the exact test evidence map is not.

Accepted:
- 42 formal IDs R12–R53 appear exactly once;
- category and disposition arithmetic both sum to 42;
- R18 restored separately from R24;
- R46 has one disposition;
- 218 test-function count is correct;
- 450/450 remains labelled EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED.

Critical issue: the 42-row test map does not use actual test declarations. Across the seven PC1-related suites, only 3 mapped class names exist, only 1 mapped function name exists (under a different class), and no class/function pair matches. Assertion descriptions are not actual assertions. Exact file paths, line ranges, source symbols and call paths are missing.

At minimum R24, R52 and R53 must be PARTIALLY_FIXED absent direct acceptance evidence. R18 may remain VERIFIED_FIXED after a precise manual comparison to the current raw artifact.

Full review: research/R26_STAGE1E_PLANNER_REVIEW.md.  
Next: R26 Stage 1F, planner/GLEPPO_R26_STAGE1F_EXECUTOR_PROMPT.md.  
PC1 remains BLOCKED.

---

## 10. Stage 1F Planner correction — 2026-11-04

**Planner decision:** REQUEST_CHANGES. Stage 1F has 42 unique Finding IDs and correct category arithmetic, but its disposition summary and test map are not accepted.

The 42 detailed rows recount to:
- 27 VERIFIED_FIXED;
- 13 PARTIALLY_FIXED;
- 1 OPEN;
- 1 UNVERIFIABLE.

The report summary, status.json and commit message instead say 22/15/1/1, which sums to 39. The ID lists in that summary contain 27 verified IDs and 13 partial IDs.

The 39 mapped class names exist in the stated test files, but only 5 function names match a real declaration in the stated class/file. The other 34 do not exist. Only 5/42 class/function/file triplets are exact. The helper script inventories declarations but does not validate the map.

The 218 count is accepted only as a declared-method inventory. 450/450 remains EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED. R18 may remain VERIFIED_FIXED on manual raw/document comparison with exact line references.

Full review: research/R26_STAGE1F_PLANNER_REVIEW.md.  
Next: R26 Stage 1G, planner/GLEPPO_R26_STAGE1G_EXECUTOR_PROMPT.md.  
PC1 remains BLOCKED.



---

## 11. Stage 1G Planner correction — 2026-11-04

**Planner decision:** REQUEST_CHANGES.

Accepted:
- 42 rows count to 27 VERIFIED_FIXED / 13 PARTIALLY_FIXED / 1 OPEN / 1 UNVERIFIABLE;
- category counts sum to 42;
- 42 classes and 218 test declarations independently confirmed;
- 37/39 mapped file/class/function/line tuples match.

Not accepted:
- R31 and R49 function names;
- generic assertion labels instead of exact assertion expressions;
- missing source call paths and uncovered acceptance conditions;
- R39 tautological test mapping;
- R53 unrelated seed-schema test mapping;
- R19 VERIFIED_FIXED while canonical protocol remains PROPOSED / NOT APPROVED;
- missing R18 exact line references;
- unresolved report commit/HEAD placeholders;
- stale handoff documents.

Full review: research/R26_STAGE1G_PLANNER_REVIEW.md.  
Next: R26 Stage 1H, planner/GLEPPO_R26_STAGE1H_EXECUTOR_PROMPT.md.  
PC1 remains BLOCKED.

---

## 12. Stage 1H Planner correction — 2026-11-04

**Planner decision:** REQUEST_CHANGES.

Accepted:
- 42 unique formal IDs R12–R53;
- disposition arithmetic 26/14/1/1 = 42;
- category counts sum to 42;
- 39/39 exact declaration mappings;
- R31/R49 corrected and R19 downgraded;
- 218 declared test functions;
- 450/450 remains not independently reproduced.

Not accepted:
- Stage 1H evidence table has no actual assertion expressions, source call paths, intended-branch analysis, acceptance coverage or uncovered conditions;
- R53 remains mapped to the unrelated seed_schema mutation test at line 130;
- R39 action/genotype exclusion lacks R16/R20 cross-genotype evidence references;
- R18 lacks complete unit/token/production-cost references;
- helper does not validate the report map;
- handoff/cumulative records are stale;
- Stage 1H report omits its final commit SHA.

Full review: research/R26_STAGE1H_PLANNER_REVIEW.md.  
Next: R26 Stage 1I, planner/GLEPPO_R26_STAGE1I_EXECUTOR_PROMPT.md.  
PC1 remains BLOCKED.

---

## 13. Stage 1H Planner decision and Stage 1I handoff — 2026-11-04

**Stage 1H Planner decision:** REQUEST_CHANGES.  
**Next Executor prompt:** `planner/GLEPPO_R26_STAGE1I_EXECUTOR_PROMPT.md`.  
**Full review:** `research/R26_STAGE1H_PLANNER_REVIEW.md`.

Accepted:
- 42 unique formal Findings R12–R53;
- 26 VERIFIED_FIXED / 14 PARTIALLY_FIXED / 1 OPEN / 1 UNVERIFIABLE;
- 39/39 exact declaration tuples;
- 218 declared test functions;
- R19 PARTIALLY_FIXED;
- 450/450 remains not independently reproduced.

Still blocking:
- no exact assertion/call-path/intended-branch/acceptance-coverage semantic map;
- R53 is mapped to an unrelated seed-schema test; status-consistency is indirect only;
- R39 needs R16/R20 instrumented cross-genotype evidence;
- R18 manual evidence needs exact units/token/production-cost caveats;
- helper does not validate the 42-row map;
- durable cumulative records need the Stage 1I semantic evidence before they can be finalized.

## 14. ECOS scientific-integrity correction

See `research/R26_ECOS_SCIENTIFIC_INTEGRITY_REVIEW.md`.

R21-C1 compares C0 LLM arithmetic execution with C4 DAC deterministic answer computation. It is not an operator/controller comparison. It does not establish that operator choice matters or that fixed-operator evolution is inadequate. Fixed-vs-adaptive, PPO-vs-rule, and PPO-vs-identical-state contextual Bandit remain UNTESTED.

The current controller specifications also disagree:
- Phase 1 design: 32-D state, generation-level reward, γ=0.95, sequential evolution episode, broad baseline suite;
- R24 preregistration: immediate child-parent effective_success reward, γ=0.99, 4/4/4 task split, 1,000-episode budget;
- PC1 R4 proposal and shared implementation: generation_reward and γ=0.95; R4 is PROPOSED / NOT APPROVED.

Do not silently select or amend a protocol in Stage 1I. After Stage 1I acceptance, conduct a separate `R26_ECOS_PROTOCOL_RECONCILIATION` before any PC1 approval or training request.

Current gates remain: PC1 BLOCKED; Formal G3 FAIL; Family C NOT ACCESSED; registered PC1 NOT EXECUTED; controller training NOT AUTHORIZED / NOT STARTED; model/API calls 0.

---

## 15. Stage 1I Planner independent review — REQUEST_CHANGES (2026-11-04)

**Reviewed Stage 1I Executor HEAD:** a1e6e65e671c876d028492bfed164205c54df08b  
**Planner review:** research/R26_STAGE1I_PLANNER_REVIEW.md  
**Next Executor prompt:** planner/GLEPPO_R26_STAGE1I_CORRECTIVE_EXECUTOR_PROMPT.md  
**Decision:** Stage 1I NOT ACCEPTED; Stage 1I-R1 corrective work required.

### Accepted improvements

- R53 now points to test_mutation_status_not_checked_by_consistency and is labeled indirect; no direct status-only hash-invariance test exists.
- R39 cites relevant cross-genotype evaluator evidence, but the R20 reference is missing from the test-evidence artifact and action-varying collector integration is not demonstrated.
- R18 manual cost notes better distinguish stub wall-clock, planned slots, actual uncached replica executions and unmeasured production tokens.
- R21-C1 correctly identified as DAC, not operator comparison.
- PPO advantage over rule-based/LinUCB remains unproven.
- 450/450 remains Executor-reported, not independently reproduced.

### Blocking findings

1. research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md is absent; the 73-line final audit and 34-line test-evidence note do not provide 42 row-level semantic records.
2. The 26/14/1/1 counts cannot be independently verified without the 42 rows.
3. scripts/_r26i_validator.py main path does not read a map or invoke validate_report_map(); the helper has file/class/function and cardinality validation gaps.
4. R39 needs precise separation of genotype-invariance test evidence, structural action exclusion, and untested action-varying PC1 integration.
5. R18 needs a row-level MANUAL entry and COST_BASELINE.md line 44 token reference.
6. latest_plan, handoff, next-session prompt and cumulative records were not updated in the Executor commit; status.json lost important scope/gate/provenance fields.
7. Final report does not record exact final Stage 1I SHA as the final report HEAD; it records the pre-work parent as CURRENT_BRANCH_HEAD.
8. GitHub has zero check runs and zero commit status entries for the exact Stage 1I SHA.

### Stage 1I-R1 required deliverables

- Canonical JSON map plus Markdown rendering with exactly 42 rows R12–R53.
- Full original acceptance criteria, exact assertions, source call paths, branch reachability, proven/indirect/uncovered conditions, evidence type and row-level disposition.
- AST-based validator that reads the JSON map and checks exact IDs, row count, file/class/function ownership, line numbers, NONE semantics and mapping counts.
- Positive and adversarial negative validator self-tests with raw output/exit codes.
- R53 remains PARTIALLY_FIXED without direct hash-invariance evidence.
- R39 scope clarified with R16 and R20 tests plus source path and limitations.
- R18 MANUAL evidence completed with all exact unit/token references.
- Corrected provenance and updated status/latest_plan/handoff/next-session records.

The previous 26/14/1/1 disposition count is not a target. Recompute it from the canonical JSON rows.

### Current gates

PC1 BLOCKED; R4 PROPOSED / NOT APPROVED; Formal G3 FAIL; Family C NOT ACCESSED; registered PC1 NOT EXECUTED; controller training NOT AUTHORIZED / NOT STARTED; no model/API calls or production runtime. No main update or cross-project reuse.

**Next:** Stage 1I-R1 Executor submission → Planner independent review. Do not proceed to protocol reconciliation or PC1.


---

## Stage 1I-R1 Status Update (2026-11-04)

**Stage 1I:** REQUEST_CHANGES (Planner decision)
**Stage 1I-R1:** executor corrective work complete, awaiting Planner independent review

### Deliverables completed
- research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json (42 rows, schema 1.0)
- research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md (1520 lines)
- research/R26_STAGE1I_R1_CORRECTIVE_REPORT.md
- scripts/_r26i_validator.py (AST-based, 15 self-tests PASS)
- Updated: R26_STAGE1I_FINAL_FINDING_AUDIT.md, R26_STAGE1I_TEST_EVIDENCE.md, status.json, latest_plan, handoff, next-session prompt

### Disposition arithmetic (from JSON)
26 VERIFIED_FIXED + 14 PARTIALLY_FIXED + 1 OPEN + 1 UNVERIFIABLE = 42

### R39/R53/R18 corrections
- R53: PARTIALLY_FIXED, INDIRECT evidence only (test_mutation_status_not_checked_by_consistency line 118)
- R39: evidence boundaries documented (direct CRN + R16/R20 cross-refs + structural; tautological test excluded)
- R18: MANUAL, 13 complete references including COST_BASELINE.md line 44

### Current gates (unchanged)
PC1 BLOCKED; R4 PROPOSED / NOT APPROVED; Formal G3 FAIL; Family C NOT ACCESSED; registered PC1 NOT EXECUTED; controller training NOT AUTHORIZED / NOT STARTED; model/API calls 0 (Executor-reported); production runtime 0 (Executor-reported); 450/450 EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED.

**Next gate:** Planner independent review of Stage 1I-R1. Do not proceed to protocol reconciliation or PC1.

---

## 16. Stage 1I-R1 Planner review — REQUEST_CHANGES (2026-11-04)

**R1 final HEAD:** 4d2ff06ee01146533501589b264d33ddd30ffcbe  
**R1 parent:** 539f74d5c898abc144992fff4a413a30744c1cc9  
**R1 source snapshot:** 29325cfa16441154c833f381f208747b57627a79  
**Planner review:** research/R26_STAGE1I_R1_PLANNER_REVIEW.md  
**R2 prompt:** planner/GLEPPO_R26_STAGE1I_R2_CORRECTIVE_EXECUTOR_PROMPT.md  
**Decision:** Stage 1I-R1 NOT ACCEPTED.

### Accepted

- 42 unique JSON IDs R12–R53.
- 42 unique Markdown headings.
- Markdown/JSON disposition consistency.
- 26/14/1/1 arithmetic mechanically correct.
- R53 PARTIALLY_FIXED and R18 MANUAL classifications retained.
- No production source or tests/ changes in R1 commit.
- Main unchanged.

### Blocking corrections

1. Relevant tests omitted from many rows, including R12 cache-hit tests, R14 r_hat test, R17 record-field test, R20 override/task/replicate tests, R23 round-trip replay, R39 six direct CRN tests and R20 cross-genotype test, R40 mutation tests, and R41 tamper/defensive-copy tests.
2. False call paths: R28 constant-only test described as reconcile; R30/R37 early guards attributed to validate_records; R44 isolated loader test described as registered analysis binding; R47 test does not reach plan ID/version checks; R50 direct art.verify test described as ApprovalGate.check.
3. Wrong/nonexistent source symbols: R17 build_evidence/save_evidence; R23 build_evidence/replay_evidence; R25 GatedPC1Runner; R48/R52 validate_reward_schema. R20 crn_seed file path is wrong.
4. Twelve source symbol entries have null line ranges; validator does not check source_symbols.
5. Validator wrong_file_path test duplicates missing-file test. Null declaration line numbers can pass. Nested schema types and source ranges are not validated.
6. Several VERIFIED_FIXED rows overclaim evidence, including R12, R17, R26, R28, R40, R44 and R51.
7. R45 mentions _DuplicateKeyChecker but has NONE evidence type and no manual source citation.

The 26/14/1/1 count is not a target. Re-evaluate all 42 rows.

### R2 deliverables

- corrected 42-row JSON map and synchronized Markdown;
- all relevant tests per multi-part Finding;
- exact source symbols/files/ranges, no null source ranges;
- truthful test-to-source call paths and branch reachability;
- strict AST validator with typed schema and line/source-range validation;
- targeted self-tests including existing-file/wrong-owner, null declaration line and null source-symbol range;
- corrected provenance with exact R1 final SHA/source snapshot;
- updated report, status, latest plan and handoff.

### Gates remain

PC1 BLOCKED; R4 PROPOSED / NOT APPROVED; Formal G3 FAIL; Family C NOT ACCESSED; registered PC1 NOT EXECUTED; controller training NOT AUTHORIZED / NOT STARTED. 450/450 remains EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED. Model/API and production-runtime zero counters remain Executor attestations.

**Next:** Stage 1I-R2 Executor completion → Planner independent review. No protocol reconciliation or PC1.

