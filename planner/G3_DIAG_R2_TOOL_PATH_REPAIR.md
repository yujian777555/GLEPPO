# Planner Decision — G3-DIAG-v2-R2 Tool-Path Repair

**Decision date:** 2026-10-29  
**Branch:** `c7-g3-diag-v2-r1-fastpath`  
**Starting commit:** `b8b70354433113bead0bbfa3560cda79f592d4f9`  
**R1 run:** `20261029T033104Z_R1`  
**Decision:** ACCEPT R1 AS A DIAGNOSTIC STOP; AUTHORIZE MINIMAL REPAIR AND A NEW BOUNDED RERUN.

## 1. R1 adjudication

Accept the R1 stop as protocol-compliant diagnostic evidence only. It proves that the generation cap and ledger worked and that the frozen tool-path gate correctly rejected the observed traces. It does NOT establish operator success/failure or formal G3 passage.

Keep all R1 artifacts immutable. Do not rewrite its report as a passing baseline.

## 2. Root causes: two independent defects

### Defect A — string-operation payload extraction

The exact current method is in `gleppo/interpreter.py`, not the LLM module docstring:

```python
    def _extract_strops_payload(self, llm_output: str, task: dict) -> str:
        """R63: extract str_ops command from LLM output or task input."""
        import re
        m = re.search(r"(upper|lower|reverse|split|join|replace)\s*[|:]\s*(.+)", llm_output, re.IGNORECASE)
        if m:
            return f"{m.group(1).lower()}|{m.group(2).strip()}"
        # Fall back to task input
        return self._extract_expr_from_text(task["input"])
```

The previous patch attempt failed because it targeted a different file/header and used `搂4` where the repository actually contains `§4`. Do not replace the module header. Replace only the method body in `gleppo/interpreter.py`.

Required behavior:
- Preserve explicit `upper|X`, `lower|X`, `reverse|X`, `split|X`, `join|X`, and `replace|...` parsing.
- Parse quoted natural-language commands such as `transform the word 'sum' to uppercase` and `transform 'hi' to uppercase` into `upper|sum` and `upper|hi`.
- Support the frozen forms for uppercase, lowercase, and reverse where the operand is quoted.
- Search the LLM output first, then the task input.
- If no valid string operation can be extracted, raise `ValueError`. NEVER fall back to extracting arithmetic as a string payload; silent wrong-tool success is the bug being fixed.

### Defect B — B2-002 is structurally incompatible with the current default genotype

`make_valid_genotype()` defaults to tools `["calc", "str_ops"]` and workflow `llm -> calc -> str_ops -> finalize`. The frozen B2-002 contract requires `py_sandbox=49 -> calc=43`. This cannot pass by fixing string parsing alone.

Also, `_extract_calc_payload` currently falls back to the first arithmetic expression in task text, so B2-002 may re-evaluate `14*3+7` and return 49 rather than the required second expression `49-6`.

Required behavior:
- Make `_extract_calc_payload` prefer an explicitly tool-directed expression such as `Then use calc to compute 49-6` when present; retain first-expression fallback for B2-001 and B2-003.
- In the diagnostic runner, construct a frozen, task-compatible reference genotype for each B2 task:
  - B2-001: available tools `calc,str_ops`; ordered workflow includes calc then str_ops.
  - B2-002: available tools `py_sandbox,calc`; ordered workflow includes py_sandbox then calc.
  - B2-003: available tools `calc,str_ops`; ordered workflow includes calc then str_ops.
- Keep a model turn in each workflow and record any model-initiated tool call separately; it may not substitute for required explicit workflow calls unless the exact ordered contract is satisfied.
- Label this configuration `task_compatible_reference`, not the unmodified default genotype. Apply each operator to the same frozen task-compatible parent for paired comparisons. For crossover, use a separately identified mate with the same task-compatible workflow but a distinct frozen prompt/configuration.
- Do not weaken or change the frozen B2 tool-path contracts.

## 3. Required offline tests

Add focused tests for:
1. quoted uppercase extraction: B2-001 `sum -> upper|sum`; B2-003 `hi -> upper|hi`;
2. explicit command syntax remains supported;
3. missing/ambiguous string operation raises `ValueError`, and no arithmetic fallback occurs;
4. B2-002 calc extraction chooses `49-6`, not `14*3+7`;
5. B2-001 and B2-003 still select their intended arithmetic expression;
6. task-compatible reference workflows expose exactly the tools and ordered steps required by each frozen B2 contract;
7. the existing hard-cap, ledger, and ordered-tool-path tests remain passing.

Run focused tests, then the full offline suite. Preserve R1 evidence. If any acceptance check fails, do not launch the model.

## 4. New bounded real-model rerun

After offline acceptance only, run a new experiment with a new timestamped ID ending in `_R2` and fresh `G3_DIAG_R2_*` artifacts.

- Frozen model revision: `a09a35458c702b33eeacc393d103063234e8bc28`.
- Hard cap: 30 actual `model.generate` calls, reserved before generation.
- Wall-clock cap: 300 seconds.
- First evaluate the task-compatible reference on B2-001/002/003.
- If any baseline tool-path contract fails, stop immediately and do not compare operators.
- Only after all three pass, compare one `tool_subset_edit` child and one `crossover` child against their paired task-compatible references, within the SAME 30-generation cap.
- Record exact per-task tool traces, final-answer success, operator/genotype hashes, actual generation IDs, token deltas, wall clock and budget state.
- If budget runs out before the matrix is complete, mark INCONCLUSIVE and stop.

## 5. Scope and claims

- No Family C.
- No PC1.
- No controller implementation or training.
- Formal G3 remains FAIL unless a later separately reviewed formal protocol passes.
- A tool-path pass is a validity prerequisite, not evidence of performance improvement.
- R1 remains an accepted diagnostic stop, not a completed operator experiment.

## 6. Required handoff

Commit source + tests first; report exact test commands and exit codes. Only then run R2. Submit raw data, per-generation ledger, report, manifest, and an independent verification result. Do not claim the model was run unless actual runtime evidence exists.
