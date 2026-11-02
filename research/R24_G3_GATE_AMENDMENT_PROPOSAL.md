# R24 G3 Gate Amendment Proposal

**Date:** 2026-11-02
**Status:** PROPOSED — requires independent review + Planner approval

## Current Circular Dependency

- Controller training requires Formal G3 PASS
- Formal G3 improvement verification requires controller training

## Proposed Gate Sequence

### 1. G3-PREFLIGHT (pre-training)

| Check | Requirement |
|-------|-------------|
| Evaluator correctness | Gold checker verified |
| Tool execution path | Tools execute correctly |
| Output format | Format compliance |
| Operator legality | All operators valid |
| Runtime completeness | Full pipeline works |
| Seed/logging | Reproducible |
| Safety constraints | No violations |

**Does NOT require learned controller improvement.**

### 2. PC1 (registered A/B diagnostic)

- Independent review ACCEPT
- Trusted Planner approval
- Runtime locked
- Budget approved
- Family C: PROHIBITED

### 3. ECOS Controller Training

- Only after PC1 GO
- Training authorization required

### 4. G3-EFFICACY (post-training)

- Independent confirm set
- ECOS vs fixed/random/rule baselines
- Statistical significance required

## Original Formal G3

**FAIL must be preserved.** G3-PREFLIGHT does NOT replace Formal G3.

## Approval Required

This amendment needs:
1. Independent review
2. Trusted Planner approval

**Executor cannot self-approve.**
