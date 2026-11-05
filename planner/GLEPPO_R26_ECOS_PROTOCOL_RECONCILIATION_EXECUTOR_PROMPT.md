# GLEPPO R26 — ECOS Protocol Reconciliation (Documentation-Only Executor Task)

**Project:** GLEPPO only  
**Repository:** `yujian777555/GLEPPO`  
**Branch:** `r25-handoff` only  
**Prior accepted gate:** R26 Stage 1I-R2.1.1  
**Accepted R2.1.1 work commit:** `362f343f43befc7f43c00ba5edd1059b01d523d1`  
**Planner acceptance report:** `research/R26_STAGE1I_R2_1_1_PLANNER_REVIEW.md`  
**Main:** `6bad0b77835a2d00c62287c0c7d9d91d1d186d5e` (must remain unchanged)  
**Task status:** DOCUMENTATION-ONLY; no experiment or training authorization.

## 1. Role and objective

You are the Executor. The Planner will independently review your outputs. Do not self-approve.

Reconcile the ECOS research and implementation protocol drift across:

1. Phase 1 design;
2. R24 controller preregistration;
3. PC1 R4 proposed diagnostic protocol;
4. the currently committed shared implementation and its tests;
5. the R26 scientific-integrity review and current status/gates.

The objective is to create one coherent, versioned, machine-readable and human-readable **proposed** ECOS contract, while preserving all historical documents and accurately recording unresolved choices.

This is not an implementation phase. Do not modify production code, tests, data, frozen protocols, historical experiment records or manifests.

## 2. Git preflight

Before reading or editing:

- Re-fetch origin and verify the current branch is exactly `r25-handoff`.
- Verify current HEAD is a descendant of `362f343f43befc7f43c00ba5edd1059b01d523d1`.
- Record current branch HEAD and `main` HEAD, ahead/behind relation, and worktree state.
- Do not checkout or update `main`; do not reset, rebase, force-push, or overwrite uncommitted work.
- Keep all new artifacts in this repository and branch.

## 3. Read these sources first

### Canonical/history documents

1. `status.json`
2. `research/PHASE1_DESIGN.md` — especially §§2–5, 3.1–3.6, 4, 5, 6 and 9
3. `research/R24_ECOS_CONTROLLER_PREREGISTRATION.md`
4. `research/PC1_PROTOCOL_R4_PROPOSED.md`
5. `research/R26_ECOS_SCIENTIFIC_INTEGRITY_REVIEW.md`
6. `research/R26_PC1_AUDIT_SUMMARY.md`
7. `research/R23_STATIC_REASSESSMENT.md`
8. `planner/GLEPPO_R24_HANDOFF.md`
9. `planner/GLEPPO_R24_CORRECTIVE_AUDIT_PROMPT.md`
10. `research/G3_DIAG_R3_PROTOCOL.md`

### Active implementation and tests (read-only)

11. `gleppo/reward.py`
12. `gleppo/evolution.py`
13. `gleppo/pc1.py`
14. `gleppo/evaluator.py`
15. Actual controller implementation files discovered in this branch (do not assume a path or infer that a controller exists).
16. Relevant existing tests for reward, state construction, operator application, seeds/CRN, PC1 estimator inputs, split isolation, budget accounting and controller interfaces.

Record exact file paths and line ranges. Distinguish a document's stated contract, current source behavior, test evidence, and Planner/Executor interpretation.

## 4. Required reconciliation dimensions

Create an evidence-backed discrepancy matrix. For every row, include: source value, exact citation (file:line), implementation value, conflict/compatibility status, proposed canonical decision, rationale, implementation gap, and whether the decision requires a later amendment or code change.

### A. Decision and execution units

Define without ambiguity:

- one operator decision;
- one generation;
- one evolution episode;
- one task instance;
- one evaluation replica;
- one rollout and rollout horizon;
- one PC1 state-action record;
- one candidate-task execution / CTX slot;
- model call, token, wall-clock and GPU-hour accounting.

Explain how these units nest and which budget ledger counts each. Do not use “episode”, “rollout”, “evaluation”, “replica”, “CTX” or “slot” interchangeably.

### B. State contract

Reconcile the Phase 1 32-dimensional state with R24's high-level description and PC1's state/action record schema.

For each feature specify:

