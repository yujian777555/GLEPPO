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
