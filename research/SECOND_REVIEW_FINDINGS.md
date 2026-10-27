# Second Review Findings

Review of commit a272a453c1147d9b2fd194c04806ba0a4dac8cdc.

Verdict: REQUEST CHANGES. PC1 is not approved and has not been executed.

Blocking findings:
1. The evaluator seed path includes the genotype behavior hash even when a common evaluation seed is supplied. This defeats paired common-random-number comparisons across action-generated genotypes.
2. Actual execution counters do not consistently account for cached evaluation bundles with multiple replicas. The smoke report lists 96 offspring slots but omits 32 initialization slots; the full planned-slot upper bound is 128 for the recorded configuration.
3. Runtime lock seed rules still document built-in hash-based seeds, contradicting SHA256 stable seeding in code.
4. StubLLM does not correctly solve all generated Family A templates, so stub success scores are not task-performance evidence.
5. The PC1 module has helper functions but not the full state sampling, rollout, clustered-bootstrap, and raw-evidence runner.

Required order: fix seed wiring and tests; correct execution accounting and smoke slot reporting; update runtime lock; test or quarantine StubLLM metrics; implement and test the PC1 runner; request another independent review. Do not run PC1, production-model experiments, or controller training until the required gates pass.

---

# Remediation Log (Executor, 2026-10-27 Phase 2A-R2)

**Base commit (second review):** `a272a453c1147d9b2fd194c04806ba0a4dac8cdc`
**Prior plan commit:** `94764f86481edb8abb674c66aea0221ede2b9219`
**PC1 status:** NOT EXECUTED / NOT APPROVED. This log does NOT self-approve.

| Finding | Fix | Evidence |
|---|---|---|
| **R8** CRN seed includes genotype hash | `Evaluator.effective_seed_parts` = (SEED, state_id, task_id, rollout_id, replicate_id, replica_index) ！ NO genotype/action component. Instrumented-interpreter tests verify identical seeds across genotypes under the same CRN tuple | `gleppo/evaluator.py`; `TestR8CRNEndToEnd` (5 tests incl. instrumented seed log) |
| **R9** CTX/cache accounting inconsistent | Cache hits are BUNDLE-level (1 bundle = n_eval replicas, 0 ran). `replicas_executed` counter + `EvalResult.replicas_run`. `EpisodeResult.cache_hits` is per-episode delta. Init uses counter deltas. Invalid offspring consume 0 CTX | `gleppo/evaluator.py`, `gleppo/evolution.py`; `TestR9Accounting` (6 tests) |
| Smoke slots omit init | `scripts/run_smoke.py` now reports `planned_init_slots=32`, `planned_offspring_slots=96`, `planned_total_slots=128` | `research/SMOKE_RAW.json` (`slot_arithmetic_ok: true`) |
| **R10** runtime lock seed docs stale | `docs/RUNTIME_LOCK.md` ′2.1 Seed hierarchy ！ all SHA256, no built-in hash; CRN stream explicitly excludes genotype/action | `docs/RUNTIME_LOCK.md` revision R10 |
| **R11** StubLLM wrong on templates | `tasks.py:solve_input` deterministic input-only solver; all 21 A/B templates verified correct across multiple seeds | `TestR11StubTemplates` (6 tests); `scripts/check_stub_templates.py` |
| PC1 runner missing | `gleppo/pc1.py:run_pc1_analysis` ！ r_hat/Q_hat same frozen reward, cluster bootstrap, D/advantage thresholds, hard-cap guard, raw replayable evidence | `TestPC1RunnerSynthetic` (8 tests, synthetic fixtures only) |

## Test evidence (2026-10-27)

- **Full unit suite: 62/62 PASS** (`python -m unittest discover -s tests`)
  - 37 prior tests + 25 new R8/R9/R11/PC1-runner tests
- **Zero-cost protocol check: PASS** (45,440 planned slots <= 50,000 cap)
- **Manifest verification: OK** (full SHA256 digests unchanged from 2A-R1)
- **G3 causality (StubLLM): PASS 5/5**
- **Smoke: planned_init=32, planned_offspring=96, planned_total=128, slot_arithmetic_ok=true**

## Units definition (R9)

- `planned slots`: conservative planned replica slots (hard-cap unit); includes init; independent of caching.
- `actual replicas run`: uncached replica executions that actually ran.
- `cache-hit bundles`: one bundle = n_eval replicas returned, 0 ran; never counted as independent samples.
- `LLM calls/tokens`: separate; never inferred from CTX.

## Open blockers

1. **Production backend PENDING_DEPLOYMENT** ！ real-model G3/smoke and LLM cost ceiling remain unmeasured. No fabricated calls.
2. **Third independent review** of this remediation required before PC1.
3. C4 literature collision re-check outstanding (non-blocking).

## Request

Independent review of this remediation + the PC1 runner scaffolding. Executor does NOT mark PC1 approved or executed.
