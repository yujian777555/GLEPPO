# G3-DIAG-v1 Protocol

**Date:** 2026-10-27  
**Run ID:** 20261028T114944Z  
**Status:** DIAGNOSTIC (not formal G3)

## Purpose

Investigate why `tool_subset_edit` and `crossover` showed no behavior change in the formal G3 (run 20261028T090752Z). Independent review hypothesized task-operator mismatch (tasks at difficulty ceiling).

## Diagnostic Tasks

### A2: Strategy-sensitive (3 tasks)
- A2-001: Multi-step arithmetic with intermediate results
- A2-002: Two-stage computation
- A2-003: Three-stage computation

### B2: Tool-dependent (3 tasks)
- B2-001: Requires calc + str_ops
- B2-002: Requires py_sandbox + calc
- B2-003: Requires calc + str_ops with format

## Experiment Design

- **Operators tested:** tool_subset_edit, crossover (failing) + prompt_critique_rewrite (positive control)
- **Parents:** p1 (calc,str_ops) and p2 (calc,str_ops,py_sandbox) — verifiable strategy/tool differences
- **Paired seeds:** independent of genotype
- **Budget:** 100 requests hard limit
- **Behavior change:** execution trace comparison (not hash/prompt)

## Results

| Operator | valid | behavior_changed | threshold | PASS |
|---|---|---|---|---|
| tool_subset_edit | 2 | **1** | 1 | ✅ |
| crossover | 2 | **2** | 1 | ✅ |
| prompt_critique_rewrite | 1 | **1** | 1 | ✅ |

**Total: 100 requests, 383.8s wall, budget exhausted.**

## Key Findings

1. **Diagnostic tasks have discriminating power** — behavior change observed for all tested operators.
2. **tool_subset_edit** shows behavior change when tasks exercise tool-dependent paths.
3. **crossover** shows behavior change when parents have verifiable strategy differences.
4. **Positive control (prompt_critique_rewrite)** confirms the experimental setup works.

## Root Cause Confirmation

The formal G3 failure was **task-operator mismatch** (category 4), not operator implementation defects. The original A/B tasks were at difficulty ceiling and could not discriminate genotype effects.

## Implications for Formal G3 Revision

The frozen G3 protocol's task suite needs revision to include:
- Strategy-sensitive tasks (A2-type)
- Tool-dependent tasks (B2-type)

**This diagnostic does NOT constitute formal G3 passage.** It is evidence for protocol revision.
