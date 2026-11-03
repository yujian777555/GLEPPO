# R26 PC1 Current Branch Finding Audit

**Date:** 2026-11-02
**Branch:** r25-handoff
**HEAD:** 89ff936fdf15f6002942cfb16fa49c899f9d62e6
**Status:** R26_STAGE1_AUDIT_COMPLETE_REQUIRES_PLANNER_REVIEW

## 1. Count Reconciliation

| Source | Count | Notes |
|--------|-------|-------|
| R25 summary claim | ~43 | Approximate |
| R25 table enumerates | 39 | 6 categories |
| **Actual definitions in reports** | **43** | R12-R60 |

### Discrepancies

**In R25 table but NOT defined in reviews (6):**
- R8, R9, R54, R55, R58, R59

**Defined in reviews but NOT in R25 table (10):**
- R12, R13, R14, R17, R18, R23, R24, R30, R32, R52

**Conclusion:** R25 table is incomplete. Actual unique finding count is **43** (R12-R60).

## 2. Finding Definitions by Review

| Review | IDs | Count |
|--------|-----|-------|
| SECOND | (blockers, no IDs) | 6 |
| THIRD | R12-R18 | 12 |
| FOURTH | R19-R25 | 17 |
| FIFTH | R26-R32 | 18 |
| SIXTH | R33-R38 | 8 |
| SEVENTH | R39-R42 | 6 |
| EIGHTH | R43-R45 | 5 |
| NINTH | R46-R49 | 8 |
| TENTH | R50-R60 | 16 |

## 3. Disposition Summary

| Disposition | Count | Notes |
|-------------|-------|-------|
| VERIFIED_FIXED | 0 | Not yet verified |
| PARTIALLY_FIXED | 0 | Not yet verified |
| OPEN | 0 | Not yet verified |
| UNVERIFIABLE | 43 | All need current-branch verification |

**All 43 findings require current-branch verification before disposition.**

## 4. Highest-Risk Findings

1. **R12/R16/R20/R34/R39** — Seed/CRN correctness (5 findings)
2. **R25/R31** — PC1 runner is accounting stub (2 findings)
3. **R43/R46/R50** — Approval gate security (3 findings)
4. **R26/R40/R45/R48** — Protocol consistency (4 findings)
5. **R22/R29/R35** — Plan/provenance (3 findings)

## 5. Evidence Standards

- Test names ≠ coverage (must inspect test bodies)
- Hash checks must compare actual bytes
- CRN must verify all seed components
- Budget must distinguish logical vs physical
- Approval must verify trusted artifact
- PC1 runner ≠ registered PC1

## 6. Conclusion

**R26_STAGE1_AUDIT_COMPLETE_REQUIRES_PLANNER_REVIEW**

43 unique findings identified. R25 table incomplete (39 listed). All findings need current-branch verification. PC1 remains BLOCKED.
