# R26 PC1 Finding Register

**Date:** 2026-11-03
**Branch:** r25-handoff
**HEAD:** a1940a2

## Taxonomy

| Classification | Count | Notes |
|----------------|-------|-------|
| FORMAL_REVIEW_FINDING | 42 | R12-R53 |
| REVIEW_RESULT | 1 | R60-R61 heading |
| UNNUMBERED_REVIEW_BLOCKER | 5-6 | SECOND review |
| EXECUTOR_REMEDIATION_ITEM | 8 | R54-R61 in TENTH |
| CROSS_REFERENCE | varies | References in later reviews |

## Formal Findings (R12-R53)

| ID | Review | Category | Disposition |
|----|--------|----------|-------------|
| R12 | THIRD | Budget | UNVERIFIABLE |
| R13 | THIRD | Statistics | UNVERIFIABLE |
| R14 | THIRD | Statistics | UNVERIFIABLE |
| R15 | THIRD | Runner | UNVERIFIABLE |
| R16 | THIRD | Seed/CRN | UNVERIFIABLE |
| R17 | THIRD | Evidence | UNVERIFIABLE |
| R18 | THIRD | Cost | UNVERIFIABLE |
| R19 | FOURTH | Protocol | UNVERIFIABLE |
| R20 | FOURTH | Seed/CRN | UNVERIFIABLE |
| R21 | FOURTH | Budget | UNVERIFIABLE |
| R22 | FOURTH | Provenance | UNVERIFIABLE |
| R23 | FOURTH | Evidence | UNVERIFIABLE |
| R24 | FOURTH | Cost | UNVERIFIABLE |
| R25 | FOURTH | Runner | UNVERIFIABLE |
| R26 | FIFTH | Protocol | UNVERIFIABLE |
| R27 | FIFTH | Budget | UNVERIFIABLE |
| R28 | FIFTH | Budget | UNVERIFIABLE |
| R29 | FIFTH | Provenance | UNVERIFIABLE |
| R30 | FIFTH | Provenance | UNVERIFIABLE |
| R31 | FIFTH | Runner | UNVERIFIABLE |
| R32 | FIFTH | Seed/CRN | UNVERIFIABLE |
| R33 | SIXTH | Budget | UNVERIFIABLE |
| R34 | SIXTH | Seed/CRN | UNVERIFIABLE |
| R35 | SIXTH | Provenance | UNVERIFIABLE |
| R36 | SIXTH | Protocol | UNVERIFIABLE |
| R37 | SIXTH | Provenance | UNVERIFIABLE |
| R38 | SIXTH | Approval | UNVERIFIABLE |
| R39 | SEVENTH | Seed/CRN | UNVERIFIABLE |
| R40 | SEVENTH | Protocol | UNVERIFIABLE |
| R41 | SEVENTH | Provenance | UNVERIFIABLE |
| R42 | SEVENTH | Approval | UNVERIFIABLE |
| R43 | EIGHTH | Approval | UNVERIFIABLE |
| R44 | EIGHTH | Provenance | UNVERIFIABLE |
| R45 | EIGHTH | Protocol | UNVERIFIABLE |
| R46 | NINTH | Approval | UNVERIFIABLE |
| R47 | NINTH | Provenance | UNVERIFIABLE |
| R48 | NINTH | Protocol | UNVERIFIABLE |
| R49 | NINTH | Protocol | UNVERIFIABLE |
| R50 | TENTH | Approval | UNVERIFIABLE |
| R51 | TENTH | Provenance | UNVERIFIABLE |
| R52 | TENTH | Protocol | UNVERIFIABLE |
| R53 | TENTH | Protocol | UNVERIFIABLE |

## Count Reconciliation

| Item | Count |
|------|-------|
| Formal findings (R12-R53) | 42 |
| SECOND blockers (unnumbered) | 5-6 |
| TENTH remediation (R54-R61) | 8 |
| R60-R61 heading (not finding) | 1 |
| **Total unique actionable** | **42-43** |

**Note:** SECOND blockers need split rule to determine if 5 or 6 distinct issues.

---

## Planner correction — 2026-11-04

R18 remains a formal Finding in the R12–R53 register. It must not be omitted or merged into R24 merely because both concern cost documentation. Stage 1D's corrected category table omitted R18 and therefore contained only 41 unique IDs. Restore R18 as a separate row in Stage 1E and reconcile the category/disposition counts to exactly 42.

Stage 1D Planner decision: REQUEST_CHANGES. See research/R26_STAGE1D_PLANNER_REVIEW.md.

---

## Stage 1E Planner correction — 2026-11-04

The Stage 1E category and ID reconciliation is accepted: R12–R53 are 42 distinct formal Findings; R18 is retained separately from R24.

The Stage 1E disposition counts 30/10/1/1 are only Executor-reported pending exact evidence review. The exact test map contains class/function names that do not match the actual test declarations. At minimum R24, R52 and R53 must be PARTIALLY_FIXED absent direct existing tests satisfying their original acceptance criteria. R18 may remain VERIFIED_FIXED after precise manual comparison of current raw and cost artifacts.

The authoritative Planner decision is REQUEST_CHANGES. See research/R26_STAGE1E_PLANNER_REVIEW.md. Stage 1F must produce the corrected evidence-backed disposition register; do not treat the Stage 1E counts as accepted dispositions.

---

## Stage 1F Planner correction — 2026-11-04

Stage 1F's 42 detailed rows contain 42 unique formal IDs R12–R53 and correct category arithmetic. However, the submitted disposition summary is inconsistent: detailed rows recount to 27 VERIFIED_FIXED / 13 PARTIALLY_FIXED / 1 OPEN / 1 UNVERIFIABLE, while status and commit message report 22/15/1/1.

The exact test map is also not accepted. Of 39 rows claiming a test, only 5 function names match the actual declaration in the stated class/file; 34 are not declared. R18, R45 and R46 are NONE. See research/R26_STAGE1F_PLANNER_REVIEW.md.

Do not treat either 22/15 or the detailed 27/13 as final accepted dispositions until Stage 1G completes the evidence-based recount and per-Finding semantic review.



---

## Stage 1G Planner correction — 2026-11-04

Stage 1G corrects the submitted row arithmetic to 27/13/1/1 = 42. Planner independently confirms 42 test classes and 218 declarations, but only 37/39 mapped file/class/function/line tuples match.

The exact evidence map is still incomplete: generic assertion labels replace actual expressions; source call paths and uncovered conditions are absent. R39 maps to a tautological same-call assertion; R53 maps to a seed-schema test unrelated to status/hash invariance; R49's related test does not prove the full approval lifecycle. R19 is over-classified while the canonical protocol is explicitly PROPOSED / NOT APPROVED.

See research/R26_STAGE1G_PLANNER_REVIEW.md. Stage 1H is required. Do not treat 27 VERIFIED_FIXED as accepted until the semantic review is complete. PC1 remains BLOCKED.

---

## Stage 1H Planner correction — 2026-11-04

Stage 1H corrects the formal register to 42 unique IDs, 26/14/1/1 dispositions and 39/39 exact test declaration mappings. R19 is correctly PARTIALLY_FIXED.

The semantic evidence audit is not accepted: no actual assertion/call-path/acceptance-coverage evidence is supplied; R53 still points to the unrelated seed_schema test at line 130; R39 lacks the R16/R20 cross-genotype evidence link; and R18's manual references omit key token/units/production-cost caveats.

See research/R26_STAGE1H_PLANNER_REVIEW.md. Stage 1I is required. PC1 remains BLOCKED.

