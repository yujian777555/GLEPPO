# Fourth Independent Review Findings — Phase 2A-R3

**Reviewed commit:** `4c727997a71d4eb1cd34c1612fe1d275009d859f`  
**Review date:** 2026-10-27  
**Review type:** read-only source/protocol audit. Reviewer did not execute repository tests or experiments.  
**GitHub CI evidence:** no combined status checks or PR-triggered workflow runs were returned for this commit. The reported 97/97 test result is therefore recorded as Executor-reported, not independently reproduced.  
**Verdict:** **REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED.**

## Improvements acknowledged

- R12's `BudgetLedger` now receives explicit evaluator replica-execution deltas instead of subtracting bundle hits from replica counts.
- R13 rejects several malformed records and no longer fills missing actions with zero.
- R14 has explicit `q_rollout` and `extra_immediate` roles.
- The dry-run arithmetic 36,000 + 4,000 + 5,440 = 45,440 is correct.
- The registered execution function refuses to launch PC1.
- The smoke raw record explicitly reports 32 initialization slots + 96 offspring slots = 128 total planned slots and 112 actual replicas.

These improvements do not close the following blockers.

## R19 — The protocol / estimator is not formally frozen (BLOCKER)

**Evidence:**
- `gleppo/pc1.py` declares `PROTOCOL_VERSION = "pc1-amendment-v3-r3"` and `ESTIMATOR_VERSION = "est-v1-r_hat=q_first+extra,q_hat=q_rollout_only"`.
- `research/PHASE2_PREFLIGHT.md` still labels the active document amendment as **v2**. Its earlier §3.3–§3.5 text continues to state the historical 80-state / 4-rollout design and an older immediate-reward description, while the v2 amendment says those sampling numbers are superseded.
- `research/PC1_INDEPENDENT_REVIEW.md` explicitly calls the 100-state / 3-rollout / extra-immediate estimator a **proposed amendment, not an approved experiment protocol**.
- `planner/latest_plan.md` currently says the R14 estimator is “confirmed unambiguous,” which overstates the approval status of that proposed amendment.

**Required fix:**
1. Create one canonical, versioned protocol revision that explicitly supersedes the historical v1 sections and agrees with code constants.
2. Record the estimator formula, sample roles, sample counts, cluster unit, seed contract, and complete budget arithmetic in that canonical revision.
3. Record explicit Planner/protocol approval of the amendment before any registered PC1 data collection. Do not describe the proposal as already frozen/approved.
4. Add a protocol-consistency test that checks the code version, active protocol version, N_STATES, Q_ROLLOUTS, HORIZON, EXTRA_IMMEDIATE, and budget constants.

## R20 — CRN override still does not guarantee task/replicate seed separation (BLOCKER)

**Evidence:** `gleppo/evaluator.py:Evaluator.effective_seed_parts` and `gleppo/pc1.py:crn_seed`.

When `eval_seed_override` is supplied, the evaluator returns only:
`("SEED_OVERRIDE", eval_seed_override, str(replica_index))`.
It intentionally drops `state_id`, `task_id`, `rollout_id`, and `replicate_id` from the effective seed tuple. The caller is documented as responsible for uniqueness.

However, the PC1 helper `crn_seed(state_id, rollout_id)` only hashes state and rollout. It has no task ID or outer replicate ID. The dry-run schedule uses this helper, and the record schema has no explicit task ID. Thus the current API contract does not itself ensure that a reused override across tasks or outer replicates produces distinct evaluation seeds.

The existing tests establish that different override strings produce different seeds and that the non-override path distinguishes state/rollout. They do not test paired CRN behavior with the actual override path while changing task ID and replicate ID.

**Required fix:**
1. Define an unambiguous override contract: either the override is a base CRN key combined with task/rollout/replicate/inner-replica fields, or the caller must provide a fully qualified tuple-derived seed.
2. Include task ID and outer replicate identity in the authoritative CRN key while excluding action/genotype.
3. Add instrumented-evaluator tests proving same task/state/rollout/replicate across actions yields identical seeds, while different task, rollout, or replicate yields distinct seeds even when using the override path.
4. Ensure the PC1 schedule and future collector use that exact tested API. Keep action/operator proposal randomness separate.

