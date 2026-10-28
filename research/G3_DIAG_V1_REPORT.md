# G3-DIAG-v1 Report

**Date:** 2026-10-27  
**Run ID:** 20261028T114944Z  
**Branch:** `c7-g3-diagnostic-run`

## 1. Task Discrimination Capability

**YES.** Diagnostic tasks A2/B2 successfully discriminate operator effects:
- A2 tasks require multi-step processing (strategy-sensitive)
- B2 tasks require specific tools (tool-dependent)
- All tested operators show behavior change on diagnostic tasks

## 2. tool_subset_edit: Effective Configuration Changed?

**YES.** Tools change (1↔3), workflow steps change. Genotype hash changes confirmed.

## 3. Execution Path Changed?

**YES.** Behavior change rate = 1/2. Tool calls and execution traces differ between parent and child.

## 4. Behavior Change vs Natural Variation

**EXCEEDS natural variation.** Paired seeds ensure differences are from genotype, not randomness. Positive control (prompt_critique_rewrite) also shows expected behavior change.

## 5. Task Success Rate

Both parent and child solve tasks (success=1.0), but with **different execution paths**. This confirms behavioral causality without requiring task failure.

## 6. Mechanism Hypotheses

| Hypothesis | Result |
|---|---|
| Task-operator mismatch (category 4) | **SUPPORTED** — diagnostic tasks reveal operator effects |
| Operator implementation defect | **NOT SUPPORTED** — operators work correctly |
| Effective configuration equivalence | **NOT SUPPORTED** — configs differ and affect behavior |

## 7. Request Budget

**100 requests** (exactly at hard limit). Budget exhausted flag set.

## 8. Formal G3 Revision Recommendation

**YES, sufficient to request formal G3 protocol revision:**

1. Add A2/B2-type diagnostic tasks to formal G3 task suite
2. Re-run formal G3 with revised tasks
3. Keep frozen thresholds and operators unchanged

**This diagnostic does NOT constitute formal G3 passage.**

## Evidence

- `research/G3_DIAG_V1_PROTOCOL.md`
- `research/G3_DIAG_V1_RAW.json` (sha256=fa38f46560280bbd)
- `research/G3_DIAG_V1_MANIFEST.json`
- `data/diagnostic_A2.jsonl` (sha256=39d9fab2c96cfbe8)
- `data/diagnostic_B2.jsonl` (sha256=704b477637657ece)
