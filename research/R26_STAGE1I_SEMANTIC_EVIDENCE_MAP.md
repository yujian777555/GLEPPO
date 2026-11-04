# R26 Stage 1I Semantic Evidence Map

**Date:** 2026-11-04
**Schema:** 1.0
**Branch:** r25-handoff
**Source Snapshot:** 29325cfa16441154c833f381f208747b57627a79

## Summary

| Disposition | Count |
|-------------|-------|
| VERIFIED_FIXED | 26 |
| PARTIALLY_FIXED | 14 |
| OPEN | 1 |
| UNVERIFIABLE | 1 |
| **Total** | **42** |

## Machine-Readable Source

See `R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json` for the canonical 42-finding map.

## Key Corrections

| ID | Correction |
|----|------------|
| R53 | Corrected to `test_mutation_status_not_checked_by_consistency` (INDIRECT) |
| R39 | Cross-referenced R16/R20 instrumented evaluator tests |
| R18 | Complete manual evidence with UNMEASURED tokens |

## Evidence Types

- **DIRECT:** Test directly exercises the failure mode
- **INDIRECT:** Test is related but doesn't prove full acceptance criterion
- **MANUAL:** Documentation evidence only
- **NONE:** No test evidence exists

## Disclaimer

This map validates declaration mapping and schema only.
It does NOT prove assertion semantics, call paths, branch reachability, or acceptance coverage.
