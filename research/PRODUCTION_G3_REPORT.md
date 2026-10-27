# Production G3 Causality Report

**Date:** 2026-10-27T12:26:48Z
**Backend:** qwen2.5-7b-instruct rev=a09a35458c702b33eeacc393d103063234e8bc28
**Tasks:** A=A-g3-prod-00, B=B-g3-prod-00
**Overall:** FAIL

| Operator | valid | invalid | hash_changed | behavior_changed | PASS |
|---|---|---|---|---|---|
| `prompt_local_edit` | 4 | 0 | 4 | 0 | NO |
| `prompt_critique_rewrite` | 4 | 0 | 4 | 0 | NO |
| `tool_subset_edit` | 2 | 2 | 2 | 0 | NO |
| `workflow_step_edit` | 4 | 0 | 2 | 0 | NO |
| `crossover` | 4 | 0 | 4 | 0 | NO |

**LLM stats:** {'model': 'qwen2.5-7b-instruct', 'revision': 'a09a35458c702b33eeacc393d103063234e8bc28', 'requests': 144, 'total_tokens': 13487, 'failures': 0, 'mean_latency_s': 2.2388582858774395, 'max_latency_s': 3.928248643875122}

**Total generations:** 72

**Paired CRN:** seeds depend on (task, replicate), NOT genotype
