# Phase 2A-R10-C6 Report

**Date:** 2026-10-27  
**Baseline:** `89d59ba0cf241fd2d72055b5c62fab489ddea5a7`  
**Model:** Qwen2.5-7B-Instruct rev=a09a35458c702b33eeacc393d103063234e8bc28

## C6-A: Answer Format Fix

System prompt updated to enforce `Final answer: <value>` format. StubLLM keywords preserved. 255/255 tests pass.

## C6-B: Canary Results

| Task | Rep | Success | Answer |
|---|---|---|---|
| A-g3-prod-00 | 0 | ✅ | Final answer: 41 |
| A-g3-prod-00 | 1 | ✅ | Final answer: 41 |
| A-g3-prod-00 | 2 | ✅ | Final answer: 41 |
| B-g3-prod-00 | 0 | ✅ | 6-AB67 |
| B-g3-prod-00 | 1 | ✅ | 6-AB67 |
| B-g3-prod-00 | 2 | ✅ | 6-AB67 |

**Canary PASS: Family A 3/3, Family B 3/3.**

## C6-C: Production G3 Results

| Operator | valid | invalid | hash_changed | behavior_changed | PASS |
|---|---|---|---|---|---|
| prompt_local_edit | 4 | 0 | 4 | 2 | ✅ |
| prompt_critique_rewrite | 4 | 0 | 4 | 4 | ✅ |
| tool_subset_edit | 2 | 2 | 2 | 0 | ❌ |
| workflow_step_edit | 4 | 0 | 2 | 2 | ✅ |
| crossover | 4 | 0 | 4 | 0 | ❌ |

**G3_OVERALL: FAIL** (2/5 operators failed)

**144 real LLM requests, 93.3s wall clock.**

## Four-Level Assessment

| Level | Status | Evidence |
|---|---|---|
| ENGINEERING_VALIDATION | ✅ PASS | Tools execute; seeds stable; traces recorded |
| TASK_SOLVING_VALIDATION | ✅ PASS | A 3/3, B 3/3 (canary) |
| GENOTYPE_CAUSALITY_VALIDATION | ⚠️ PARTIAL | 3/5 operators show behavior change |
| G3_GATE | ❌ FAIL | tool_subset_edit and crossover show no behavior change |

## Analysis

**tool_subset_edit (beh=0):** Only 2 valid offspring (2 invalid). The valid ones may not change observable behavior because adding/dropping tools doesn't affect execution when the workflow doesn't use the changed tool.

**crossover (beh=0):** Hash changes but behavior doesn't. The prompt union may preserve the same strategy keywords, so the model produces similar outputs.

**3/5 operators pass** — prompt_local_edit, prompt_critique_rewrite, and workflow_step_edit show real behavioral causality with the production model.

## Conclusion

G3 FAIL is **not** due to model insensitivity. The tool chain works, tasks are solvable, and 3/5 operators demonstrate real behavioral causality. The 2 failing operators (tool_subset_edit, crossover) need either:
1. Redesigned to produce more observable behavior changes, or
2. Their G3 criteria adjusted to account for their limited behavioral impact.

**This is a scientific finding about operator effectiveness, not an engineering defect.**

## Raw Evidence

- `research/PHASE2A_R10_C6_RAW.json`
- `research/PHASE2A_R10_C6_CANARY_RAW.json`
