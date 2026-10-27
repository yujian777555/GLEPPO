# Planner Latest Plan — GLEPPO Phase 2A

**Status:** READY FOR EXECUTION  
**Repository:** `yujian777555/GLEPPO` only  
**Active candidate:** M1 ECOS. M2 FMPS remains frozen.  
**Current state:** Phase 1 design accepted; implementation and experiments have not started.

## Planner's independent audit of Phase 1

The Phase 1 design and reported commit `f537032999412b7635f580a1eab9a7e927ae04f9` are present on `main`. The overall GO-to-Phase-2 decision is accepted, but implementation must not blindly copy every numerical instruction before resolving:

1. **PC1 cost contradiction:** 200 states × 5 actions × 20 rollouts × 5 steps × λ=4 × n_eval=3 implies up to 1.2 million candidate-task executions, while the design sets a 50,000-episode diagnostic guard if episode means candidate-task execution.
2. **State vector packing:** the declared 32 dimensions (12+12+8) are not yet supported by one exact feature table; enumerated feature counts and operator-history packing are ambiguous.
3. **Operator/runtime lock:** `prompt_local_edit` has an unresolved 0-or-1 proposal-call path, and the exact model/backend revision must be pinned before real execution.

These are design/implementation consistency gaps, not evidence that the research idea failed. Phase 2 must resolve them transparently before expensive runs.

## Executor prompt (copy verbatim)

You are the Executor for the independent GLEPPO project. The only user project repository you may modify is `yujian777555/GLEPPO`. Do not access, import, or mix code, data, experiment results, plans, or status from any unrelated user project. Public papers and official research repositories may be inspected as sources, but do not copy GLEET code.

### Objective

Implement the minimal ECOS environment and verify genotype causality, reproducibility, data isolation, and measured runtime cost. Do not train PPO until the amended PC1 myopia diagnostic has passed.

### Required tasks

1. Read `docs/PHASE2_IMPLEMENTATION_PROTOCOL.md`, `research/PHASE1_DESIGN.md`, `docs/PROJECT_CHARTER.md`, and P0.1 artifacts. Preserve P0.1 C1–C5 and Phase 1 PC1/SR1–SR5.
2. Create `research/PHASE2_PREFLIGHT.md` before any expensive run. Recalculate PC1's execution count, define counting units, propose a statistically defensible diagnostic under a hard cost cap, and record every deviation from the Phase 1 registration. Do not run PC1 until this amendment is reviewed.
3. Resolve the state-vector packing in a canonical feature table with exact dimensions, sources, normalization, timing, and missing-value behavior. State the dimension sum explicitly and test it.
4. Create `docs/RUNTIME_LOCK.md` pinning the exact model/checkpoint, tokenizer, inference backend/version, decoding, seeds, tools, timeouts, and hardware/quantization before real model execution. Freeze the operator call count for every operator.
5. Implement the declarative genotype, interpreter, five operators, task generators, evaluator, evolution loop, and hash-frozen manifests, all in GLEPPO only.
6. Add unit and integration tests for schema, canonical serialization, genotype hashes, behavior traces, evaluator-label isolation, manifest verification, seed reproducibility, reward arithmetic, and invalid-offspring accounting.
7. Run the G3 causality gate on train-family tasks only; every retained operator must show a reproducible observable behavior change. Revise a no-op operator once; if no valid five-operator library results, stop and report.
8. Run only a small training-family smoke test to measure real runtime and cost. Record exact calls/tokens/episodes/latency/failures in `research/COST_BASELINE.md`; do not fabricate costs and do not touch Family C.
9. After preflight review, G3, manifest freeze, and smoke-cost review, run PC1 only under the approved amended protocol. Report D, non-myopic advantage, uncertainty, exact counts, and SR1 decision.
10. Do not implement or train PPO, Q-learning, or bandit controllers in this task. The next plan will authorize them only after PC1 passes. Baseline implementation can be proposed separately if needed.
11. Update `status.json` and this plan with actual outcomes, tests, hashes, and evidence. Commit and push to `main`.

### Acceptance criteria

- Documentation explicitly resolves PC1 cost arithmetic and state feature dimensions.
- Runtime lock precedes real model execution.
- G3 causality and manifest-integrity checks pass or the report recommends a stop/revision.
- Only train/validation families are used; Family C remains untouched.
- Smoke costs are measured, not guessed.
- PC1 is not run until its amendment is reviewed.
- No controller training, no performance claims, no GLEET code reuse, no cross-project contamination.
- Report commit SHA, files changed, tests run, exact execution counts, and unresolved risks.

### Stop rules

- If no credible sequential-control advantage is found by PC1, STOP the PPO hypothesis (SR1).
- If the revised PC1 protocol cannot be made statistically meaningful within a defensible cap, STOP or return for a design decision; do not exceed the cap silently.
- If G3 fails after one operator-library revision, stop and report.
- If held-out C is accessed during development/tuning, invalidate the split and stop to rebuild the manifest.
- No third mechanism or action-space expansion to rescue a failed hypothesis.
