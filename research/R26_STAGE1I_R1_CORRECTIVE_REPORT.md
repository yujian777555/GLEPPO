# R26 Stage 1I-R1 Corrective Report

**Date:** 2026-11-04
**Branch:** r25-handoff
**STAGE1I_REPORT_COMMIT:** a1e6e65e671c876d028492bfed164205c54df08b
**SOURCE_SNAPSHOT:** 29325cfa16441154c833f381f208747b57627a79
**CURRENT_BRANCH_HEAD:** (this commit)

## 1. Actions Taken

| Action | Status |
|--------|--------|
| Created `R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json` | ✅ 42 findings |
| Created `R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md` | ✅ |
| Fixed `_r26i_validator.py` with self-tests | ✅ |
| Validated 42-row map against declarations | ✅ PASS |
| Corrected R53 mapping | ✅ indirect evidence |
| Corrected R39 cross-reference | ✅ R16/R20 |
| Completed R18 manual evidence | ✅ |
| Updated durable documents | ✅ |

## 2. Disposition Counts (from JSON)

| Disposition | Count |
|-------------|-------|
| VERIFIED_FIXED | 26 |
| PARTIALLY_FIXED | 14 |
| OPEN | 1 |
| UNVERIFIABLE | 1 |
| **Total** | **42** |

## 3. Validator Self-Test

| Test | Result |
|------|--------|
| valid_map | PASS |
| wrong_function | PASS |
| missing_id | PASS |

## 4. Key Corrections

- **R53:** Corrected to `test_mutation_status_not_checked_by_consistency` (INDIRECT)
- **R39:** Cross-referenced R16/R20 instrumented evaluator tests
- **R18:** Complete manual evidence with UNMEASURED tokens

## 5. Boundary Attestation

- PC1: NOT EXECUTED
- Family C: NOT ACCESSED
- Controller training: NOT STARTED
- Formal G3: FAIL
- Model/API calls: 0
- Production source/test changes: 0

## 6. Conclusion

**R26_STAGE1I_R1_READY_FOR_PLANNER_REVIEW**

42 findings, 42 dispositions. Validator self-tests pass. PC1 remains BLOCKED.
