# G3-DIAG-v2-R1 Fast Path — Executor Report

**Date:** 2026-10-29
**Branch:** `c7-g3-diag-v2-r1-fastpath`
**Base commit:** `7b0017fee427a49f3f9eb34532bc447f4c2bb7cd`
**Status:** STAGE A ACCEPTED → STAGE B PARTIAL (baseline tool-path failure)

## Decision Table

| Gate | Status | Evidence |
|------|--------|----------|
| Stage A: hard cap at generate boundary | ✅ PASS | 29 new tests, `test_generate_not_called_when_cap_exceeded` |
| Stage A: per-call ledger (unique IDs, deltas) | ✅ PASS | `test_ledger_rows_have_unique_call_ids`, `test_token_deltas_are_per_call` |
| Stage A: tool-path ordered gate | ✅ PASS | 13 tool-path tests reject missing/reordered/failed/wrong-output |
| Stage A: full offline suite | ✅ PASS | 375/375 tests |
| Stage B: revision match | ✅ PASS | `a09a35458c702b33eeacc393d103063234e8bc28` |
| Stage B: baseline B2-001 tool path | ❌ FAIL | `str_ops` output `25*3-11` ≠ `SUM` |
| Stage B: baseline B2-002 tool path | ❌ FAIL | `py_sandbox` absent; `calc` output `49` ≠ `43` |
| Stage B: baseline B2-003 tool path | ❌ FAIL | `str_ops` output `8*8-4` ≠ `HI` |
| Stage B: operator comparison | ⏸ NOT RUN | Per protocol: stop at baseline failure |
| Budget compliance | ✅ PASS | 6/30 generations, 14.9s/300s, ledger=counter, deltas=sum |
| Hard G3 status | FAIL (unchanged) | No formal G3 claim |
| PC1 / Family C / training | NOT EXECUTED | Compliant |

## Stage A — Offline Acceptance

### Code changes
1. **`gleppo/llm.py`**: `BudgetExceededError`, `_reserve_generation_slot()` raises BEFORE `model.generate`. Per-call ledger with monotonic `call_id`, per-call `input_tokens`/`output_tokens` deltas, `duration_s`, `status`, `error`, `seed_digest`, provenance fields. Separate counters: `evaluations`, `episodes`, `tool_invocations`. `get_generation_ledger()` returns immutable copy.
2. **`gleppo/tool_path.py`**: Ordered tool-path contracts. B2-001/002/003 validators enforce exact tool ORDER and frozen EXPECTED OUTPUTS. Missing, reordered, failed, wrong-output → FAIL.
3. **`gleppo/interpreter.py`**: `run()` accepts `provenance` dict; per-turn provenance passed to LLM ledger.
4. **`tests/test_r1_fastpath.py`**: 29 regression tests covering hard cap, unique IDs, token deltas, failed calls, ledger completeness, all tool-path rejection cases.

### Test results
```
python -m unittest discover -s tests
Ran 375 tests in 3.525s
OK
```
New: 29 tests. Existing: 346 tests (all preserved, no regressions).

### Stage A acceptance criteria
- ✅ Cap enforced at generation boundary (`test_generate_not_called_when_cap_exceeded`)
- ✅ Reported actual-call count == ledger row count == runtime counter
- ✅ Per-call token deltas sum to runtime total
- ✅ Tool-path validators reject missing, reordered, failed, wrong-output events

## Stage B — Bounded Diagnostic

### Run metadata
| Field | Value |
|-------|-------|
| Run ID | `20261029T033104Z_R1` |
| Protocol | `G3-DIAG-v2-R1` |
| Model revision (loaded) | `a09a35458c702b33eeacc393d103063234e8bc28` |
| Revision match | ✅ |
| Actual generations | 6 / 30 |
| Wall clock | 14.93s / 300s |
| Budget exhausted | No |
| Ledger counter match | ✅ |
| Token sum match | ✅ |

### Baseline tool-path validation results

**B2-001** — contract: `calc`→`64`, `str_ops`→`SUM`
- Actual: `calc`→`64` ✅, `str_ops`→`25*3-11` ❌
- Answer: `64-SUM` (correct by gold checker)
- **Failure:** `str_ops` receives raw task text instead of `upper|sum`

**B2-002** — contract: `py_sandbox`→`49`, `calc`→`43`
- Actual: `calc`→`49` ❌, `str_ops`→`14*3+7` ❌
- Answer: `49` (wrong)
- **Failure:** `py_sandbox` never invoked; workflow uses `calc`+`str_ops` (default genotype tools)

**B2-003** — contract: `calc`→`60`, `str_ops`→`HI`
- Actual: `calc`→`60` ✅, `str_ops`→`8*8-4` ❌
- Answer: `60-HI` (correct by gold checker)
- **Failure:** `str_ops` receives raw task text instead of `upper|hi`

### Root cause
`Interpreter._extract_strops_payload()` falls back to `_extract_expr_from_text()` which extracts arithmetic expressions from task input when no `upper|...` pattern is found. The default workflow passes raw task text as the `str_ops` payload, producing garbage output instead of string transforms.

### Protocol compliance
Per plan: "If the required tool path or output fails, STOP the run immediately and report which task/tool failed. Do not spend the remaining budget on operator comparisons."

✅ **Run correctly stopped.** Operator comparison not attempted. 24 of 30 budgeted generations remain unused.

## Budget Accounting (actual-generation interpretation)

| Metric | Value |
|--------|-------|
| Actual `model.generate` calls | 6 |
| Generation ledger rows | 6 |
| Runtime counter | 6 |
| Per-call output token delta sum | matches runtime `total_tokens` |
| Evaluations | 3 |
| Episodes | 3 |
| Tool invocations | 6 |
| Failures | 0 |

**v2 noncompliance note:** v2 reported 240 actual generations against a stated 60-request cap. Under actual-generation counting, v2 is budget-noncompliant. v2 artifacts preserved and not reinterpreted.

## Explicit Non-Claims

- Behavior difference ≠ performance improvement.
- Passing synthetic tests ≠ real-model evidence.
- This diagnostic does NOT make formal G3 pass.
- This plan does NOT authorize PC1 or controller training.
- Baseline tool-path failure is NOT evidence against operator correctness — it reflects payload extraction in the default workflow.

## Smallest Proposed Fix (for Planner review)

The `_extract_strops_payload` method should recognize natural-language string transforms:
- Pattern: `transform 'X' to uppercase` → `upper|X`
- Pattern: `make 'X' uppercase` → `upper|X`
- Pattern: `upper-case the token X` → `upper|X`

This is a payload extraction fix, not a tool implementation or protocol change.

## Evidence Artifacts

| Artifact | SHA-256 (first 16) |
|----------|-------------------|
| `research/G3_DIAG_R1_RAW.json` | `c56cca9d960975dc` |
| `research/G3_DIAG_R1_LEDGER.jsonl` | `a83292f8e4e4a7cb` |
| `tests/test_r1_fastpath.py` | (see manifest) |
| `gleppo/llm.py` | (see manifest) |
| `gleppo/tool_path.py` | (see manifest) |
| `gleppo/interpreter.py` | (see manifest) |
| `scripts/_run_g3_diag_r1.py` | (see manifest) |

Full SHA-256 manifest: `research/G3_DIAG_R1_MANIFEST.json`

## Next Gate

Submit to Planner for review of:
1. Whether the str_ops payload extraction fix should be authorized
2. Whether a corrected baseline re-run is warranted within a new budget
3. Whether the R1 stop-at-baseline-failure outcome is accepted as the diagnostic result
