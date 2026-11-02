# GLEPPO R19 — Execution-Trace Answer Selection (TGAB Assessment)

**Status:** `COMPLETE` (offline, 0 model calls)
**Decision:** **TGAB NOT APPLICABLE** — root cause is LLM computation error, not tool misselection

## 1. R18 Root Cause Finding

**DONE-23 is NOT a tool result.** It's an LLM computation error.

| Source | Value | Match? |
|--------|-------|--------|
| calc (19*2-5) | 33 | ❌ |
| str_ops ('done'→'DONE') | DONE | ✅ |
| Direct tool output | — | ❌ 23 not a tool result |
| LLM arithmetic | 23 | **YES — computation error** |

## 2. TGAB Assessment

| Question | Answer |
|----------|--------|
| Are answer errors from tool misselection? | **NO** |
| Are answer errors from LLM computation? | **YES** |
| Will answer source verification help? | **NO** |
| Is TGAB the right approach? | **NO** |

**TGAB addresses tool result misselection, NOT LLM computation errors.**

## 3. Alternative: Deterministic Answer Calculation

Instead of TGAB, implemented `answer_binding.py` with deterministic calculation from tool outputs:

| Pattern | Method | Example |
|---------|--------|---------|
| calc + str_ops | `{WORD}-{calc_result}` | DONE-33 |
| py_sandbox + calc | `{calc_result}` | 17 |
| single calc | `{calc_result}` | 44 |

**Key feature:** Bypasses LLM arithmetic entirely.

## 4. Regression Tests (15 tests)

- Tool output extraction
- Deterministic calculation patterns
- Answer source verification
- TGAB selection (deterministic wins over LLM)
- Gold independence
- Deterministic reproducibility

**All 15 PASS. Full suite: 451/451 PASS.**

## 5. Decision

| Criterion | Status |
|-----------|--------|
| Root cause identified | ✅ LLM computation error |
| TGAB applicable | ❌ Not for this root cause |
| Alternative implemented | ✅ Deterministic calculation |
| Offline tests pass | ✅ 15/15 |
| Full tests pass | ✅ 451/451 |
| Model calls | 0 |

**VERDICT: TGAB NOT APPLICABLE** — R18 root cause is LLM arithmetic error, not tool misselection. Implemented deterministic calculation as alternative.

## 6. Next Steps

1. **Test deterministic calculation** in real model experiment (R20)
2. **Compare C0 vs C4** (deterministic answer selection)
3. **Verify** deterministic calculation preserves tool path compliance

## 7. Boundary Compliance

R1-R18 data preserved | Family C not accessed | PC1 not executed | Controller not trained | Formal G3 FAIL | 0 model calls
