# Planner Latest Plan — GLEPPO Phase 2A-R3 (OUTCOME)

**Status:** EXECUTED 2026-10-27 · awaiting FOURTH independent review  
**Repository:** `yujian777555/GLEPPO` only  
**Base commit (third review):** `f329a45e91b8011a42e6cc3fee49817da940966b`  
**PC1 status:** NOT APPROVED · NOT EXECUTED  
**Production backend:** PENDING_DEPLOYMENT

## Outcome

**All R12–R18 fixed with regression tests. PC1 dry-run plan complete. Registered PC1 refused by default entry point.**

| Finding | Fix | Tests |
|---|---|---|
| R12 BudgetLedger unit mixing | explicit `replicas_run_delta` from evaluator counters | 6 |
| R13 fail-closed validation | reject missing actions, wrong horizon, non-finite, cluster conflicts, duplicates | 10 |
| R14 sample roles | `q_rollout`/`extra_immediate`; r̂=Q_first+extra; Q̂=q_rollout only | 3 |
| R15 collection runner | dry-run plan (2040 units) + `execute_registered_pc1` refuses | 4 |
| R16 seed/CRN/cache | `eval_seed` authoritative; cache key includes state/rollout/replicate | 7 |
| R17 replayable evidence | full sanitized records + provenance + bootstrap config | 3 |
| R18 cost report | 45,440 PC1 / 32+96=128 smoke / 112 actual / 0.021s stub | consistency PASS |

## Verification (actual outputs)

- `python -m unittest discover -s tests` → **97/97 PASS**
- `zero_cost_protocol_check()` → **PASS** (45,440 ≤ 50,000)
- `generate_pc1_dry_run_plan()` → **within_cap=True, total=45,440, schedule=2040 units**
- Manifest verification → **OK**
- Smoke → **planned_init=32, planned_offspring=96, planned_total=128, actual=112, slot_arithmetic_ok=true**
- Cost documentation consistency → **PASS**

## R14 estimator (confirmed unambiguous)

Per `research/PC1_INDEPENDENT_REVIEW.md` proposed amendment: `r_hat` uses Q-rollout first rewards **plus** extra immediate draws. `Q_hat` uses only complete q_rollout records. No protocol ambiguity.

## Next steps

1. **Fourth independent review** of this remediation.
2. Deploy production backend → real-model smoke/G3 → LLM cost ceiling.
3. Execute **PC1** (approval + production gate required).
4. Only if PC1 **PASS** → controller implementation plan.

## Forbidden (unchanged)

No PC1 before review. No controllers. No Family C. No GLEET code. No M2/third mechanism. No fabricated results.
