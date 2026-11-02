# R18 Root Cause Audit — Answer Source Analysis

**Date:** 2026-10-29
**Status:** COMPLETE (offline)

## 1. R18 B2-055/B2-061 Trace Analysis

### B2-055 (Expected: DONE-33)

| Arm | Seed | Answer | Correct? |
|-----|------|--------|----------|
| C0 | 001 | DONE-33 | ✅ |
| C0 | 002 | DONE-33 | ✅ |
| C0 | 003 | DONE-33 | ✅ |
| C3 | 001 | DONE-23 | ❌ |
| C3 | 002 | DONE-23 | ❌ |
| C3 | 003 | DONE-23 | ❌ |

### B2-061 (Expected: DONE-33)

Same pattern: C0=3/3 correct, C3=0/3 wrong (DONE-23).

## 2. Answer Source Analysis

**Expected:** `DONE-33` where 33 = 19*2-5 (calc), DONE = 'done' uppercase (str_ops)

**C3 output:** `DONE-23` where 23 = ???

### Where does 23 come from?

| Source | Value | Match? |
|--------|-------|--------|
| calc (19*2-5) | 33 | ❌ |
| str_ops ('done'→'DONE') | DONE | ✅ |
| Direct tool output | — | ❌ 23 not a tool result |
| LLM arithmetic | 23 | **YES — computation error** |

**Key finding: DONE-23 is NOT a direct tool result.** It's an LLM computation error.

## 3. Implications for TGAB

| Question | Answer |
|----------|--------|
| Are answer errors from tool misselection? | **NO** |
| Are answer errors from LLM computation? | **YES** |
| Will answer source verification help? | **NO** |
| Is TGAB the right approach? | **NO** |

## 4. Root Cause Summary

**C3 constraint causes LLM to produce wrong arithmetic (23 instead of 33).** This is NOT a tool result selection problem — it's an LLM reasoning problem.

TGAB (Execution-Trace-Grounded Answer Selection) addresses tool result misselection, NOT LLM computation errors. **TGAB is not applicable to this root cause.**

## 5. Alternative Approaches

Since the problem is LLM computation errors (not tool misselection):

1. **Post-hoc answer verification** — re-compute using tool outputs
2. **Deterministic calculation layer** — bypass LLM for arithmetic
3. **Simpler prompt** — less constraint = fewer errors (C0 works!)
4. **Answer extraction from tool outputs** — don't trust LLM arithmetic

## 6. Conclusion

R18 root cause is **LLM computation error under format constraint**, NOT tool result misselection. TGAB is not the right solution. Need different approach.
