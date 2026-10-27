# Third Independent Review Findings — Phase 2A-R2

**Reviewed commit:** `f329a45e91b8011a42e6cc3fee49817da940966b`  
**Review date:** 2026-10-27  
**Review type:** read-only source audit. The reviewer did not execute repository tests or experiments.  
**Verdict:** **REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED.**

The R8 evaluator-seed tests and R9 evolution-loop accounting are meaningful improvements, and the smoke planned-slot arithmetic is now correct (32 init + 96 offspring = 128). However, the PC1 analysis/accounting path still contains correctness gaps and is not yet a complete registered experiment runner.

## R12 — PC1 BudgetLedger still mixes bundle hits and replica counts (BLOCKER)

**Evidence:** `gleppo/pc1.py:BudgetLedger.record_generation` and `record_init`.

- `record_generation` computes `actual_ctx += valid * n_eval - cache_hits`. Here `cache_hits` is defined elsewhere as a count of **bundles**, where one bundle represents `n_eval` replicas. Subtracting one bundle from a replica count is dimensionally wrong.
- `record_init` computes `actual_ctx += actual - cache_hits`, with the same unit mismatch if `actual` is a replica count and `cache_hits` is a bundle count.
- The new R9 tests cover `Evaluator` and `EpisodeResult`, but do not cover `BudgetLedger`; the stale logic remains.

**Required fix:** pass actual uncached replica-execution deltas into the ledger directly (preferred), or convert bundle hits to replica units consistently. Add tests for init and generations with `n_eval=2`, cache hits, invalid offspring, and a shared evaluator. Do not infer actual CTX from planned slots or bundle counts.

## R13 — PC1 estimator does not fail closed on incomplete/malformed records (BLOCKER)

**Evidence:** `gleppo/pc1.py:compute_r_hat`, `compute_q_hat`, `_per_state_stats`, `run_pc1_analysis`.

- `_per_state_stats` fills missing actions with a default value of `0.0`. Missing actions can therefore affect argmax selection rather than causing the analysis to reject incomplete data.
- The analysis does not enforce the registered shape: at least 100 distinct states, all 5 actions per state, the required Q-rollout count, and the required horizon-3 traces.
- `compute_q_hat` accepts short or empty traces; there is no validation that each Q record has exactly `HORIZON=3` reward values.
- `by_state = {rec.state_id: rec.cluster_id ...}` silently overwrites cluster membership if one state ID occurs under multiple cluster IDs.
- No guard checks that each state-action has the expected independent sample count or that replicate/rollout IDs are unique where required.

**Required fix:** validate record schema and coverage before computing statistics; reject missing actions, duplicate/conflicting state-cluster assignments, malformed reward traces, insufficient states/replicates, and empty cluster sets. Never substitute zeros for missing action estimates. Add negative tests for every rejection case.

## R14 — The planned extra immediate-reward draw is not represented separately (BLOCKER)

**Evidence:** protocol constants `EXTRA_IMMEDIATE=1` and the `StateActionRecord` schema / `compute_r_hat` / `compute_q_hat`.

The 45,440 planned-slot budget includes 4,000 extra immediate-reward slots. However, records have no sample-role field to distinguish Q-rollout records from extra immediate-only draws. `compute_r_hat` averages the first reward from every record; `compute_q_hat` also consumes every record, including any short extra-immediate record if one is supplied. This means the budget and estimator do not currently describe a consistent sampling plan.

**Required fix:** add a registered sample role (for example `q_rollout` versus `extra_immediate`) and explicit validation. Use Q-rollout records for `Q_hat`; use the intended registered set of first-step rewards for `r_hat`. If the protocol intends a different estimator, stop and obtain a planner decision before changing it. Reconcile the budget arithmetic with the actual planned sampling procedure.

## R15 — PC1 collection/rollout execution is not implemented

**Evidence:** `gleppo/pc1.py:run_pc1_analysis`.

The current function analyzes a list of preconstructed `StateActionRecord` values; it does not collect 100 states, execute the 5 candidate operators, perform the 3-rollout/horizon-3 comparisons, or invoke the evaluator. It is an analysis function, not a complete experiment runner.

