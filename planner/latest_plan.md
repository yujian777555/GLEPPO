# Planner Latest Plan — R2 Independent Review / R3 Performance-Validity Pilot

**Status:** R2 ACCEPTED WITH LIMITATIONS · R3 TASK/METRIC GATE NEXT  
**Branch:** `c7-g3-diag-v2-r1-fastpath`  
**R2 commit:** `d1a10a04f237f98bab32867fb8e8400788219458`  
**Independent review:** `research/G3_DIAG_R2_INDEPENDENT_REVIEW.md`

## R2 verdict

R2 is accepted as bounded diagnostic evidence. Raw/ledger audit confirms 30 unique monotonically increasing generation IDs, 771 output-token delta sum matching runtime total, paired reference/child seed digests, and 3/3 baseline tool paths passing.

However, `behavior_changed=3/3` is not operator effectiveness:
- `tool_subset_edit`: child path validity 0/3, answer correctness 1/3; parent correctness was 2/3.
- `crossover`: child path validity 3/3, answer correctness 0/3; parent correctness was 2/3.
- Baseline answer correctness is 2/3 because B2-002 follows the required path but returns `37` rather than gold `43`.

Formal G3 remains FAIL. Do not start PC1 or controller training.

## Immediate task — R3 protocol and validity gate

1. Preserve all R2/R1/v2 artifacts unchanged.
2. Update `status.json` so it no longer claims R2 has not run.
3. Keep B2-002 as a documented baseline failure. Create a new separately identified task B2-004 for a two-stage tool task; never overwrite B2-002 or put the gold answer in the task prompt.
4. Freeze a new R3 protocol, task JSONL, and SHA-256 manifest before any model calls.
5. Add offline tests that distinguish:
   - hard validity (required tool path + format compliance),
   - gold answer correctness,
   - behavior change (diagnostic only).
6. Baseline canary: B2-004, three predeclared distinct seeds. Proceed only if tool path passes 3/3 and answer correctness is at least 2/3. Otherwise stop and revise offline.
7. If canary passes, run the paired pilot on B2-001, B2-003 and B2-004 with at least three paired seeds per task, comparing the task-compatible reference, `tool_subset_edit`, and `crossover`. Hard cap: **100 actual model generations**, **300 seconds**. If the complete predeclared matrix cannot fit, stop and label INCONCLUSIVE.
8. Report answer correctness, hard-validity rate, path pass rate, paired correctness deltas, and format failures. A child with a failed required path is invalid even if its answer string matches gold.
9. Do not begin PC1, controller training, or Family C. Formal G3 remains FAIL pending a separate review of a complete, sufficiently replicated protocol.

**R3 acceptance is a pilot gate, not formal G3 authorization.**