## R21 — Registered budget enforcement can be bypassed by inconsistent caller-supplied totals (BLOCKER)

**Evidence:** `gleppo/pc1.py:run_pc1_analysis`, `validate_records`, `BudgetLedger`.

- `run_pc1_analysis` rejects only when `planned_slots_total > HARD_CAP_SLOTS`; it does not reject negative totals, require the registered total, or reconcile the supplied total with record slot counts.
- `validate_records` requires at least the registered number of Q rollouts and extra samples, not the exact registered counts. Additional records can therefore be accepted even though they may exceed the planned sampling design.
- The analysis ledger is reconstructed only from `StateActionRecord` objects, whose roles are `q_rollout` and `extra_immediate`. It cannot represent the 5,440 state-collection slots, while the separate `planned_slots_total` includes those slots. The emitted evidence can therefore report one total in `budget.planned_slots` and a different total in `planned_slots_total` without reconciliation.
- There is no explicit validation that record-level planned slots and actual-replica counters are compatible with each record's sample role and registered rollout structure.

**Required fix:**
1. Reject non-positive or otherwise invalid totals and reconcile every budget component before analysis.
2. Record state-collection planned/actual counters as a separate explicit component; include them in the total without pretending they are diagnostic-rollout records.
3. For registered PC1, require the exact registered sample counts and reject surplus samples unless a formally approved protocol says otherwise.
4. Validate that per-record slot counts and counter deltas are consistent with the relevant sample role.
5. Add negative tests demonstrating that a low caller-supplied total, surplus samples, or inconsistent component totals cannot yield a decision.

## R22 — Cluster provenance is too weak for the registered bootstrap (BLOCKER)

**Evidence:** `gleppo/pc1.py:validate_records`, `generate_pc1_dry_run_plan`, and `_cluster_bootstrap`.

- Registered design specifies 40 independent state-collection episodes and a cluster bootstrap by independent task/episode.
- Validation currently requires only two distinct cluster IDs.
- The dry-run schedule lists collection episodes (`col000...`) separately from diagnostic state IDs (`s000...`); it does not assign each sampled state to a specific collection episode/task cluster.
- `StateActionRecord` contains a generic `cluster_id` and family label, but no task ID or collection-episode provenance that proves the cluster came from the registered 40-episode collection.
- The analysis therefore accepts cluster labels that cannot be traced to the planned sampling process.

**Required fix:**
1. Include task ID and source collection-episode ID in the state/record provenance.
2. Emit an explicit state-to-episode/cluster assignment in the dry-run plan and require the collected records to match it.
3. Enforce the registered independent-cluster requirement and reject missing, unknown, or conflicting cluster mappings.
4. Add tests for insufficient clusters, unassigned states, unrecognized collection episodes, and cluster bootstrap preserving whole episode clusters.

## R23 — Raw evidence is not yet independently replayable (BLOCKER)

**Evidence:** `gleppo/pc1.py:run_pc1_analysis`, `_sanitize_record`, and `tests/test_r12_r17.py:TestR17Evidence`.

- The `raw_evidence` object omits the calculated `D`, `advantage`, `D_ci`, and `adv_ci` values, even though these are the decision-critical statistics.
- `manifest_hash`, `runtime_revision`, and `evaluator_version` have empty-string defaults; the registered analysis path does not require them to be nonempty.
- There is no explicit input-record artifact hash.
- The emitted replay command refers to `records_from_raw`, but no loader or round-trip reconstruction is provided in the reviewed module.
- Tests only assert that a `replay_command` key exists; they do not serialize the artifact, reload it, recompute the analysis, and compare outputs.

**Required fix:**
1. Include point estimates, confidence intervals, sample counts, decision, all bootstrap parameters, protocol hash, input-record hash, manifest hash, runtime/evaluator revisions, and budget-component breakdown.
2. Require nonempty provenance fields for registered analysis; synthetic test mode must be explicitly marked and cannot masquerade as registered evidence.
3. Implement a real serializer/loader/replay command that reconstructs records from a saved artifact and recomputes the same statistics.
4. Add a round-trip test asserting exact agreement for D, advantage, both CIs, sample counts, decision, and budget counters.
5. Do not expose gold labels to the controller/operator.

