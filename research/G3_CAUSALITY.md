# G3 Genotype-Causality Report

**Date:** 2026-10-27T03:44:26Z
**Mode:** STUB_LL M_v1 (docs/RUNTIME_LOCK.md §4) — structural causality, not production-model validation
**Families used:** A/B only. Family C accessed: False
**Parents:** 4 · **Tasks:** 8 (signature probe uses 2/operator/parent) · **Replicas:** 2

| Operator | valid | invalid | hash_changed | behavior_changed | no_op | PASS |
|---|---|---|---|---|---|---|
| `prompt_local_edit` | 4 | 0 | 4 | 4 | 0 | YES |
| `prompt_critique_rewrite` | 4 | 0 | 4 | 4 | 0 | YES |
| `tool_subset_edit` | 2 | 2 | 2 | 2 | 0 | YES |
| `workflow_step_edit` | 4 | 0 | 2 | 2 | 2 | YES |
| `crossover` | 4 | 0 | 4 | 4 | 0 | YES |

**Overall G3 (stub mode):** PASS

## Notes
- Evidence JSON: `research/G3_CAUSALITY.json` (hashes, diffs, traces).
- StubLLM preserves causal structure (prompt/tool/workflow edits change traces);
  production-model G3 must be re-run after RUNTIME_LOCK production fields are filled.
- Invalid offspring are counted and dropped, never silently replaced by parents.