The record schema has no task-family field, and the analysis function does not apply a `FamilyCGuard` or verify that records originate only from training-family A/B data. It also does not invoke or verify the CRN seed path. The registered PC1 experiment therefore cannot yet be run through an auditable, guarded code path.

**Required fix:** implement the data-collection/rollout orchestration as a separate, explicitly non-launched entry point. It must enforce A/B-only input and Family-C guard, create the required state/action/rollout/replicate records, pass paired CRN metadata through the actual evaluator, respect the hard planned-slot cap before executing each unit, and produce a deterministic dry-run plan. Tests must use synthetic fixtures only; do not launch registered PC1.

## R16 — CRN helpers and evaluator API are not one authoritative seed path (BLOCKER)

**Evidence:** `gleppo/pc1.py:crn_seed`, `replicate_seed`; `gleppo/evaluator.py:Evaluator.evaluate`; `docs/RUNTIME_LOCK.md` §2.1; `research/PHASE2_PREFLIGHT.md` §11.

- `Evaluator.evaluate` does not use the supplied `eval_seed` to construct the interpreter RNG seed; `eval_seed` affects the cache key, while the actual seed is built from `state_id/task_id/rollout_id/replicate_id/replica_index`.
- The `crn_seed` and `replicate_seed` helpers in `pc1.py` are not wired into a PC1 collector. `replicate_seed` includes the action ID, which would break paired evaluation randomness if used as the evaluation replicate seed.
- The evaluator cache key uses `eval_seed` instead of including `state_id` and `rollout_id` when `eval_seed` is supplied, even though those values still affect the actual RNG seed. Reusing the same explicit `eval_seed` for the same genotype/task/replicate under different state/rollout IDs can therefore return a cached result produced under different effective seed inputs.

**Required fix:** define one seed contract and use it consistently. Separate action-specific proposal randomness from paired environment/evaluation randomness. Ensure the cache key includes every input that affects effective evaluation seeds. Add tests for same CRN across actions, distinct rollout/replicate IDs, explicit-seed consistency, and cache separation across different state/rollout tuples.

## R17 — Raw PC1 evidence is not sufficient for independent replay (BLOCKER)

**Evidence:** `run_pc1_analysis` output `raw_evidence`.

The emitted evidence includes aggregate estimates and summary rows but omits the complete input records and their family, cluster, CRN seed, rollout/replicate IDs, per-record reward traces, input/manifest hashes, evaluator/runtime revisions, and actual counter breakdown. The `crn_seed` field on `StateActionRecord` is not included in the output.

**Required fix:** write a replayable raw artifact containing the exact sanitized input records, manifest/input hashes, protocol/runtime/evaluator versions, seed hierarchy, cluster assignments, sample roles, reward traces, per-record slot/CTX/cache/invalid counters, aggregate statistics and bootstrap configuration/seed. Do not include gold labels in controller-visible state; the audit artifact may only include fields permitted by the registered protocol. Keep Family C untouched.

## R18 — Cost baseline still contains contradictory old values

**Evidence:** `research/COST_BASELINE.md`.

The R2-revised §2 reports 112 actual replicas and 0.021 seconds, but §5 still reports 96 as agent execution CTX and 0.012 seconds. §4 and §6 still refer to 47,200 for PC1, while the active v2 protocol/code budget is 45,440 planned slots. These are not the same units and must not be presented interchangeably.

The Executor's reported “String to replace not found” indicates one attempted exact replacement did not apply. The file must be corrected by editing the actual current section, not by assuming the failed replacement succeeded.

**Required fix:** reconcile all repeated figures against `SMOKE_RAW.json` and the active v2 amendment. Label the 96 figure only as offspring planned slots, 128 as total smoke planned slots, 112 as actual uncached replica executions, 0.021 seconds as the current recorded smoke wall-clock, and 45,440 as PC1 planned slots (not measured actual CTX or model cost). Mark all production token/latency/cost values UNMEASURED.

## Required remediation order

1. Fix R12 BudgetLedger units and add direct tests.
2. Fix R13 validation / fail-closed behavior.
3. Resolve R14 sample-role semantics and align the sampling plan with the budget.
4. Implement the guarded PC1 data-collection/rollout entry point without executing it.
5. Unify R16 seed/CRN/cache-key semantics end-to-end.
6. Make R17 raw evidence replayable.
7. Correct R18 cost documentation.
8. Run focused tests, full tests, manifest verification and synthetic-only PC1 tests; report actual command outputs.
9. Update status and request another independent review. Do not self-approve.

