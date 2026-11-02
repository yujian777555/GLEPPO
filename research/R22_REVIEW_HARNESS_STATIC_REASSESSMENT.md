# R22 Review Harness — Static Reassessment

**Reviewed commit:** `ff34219185d1b0f5e07afb31e08b4060b365c1ca`  
**Branch:** `c7-g3-diag-v2-r1-fastpath`  
**Date:** 2026-11-02  
**Review type:** Static source inspection of the R22 review/gate scripts and status artifacts.  
**Important scope limit:** This note does not claim to have re-executed the R21 run, recomputed file SHA-256 values from repository bytes, or performed a full dynamic DAC taint audit.

## Decision

**R22's claim that R21-C1 received a complete independent review is PROVISIONAL and is not accepted as a fully evidenced independent review yet.**

This does not invalidate the R21-C1 raw result by itself. The raw report records C0=9/24, C4=24/24 and the paired counts; the issue is that the committed R22 review harness does not establish all of the audit claims it prints as PASS.

## Findings in `scripts/_r22_review.py`

1. **C4 outcome semantics are not independently established.** Lines 36 and 41–43 count `c4_result.source_valid` as if it were the C4 effective-success outcome. The script does not prove that `source_valid` is semantically equivalent to the complete registered `effective_success` definition, including answer, format, tool-path and hard-validity requirements. The next review must inspect the C4 evaluator path and define the exact outcome from the frozen protocol.

2. **Manifest verification is print-only.** Lines 63–69 calculate local SHA-256 values and print truncated prefixes. They are not compared with the expected `raw_sha256`, `ledger_sha256`, and `frozen_manifest_sha256` in `R21_RESULT_MANIFEST.json`; the source-file hashes and byte sizes in `R21_FROZEN_MANIFEST.json` are also not checked against the actual source files. A missing file is printed as MISSING but does not cause a failing exit.

3. **Coverage checks are incomplete.** The script checks whether the two task-name lists are disjoint, but does not assert exact expected task membership, exactly 3 seeds per task, unique unit keys, complete 24-unit coverage, per-unit DEV/CONFIRM assignment, or consistency between group aggregates and unit-level records.

4. **The DAC leakage check is a narrow string scan.** Lines 76–87 inspect only `gleppo/answer_binding.py`, search for a few literal substrings, and scan a short list of quoted number strings. This does not inspect the transitive runtime dependency path, imported helpers, task-contract construction, prompt/tool inputs, evaluator boundary, or runtime data flow. It does not provide perturbation tests proving that DAC consumes actual tool outputs and is invariant to gold/checker changes.

5. **The final PASS verdict is unconditional.** Lines 90–94 print PASS labels after the calculations without asserting that the computed values match registered expectations. The script can print a PASS verdict even when earlier printed checks are false or files are missing.

6. **The R22 gate script is not an authoritative gate evaluator.** `scripts/_r22_gates.py` prints `R21-C1 Independent Review: PASS` and hardcodes the formal G3 status and blocker descriptions. Meanwhile, the same commit's `status.json` says `training_readiness.r21_c1_independent_review = PENDING_ON_CURRENT_COMMIT`. These artifacts contradict each other.

7. **No full independent-review report is committed in R22.** `research/R22_STATUS.md` is a status summary; it does not provide a finding-by-finding review record, source evidence, independent recomputation procedure, or reviewer limitations.

## What remains supported by the available artifacts

- The R21-C1 raw JSON contains 24 unit records and records the 8 DEV/CONFIRM tasks.
- Its reported aggregate values are C0=9/24 and C4 source-valid=24/24.
- The reported paired pattern is 15 C4-only wins, 0 C0-only wins and 9 both-success cases.
- For 15 discordant pairs in one direction, the two-sided exact McNemar value is (2/2^{15}=0.00006103515625), conditional on the paired classification being correct.

These are reported/raw-artifact observations, not a substitute for full hash verification, outcome-semantic validation, and a complete independent audit.

## Required correction in R23

- Treat R22's full independent-review PASS as **not yet established**.
- Preserve every R21/R22 raw artifact unchanged.
- Build a fail-closed verifier with actual hash comparisons and exact coverage assertions.
- Independently derive C4 effective success from the registered execution/evaluator semantics, not by assuming `source_valid` is sufficient.
- Perform AST/dependency/data-flow review plus metamorphic tests for DAC gold isolation.
- Produce a complete `R21_C1_INDEPENDENT_REVIEW_R23.md` report.
- Add tamper tests proving the verifier exits non-zero for changed hashes, missing/duplicate units, ledger mismatches, altered outcomes, and gold-leakage fixtures.
- Only after that review may PC1 blocker re-audit proceed to independent review and authorization.

## Gate state

PC1 remains `PROPOSED_NOT_APPROVED`; formal G3 remains `FAIL`; PC1 has not run; controller training has not started; Family C remains forbidden. No authorization is granted by this static reassessment.