## R24 — Cost documentation still conflicts with the raw smoke artifact (BLOCKER)

**Evidence:** `research/SMOKE_RAW.json` totals report `wall_clock_s = 0.0188`; `research/COST_BASELINE.md` reports `0.021 s`.

The raw artifact is the evidence source, so the discrepancy must be explained by a new separately identified run or the cost report must use the raw artifact's 0.0188 s. No second raw artifact or measurement identifier was found in the reviewed files.

The cost report also still has labels that violate its own units policy:
- §4 table header is `CTX (EXT)`, and the PC1 row places 45,440 under that column even though 45,440 is a **planned-slot budget**, not measured actual CTX.
- §5 labels “Agent execution CTX (planned offspring slots)” as 96, conflating a planned quantity with actual CTX.
- §6 describes “PC1's 45,440 CTX” and uses it as if it were an actual execution count.

**Required fix:**
1. Reconcile wall-clock to the source artifact (or add the distinct raw artifact for a separately measured 0.021 s run).
2. Separate planned slots, actual replica executions, extrapolated execution estimates, and model-completion estimates in the table headings and prose.
3. Remove every claim that 45,440 is actual CTX. If using it as a conservative workload proxy for forecasting, label that explicitly as an assumption, not a measurement.
4. Add a consistency test that parses the raw artifact and checks the cost report's stated values and units, not merely that expected strings exist.

## R25 — The “collection/rollout runner” is still only a dry-run planner plus refusal (BLOCKER for future PC1 readiness)

**Evidence:** `gleppo/pc1.py:generate_pc1_dry_run_plan` and `execute_registered_pc1`.

The current module has a deterministic schedule generator and an analysis function. The registered execution entry point unconditionally raises `PC1ExecutionRefused`; it has no explicit approval-gate parameters, production-runtime gate, task loader, collection loop, evaluator invocation, rollout state updates, or artifact writer. This is a valid safety interlock, but it is not a complete gated collection/rollout runner.

The schedule's 2,040 entries are aggregate units (40 collection episodes + 1,500 Q-rollout groups + 500 extra-immediate groups), not a record of every individual generation/replica execution. It is therefore a plan summary, not yet a fully replayable execution schedule.

**Required fix:**
- Implement the collection/rollout orchestration behind explicit independent-review and production-runtime gate objects, with a default-deny behavior.
- The code path must remain unlaunchable in this phase because the review approval and production backend are absent; unit-test the gate and orchestration using fake/synthetic components only.
- Add per-generation and per-replica planned unit identities so actual counter deltas can be reconciled to the dry-run schedule.
- If implementing the real gated collector is deliberately deferred, change all status/report wording to say “dry-run planner + analysis only; collection runner not implemented” and keep PC1 blocked.

## Required remediation order

1. Freeze and version the canonical protocol/estimator (R19), explicitly distinguishing proposed from approved amendments.
2. Fix the CRN override contract and tests (R20).
3. Make the budget guard fail closed and reconcile record/collection totals (R21).
4. Establish collection-episode/task cluster provenance (R22).
5. Make raw evidence round-trip replayable (R23).
6. Reconcile cost report to raw measurements and units (R24).
7. Implement a genuinely gated collection/rollout runner or accurately downgrade the completion claim (R25).
8. Run focused tests, the full unit suite, zero-cost checks, manifest verification, dry-run checks and document consistency tests. Report exact outputs.
9. Update status and request another independent review. Do not self-approve.

## Forbidden until further approval

- Do not execute registered PC1.
- Do not load, execute, or tune on Family C.
- Do not deploy/run production-model smoke or G3 while the production backend is pending.
- Do not implement/train PPO, Q-learning, or bandit controllers.
- Do not reuse GLEET code or other project artifacts.
- Do not fabricate test results, measurements, tokens, costs, or approval.

## Final decision

**REQUEST CHANGES — PC1 NOT APPROVED / NOT EXECUTED.** The R12–R18 work is a meaningful improvement, but protocol approval, CRN uniqueness, hard-budget reconciliation, cluster provenance, replayable evidence, cost-source consistency, and the actual gated collection/rollout runner remain unresolved.
