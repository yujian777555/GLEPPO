# R7 Protocol — C1 Format Constraint Paired Validation

**Status:** PROTOCOL FROZEN; no model calls until manifest written and preflight passes.
**Parent evidence:** R6 `20261029T064914Z_R6` (immutable).
**Model:** Qwen2.5-7B-Instruct, revision `a09a35458c702b33eeacc393d103063234e8bc28`.
**Hard caps:** 150 actual `model.generate` calls; 300 seconds wall clock.

## 1. Research Question

**Does adding ONLY an output format constraint to original crossover stably improve effective success rate on new tasks?**

## 2. Experiment Arms (2)

| Arm | Description | Difference |
|-----|-------------|------------|
| **C0** | Original `crossover` | Baseline |
| **C1** | Original `crossover` + format constraint ONLY | + format constraint |

**C1 format constraint (frozen):**
```
Your FINAL answer MUST start with 'Final answer: ' followed by ONLY the answer value.
Do NOT include tool outputs, reasoning, or any text before 'Final answer:'.
Do NOT include markdown, explanations, or text after the answer.
```

**Verified:** C0 and C1 differ ONLY in this format constraint. Tools, workflow, and strategy are identical.

## 3. Frozen Tasks (6 NEW tasks, B2-012 to B2-017)

| Task | Tools | Contract | Structure |
|------|-------|----------|-----------|
| B2-012 | calc, str_ops | calc→28, str_ops→DONE | Format-sensitive DONE-NUMBER |
| B2-013 | py_sandbox, calc | py_sandbox→35, calc→70 | Tool chain dependency |
| B2-014 | str_ops, calc | str_ops→OUTPUT, calc→31 | Reverse order + format |
| B2-015 | calc, str_ops, py_sandbox | calc→45, str_ops→VALUE, py_sandbox→50 | Three-tool sequential |
| B2-016 | calc, py_sandbox | calc→31, py_sandbox→22, calc→66 | Multiple intermediates |
| B2-017 | py_sandbox, str_ops | py_sandbox→41, str_ops→RESULT | Format with compound output |

**At least 4 tasks structurally distinct from R5/R6** ✅

## 4. Frozen Seeds (3 per task)

```
r7-paired-seed-001
r7-paired-seed-002
r7-paired-seed-003
```

## 5. Budget Matrix

6 tasks × 3 seeds × 2 arms = 36 units.
Each unit: 1 parent + 1 child = 2 evaluations.
Each evaluation ≈ 2 generations.
Estimated: 36 × 2 × 2 = 144 generations.

**HARD CAP: 150 generations.** Sufficient.

## 6. Metrics

Primary: `effective_success`
Secondary: `answer_correct`, `format_compliant`, `tool_path_valid`, `hard_validity`

## 7. Decision Criteria

| Outcome | Condition |
|---------|-----------|
| **GO** | C1 > C0 effective_success, improvement not single-task, format improvement reproduced, no new violations |
| **NO-GO** | C1 fails to improve, or format gain offset by correctness drop, or unacceptable violations |
| **INCONCLUSIVE** | Budget exhausted, task-sensitive results, or insufficient paired evidence |

## 8. Boundaries

R1-R6 data preserved | Formal G3 FAIL | PC1/training/Family C NOT AUTHORIZED