- stable name and index;
- formula and units;
- observation source;
- decision-time availability;
- update timing;
- missing-value and clipping semantics;
- normalization constants or fitting source;
- whether it can leak task identity, gold labels, future outcomes, or evaluation-only data.

Do not invent missing feature definitions. If the exact 32-D vector is not fully implemented or cannot be reconstructed from committed evidence, mark the unresolved dimensions explicitly and propose the minimum safe resolution. State whether the current PC1 state is identical to the controller state or only a diagnostic projection.

### C. Action contract

Reconcile the five operator IDs, names and exact semantics across Phase 1, R24 and source. Confirm whether exactly one operator is selected per generation and applied to all `lambda` offspring, and identify any exceptions/fallbacks. Distinguish operator-generation RNG from evaluation RNG. Do not expand the action space to rescue the PPO hypothesis.

### D. Reward contract

There is a known material conflict:

- Phase 1 and active shared code describe generation reward based on `Δbest`, `valid_rate`, and `Δmean`, clipped to [-0.5, 1.0].
- R24 describes immediate `effective_success(child) - effective_success(parent)`.
- PC1 R4 imports and uses the shared generation reward for its estimators.

Verify the exact source and call paths. Decide whether the canonical objective is one shared reward or whether distinct rewards are scientifically justified for separate roles. If separate, define the mapping and explain why the PC1 myopia diagnostic still tests the controller's actual objective rather than a surrogate.

Do not silently choose the current implementation merely because it exists. Conversely, do not replace the current objective without explaining the scientific and implementation consequences. Preserve R24 as historical; do not edit it.

### E. Discounting and PPO/return calculation

Reconcile:

- Phase 1 `gamma`;
- R24 `gamma` and GAE `lambda`;
- PC1 R4 `gamma`;
- active `gleppo.reward.GAMMA` and all estimator/return call sites;
- PPO architecture, rollout length, advantage normalization, clipping, entropy/value coefficients, optimizer and update cadence, but only where committed evidence exists.

Specify one proposed `gamma` and GAE `lambda`, or mark unresolved with a precise reason. Ensure the PC1 continuation-value calculation and the controller's training return use compatible reward/discount semantics.

### F. Train / validation / confirm / held-out split

Reconcile:

- Phase 1: Train A+B, validation A_val/B_val, Family C held out;
- R24: 4 train / 4 validation / 4 confirm tasks, 3 seeds each;
- PC1 R4: training-family diagnostic only;
- any actual committed task manifests and seed lists.

Provide an explicit task/family identity table if committed evidence permits. Explain whether R24 confirm is equivalent to Phase 1 Family C; do not assume it is. Specify which data may be used for controller fitting, hyperparameter selection, PC1 diagnostics, final confirmation and one-time held-out evaluation.

Do not load, inspect gold labels from, execute or tune on Family C. If task identity or manifest provenance is missing, record it as a blocker rather than fabricate it.

### G. Baselines and ablations

Reconcile Phase 1's baseline suite with R24's smaller list. Propose a tiered comparison plan:

- minimum core controls needed to test adaptive selection vs fixed strategy;
- competent rule baseline;
- identical-state contextual Bandit baseline(s), especially LinUCB;
- sequential RL comparison(s), including PPO and Q-learning only if still justified;
- random baseline;
- FM rewrite/external strategy and state/reward/operator ablations.

For every baseline specify identical state access, action set, initialization, seeds, offspring/evaluation budget, stopping rule and model-call/token accounting. Distinguish mandatory from optional; justify any deferral. Do not claim R21-C1 is an operator/controller comparison.

### H. Outcomes and statistical analysis

Separate:

1. controller training reward;
2. PC1 myopia diagnostic endpoints (including disagreement D and continuation-advantage estimates);
3. primary held-out Agent task-performance endpoint;
4. secondary answer/format/tool-path/constraint metrics;
5. hard validity and safety failures;
6. cost and efficiency metrics.

Reconcile `Succ_C(best)`, `Succ_C(mean)`, `effective_success_rate`, answer correctness, format compliance, tool-path validity and PC1 D/advantage. Define the primary estimand, analysis unit, paired comparison, confidence interval, multiplicity correction and minimum practically meaningful effect. Do not collapse these into one opaque score.

### I. Budget ledgers

Keep separate:

