# R8 Protocol — Format Constraint on Format-Error-Prone Tasks

**Status:** PROTOCOL FROZEN; no model calls until manifest written and preflight passes.
**Parent evidence:** R7 `b4509c3` (immutable).
**Model:** Qwen2.5-7B-Instruct, revision `a09a35458c702b33eeacc393d103063234e8bc28`.
**Hard caps:** 150 actual `model.generate` calls; 300 seconds wall clock.

## 1. Research Question

**On tasks where format errors actually occur, does adding ONLY an output format constraint convert otherwise-invalid executions into effective successes?**

## 2. Experiment Arms (2)

| Arm | Description |
|-----|-------------|
| **C0** | Original `crossover` |
| **C1** | Same crossover child + format constraint ONLY |

**C1 format constraint (frozen):**
```
Do NOT include tool outputs before 'Final answer:'.
```

## 3. Task Groups

### Group A: Historical Format-Sensitive (R5 tasks)
| Task | Source | Format Risk |
|------|--------|-------------|
| B2-001 | R5 | HIGH (R5 showed 67% format failure) |
| B2-003 | R5 | HIGH (R5 showed 67% format failure) |

### Group B: New Confirmation Tasks
| Task | Tools | Structure |
|------|-------|-----------|
| B2-018 | calc, str_ops | Multi-step, explicit format FINAL-NUMBER |
| B2-019 | py_sandbox, calc | Tool output separation |
| B2-020 | calc, str_ops | Precise format OUTPUT-NUMBER |
| B2-021 | str_ops, calc, py_sandbox | Three-tool workflow dependency |

**At least 3 tasks structurally distinct from R5-R7** ✅

## 4. Seeds

- Group A: 2 seeds per task (historical replication)
- Group B: 3 seeds per task (confirmation)

## 5. Budget Matrix

| Group | Tasks | Seeds | Arms | Units |
|-------|-------|-------|------|-------|
| A | 2 | 2 | 2 | 8 |
| B | 4 | 3 | 2 | 24 |
| **Total** | **6** | | | **32** |

Each unit: 1 parent + 1 child = 2 evaluations.
Each evaluation ≈ 2 generations.
Estimated: 32 × 2 × 2 = 128 generations. **Within 150 cap.**

## 6. Decision Criteria

| Outcome | Condition |
|---------|-----------|
| **GO** | Meaningful positive trend on new tasks, not single-task driven, no new violations |
| **NO-GO** | No improvement, or correctness drop offsets format gain |
| **INCONCLUSIVE** | No format failures, insufficient tasks, single-task effect, or incomplete matrix |

## 7. Boundaries

R1-R7 data preserved | Formal G3 FAIL | PC1/training/Family C NOT AUTHORIZED
