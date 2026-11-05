# R26 Algorithm Pilot — Results

**Date:** 2026-11-05 | **Branch:** r26-algorithm-pilot | **Surrogate:** StubLLM only

## Summary

All 9 arms (F1-F5, RND, RULE, LINUCB, QLEARN) achieve **identical results**: `best_success = 1.000`, `discounted_return = 1.073` on both TRAIN (24 episodes/arm) and VALIDATION (12 episodes/arm).

**Root cause:** StubLLM is a deterministic solver that correctly solves all Family A/B tasks regardless of which evolutionary operator is applied. The surrogate is at **ceiling level** — there is zero headroom for adaptive operator selection to differentiate.

## Paired Comparisons (VAL, 12 paired units)

All differences are exactly **0.0000** with 95% CI **[0.0000, 0.0000]**.

## Decision Rule Outcome

Per Section 8 of the pilot specification:

> "If all five fixed operators are statistically/practically indistinguishable in this surrogate, the current benchmark/operator library cannot identify adaptive-selection value. Revise the task/operator mechanism before training."

**This condition is met.** The StubLLM surrogate cannot distinguish operators. Recommendations:

1. **Do NOT proceed to PPO** — no signal to learn from
2. **Revise the benchmark** — need tasks where operator choice matters (e.g., harder tasks, tasks where different operators produce different quality genotypes)
3. **Consider real LLM evaluation** — StubLLM ceiling masks real differences; a stochastic LLM (even small) would show operator effects
4. **Operator library may need redesign** — if all operators produce equally-valid genotypes on easy tasks, the library has no differential effect

## What This Pilot Does NOT Show

- NOT evidence about real LLM performance (StubLLM only)
- NOT evidence about Family C generalization
- NOT evidence about PPO vs bandits
- NOT confirmatory or publication-ready

## Artifacts

- `RUN_MANIFEST.json` — full configuration
- `RAW_EPISODES.jsonl` — 324 episodes with per-generation logs
- `SUMMARY.json` — aggregate metrics
- `controllers.py` — pilot context, RULE, LINUCB, QLEARN
- `paired_seed_tests.py` — 5 seed pairing tests (all PASS)