- equalized candidate-task evaluation budget (e.g. T × lambda × n_eval);
- R24 episode/GPU-hour/model-call/token/wall-clock limits;
- PC1 planned evaluation slots and hard cap (R4 currently states 45,440 planned slots / 50,000 cap);
- controller-training compute;
- operator LLM calls, if any.

Verify arithmetic from source and document. Identify any double counting, omitted initialization, planned-vs-actual CTX distinction, cache-hit accounting and budget guard gaps. Never add incomparable budget units into one total.

### J. Seeds and reproducibility

Reconcile the R39/R20 situation explicitly:

- `gleppo/pc1.py::crn_seed`;
- `gleppo/evaluator.py::Evaluator.effective_seed_parts`;
- every call site that supplies the evaluation seed;
- base override semantics (absent, empty, value);
- task/state/rollout/replicate/replica fields;
- action/genotype exclusion for paired evaluation;
- separate action/operator-specific RNG;
- cache-key identity and paired-seed tests.

Do not claim a shared canonical CRN implementation if source still contains two independent serialization paths. Propose one typed, versioned seed schema and list exact implementation/tests needed in a later approved code phase. Do not modify source or tests now.

### K. Stop rules and gates

Reconcile Phase 1 SR1 and PC1 R4's PASS/FAIL/INCONCLUSIVE rules with R24's budget/no-improvement/validation-degradation stopping rules.

Specify:
- what stops the PPO hypothesis;
- what yields inconclusive and whether it permits another diagnostic;
- what stops a training run;
- what constitutes validation degradation;
- what requires a protocol amendment;
- what gates precede PC1, controller training and held-out confirmation.

No post-hoc threshold changes. No gate may be treated as passed merely because its report is labelled ready.

## 5. Required deliverables

Create these new artifacts; do not overwrite the historical source documents:

1. `research/R26_ECOS_PROTOCOL_RECONCILIATION.md`
   - executive decision;
   - source inventory and exact line citations;
   - full discrepancy matrix;
   - decision-by-decision rationale;
   - unresolved blockers;
   - implementation changes deferred to later stages;
   - explicit statement of what is and is not authorized.

2. `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.md`
   - complete proposed human-readable contract;
   - all sections A–K above;
   - exact version and date;
   - status must be **PROPOSED / NOT APPROVED**.

3. `research/ECOS_CANONICAL_PROTOCOL_R1_PROPOSED.json`
   - machine-readable mirror of the proposed contract;
   - explicit schema version;
   - no undocumented defaults;
   - units and provenance references for every parameter;
   - unresolved values represented explicitly (not guessed);
   - deterministic serialization.

4. Update `status.json`, `planner/latest_plan.md` and `planner/GLEPPO_R26_HANDOFF.md` with the new phase, reviewed base SHA, deliverables, blockers, hard gates and next Planner review. Keep the accepted R2.1.1 decision and historical SHA chain intact.

5. Add a next-session handoff prompt only if necessary; do not create duplicate prompts.

## 6. Non-negotiable restrictions

- No production source changes.
- No `tests/` changes.
- No changes to `PHASE1_DESIGN.md`, R24 preregistration, PC1 R4, frozen manifests, raw data or historical experiment records.
- No model/API calls, production runtime, signing-key access, PC1 execution, controller training or Formal G3.
- No Family C loading, gold-label inspection, execution or tuning.
- No baseline experiment or pilot during this documentation-only phase.
- No main update/merge/rebase/reset/force-push.
- No reuse of code/data/reports from any other project.
- Do not upgrade any scientific claim: fixed-vs-adaptive, PPO-vs-rule, PPO-vs-LinUCB, reward validity, state utility and delayed effects remain unproven unless exact evidence is supplied.

Current gates remain: PC1 BLOCKED; R4 PROPOSED / NOT APPROVED; Formal G3 FAIL; Family C NOT ACCESSED; registered PC1 NOT EXECUTED; controller training NOT AUTHORIZED / NOT STARTED. The 450/450 suite remains Executor-reported and not independently reproduced.

## 7. Stop condition

After the three reconciliation artifacts and durable status/handoff records are committed and pushed, stop and request Planner independent review.

Do not execute PC1, train a controller, access Family C, run G3 efficacy, or begin the baseline experiment. A later Planner decision must approve the canonical protocol and separately determine the next authorization gate.
