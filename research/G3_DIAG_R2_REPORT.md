# G3-DIAG-v2-R2 Tool-Path Repair — Executor Report

**Date:** 2026-10-29
**Branch:** `c7-g3-diag-v2-r1-fastpath`
**R2 Run ID:** `20261029T040254Z_R2`
**Status:** BASELINE ALL PASS → OPERATOR COMPARISON COMPLETE

## Decision Table

| Gate | Status | Evidence |
|------|--------|----------|
| str_ops natural-language extraction | ✅ FIXED | 30 focused tests + full suite 405/405 |
| calc tool-directed expression (49-6) | ✅ FIXED | `test_b2_002_chooses_49_minus_6` |
| py_sandbox payload extraction | ✅ FIXED | Expression-only capture, no trailing text |
| Task-compatible reference workflows | ✅ CREATED | B2-001/002/003 exact tools + ordered steps |
| Baseline B2-001 tool path | ✅ PASS | calc→64, str_ops→SUM |
| Baseline B2-002 tool path | ✅ PASS | py_sandbox→49, calc→43 |
| Baseline B2-003 tool path | ✅ PASS | calc→60, str_ops→HI |
| tool_subset_edit behavior change | ✅ PASS | 3/3 tasks behavior_changed |
| crossover behavior change | ✅ PASS | 3/3 tasks behavior_changed |
| Budget compliance | ✅ PASS | 30/30 gens, 32.5s, ledger=counter |
| Formal G3 status | FAIL (unchanged) | No formal G3 claim |
| PC1 / Family C / training | NOT EXECUTED | Compliant |

## Defects Fixed

### Defect A — str_ops natural-language extraction
- **Before:** fell back to arithmetic expression extraction (silent wrong-tool success)
- **After:** parses quoted/unquoted natural language (`transform 'sum' to uppercase` → `upper|sum`), raises ValueError when no valid transform found
- Patterns supported: quoted words, unquoted words, "make X all capitals", "upper-case the token X", "X in upper case", "X upper-cased"

### Defect B — calc tool-directed expression
- **Before:** always extracted first arithmetic expression (B2-002 got `14*3+7` instead of `49-6`)
- **After:** prefers "use calc to compute 49-6" pattern, falls back to first expression

### Defect C — py_sandbox payload over-capture
- **Before:** `result = (.+)` captured trailing text → syntax error
- **After:** captures only the expression up to delimiter

### Task-compatible reference workflows
- B2-001: `calc`, `str_ops` — workflow: llm → calc → str_ops → finalize
- B2-002: `py_sandbox`, `calc` — workflow: llm → py_sandbox → calc → finalize
- B2-003: `calc`, `str_ops` — workflow: llm → calc → str_ops → finalize
- Labeled `task_compatible_reference`, NOT the unmodified default genotype

## Test Results

```
Focused R2 tests:  30/30 OK
Full offline:     405/405 OK
```

## R2 Real-Model Diagnostic

### Run Metadata
| Field | Value |
|-------|-------|
| Run ID | `20261029T040254Z_R2` |
| Model revision (loaded) | `a09a35458c702b33eeacc393d103063234e8bc28` |
| Revision match | ✅ |
| Actual generations | 30 / 30 |
| Wall clock | 32.5s / 300s |
| Budget exhausted | No (exact cap) |
| Ledger counter match | ✅ |
| Token sum match | ✅ |

### Baseline Tool-Path Validation

| Task | Contract | Result | Success |
|------|----------|--------|---------|
| B2-001 | calc→64, str_ops→SUM | ✅ PASS | 1.0 |
| B2-002 | py_sandbox→49, calc→43 | ✅ PASS | 0.0* |
| B2-003 | calc→60, str_ops→HI | ✅ PASS | 1.0 |

*B2-002 success=0.0 because the LLM answers "49" instead of "43" — tool path is correct, final answer is wrong. This is a task difficulty issue, not a tool-path issue.

### Operator Comparison

| Operator | valid | behavior_changed | threshold | PASS |
|----------|-------|------------------|-----------|------|
| tool_subset_edit | 3 | **3** | 1 | ✅ |
| crossover | 3 | **3** | 1 | ✅ |

All 3 B2 tasks show behavior change for both operators.

### Budget Accounting (actual-generation interpretation)

| Metric | Value |
|--------|-------|
| Actual `model.generate` calls | 30 |
| Generation ledger rows | 30 |
| Runtime counter | 30 |
| Per-call output token delta sum | matches runtime total |
| Evaluations | 15 |
| Tool invocations | 30+ |

## Explicit Non-Claims

- Behavior difference ≠ performance improvement
- Tool-path pass is a validity gate, not proof of performance
- This diagnostic does NOT make formal G3 pass
- PC1 / Family C / controller training NOT authorized

## Evidence Artifacts

| Artifact | SHA-256 (first 16) |
|----------|-------------------|
| `research/G3_DIAG_R2_RAW.json` | `2328fd2d1c0df7aa` |
| `research/G3_DIAG_R2_LEDGER.jsonl` | `88c2fce336073622` |
| `research/G3_DIAG_R2_MANIFEST.json` | (see file) |
| `tests/test_r2_tool_path.py` | (see manifest) |
| `gleppo/interpreter.py` | (see manifest) |
| `gleppo/genotype.py` | (see manifest) |

## Next Gate

Submit to Planner for review of R2 results. Key questions:
1. B2-002 tool path passes but task success=0.0 — is this acceptable as diagnostic evidence?
2. All operators show behavior change — sufficient to request formal G3 protocol revision?
3. Formal G3 status remains FAIL pending separate review.
