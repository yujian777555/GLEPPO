# R4 Protocol — Selection Mechanism Generalization

**Status:** PROTOCOL FROZEN; no model calls until manifest is written and preflight passes.
**Parent evidence:** R3 `20261029T052350Z_R3` (immutable).
**Model:** Qwen2.5-7B-Instruct, revision `a09a35458c702b33eeacc393d103063234e8bc28`.
**Hard caps:** 150 actual `model.generate` calls; 300 seconds wall clock.

## 1. Research Question

Can a selection mechanism that does NOT use gold answers or leak final execution results reduce harmful offspring and improve effective success rate on tasks not used in rule development?

Three distinguishable layers:
1. **Static structural checks** (pre-execution): can identify contract violations without running.
2. **Post-execution hard constraint checks**: can identify actual violations after running.
3. **Selection mechanism improving performance**: not implied by (1) or (2).

## 2. Frozen Tasks (5 tasks, structurally distinct)

| Task | Tools | Contract | Structure |
|------|-------|----------|-----------|
| B2-001 | calc, str_ops | calc→64, str_ops→SUM | Two-tool, string transform, SUM-STRING format |
| B2-003 | calc, str_ops | calc→60, str_ops→HI | Two-tool, string transform, NUMBER-STRING format |
| B2-004 | py_sandbox, calc | py_sandbox→32, calc→41 | Two-tool, numeric chain, intermediate≠final |
| B2-005 | calc, py_sandbox | calc→58, py_sandbox→71 | Two-tool, REVERSED order vs B2-004 |
| B2-006 | calc, str_ops, py_sandbox | calc→40, str_ops→FINAL, py_sandbox→42 | Three-tool, complex, format degradation risk |

**B2-005** tests tool-order sensitivity (calc first, then py_sandbox).
**B2-006** tests three-tool complexity and crossover format degradation.

## 3. Frozen Seeds (5 pre-declared paired seeds)

```
r4-paired-seed-001
r4-paired-seed-002
r4-paired-seed-003
r4-paired-seed-004
r4-paired-seed-005
```

Seed derivation: `protocol_id | task_id | seed_id`. Never includes genotype, operator, or hash.

## 4. Generation Strategies (3)

1. **Reference**: task-compatible reference genotype (per-task tools + ordered workflow).
2. **tool_subset_edit**: one child from reference.
3. **crossover**: one child from reference + mate.

## 5. Pre-Registered Selection Mechanisms

### S0: Unfiltered (baseline)
Accept all structurally valid offspring. No filtering.

### S1: Static pre-execution hard constraint filter
Uses ONLY pre-execution information:
- All tools exist in `ALLOWED_TOOLS` registry.
- Workflow references only enabled tools.
- Required tools appear in workflow in correct order (as subsequence).
- Genotype passes `validate_genotype()`.
- **Does NOT use**: gold answers, execution results, LLM outputs.

If the genotype representation cannot verify a constraint, mark it `NOT_CHECKABLE`.

### S2: S1 + static parent-child selection
Apply S1 first. Then compare parent vs child using ONLY static features:
- `behavior_hash` difference (structural change detection).
- Workflow step count difference.
- Tool set difference.
- **Does NOT use**: answer_correct, execution traces, gold labels.

### S3: Post-execution hard constraint diagnostic (upper bound)
Uses execution traces to check `tool_path_valid` AND `format_compliant`.
This is a **diagnostic ceiling** — it requires execution, so it cannot prevent execution cost.

## 6. Metrics

Per task × seed × strategy, record:
- `answer_correct` (gold checker)
- `format_compliant` (prefix + length + no extra lines)
- `tool_path_valid` (ordered contract with expected outputs)
- `hard_validity` = `format_compliant AND tool_path_valid`
- `effective_success` = `answer_correct AND hard_validity`
- `offspring_accepted` (per selection mechanism)
- `harmful_offspring` (effective_success=False among accepted)
- `model.generate` calls, token deltas, wall clock

**Primary endpoint:** paired change in `effective_success` (child − parent).
**Secondary:** harmful offspring rate, rejection rate, call cost.

## 7. Budget Matrix

5 tasks × 5 seeds × 3 strategies = 75 units.
Each unit: 1 parent + 1 child = 2 evaluations.
Each evaluation ≈ 2 generations (workflow has LLM + tool + finalize).
Estimated: 75 × 2 × 2 = 300 generations.

**HARD CAP: 150 generations.** If the full matrix cannot complete, mark `INCONCLUSIVE`.
No seed/task reduction to force completion.

## 8. Statistical Analysis

- Paired binary outcomes: McNemar exact test.
- Proportions: Wilson 95% CI.
- Account for task clustering (5 tasks, not 75 independent units).
- Report per-task and aggregate.

## 9. Stop Rules

1. Predicted calls > 150 → STOP, `INCONCLUSIVE`.
2. Wall clock > 300s → STOP, `INCONCLUSIVE`.
3. Ledger ≠ runtime count → STOP, `ERROR`.
4. Manifest hash mismatch → STOP, `ERROR`.
5. Gold leakage detected → STOP, `ERROR`.
6. Task cannot discriminate candidates → STOP, `INCONCLUSIVE`.

## 10. Decision Boundaries

| Outcome | Condition |
|---------|-----------|
| **Support** | S1 or S2 improves effective_success on non-rule-making tasks, within constraints |
| **Safety only** | Static filter reduces violations but no performance improvement |
| **Falsify** | Filter cannot identify harmful offspring, or selected effective_success ≤ baseline |
| **Inconclusive** | Insufficient sample, wide CI, task discrimination failure, or early budget stop |

## 11. Artifacts

Each run writes to `research/runs/<R4_RUN_ID>/`:
- `R4_FROZEN_MANIFEST.json` (pre-model-load SHA-256)
- `R4_RAW.json`
- `R4_LEDGER.jsonl`
- `R4_REPORT.md`
- `R4_RESULT_MANIFEST.json`
- Independent recomputation output

## 12. Boundaries

- Formal G3 remains FAIL.
- PC1, controller training, Family C: NOT AUTHORIZED.
- R1/R2/R3 data preserved.
- No gold label modification.
