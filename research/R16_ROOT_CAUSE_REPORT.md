# GLEPPO R16 — Validation Signal Root Cause & C2 Fix

**Status:** `COMPLETE` (offline, 0 model calls)
**Decision:** **GO for R17** (root cause found, fix validated offline)

## 1. B2-050 Root Cause: **C — Validation vs Final Context Differs**

| Step | Validation Phase | Final Phase |
|------|-----------------|-------------|
| Seed | `r15-val-seed-001` | `r15-final-seed-001/002/003` |
| Output | "Final answer: BASE-23" (compliant) | "Let's break down..." (no prefix) |
| Format | OK | FAILS |

**Same child, different seeds → different outputs.** Validation seed produces compliant output; final seeds produce verbose output without "Final answer:" prefix.

## 2. Historical Confusion Matrix (combined R12+R14+R15)

| Metric | Value | Denominator |
|--------|-------|-------------|
| TP | 4 | |
| FP | 8 | |
| FN | 2 | |
| TN | 13 | |
| **Precision** | **33.3%** | 4/12 |
| **Recall** | **66.7%** | 4/6 |
| **Specificity** | **61.9%** | 13/21 |
| **NPV** | **86.7%** | 13/15 |
| **Accuracy** | **63.0%** | 17/27 |

**R15 has FN=2 (B2-050 misses)** — validation says OK but final fails.

## 3. M0-M3 Signal Comparison

| Signal | Type | Catches FN=2? | FP Rate | Gold Needed? |
|--------|------|---------------|---------|--------------|
| M0 (existing) | Post-validation | ❌ No | High | No |
| M1 (deterministic) | Post-validation | ❌ No | High | No |
| **M2 (structural)** | **Pre-execution** | **✅ Yes** | High | **No** |
| M3 (combined) | Both | ✅ Yes | High | No |

**M2 recommendation:** Task has `str_ops` in `required_tools` → risky → intervene.

## 4. Regression Tests (18 tests)

- Format checker: missing prefix, empty answer, long answer, tool output, etc.
- Validation signal: TN/TP/FN/FP semantics
- Structural signal: B2-050 risky, B2-051 not risky
- Gold independence: checker doesn't read gold

**All 18 PASS. Full suite: 436/436 PASS.**

## 5. Decision

| Criterion | Status |
|-----------|--------|
| Root cause reproducible | ✅ C (seed variance) |
| Fix validated offline | ✅ M2 structural signal |
| Regression tests pass | ✅ 18/18 |
| Full tests pass | ✅ 436/436 |
| Independent tasks for R17 | ⚠️ Need new tasks |

**VERDICT: GO for R17** — Root cause found (seed variance), M2 structural signal catches B2-050-type misses. Ready for independent confirmation experiment.

## 6. R17 Prerequisites

1. New tasks NOT used in signal design
2. M2 structural signal frozen (str_ops → intervene)
3. Budget pre-check completed
4. Development/audit set boundary clear

## 7. Boundary Compliance

R1-R15 data preserved | Family C not accessed | PC1 not executed | Controller not trained | Formal G3 FAIL | 0 model calls
