# Planner Latest Plan — GLEPPO Phase 2A-R1 (OUTCOME)

**Status:** EXECUTED 2026-10-27 · awaiting SECOND independent review  
**Repository:** `yujian777555/GLEPPO` only  
**Base commit (under review):** `315796399116c4e1ec540f42d3e78a061043fb7e`  
**PC1 status:** NOT APPROVED · NOT EXECUTED  
**Controller status:** no PPO / Q-learning / bandit controllers implemented or trained

## Task (as executed)

Phase 2A-R1 correctness remediation per `research/PC1_INDEPENDENT_REVIEW.md` R1–R7. No new mechanisms, no scope expansion.

## Outcome

**All R1–R7 findings fixed with regression tests. PC1 still not executed — second review requested.**

| Finding | Fix | Test evidence |
|---|---|---|
| R1 gold correctness | A/B/C checkers compare actual answers/values to gold | `TestR1EvaluatorCorrectness` (adversarial wrong answers fail) |
| R2 state count | N_STATES=100 (>=100 honored); 80-claim retracted | `TestR7Budget` + zero-cost check |
| R3 reward identity | `gleppo/reward.py` single frozen function for r_hat & Q_hat | zero-cost checks 2/2 |
| R4 seeds/cache/CRN | SHA256 seeds, replicate-aware cache, CRN paired | `TestR4SeedsCache` incl. PYTHONHASHSEED subprocess |
| R5 templates | Real distinct generation rules; disjoint train/val | `TestR5Templates` + regenerated manifests |
| R6 Jaccard distance | div_* = 1 - similarity | `TestR6JaccardDistance` |
| R7 budget units | `BudgetLedger`; init slots included; 45,440<=50,000 | zero-cost check + `BudgetLedger` |

## Verification runs (2026-10-27)

- `python -m unittest discover -s tests` → **37/37 PASS**
- `gleppo.pc1.zero_cost_protocol_check()` → **10/10 PASS** (45,440 planned slots, CRN/reward identity OK)
- `python scripts/run_g3_causality.py` → **PASS 5/5** (StubLLM structural causality)
- `python scripts/run_smoke.py` → 4 tasks A/B, 96 planned slots, 0 Family-C access
- `python scripts/build_manifest.py` → VERIFY OK

## Manifest SHA256 (regenerated)

```
train_A bc8e62255bebb3975a9c37b9422ab792a2891dfee783d9e060709f82a7cbc3f9
train_B c5b0d99d4cbde9c7a7ab73979061a706482618c871cbc4bd0ceb59c3157a9b9b
val_A   01591cb93bd445ec879c706fe80f7c9924184536f0b280fea6d0b4558b40c5ee
val_B   6300f14a85acb04c9496a2d3796d69c19f4889813b785855165ca1ca5dadbe79
test_C  67109af7d01e262f6c03ea75e27959e5136e2ce1700c56957f27853320a6bcb9   (never executed)
```

## Production smoke / real-model G3 — BLOCKED

`docs/RUNTIME_LOCK.md` production backend is `PENDING_DEPLOYMENT` (no credentials/hardware). Real-model G3, token/latency measurements, and the PC1 LLM cost ceiling cannot be produced. **No fabricated model calls or costs.** StubLLM results are labeled stub-only and are not real-model evidence.

## Next steps (shortest path)

1. **Second independent review** of `research/PC1_INDEPENDENT_REVIEW.md` remediation table + `research/PHASE2_PREFLIGHT.md` Amendment v2.
2. Deploy production backend → fill RUNTIME_LOCK production fields.
3. Real-model A/B smoke + G3 (still no Family C) → set LLM inference ceiling.
4. Execute **PC1** under 50,000 planned-slot cap and the separate LLM ceiling.
5. Only if PC1 **PASS** → request controller implementation plan (random/fixed/adaptive/bandit/FM-rewrite/Q-learning/PPO).

## Forbidden (unchanged)

No PC1 before second review. No controllers. No Family C execution. No GLEET code. No M2/third mechanism. No fabricated results.
