# G3 Causality Diagnostic Report

**Date:** 2026-10-27  
**Run ID:** 20261028T090752Z  
**Model:** Qwen2.5-7B-Instruct rev=a09a35458c702b33eeacc393d103063234e8bc28  
**Branch:** `c7-g3-diagnostic-run`

## Canary Result: **PASS**

| Task | Rep 0 | Rep 1 | Rep 2 | Score |
|---|---|---|---|---|
| A-g3-prod-00 | ✅ | ✅ | ✅ | **3/3** |
| B-g3-prod-00 | ✅ | ✅ | ✅ | **3/3** |

6 requests, 2.9s wall, 0 failures.

## G3 Result: **FAIL** (3/5 operators pass)

| Operator | valid | invalid | hash_changed | behavior_changed | threshold | PASS |
|---|---|---|---|---|---|---|
| prompt_local_edit | 4 | 0 | 4 | **2** | 2 | ✅ |
| prompt_critique_rewrite | 4 | 0 | 4 | **4** | 2 | ✅ |
| tool_subset_edit | 2 | 2 | 2 | **0** | 1 | ❌ |
| workflow_step_edit | 4 | 0 | 2 | **2** | 2 | ✅ |
| crossover | 4 | 0 | 4 | **0** | 2 | ❌ |

**Total: 144 requests, 91.4s wall, 0 failures, budget not exhausted.**

## Analysis

**Passing operators (3/5):** prompt_local_edit, prompt_critique_rewrite, workflow_step_edit — all show real behavioral causality with the production model.

**Failing operators (2/5):**
- `tool_subset_edit`: only 2 valid offspring (2 invalid). Valid ones show no behavior change — adding/dropping tools doesn't affect execution when the workflow doesn't use the changed tool.
- `crossover`: hash changes but behavior doesn't. Prompt union preserves the same strategy keywords, so model produces similar outputs.

## Four-Level Assessment

| Level | Status |
|---|---|
| ENGINEERING_VALIDATION | ✅ PASS (tool chain, seeds, evidence) |
| TASK_SOLVING_VALIDATION | ✅ PASS (canary 6/6) |
| GENOTYPE_CAUSALITY_VALIDATION | ⚠️ PARTIAL (3/5 operators) |
| G3_GATE | ❌ FAIL |

## Evidence

- `research/CANARY_20261028T090653Z.json` (sha256=3df367b7606ec42b)
- `research/G3_DIAGNOSTIC_20261028T090752Z.json` (sha256=80e8e3a7a042880b)

## Budget & Safety
- Real model calls: 150 (6 canary + 144 G3)
- Tokens: 90 (canary) + ~10K (G3)
- Wall clock: 2.9s + 91.4s
- API costs: $0 (local model)
- PC1: NOT executed
- Family C: NOT accessed

## Conclusion

**G3 FAIL is a genuine scientific finding about operator effectiveness, not an engineering defect.** The tool chain works, tasks are solvable, and 3/5 operators demonstrate real behavioral causality. tool_subset_edit and crossover need redesign to produce observable behavior changes.
