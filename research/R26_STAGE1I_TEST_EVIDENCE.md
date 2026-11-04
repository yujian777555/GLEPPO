# R26 Stage 1I Test Evidence

**Date:** 2026-11-04
**Branch:** r25-handoff

## Declaration Map Validator

`scripts/_r26i_validator.py` — validates declaration existence and line numbers.

**Scope:** Declaration inventory only. Semantic evidence requires manual assertion/call-path review.

## R53 Corrected Mapping

| Field | Value |
|-------|-------|
| Test File | tests/test_r39_r42.py |
| Test Class | TestR40ProtocolConsistency |
| Test Function | test_mutation_status_not_checked_by_consistency |
| Line | 118 |
| Evidence Type | **Indirect** |
| Limitation | Proves consistency check ignores status, NOT hash invariance |

## R39 Cross-Reference Evidence

| Test | Class | Line | Supports |
|------|-------|------|----------|
| test_same_crn_identical_across_genotypes | TestR16SeedContract | 246 | CRN across genotypes |
| test_cache_identity_is_genotype_specific | TestR8CRNEndToEnd | 84 | Cache isolation |
| test_operator_rng_independent_of_eval_seed | TestR16SeedContract | 295 | RNG independence |

## 450/450 Provenance

**EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED** — no raw log or CI run available.
