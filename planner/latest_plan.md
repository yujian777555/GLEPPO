# Planner Latest Plan — GLEPPO Second Review

**Status:** REQUEST CHANGES. PC1 is not approved and has not been executed.  
**Reviewed commit:** `a272a453c1147d9b2fd194c04806ba0a4dac8cdc`  
**Review record:** [research/SECOND_REVIEW_FINDINGS.md](../research/SECOND_REVIEW_FINDINGS.md)

## Findings

1. The evaluator appends the genotype behavior hash to the effective seed even when a common random seed is supplied, so paired action comparisons do not actually share seed inputs.
2. Actual execution counters do not consistently subtract cached evaluation bundles containing multiple replicas.
3. The smoke report's 96 slots count offspring only; including initialization gives 128 planned slots for the recorded configuration.
4. Runtime lock seed rules still document built-in hash-based seeds instead of the SHA256 rules in code.
5. StubLLM does not correctly solve every generated Family A template. Stub success scores are not task-performance evidence.
6. The PC1 module has helpers but lacks a complete state-sampling, rollout, cluster-bootstrap and raw-evidence runner.

## Next executor task

- Fix the common-random-number seed path and test effective seeds through an instrumented evaluator.
- Correct actual CTX/cache accounting and smoke planned-slot reporting.
- Update the runtime lock to match code.
- Test StubLLM against every generated template or quarantine its success scores as non-evidence.
- Implement and test the PC1 runner without executing PC1.
- Update status and evidence, push to `main`, and request another independent review.

## Forbidden until approval

- Do not execute PC1.
- Do not run production-model G3 or smoke before the runtime is pinned and deployed.
- Do not access or tune against Family C.
- Do not implement/train PPO, Q-learning or bandit controllers.
- Do not introduce M2 or another mechanism, copy GLEET code, or fabricate results.

PC1 may proceed only after a later independent review approves the protocol and the production smoke/G3 gate is complete. If PC1 is eventually inconclusive at the hard cap, apply SR1 and stop the PPO hypothesis.
