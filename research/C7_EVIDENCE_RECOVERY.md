# C7 Evidence Recovery Report

**Date:** 2026-10-27  
**Base:** `be883ff`

## C6 Evidence Status

| File | Status | SHA-256 (16) |
|---|---|---|
| PHASE2A_R10_C6_REPORT.md | EXISTS | 1f18dc44163efe6c |
| PHASE2A_R10_C6_RAW.json | **MISSING** | — |
| PHASE2A_R10_C6_CANARY_RAW.json | **MISSING** | — |
| PRODUCTION_G3_RAW.json | EXISTS | 580cce66387347c3 |
| PRODUCTION_SMOKE_RAW.json | EXISTS | 23e5ff1422c0cc51 |

## Contradiction Found

| Source | prompt_local_edit | prompt_critique | tool_subset | workflow_step | crossover | Overall |
|---|---|---|---|---|---|---|
| **PRODUCTION_G3_RAW.json** | 0/4 | 0/4 | 0/2 | 0/4 | 0/4 | **FAIL** |
| **C6 report claim** | 2/4 | 4/4 | 0/2 | 2/4 | 0/4 | **FAIL** |

**The committed raw data shows ALL operators behavior_changed=0.** The C6 report's claim of 3/5 operators passing is **NOT_INDEPENDENTLY_VERIFIABLE** — the raw data files (`PHASE2A_R10_C6_RAW.json`, `PHASE2A_R10_C6_CANARY_RAW.json`) were never committed.

## C6 3/5 Result Classification

**`NOT_INDEPENDENTLY_VERIFIABLE`** — Cannot reconstruct per-replicate execution records from summary reports. No fabrication permitted.

## What IS Verifiable

- PRODUCTION_G3_RAW.json: 144 requests, 13487 tokens, 0 failures, model rev=a09a35458c702b33eeacc393d103063234e8bc28
- All operators show behavior_changed=0 in the actual raw data
- Previous stub G3 showed structural causality (different measurement)

## Implication

The C6 "3/5 operators pass" claim cannot serve as a scientific baseline. The actual evidence shows **all operators fail to produce observable behavior changes** with the production model. This makes the operator fixes (Task B/C) even more critical.
