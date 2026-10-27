# Production G3 Diagnostic Report

**Date:** 2026-10-27  
**Baseline:** `7dcac24`  
**Model:** Qwen2.5-7B-Instruct rev=a09a35458c702b33eeacc393d103063234e8bc28  
**GPU:** A800 80GB on 10.10.24.107:30939

## Engineering Validation (R62-R64)

| Check | Result |
|---|---|
| R62 behavior measurement | ✅ trace saved; prompt_sig excluded from comparison |
| R63 tool call chain | ✅ calc/str_ops now execute correctly |
| R64 stable seeds | ✅ SHA256-based; not Python hash() |
| Tool registry validation | ✅ invalid tool names rejected |
| Payload extraction | ✅ arithmetic extracted from LLM output |

## Canary Results (Family A/B)

| Task | Success | Failure | Tool Chain | Model Output |
|---|---|---|---|---|
| A-canary (A) | ❌ | wrong_answer | ✅ calc+str_ops OK | Natural language |
| B-canary (B) | ❌ | wrong_answer | ✅ calc+str_ops OK | Natural language |

**Key finding:** Tool chain now works correctly. Failure shifted from `tool_error` to `wrong_answer`. The model produces natural language answers that don't match the gold checker's expected format ("Final answer: <number>").

## Four-Level Assessment

| Level | Status | Evidence |
|---|---|---|
| **ENGINEERING_VALIDATION** | ✅ PASS | Tools execute; model receives input; seeds stable |
| **TASK_SOLVING_VALIDATION** | ❌ FAIL | Model produces natural language, not formatted answers |
| **GENOTYPE_CAUSALITY_VALIDATION** | Not tested | Requires working task solving first |
| **G3_GATE** | Cannot assess | Depends on above |

## Diagnosis

The G3 FAIL in the previous round was **partially caused by tool chain defects** (R63), not solely by model insensitivity. After fixing the tool chain:

1. Tools now execute correctly (calc produces valid results)
2. Model produces coherent natural language responses
3. But model doesn't follow the expected "Final answer: <number>" format

**This is a prompt engineering / output format issue, not a fundamental model capability limitation.**

## Recommendations

1. **Improve system prompt** to enforce answer format ("Final answer: <number>")
2. **Or modify gold checker** to extract numbers from natural language responses
3. **Re-run G3** after format fix to test genotype causality
4. **Do not conclude** that "real model is not sensitive to genotype edits" until format issue is resolved

## Raw Evidence

- `research/PRODUCTION_G3_DIAGNOSTIC_RAW.json`
- Previous round: `research/PRODUCTION_SMOKE_RAW.json`, `research/PRODUCTION_G3_RAW.json`