## Forbidden until further approval

- Do not execute the registered PC1 experiment.
- Do not access or execute Family C tasks or outcomes.
- Do not deploy/run production-model smoke or G3 while the production backend is pending and the runtime/cost gate is incomplete.
- Do not implement/train PPO, Q-learning or bandit controllers.
- Do not copy GLEET code or add another research mechanism.
- Do not fabricate test, model-call, cost or approval evidence.

## Final decision

**REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED.** R8/R9 evolution-loop improvements are acknowledged, but the remaining BudgetLedger, estimator validation, sampling-role, CRN integration, raw-evidence and cost-documentation issues must be resolved before a further review.

---

# Remediation Log (Executor, 2026-10-27 Phase 2A-R3)

**Base commit (third review):** `f329a45e91b8011a42e6cc3fee49817da940966b`
**PC1 status:** NOT EXECUTED / NOT APPROVED. This log does NOT self-approve.

| Finding | Fix | Evidence |
|---|---|---|
| **R12** BudgetLedger mixes bundle/replica units | `record_evaluation`/`record_init` receive explicit `replicas_run_delta` from evaluator counters; no `valid*n_eval - cache_hits` arithmetic | `gleppo/pc1.py:BudgetLedger`; `TestR12BudgetLedger` (6 tests) |
| **R13** estimator does not fail closed | `validate_records` rejects: missing actions, wrong horizon, non-finite rewards, cluster conflicts, duplicate keys, invalid action/role, negative counters, missing seeds; `_per_state_stats` raises on missing actions (no 0.0 default) | `TestR13FailClosed` (10 tests) |
| **R14** extra immediate draws unrepresented | `sample_role` field (`q_rollout`/`extra_immediate`); `Q_hat` uses only q_rollout; `r_hat` = Q-first + extra (estimator per PC1_INDEPENDENT_REVIEW); extra cannot pollute Q_hat | `TestR14SampleRoles` (3 tests) |
| **R15** no collection/rollout runner | `generate_pc1_dry_run_plan()` emits full schedule (2040 units); `execute_registered_pc1()` refuses execution; FamilyCGuard at eval boundaries | `TestR15DryRunPlan` (4 tests) |
| **R16** seed/CRN/cache inconsistency | `eval_seed` now authoritative for RNG (not cache-only); cache key includes state_id+rollout_id+replicate_id+eval_seed+genotype+runtime; operator RNG separate | `TestR16SeedContract` (7 tests) |
| **R17** evidence not replayable | `raw_evidence` includes full sanitized records (family, cluster, seed parts, reward traces, counters), manifest hash, runtime/evaluator versions, bootstrap config, replay command | `TestR17Evidence` (3 tests) |
| **R18** cost report contradictions | 47,200 replaced with 45,440; 0.012 s latency fixed to 0.021 s stub; 96 labeled as offspring-only planned slots; consistency check PASS | `research/COST_BASELINE.md` |

## Test evidence (2026-10-27)

- **Full unit suite: 97/97 PASS** (37 core + 25 R8/R9/R11/PC1 + 35 R12-R17)
- **Zero-cost protocol check: PASS** (45,440 <= 50,000)
- **Dry-run plan: within_cap=True, total=45,440, schedule=2040 units**
- **Manifest verification: OK** (digests unchanged)
- **Smoke: planned_init=32, planned_offspring=96, planned_total=128, actual=112, slot_arithmetic_ok=true**
- **Cost documentation consistency: PASS**

## PC1 execution status

`execute_registered_pc1()` raises `PC1ExecutionRefused`. Registered PC1 is NOT APPROVED and NOT EXECUTED. Only dry-run plan generation and synthetic analysis tests were run.

## Open blockers

1. Production backend PENDING_DEPLOYMENT.
2. Fourth independent review required.
3. C4 literature collision re-check outstanding.

## Request

Independent review of this remediation. Executor does NOT mark PC1 approved or executed.
