# Planner Latest Plan — GLEPPO Phase 1 (OUTCOME)

**Status:** EXECUTED 2026-10-26  
**Repository:** `yujian777555/GLEPPO` only  
**Scope:** design-only. No controller code, no environment implementation, no model/API calls, and no training.

## Planner decision (preserved)

Select **M1 — Execution-Conditioned Operator Selection (ECOS)** as the sole active candidate for Phase 1. Freeze M2 (FMPS) as inactive; do not implement or develop it in parallel.

Rationale: M1's discrete operator action is simpler to isolate and audit. This is a tractability choice, not a novelty claim. The central risk is that a contextual bandit can solve the problem as well as PPO. The Phase 1 design must make this a serious, falsifiable gate.

## Executor prompt (as executed)

The Phase 1 executor prompt in `docs/PHASE1_DESIGN_PROTOCOL.md` and this plan's previous version was executed as specified: read charter/protocol/P0.1 artifacts, define genotype and operators, freeze M1-only decision family, specify MDP with delayed-effect justification, reward/evaluation semantics, task-family split with manifest/hash freeze, fair baselines including identical-state contextual bandit and FM-rewrite, feasibility/cost method, GO/REVISE/STOP.

## Outcome

**Decision: GO** (to Phase 2), with hard condition **PC1** (myopia diagnostic before any PPO training) and stop rules **SR1–SR5**.

| Deliverable | Path | State |
|---|---|---|
| Phase 1 design | `research/PHASE1_DESIGN.md` | done (written against `docs/PHASE1_DESIGN_PROTOCOL.md`) |
| Design protocol | `docs/PHASE1_DESIGN_PROTOCOL.md` | from planner; preserved |
| status.json | `status.json` | updated (merged planner framing + executor outcome) |
| this plan | `planner/latest_plan.md` | updated with outcome |

## Key design locks (summary)

- Genotype: declarative `system_prompt + tools + workflow` (not free-form code); fixed model/tools/interpreter; canonical serialization defined.
- Operators K=5: `prompt_local_edit`, `prompt_critique_rewrite`, `tool_subset_edit`, `workflow_step_edit`, `crossover`. FM-rewrite is **baseline B5**, not in K. Each operator has a specified I/O schema, LLM-call count, and failure handling.
- Frozen evolution: μ=8, λ=4, T=15, tournament-2 parents, (μ+λ) elitist survivors; **one operator per generation**.
- MDP: state = execution-outcome + population/operator-history + progress blocks; reward = population-best improvement + validity; **γ=0.95**; episode = one evolution run on one task.
- PPO vs bandit: delayed effects (diversity investment, scaffolding, stagnation escape) make the problem sequential; **myopia diagnostic must pass (PC1)** or **STOP (SR1)**. Identical-state LinUCB/neural-CE are kill baselines. Value-based Q-learning included as B6.
- Families: train A/B (arithmetic, tool-composition), val A′/B′ (disjoint seeds/templates), **held-out C** (structured constraints); hash-frozen manifests; golds never in controller process. Generated tasks used deliberately (no public-benchmark license assumption).
- Baselines B0–B6 mandatory.

## Next executor (Phase 2) must

1. `docs/RUNTIME_LOCK.md` (model + decoding + tools).
2. Genotype/interpreter/5 operators + **G3 causality** report.
3. Task generators + `data/manifest.json` freeze.
4. Evolution loop with frozen selection rules.
5. **Myopia diagnostic → PC1 gate** before any PPO code.
6. Baselines B0–B6 in one harness.
7. PPO trainer only after PC1 pass (independent code; no GLEET).

## Forbidden (unchanged)

- No GLEET code copy. No M2. No third mechanism. No budget-allocation novelty. No unproven novelty claims. No fabricated costs/results.
