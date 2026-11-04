# R26 Stage 1I Final Finding Audit

**Date:** 2026-11-04
**Branch:** r25-handoff
**STAGE1H_REPORT_COMMIT:** 532ee8adf498e83967016723d28cb1e7dc30bf5f
**SOURCE_SNAPSHOT:** 29325cfa16441154c833f381f208747b57627a79
**CURRENT_BRANCH_HEAD:** e2cb353 (at Stage 1I work)

## 1. Disposition Counts (from 42 rows)

- **VERIFIED_FIXED: 26**
- **PARTIALLY_FIXED: 14**
- **OPEN: 1** (R15)
- **UNVERIFIABLE: 1** (R46)
- **Total: 42**

## 2. Key Corrections from Stage 1H

| ID | Issue | Correction |
|----|-------|------------|
| R53 | Wrong test mapped | → `test_mutation_status_not_checked_by_consistency` (line 118) as **indirect** evidence |
| R39 | Tautological evidence | → Cross-reference R16/R20 instrumented evaluator tests for action/genotype exclusion |
| R18 | Incomplete manual evidence | → Added UNMEASURED tokens, units note, PC1 planned-workload caveat |
| Validator | No real validation | → Created `_r26i_validator.py` with declaration map validation |

## 3. R53 Corrected Mapping

**Original:** `test_mutation_seed_contract_fails` (line 130) — mutates seed_schema, UNRELATED to lifecycle-status hash invariance.

**Corrected:** `test_mutation_status_not_checked_by_consistency` (line 118) — **indirect/related evidence only**.

**Limitation:** This test proves `protocol_consistency_check()` ignores status. It does NOT prove `compute_protocol_hash()` excludes status. **No direct status-only hash invariance test exists.**

## 4. R39 Cross-Reference

**Local test:** `test_action_genotype_excluded` (line 96) — compares same call with itself (tautological).

**Stronger evidence from R16/R20:**
- `test_same_crn_identical_across_genotypes` (R16, line 246)
- `test_cache_identity_is_genotype_specific` (R16, line 84)
- `test_operator_rng_independent_of_eval_seed` (R16, line 295)

These provide cross-genotype CRN evidence that supports R39's action/genotype exclusion criterion.

## 5. R18 Complete Manual Evidence

| Source | Line | Value | Note |
|--------|------|-------|------|
| SMOKE_RAW.json | 276 | wall_clock_s = 0.0261 | Stub latency |
| SMOKE_RAW.json | 277-279 | 32/96/128 planned slots | Not actual CTX |
| SMOKE_RAW.json | 284 | actual_replicas_run = 112 | Uncached replicas |
| SMOKE_RAW.json | 291 | production tokens UNMEASURED | |
| SMOKE_RAW.json | 293 | planned slots ≠ actual CTX | |
| COST_BASELINE.md | 4 | production tokens/latency UNMEASURED | |
| COST_BASELINE.md | 22 | stub wall-clock 0.0261 s | |
| COST_BASELINE.md | 30 | total planned smoke slots 128 | |
| COST_BASELINE.md | 47 | actual replicas = uncached | |
| COST_BASELINE.md | 82 | PC1 planned slots 45,440 | |
| COST_BASELINE.md | 101 | 0.0261s is stub, not production | |
| COST_BASELINE.md | 110-111 | 45,440 is forecast proxy | |

## 6. ECOS Scientific Integrity Note

**R21-C1 is DAC comparison, NOT operator comparison.** It does NOT prove adaptive operator selection beats fixed strategy.

PPO advantage over rule-based/LinUCB NOT established. Reward/parameter definitions have conflicts across Phase 1, R24, PC1 R4.

## 7. Conclusion

**R26_STAGE1I_AUDIT_COMPLETE_REQUIRES_PLANNER_REVIEW**

42 findings, 42 dispositions. Declaration validator created. PC1 remains BLOCKED.
