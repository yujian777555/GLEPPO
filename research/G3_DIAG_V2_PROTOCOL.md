# G3-DIAG-v2 Protocol

**Date:** 2026-10-28
**Run ID:** 20261028T130000Z
**Status:** DIAGNOSTIC (not formal G3)
**Branch:** `c7-g3-diag-v2`
**Baseline:** `7f9cc3437feb0d06d65094797a7094486d78ccd7`

## Purpose

Fix G3-DIAG-v1 experimental validity issues and re-verify that `tool_subset_edit` and `crossover` can cause real behavior changes on discriminating tasks.

## Phase 1 Fixes (Offline)

### Gold Label Corrections
- **A2-001:** 21 → 23 (arithmetic error: (3*7)+(12-4)-(2*3)=23)
- **B2-001:** 64-75 → 64-SUM (phantom 75 removed; redesigned to calc+str_ops consistent task)

### Task Definition Fixes
- **B2-001:** Redesigned to "Compute 25*3-11 using calc, then transform 'sum' to uppercase using str_ops. Report as SUM-STRING."
- **B2-002:** Cleaned up wording: "Use py_sandbox to compute result = 14*3+7. Then use calc to compute 49-6. Report the final result."
- **B2-003:** Unchanged: "Compute 8*8-4 using calc, then transform 'hi' to uppercase using str_ops. Report as NUMBER-STRING."

### Tool Path Verification
- **B2-001:** Must verify calc AND str_ops called in trace, str_ops output='SUM'
- **B2-002:** Must verify py_sandbox AND calc called in trace, py_sandbox output='49'
- **B2-003:** Must verify calc AND str_ops called in trace, str_ops output='HI'

### Run ID Consistency
- All artifacts (protocol, raw data, report, manifest) reference Run ID: `20261028T130000Z`

### Per-Request Ledger
- Records: request_id, task_id, operator, parent_id, replicate, request_type, timestamp, tokens, success, error
- All report aggregates computed from ledger (not hand-filled)

### Offline Validation Suite
1. Gold label recomputation
2. Required tool checks
3. Run ID consistency
4. Manifest hash verification
5. Request ledger completeness

## Phase 2 Freeze

### Frozen Task Set
- `data/diagnostic_A2.jsonl` (sha256=fe44f18e72483901)
- `data/diagnostic_B2.jsonl` (sha256=7ebe2ec735fd7dbf)

### Frozen Gold Checker
- Family A: numeric exact match
- Family B: case-insensitive string match after `Final answer:` extraction

### Frozen Tool Path Rules
- Required tools must appear in execution trace with `ok=true`
- Tool outputs must match expected values (for string transformation tasks)

### Frozen Parent Configurations
- **p1:** default genotype (calc, str_ops)
- **p2:** modified genotype (calc, str_ops, py_sandbox) with different system_prompt

### Frozen Operators
- `tool_subset_edit` (failing operator 1)
- `crossover` (failing operator 2)
- `prompt_critique_rewrite` (positive control)

### Paired Seed Rules
- Paired comparison shares same random seed
- Seed = `f"diag-{task_id}-p{parent_idx}"`
- Seed does NOT depend on genotype or action

### Behavior Change Determination
Behavior is considered changed if ANY of:
1. success_rate differs
2. mean_tool_calls differs
3. mean_turns differs
4. failure_category distribution differs
5. execution trace (type/ok/detail/output) differs
6. final answer differs

### Request Limit and Stop Rules
- **Hard limit:** 60 requests (including all parent/child evaluations)
- **Wall clock limit:** 600 seconds
- **Stop rule:** budget exhausted → stop immediately, no additional sampling

## Phase 3 Experiment

### Scope
- `tool_subset_edit`
- `crossover`
- `prompt_critique_rewrite` (positive control)

### Model
- **Revision:** `a09a35458c702b33eeacc393d103063234e8bc28`
- **Runtime:** A800 GPU (10.10.24.107:30939)
- **Frozen:** same as G3-DIAG-v1

### Evaluation
- 2 replicates per genotype per task (paired seeds)
- Tool path verification for B2 tasks
- All parent and child trajectories saved (including failures)

## Phase 4 Reporting

### Metrics to Report
1. Genotype change rate
2. Valid configuration change rate
3. Behavior change rate
4. Tool path change rate
5. Parent and child task success rates
6. Gold Checker vs raw answer consistency
7. Positive control results
8. Actual request count, tokens, wall clock, failures

### Distinction Requirements
Must distinguish:
- **Behavior changed:** execution traces differ
- **Behavior change exceeds natural variance:** paired seeds ensure difference is from genotype
- **Task performance improved:** success rate increased

These three cannot substitute for each other.

## Strict Boundaries

- **PC1:** not executed
- **Controller training:** not started
- **Family C:** not accessed
- **Historical raw data:** not overwritten
- **Formal G3:** remains FAIL status until independent review and formal re-verification approved
- All tests, requests, and costs from actual run results

## Budget Limits

| Metric | Limit |
|--------|-------|
| Total requests | 60 |
| Wall clock | 600s |
| Replicates per eval | 2 |
| Tasks | 6 (3 A2 + 3 B2) |
| Operators | 3 |
| Parents | 2 |
