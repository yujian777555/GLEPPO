# Planner Latest Plan — GLEPPO Phase 1 Design

**Status:** READY FOR EXECUTION  
**Repository:** `yujian777555/GLEPPO` only  
**Scope:** design-only. No controller code, no environment implementation, no model/API calls, and no training in this task.

## Planner decision

Select **M1 — Execution-Conditioned Operator Selection (ECOS)** as the sole active candidate for Phase 1. Freeze M2 (FMPS) as inactive; do not implement or develop it in parallel.

Rationale: M1's discrete operator action is simpler to isolate and audit. This is a tractability choice, not a novelty claim. The central risk is that a contextual bandit can solve the problem as well as PPO. The Phase 1 design must make this a serious, falsifiable gate.

## Executor prompt (copy verbatim)

You are the Executor for the independent GLEPPO research project. The only user project repository you may modify is `yujian777555/GLEPPO`. Do not import, access, copy, or mix code, data, results, plans, or status from any unrelated user project. Public papers and official repositories may be inspected as research sources.

### Objective

Produce a build-ready design for M1 ECOS: a PPO-trained controller that selects among a small fixed set of agent-variation operators using population state and actual LLM-agent execution feedback. Decide whether the proposed sequential problem genuinely warrants PPO over a contextual bandit before any implementation.

### Required work

1. Read `docs/PROJECT_CHARTER.md`, `docs/PHASE1_DESIGN_PROTOCOL.md`, `research/CANDIDATE_MECHANISMS.md`, and the P0.1 audit/report. Preserve P0.1 conditions C1–C5.
2. Define a minimal, inspectable agent genotype and fixed runtime. Specify legal edits, operator input/output schemas, validity checks, and concrete examples of behavior-changing edits.
3. Freeze M1 as the only active decision family. Define a small operator set; hold parent selection, survivor selection, population size, and offspring count fixed.
4. Define the MDP precisely. Prefer one operator action per generation. Explain the delayed state consequences that PPO could learn beyond contextual bandits. If this rationale is not credible, recommend STOP before implementation.
5. Specify primary task-success metric, reward, invalid-offspring accounting, stochasticity handling, train/validation/held-out task-family split, leakage prevention, and manifest/hash protocol.
6. Pre-register fair baselines: fixed, random, adaptive rule, UCB1/EXP3, a contextual bandit using the same state features, FM-rewrite, and PPO; assess whether a value-based RL baseline is needed.
7. Provide a realistic pilot-cost model in terms of candidate evaluations, model calls, and environment steps. Clearly mark unknown quantities that require a later pilot; do not invent a precise cost estimate.
8. Audit licenses and split suitability for any proposed public task benchmark. Do not assume a dataset is licensed or has valid train/test splits from its name alone.
9. Create `research/PHASE1_DESIGN.md`, update `status.json` and this plan with the actual outcome, then commit and push documentation-only changes to `main`.
10. End with a clear GO / REVISE / STOP decision and list unresolved risks.

### Acceptance criteria

- M1 is the sole active candidate; M2 is frozen.
- Design is specific enough to implement without guessing.
- Contextual bandit is treated as the main falsification baseline.
- The held-out family is untouched during design-time tuning.
- No code implementation, model/API calls, training, or experiments.
- No claims of novelty or performance beyond the bounded P0.1 evidence.
- No unrelated repositories or project artifacts used.
- Report the final commit SHA, changed files, and any source-access limitations.

### Stop rule

If the design cannot identify a credible sequential-control advantage for PPO over a contextual bandit, recommend STOP for the PPO hypothesis rather than enlarging the action space, adding M2, or stacking more mechanisms.
