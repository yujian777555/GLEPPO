# R9 Protocol — Format Constraint Cross-Task Replication

**Status:** PROTOCOL FROZEN; no model calls until manifest written and preflight passes.
**Parent evidence:** R8 `b55b416` (immutable).
**Model:** Qwen2.5-7B-Instruct, revision `a09a35458c702b33eeacc393d103063234e8bc28`.
**Hard caps:** 150 actual `model.generate` calls; 300 seconds wall clock.

## 1. Research Question

**On tasks where format errors constitute a barrier to effective success, can C1 (format constraint) improve effective success rate by reducing format failures, and does this benefit replicate across multiple tasks?**

## 2. Hypotheses (Pre-Registered)

- **H1 (Format Mechanism Replication):** On tasks where C0 has format failures, C1 reduces format failure rate.
- **H2 (Performance Conversion):** Format failure reduction converts to effective success improvement (not just output appearance).
- **H3 (Task-Conditioned Dependence):** On tasks where C0 is already format-compliant, C1 should NOT be expected to have stable benefit.

H1 ≠ H2. H2 ≠ H3.

## 3. Experiment Arms

| Arm | Description |
|-----|-------------|
| **C0** | Original `crossover` |
| **C1** | Same crossover child + format constraint ONLY |

## 4. Task Composition (5 tasks)

### Format-Sensitive Tasks (expect C0 format failures)
| Task | Tools | Structure | Format Risk |
|------|-------|-----------|-------------|
| B2-001 | calc, str_ops | SUM-STRING format | HIGH (R8: 0% C0 fmt) |
| B2-022 | calc, str_ops | DONE-NUMBER format | MEDIUM |
| B2-024 | str_ops, calc, py_sandbox | OUTPUT-NUMBER, 3-tool | MEDIUM |
| B2-026 | calc, str_ops | RESULT-NUMBER format | MEDIUM |

### Format-Insensitive Tasks (C0 already compliant)
| Task | Tools | Structure | Format Risk |
|------|-------|-----------|-------------|
| B2-023 | py_sandbox, calc | Pure numeric | LOW |
| B2-025 | calc, py_sandbox | Multi-step numeric | LOW |

## 5. Seeds (3 per task)

```
r9-paired-seed-001
r9-paired-seed-002
r9-paired-seed-003
```

## 6. Budget Matrix

6 tasks × 3 seeds × 2 arms = 36 units.
Each unit: 1 parent + 1 child = 2 evaluations.
Each evaluation ≈ 2 generations.
Estimated: 36 × 2 × 2 = 144 generations. **Within 150 cap.**

## 7. Decision Criteria

| Outcome | Condition |
|---------|-----------|
| **GO** | H1+H2 on multiple tasks, not single-task driven, no violations |
| **NO-GO** | Format improvement doesn't convert, or answer drop offsets gain |
| **INCONCLUSIVE** | No format failures, insufficient tasks, single-task effect |

## 8. Boundaries

R1-R8 data preserved | Formal G3 FAIL | PC1/training/Family C NOT AUTHORIZED
