# Planner Latest Plan — GLEPPO Phase 2A-R1 Correctness Remediation

**Status:** REQUEST CHANGES — READY FOR EXECUTOR  
**Repository:** `yujian777555/GLEPPO` only  
**Reviewed main:** `315796399116c4e1ec540f42d3e78a061043fb7e`  
**PC1 status:** NOT APPROVED / NOT EXECUTED  
**Controller status:** No PPO, Q-learning, or bandit controller may be implemented or trained yet.

## Independent review result

See `research/PC1_INDEPENDENT_REVIEW.md`. The environment skeleton is useful, but PC1 cannot be approved because:
1. A/B/C checkers do not verify actual answer correctness against gold.
2. The proposed 80-state PC1 plan conflicts with Phase 1's ≥100-state guard.
3. `r_hat` and `Q_hat` currently compare different reward definitions.
4. The cache/seed path does not implement independent Monte Carlo replicates or the claimed common-random-number comparison.
5. Train/validation template IDs are not genuinely disjoint templates.
6. The three diversity features store Jaccard similarity where Phase 1 specifies distance.
7. The 47,200-slot budget omits initial-population evaluations and does not separate planned slots from actual CTX/model calls.

This is a methodology/evaluator correctness block, not a rejection of the GLEPPO hypothesis.

## Executor prompt (copy verbatim)

You are the Executor for the independent GLEPPO research project. The only user project repository you may modify is `yujian777555/GLEPPO`. Do not access, import, copy, or mix code, data, results, plans, or status from any unrelated user project. Do not copy GLEET code.

### Objective

Resolve every blocking finding in `research/PC1_INDEPENDENT_REVIEW.md` before any production G3 or PC1 run. This is a correctness-remediation task, not a controller-training task.

### Required tasks

1. **Evaluator correctness:** rewrite Family A/B checkers to compare normalized final answers against gold; rewrite Family C checker to parse JSON and verify actual values/constraints, not just key presence. Gold must remain evaluator-only. Add positive and adversarial negative tests for wrong arithmetic, wrong string transforms, wrong JSON values, malformed JSON, and correct answers.
2. **Template validity:** make template IDs correspond to actual different prompt/input generation rules. Ensure train and validation template sets are disjoint. Regenerate manifests, record new full SHA256 digests, and explain that this occurs before any controller training. Do not execute Family C.
3. **Feature semantics:** change the three registered diversity features to actual Jaccard distance (or submit an explicit reviewed schema amendment to similarity semantics). Add tests for identical/disjoint/partial overlap.
4. **Deterministic seeds:** replace Python built-in `hash(task_id)` in evolution seeding with a stable SHA256-derived seed. Add a subprocess test proving repeatability across different `PYTHONHASHSEED` values.
5. **PC1 replicate/cache/CRN path:** distinct Monte Carlo replicates must not reuse cache results; paired action comparisons must use the declared common random seeds across actions while distinct replicates use distinct seeds. Cache keys must account for effective replicate/seed and runtime/model revision. Record cache hits separately and never count a cache hit as a new sample.
6. **Reward identity:** `r_hat(s,a)` and the first-step reward used in `Q_hat(s,a)` must use exactly the same frozen reward function, including all terms and clipping. Define Q as the h-step return under the fixed random continuation policy.
7. **Budget amendment:** revise `research/PHASE2_PREFLIGHT.md` with an explicit counting-unit table, initial-population costs, random and heuristic state-collection costs, invalids/cache accounting, operator-proposal calls, model completions/tokens, and a hard cap. Do not claim the original registration allowed 80 states. The candidate 100-state / 3-rollout / h=3 / one extra immediate draw / 40 source-episode design in the independent review may be evaluated, but do not adopt it without documenting the rationale.
8. **Production smoke gate:** only after the evaluator tests and template/manifest fixes pass, deploy the exact model/backend in a new runtime-lock revision, record device/dtype/quantization/revisions, run a small A/B smoke test, re-run G3, and measure actual LLM calls/tokens/latency. No Family C execution.
9. **Review loop:** update tests, `research/PC1_INDEPENDENT_REVIEW.md` remediation table, `status.json`, and this plan with actual evidence. Commit and push. Do not self-mark PC1 approved; request a second independent review.

### Forbidden

- No PC1 execution.
- No PPO, Q-learning, or bandit controller implementation/training.
- No Family C execution or tuning.
- No invented results, tokens, or costs.
- No third mechanism, no M2, no GLEET code reuse, no cross-project artifacts.

### Acceptance criteria

- Every R1–R7 finding has a code-level fix and regression test or an explicit reviewed protocol amendment.
- Actual answer correctness is enforced by the evaluator.
- The split manifest is regenerated and verifies; train/validation templates are truly distinct.
- PC1 reward/CRN/cache semantics are statistically coherent and reproducible across processes.
- Cost cap is arithmetically correct and includes initialization plus state collection; model-call/runtime ceilings are separately measured.
- All relevant tests pass; Family C remains untouched.
- Report commit SHA, changed files, test output, full manifest digests, production smoke measurements, and unresolved risks.

### Stop rules

If actual scoring cannot be made reliable, do not proceed. If the amended PC1 is infeasible or inconclusive under the declared cap, apply SR1 and stop the PPO hypothesis. Do not relax thresholds after seeing PC1 results or stack mechanisms to rescue a failed hypothesis.
