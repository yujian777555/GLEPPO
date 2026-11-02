# GLEPPO R21 — DAC Real Model Paired Verification

**Run ID:** `20261102T121502Z_R21`
**Status:** `COMPLETE` (24/24 units, 96/150 generations)
**Decision:** **NO-GO (implementation bug — contracts missing)**

## 1. R21 Results

| Group | C0 (LLM) | C4 (DAC) |
|-------|----------|----------|
| **DEV** | 5/12 (41.7%) | **0/12 (0%)** |
| **CONFIRM** | 4/12 (33.3%) | **0/12 (0%)** |
| **Total** | **9/24 (37.5%)** | **0/24 (0%)** |

**Paired: C0 wins=9, C4 wins=0, Both fail=15**

## 2. Root Cause: Missing TaskContracts

**All 24 C4 evaluations return `invalid_contract`** — B2-065 to B2-072 have NO TaskContract in `TASK_CONTRACTS`.

```
B2-065: method=llm_fallback abstain=invalid_contract
B2-066: method=llm_fallback abstain=invalid_contract
...
B2-072: method=llm_fallback abstain=invalid_contract
```

**This is an implementation bug, NOT evidence that DAC doesn't work.**

## 3. What Happened

1. R20 implemented DAC with contracts for B2-055, B2-061-064
2. R21 created new tasks B2-065-072
3. **Forgot to add TaskContracts for new tasks**
4. DAC returns `invalid_contract` for all new tasks
5. Falls back to `llm_fallback` which returns LLM answer (not deterministic)

## 4. Hypothesis Assessment

| Hypothesis | Verdict | Note |
|------------|---------|------|
| H1: DAC reduces arithmetic errors | **CANNOT TEST** | No contracts = no DAC |
| H2: DAC improves effective_success | **CANNOT TEST** | No contracts = no DAC |
| H3: DAC generalizes | **CANNOT TEST** | No contracts = no DAC |

**All hypotheses UNTESTABLE due to implementation bug.**

## 5. C0 Baseline (for reference)

| Task | C0 effective |
|------|-------------|
| B2-065 | 3/3 |
| B2-066 | 1/3 |
| B2-067 | 1/3 |
| B2-068 | 0/3 |
| B2-069 | 3/3 |
| B2-070 | 1/3 |
| B2-071 | 0/3 |
| B2-072 | 0/3 |

## 6. Decision

**NO-GO for R21** — implementation bug (missing TaskContracts) makes DAC untestable. Not a verdict on DAC mechanism.

## 7. Fix Required

Add TaskContracts for B2-065 to B2-072 before re-running:

```python
"B2-065": TaskContract(
    steps=[ComputationStep("result", "calc", "int")],
    output_format="{result}",
),
"B2-066": TaskContract(
    steps=[
        ComputationStep("num", "calc", "int"),
        ComputationStep("word", "str_ops", "upper"),
    ],
    output_format="{word}-{num}",
),
...
```

## 8. Boundary Compliance

R1-R20 data preserved | Family C not accessed | PC1 not executed | Controller not trained | Formal G3 FAIL

## 9. Artifacts

`research/runs/20261102T121502Z_R21/` — R21_RAW.json, R21_LEDGER.jsonl (96 rows)
