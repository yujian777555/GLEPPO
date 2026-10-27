# Planner Latest Plan — GLEPPO Phase 2A-R2 (OUTCOME)

**Status:** EXECUTED 2026-10-27 · awaiting THIRD independent review  
**Repository:** `yujian777555/GLEPPO` only  
**Base commit (second review):** `a272a453c1147d9b2fd194c04806ba0a4dac8cdc`  
**PC1 status:** NOT APPROVED · NOT EXECUTED  
**Controller status:** no PPO / Q-learning / bandit controllers implemented or trained

## Task (as executed)

Phase 2A-R2 remediation per `research/SECOND_REVIEW_FINDINGS.md` R8–R11 + smoke slot fix + PC1 runner scaffolding. No new mechanisms.

## Outcome

**All R8–R11 fixed with end-to-end regression tests. PC1 runner implemented and tested on synthetic fixtures only.**

| Finding | Fix | Test evidence |
|---|---|---|
| R8 CRN seed includes genotype | `Evaluator.effective_seed_parts` excludes genotype/action; instrumented-interpreter tests | `TestR8CRNEndToEnd` (5) |
| R9 CTX/cache accounting | bundle-level cache hits; `replicas_run`; per-episode deltas; init via counter deltas | `TestR9Accounting` (6) |
| Smoke slots omit init | `planned_init=32 + planned_offspring=96 = 128` | `slot_arithmetic_ok: true` |
| R10 runtime lock stale seeds | §2.1 Seed hierarchy (SHA256, no built-in hash) | `docs/RUNTIME_LOCK.md` rev R10 |
| R11 StubLLM wrong templates | `solve_input` input-only solver; 21 templates × 3 seeds | `TestR11StubTemplates` (6) |
| PC1 runner missing | `run_pc1_analysis` + cluster bootstrap + hard-cap guard | `TestPC1RunnerSynthetic` (8) |

## Verification runs (2026-10-27)

- `python -m unittest discover -s tests` → **62/62 PASS** (37 prior + 25 new)
- `gleppo.pc1.zero_cost_protocol_check()` → **PASS** (45,440 ≤ 50,000)
- `python scripts/build_manifest.py` → **VERIFY OK** (digests unchanged)
- `python scripts/run_g3_causality.py` → **PASS 5/5**
- `python scripts/run_smoke.py` → **planned_init=32, planned_offspring=96, planned_total=128, actual_replicas=112, cache_bundles=0, slot_arithmetic_ok=true**

## CTX vs cache units (R9)

- `planned slots` = conservative planned replica slots (hard-cap unit), includes init
- `actual replicas run` = uncached replica executions that ran
- `cache-hit bundles` = 1 bundle = n_eval replicas returned, 0 ran; never a new sample

## PC1 runner — implemented but NOT executed

`gleppo/pc1.py:run_pc1_analysis` computes D, advantage, cluster-bootstrap CIs from the frozen reward; enforces the 50k planned-slot cap; emits raw replayable evidence. Tested only on synthetic fixtures. **Registered PC1 experiment NOT run.**

## Production smoke / real-model G3 — BLOCKED

Production backend `PENDING_DEPLOYMENT`. No fabricated model calls or costs.

## Next steps

1. **Third independent review** of this remediation + PC1 runner.
2. Deploy production backend → real-model smoke + G3 → LLM cost ceiling.
3. Execute **PC1** under 50k planned-slot cap + separate LLM ceiling.
4. Only if PC1 **PASS** → request controller plan (random/fixed/adaptive/bandit/FM-rewrite/Q-learning/PPO).

## Forbidden (unchanged)

No PC1 before review. No controllers. No Family C execution. No GLEET code. No M2/third mechanism. No fabricated results.
