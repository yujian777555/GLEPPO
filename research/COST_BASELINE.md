# GLEPPO Cost Baseline (Phase 2A / 2A-R2 revision)

**Date:** 2026-10-27  
**Mode:** **STUB_LL M_v1** (deterministic, stdlib only, no network). Production LLM tokens/latency are **UNMEASURED** until a real backend is deployed under `docs/RUNTIME_LOCK.md`.  
**Raw counters:** `research/SMOKE_RAW.json` · **G3 evidence:** `research/G3_CAUSALITY.json`  
**Family C:** never executed. Manifest written and hashed only.

---

## 1. Counting units (same as `research/PHASE2_PREFLIGHT.md` §1)

`CTX` = one agent×task execution; `GEN` = one generation (λ offspring × n_eval CTX); `ROL` = one evolution run (T generations); `LLM` = one model completion.

---

## 2. Smoke test (measured 2026-10-27 R2, training families only)

| Parameter | Value |
|---|---|
| Tasks | 4 (train_A x2, train_B x2) |
| Evolution config | mu=4, lam=2, T=6, n_eval=2 |
| Wall-clock (total) | **0.0273 s** (stub; not representative of real LLM latency) |

### 2.1 Planned-slot arithmetic (Task C - explicit)

| Component | Formula | Slots |
|---|---|---|
| **Initialization slots** | n_tasks x mu x n_eval = 4 x 4 x 2 | **32** |
| **Offspring slots** | n_tasks x T x lam x n_eval = 4 x 6 x 2 x 2 | **96** |
| **Total planned slots** | 32 + 96 | **128** |

slot_arithmetic_ok: true in research/SMOKE_RAW.json.

### 2.2 Actual execution counters (R9)

| Counter | Value |
|---|---|
| Actual replicas run (uncached CTX) | **112** |
| Cache-hit bundles | **0** |
| Valid offspring | 40 |
| Invalid offspring | 8 (16.7%) - dropped, never parent-cloned |
| Evaluator cache misses | 56 |
| Family C access | **0** (guard enforced) |
| LLM tokens | **UNMEASURED** (StubLLM) |

R9 units: planned_*_slots = conservative planned replica slots (hard-cap unit);
actual_replicas_run = uncached replica executions that ran;
cache_hit_bundles = cached evaluation bundles (1 bundle = n_eval replicas, 0 ran).
Planned slots are NOT actual CTX. 112 actual < 128 planned because 8 invalid
offspring consumed 0 evaluator CTX (planned slots still counted conservatively).

Per-task best success on smoke (stub oracle): A-0000 1.0, A-0001 1.0, B-0000 1.0, B-0001 1.0.

### 2.1 Invalid-offspring note

8/48 invalid in smoke came from `tool_subset_edit` dropping a tool still referenced by the workflow (validity rejection). This is intended behavior (counted, dropped). G3 also recorded 2/4 invalid for `tool_subset_edit` in drop mode.

---

## 3. Operator cost (stub vs production)

| Operator | LLM calls (production) | LLM calls (stub) | Measured stub cost |
|---|---|---|---|
| `prompt_local_edit` | 0 | 0 | negligible (regex) |
| `prompt_critique_rewrite` | 2 | 0 | negligible |
| `tool_subset_edit` | 0 | 0 | negligible |
| `workflow_step_edit` | 0 | 0 | negligible |
| `crossover` | 0 | 0 | negligible |

Production LLM cost of `prompt_critique_rewrite` = 2 completions per application. With λ=4 and T=15: up to **120 LLM calls per ROL** if op2 is chosen every generation (plus agent-execution calls).

---

## 4. Extrapolations (NOT measurements)

Marked `EXT`. They use the smoke ratio and Phase 1 formulas; they are **not** observed values.

| Scenario | Formula | Planned slots (EXT, not measured CTX) | LLM agent turns (EXT) |
|---|---|---|---|
| Main evolution ROL (μ=8, λ=4, T=15, n_eval=3) | 15×4×3 | **180** | 180 × turns/task (TBD) |
| Smoke→main scale factor | 180/96 | 1.875× | — |
| PC1 amended (PHASE2_PREFLIGHT §3.3) | — | **45,440** | TBD after real-mode smoke |
| PC1 original (unaffordable) | 200×5×20×5×4×3 | 1,200,000 | — |

**Real-model smoke is required** before any reliable token/latency forecast. Placeholders only:

- Agent turns per task episode (stub observed 2–6; production expected 3–8) → **UNMEASURED**.
- Tokens/turn → **UNMEASURED**.
- Wall-clock/ROL → **UNMEASURED**.

---

## 5. Cost by category (to fill after production smoke)

| Category | Stub (measured) | Production |
|---|---|---|
| Agent execution (planned offspring slots, not actual CTX) | 96 (offspring only; total smoke planned = 128 incl. init) | TBD |
| Agent LLM turns | n/a (stub) | TBD |
| Operator proposal LLM calls | 0 | TBD (0–2/app) |
| Tokens in/out | UNMEASURED | TBD |
| Latency | 0.0273 s (stub smoke; not production) | TBD |
| Peak memory | not profiled | TBD |
| Failure rate (invalid offspring) | 16.7% | expected similar (structural) |

---

## 6. Implications for PC1 and Phase 3

1. **PC1 remains unexecuted** pending independent review of `research/PHASE2_PREFLIGHT.md` (protocol §1.1).
2. Structural overhead is trivial in stub mode; the real cost driver is **agent-execution LLM calls** (CTX × turns/episode). PC1's 45,440 planned slots at even 4 turns/episode ≈ 190k completions — must be budgeted against the actual deployment backend before running.
3. If production smoke shows turns/episode >8 or latency making 45,440 planned slots infeasible, **SR5** applies: one scale revision, then STOP. Do not silently reduce n_eval in main experiments.

---

## 7. Unresolved cost questions

- Production backend device/quantization (RUNTIME_LOCK §1 PENDING_DEPLOYMENT).
- True turns/episode distribution under the real model.
- Whether op2's 2 proposal calls dominate cost when selected often (track selection frequency in PC1).
