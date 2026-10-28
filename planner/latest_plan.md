# Planner Latest Plan — G3-DIAG-v2-R1 Fast Path

**Status:** ACTIVE EXECUTOR TASK — OFFLINE FIXES FIRST  
**Branch:** `c7-g3-diag-v2-r1-fastpath`  
**Base SHA:** `7b0017fee427a49f3f9eb34532bc447f4c2bb7cd`  
**Detailed plan:** `planner/G3_DIAG_V2_R1_FASTPATH.md`

## Objective

Move quickly to a trustworthy small real-model diagnostic. Do not restart broad literature review or repeat already-passing generic tests. Fix only the blockers that invalidated G3-DIAG-v2's budget accounting and B2 tool-path evidence.

## Stage A — Mandatory offline acceptance

1. Enforce the hard cap at the actual `model.generate` boundary, before the call occurs.
2. Record one unique ledger row per actual generation, including per-call input/output token deltas, elapsed time, status/error and provenance.
3. Separate actual generations from evaluations, episodes and tool invocations. Historical v2's 240 actual generations against a stated 60-request cap must remain marked noncompliant under actual-generation counting.
4. Make tool-path verification a real gate: required tools must succeed in the required order and return the frozen expected outputs for B2-001/002/003.
5. Remove hardcoded success fields; add focused regression tests and run the full offline test suite.
6. Preserve every v2 artifact; R1 artifacts must use fresh names and a new run ID.

Stage A failure means stop; no real-model launch.

## Stage B — Authorized bounded diagnostic

After Stage A acceptance is evidenced, this plan authorizes a diagnostic-only run:
- Maximum **30 actual model generations**, enforced at the generation boundary.
- Maximum **300 seconds** wall clock.
- Baseline tool-path validation on B2-001/002/003 first.
- If all baseline paths pass, compare one `tool_subset_edit` child and one `crossover` child against paired baselines within the same cap.
- Stop immediately on baseline tool-path failure or budget exhaustion; report partial/inconclusive results honestly.
- Use the frozen model revision and record the actual loaded revision.
- No Family C, no formal G3 approval, no PC1, no controller training.

See the detailed plan for exact acceptance conditions and required artifacts.

## Frozen project boundaries

- Formal G3 remains **FAIL** until separately reviewed.
- PC1 remains **NOT APPROVED / NOT EXECUTED**.
- Controller training remains **NOT AUTHORIZED** until PC1 passes.
- Do not alter historical raw data or reinterpret the v2 ledger as compliant.
- No fabricated calls, tokens, test results, approvals or cost claims.

## Executor handoff

Complete Stage A, provide exact commands/exit codes and evidence, then run Stage B only if Stage A passes. Submit the result for Planner review. Do not wait for another broad planning cycle.
