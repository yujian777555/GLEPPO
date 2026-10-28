# G3 Independent Review — Real Model Causality Diagnostic

**Date:** 2026-10-27  
**Reviewer:** Independent (read-only)  
**Experiment commit:** `17ffc41` on `c7-g3-diagnostic-run`  
**Run ID:** 20261028T090752Z

## 1. Experiment Verification

| Item | Reported | Independently Verified | Status |
|---|---|---|---|
| Model revision | a09a35458c702b33eeacc393d103063234e8bc28 | ✅ matches RUNTIME_LOCK | OK |
| Total requests | 150 (6 canary + 144 G3) | 144 G3 requests recomputed = 36×2×2 | OK |
| behavior_changed | 2/4/0/2/0 | recomputed from diffs: match | OK |
| Budget exhausted | False | confirmed in raw JSON | OK |
| Wall clock | 91.4s | confirmed in raw JSON | OK |
| Evidence files | CANARY_*.json + G3_DIAGNOSTIC_*.json | both exist with SHA-256 | OK |

## 2. Recomputation Results

All five operators' `behavior_changed` counts **match** the raw evidence. The experiment is internally consistent.

## 3. Canary & Task Solving

**Canary: PASS (6/6).** Both Family A and B tasks solved correctly by the default genotype. Task solving is confirmed.

## 4. CRN & Behavior Change

- Paired seeds used for parent-child comparison (independent of genotype).
- Behavior change determined by **execution trace comparison** (not hash or prompt text).
- For failing operators: traces are **byte-identical** between parent and child.

## 5. Root Cause: tool_subset_edit

| Evidence | Finding |
|---|---|
| hash_changed | 2/2 (genotype changed) |
| behavior_changed | 0/2 |
| Trace comparison | **identical** (same answer, same tool calls) |

**Diagnosis: Category 3 + 4 (Execution path not affected + Task-operator mismatch)**

- The operator changes `tools` list and may add/remove workflow steps.
- But both tasks (A/B) are solved with the **same 2 tool calls** regardless of tool set.
- Adding `py_sandbox` doesn't change execution because the workflow's existing steps don't need it.
- The tasks don't exercise tool-dependent behavior differences.

## 6. Root Cause: crossover

| Evidence | Finding |
|---|---|
| hash_changed | 4/4 (genotype changed) |
| behavior_changed | 0/4 |
| Trace comparison | **identical** |

**Diagnosis: Category 3 + 4 (Execution path not affected + Task-operator mismatch)**

- Crossover produces different prompt text and metadata.
- But the **effective behavior configuration** (strategy keywords + tools + workflow) remains functionally equivalent.
- All genotypes solve the tasks identically (success=1.0, tools=2.0).
- The tasks are too easy to differentiate genotypes.

## 7. Experimental Validity Blockers

- **Task difficulty ceiling:** A-g3-prod-00 and B-g3-prod-00 are solved by ALL genotypes. They cannot discriminate operator effects.
- **Tool sensitivity:** Tasks don't require tools whose presence/absence changes behavior.
- **Strategy discrimination:** Tasks don't test whether prompt strategy differences matter.

## 8. Minimal Next Experiment

**Goal:** Create tasks that discriminate between genotypes.

| Modification | Hypothesis | Control | Metric | Support | Falsify | Budget |
|---|---|---|---|---|---|---|
| **Harder Family A/B tasks** | Current tasks are at difficulty ceiling | Same operators on harder tasks | behavior_changed rate | Rate > 0 for failing ops | Rate still 0 | 100 requests |
| **Tool-dependent tasks** | tool_subset_edit needs tasks that use tools | Task requiring py_sandbox | tool_calls differ | Different tool calls | Same tool calls | 50 requests |
| **Strategy-sensitive tasks** | crossover needs tasks testing prompt strategy | Task with strategy-dependent answers | answer differs | Different answers | Same answers | 50 requests |

**Priority:** #1 (harder tasks) — most likely to reveal all operator effects.

## 9. Review Conclusion

**ACCEPT WITH LIMITATIONS**

- The G3 experiment is **real, complete, and reproducible**.
- The G3 FAIL result is a **valid experimental finding** about the current task suite's ability to discriminate operators.
- The root cause is **task-operator mismatch** (category 4), not operator implementation defects.
- This does **not** mean G3 Gate passes or PC1 is approved.

**Next step:** Design harder Family A/B tasks that exercise tool-dependency and strategy-sensitivity, then re-run G3.
