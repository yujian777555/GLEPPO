# R6 Protocol — crossover_fixed Generalization + Mechanism Ablation

**Status:** PROTOCOL FROZEN; no model calls until manifest written and preflight passes.
**Parent evidence:** R5 `20261029T063026Z_R5` (immutable).
**Model:** Qwen2.5-7B-Instruct, revision `a09a35458c702b33eeacc393d103063234e8bc28`.
**Hard caps:** 150 actual `model.generate` calls; 300 seconds wall clock.

## 1. Research Questions

- **H1:** `crossover_fixed` outperforms original `crossover` on NEW tasks (not in R5).
- **H2:** Explicit output format constraint reduces format failures and improves effective success.
- **H3:** Improvement is not due to task difficulty, parent quality, or seed differences.
- **H4:** crossover_fixed does not sacrifice tool_path compliance for answer correctness.

## 2. Experiment Arms (4)

| Arm | Description | Tests |
|-----|-------------|-------|
| **P0** | Reference parent (task-compatible genotype) | Baseline |
| **C0** | Original `crossover` | Original behavior |
| **C1** | Original `crossover` + format constraint ONLY | H2 ablation |
| **C2** | `crossover_fixed` (strategy + format + workflow) | Full fix |

**C1 construction:** Take `op_crossover` output, append ONLY the format constraint sentence to system_prompt. No other changes.

## 3. Frozen Tasks (5 NEW tasks, structurally distinct from R5)

| Task | Tools | Contract | Structure |
|------|-------|----------|-----------|
| B2-007 | calc, py_sandbox | calc→39, py_sandbox→47 | Intermediate≠final, order sensitivity |
| B2-008 | calc, str_ops | calc→70, str_ops→RESULT | Format-sensitive RESULT-NUMBER |
| B2-009 | str_ops, calc, py_sandbox | str_ops→BASE, calc→54, py_sandbox→61 | Three-tool reversed order |
| B2-010 | calc, py_sandbox | calc→58, py_sandbox→52 | Multiple same-tool calls |
| B2-011 | py_sandbox, str_ops | py_sandbox→59, str_ops→ANSWER | Tool-chain format dependency |

**All 5 tasks are NEW** — not used in R1-R5 rule development.

## 4. Frozen Seeds (5 pre-declared paired seeds)

```
r6-paired-seed-001
r6-paired-seed-002
r6-paired-seed-003
r6-paired-seed-004
r6-paired-seed-005
```

## 5. Budget Matrix

5 tasks × 5 seeds × 4 arms = 100 units.
Each unit: 1 parent + 1 child = 2 evaluations.
Each evaluation ≈ 2 generations (LLM + tool + finalize).
Estimated: 100 × 2 × 2 = 400 generations.

**HARD CAP: 150 generations.** This is INSUFFICIENT for the full matrix.

**Revised budget plan:**
- Priority 1: C0 vs C2 on all 5 tasks × 5 seeds (50 units, ~200 generations) — TOO MANY
- **Revised: 5 tasks × 3 seeds × 3 arms (C0, C1, C2) = 45 units, ~180 generations** — STILL TOO MANY
- **Final: 5 tasks × 3 seeds × 2 arms (C0, C2) + 5 tasks × 1 seed × 1 arm (C1) = 35 units, ~140 generations**

**R6 Revised Matrix:**
- C0: 5 tasks × 3 seeds = 15 units (30 evaluations)
- C2: 5 tasks × 3 seeds = 15 units (30 evaluations)
- C1: 5 tasks × 1 seed = 5 units (10 evaluations)
- Total: 35 units = 70 evaluations ≈ 140 generations

## 6. Metrics

Per task × seed × arm:
- `answer_correct`, `format_compliant`, `tool_path_valid`, `hard_validity`, `effective_success`
- `behavior_changed` (diagnostic only)

Primary endpoint: paired change in `effective_success` (C2 − C0).

## 7. Statistical Analysis

- McNemar exact test for paired binary outcomes
- Wilson 95% CI for proportions
- Task clustering accounted (5 tasks, not 35 independent units)

## 8. Decision Criteria

| Outcome | Condition |
|---------|-----------|
| **Support H1** | C2 > C0 on new tasks, reproducible, no constraint violations |
| **Support H2** | C1 reduces format failures vs C0, consistent with effective success |
| **Falsify H1** | No improvement on new tasks, or new systematic degradation |
| **Inconclusive** | Statistical uncertainty, incomplete budget, or task coverage gap |

## 9. Stop Rules

1. Predicted calls > 150 → STOP, `INCONCLUSIVE`
2. Wall clock > 300s → STOP, `INCONCLUSIVE`
3. Ledger ≠ runtime count → STOP, `ERROR`
4. Manifest hash mismatch → STOP, `ERROR`

## 10. Boundaries

- R1-R5 data preserved
- Formal G3 remains FAIL
- PC1, controller training, Family C: NOT AUTHORIZED
