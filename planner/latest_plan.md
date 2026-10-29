# Planner Latest Plan — G3-DIAG-v2-R2 Tool-Path Repair

**Status:** R1 ACCEPTED AS DIAGNOSTIC STOP · R2 AUTHORIZED  
**Branch:** `c7-g3-diag-v2-r1-fastpath`  
**R1 commit:** `b8b70354433113bead0bbfa3560cda79f592d4f9`  
**Detailed R2 decision:** `planner/G3_DIAG_R2_TOOL_PATH_REPAIR.md`

## Decision

Accept R1 as a protocol-compliant diagnostic stop. The hard cap, per-generation ledger, and fail-closed tool-path verifier behaved correctly. No operator comparison occurred, so R1 is not evidence for or against `tool_subset_edit` or `crossover`.

## Immediate executor task

1. Fix `Interpreter._extract_strops_payload` in `gleppo/interpreter.py` (not the LLM module header). Parse quoted natural-language string transformations into valid `str_ops` commands; remove arithmetic-expression fallback and fail closed with `ValueError` when no valid transform is present.
2. Fix `_extract_calc_payload` to select the tool-directed expression `49-6` for B2-002 while retaining the correct expression for B2-001/B2-003.
3. Fix the experiment harness: the default genotype has only `calc,str_ops`, so it cannot satisfy B2-002's `py_sandbox -> calc` contract. Construct and freeze a task-compatible reference workflow for each B2 task; do not weaken the contracts or call it the unmodified default genotype.
4. Add focused regression tests, run them and the full offline suite. No real-model run before this passes.
5. Then run a fresh R2 baseline with a new run ID, hard cap **30 actual generations**, wall cap **300 seconds**. If any baseline tool path fails, stop before operator comparisons. If all pass, compare one `tool_subset_edit` child and one `crossover` child against paired references within the same cap.

## Frozen boundaries

- R1 raw/report/ledger/manifest remain immutable.
- R2 uses fresh `G3_DIAG_R2_*` artifacts.
- No Family C, no PC1, no controller training.
- Formal G3 remains FAIL until separately reviewed.
- A tool-path pass is a validity gate, not proof of performance improvement.

**Required handoff:** source diff, focused/full test logs and exit codes, then R2 raw traces, per-generation ledger, report, SHA-256 manifest and independent verification.
