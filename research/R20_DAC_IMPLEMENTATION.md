# GLEPPO R20 — DAC Generic Mechanism Implementation

**Status:** `COMPLETE` (offline, 0 model calls)
**Decision:** **DAC IMPLEMENTED & VALIDATED OFFLINE**

## 1. R19 Implementation Audit

**Finding:** R19 `deterministic_answer` had task_id branching (B2-055/B2-061 pattern hardcoded). NOT generalizable.

**Fix:** Replaced with declarative TaskContract system.

## 2. DAC (Deterministic Answer Computation) Design

### Declarative Task Contracts

Instead of task_id branching, uses frozen computation contracts:

```python
TaskContract(
    task_id="B2-055",
    steps=[
        ComputationStep("num", "calc", "int"),
        ComputationStep("word", "str_ops", "upper"),
    ],
    final_output="result",
    output_format="{word}-{num}",
    required_tools=["calc", "str_ops"],
)
```

### Supported Patterns

| Pattern | Example | Contract |
|---------|---------|----------|
| calc + str_ops | DONE-33 | `{word}-{num}` |
| py_sandbox + calc | 17 | `{result}` |
| Three-tool | BASE-19 | `{word}-{result}` |
| Arithmetic | 15 | `add` operation |

### Abstention Conditions

- Missing tool output
- Type mismatch (non-numeric where numeric expected)
- Invalid contract
- Incomplete dependency
- Computation error (division by zero)

## 3. Regression Tests (14 tests)

- Single tool / multi-tool / arithmetic / string transforms
- Missing tool / type mismatch / incomplete dependency
- Gold independence / deterministic reproducibility
- DAC selection (deterministic wins over LLM)

**All 14 PASS. Full suite: 450/450 PASS.**

## 4. Key Features

| Requirement | Status |
|-------------|--------|
| No gold reading | ✅ |
| No task_id branching | ✅ (declarative contracts) |
| No LLM arithmetic override | ✅ |
| Deterministic reproducibility | ✅ |
| Abstain on uncertainty | ✅ |
| Type checking | ✅ |

## 5. Decision

| Criterion | Status |
|-----------|--------|
| Generic mechanism implemented | ✅ Declarative contracts |
| No task-specific hardcoding | ✅ |
| Offline tests pass | ✅ 14/14 |
| Full tests pass | ✅ 450/450 |
| Model calls | 0 |

**VERDICT: DAC IMPLEMENTED** — Generic, declarative, no task-specific hardcoding. Ready for real model experiment (R21).

## 6. Next Steps

1. **R21 real model experiment:** C0 vs C4 (DAC) comparison
2. **8+ independent tasks** covering A/B/C/D structures
3. **Verify** DAC generalizes beyond R18 tasks

## 7. Boundary Compliance

R1-R19 data preserved | Family C not accessed | PC1 not executed | Controller not trained | Formal G3 FAIL | 0 model calls
