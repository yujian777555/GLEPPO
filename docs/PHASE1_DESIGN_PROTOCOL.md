# Phase 1 Design Protocol — GLEPPO

**State:** design-only gate; no controller implementation or training authorized in this task.  
**Primary candidate selected by Planner:** M1 — Execution-Conditioned Operator Selection (ECOS).  
**M2 — Failure-Mode-Conditioned Parent Selection (FMPS):** frozen as inactive; do not develop in parallel.

## Why select M1 first?

M1 has a small discrete action space and lets us isolate whether a trained controller chooses useful agent-variation operators. It is easier to audit and compare fairly than combinatorial parent-pair selection. This is a tractability decision, not a novelty or success claim.

The strongest risk is that the problem collapses to contextual bandit selection. Phase 1 must explicitly test whether the proposed sequential environment gives PPO a meaningful temporal-control problem. If not, do not manufacture an MDP merely to justify PPO.

## Required design deliverable

Create `research/PHASE1_DESIGN.md` with all sections below.

### 1. Agent genotype and runtime

Specify a minimal, inspectable agent genotype and its fixed runtime:
- Keep the base model, tool schema, tool availability, decoding settings, and evaluator fixed across methods.
- Prefer a structured prompt/module representation for the first version; do not introduce arbitrary code execution unless justified.
- Define the exact genotype schema, legal values, mutation/crossover boundaries, validity rules, and canonical serialization.
- Demonstrate on paper with concrete examples how each allowed edit can change observable behavior. No code or experiment is required in this task.
- Identify what is fixed and what evolves. Do not simultaneously evolve tools, workflow topology, parent pairing, and operator choice.

### 2. ECOS action and sequential-control justification

- Freeze the primary action family to **operator choice only**.
- Recommend a small, pre-registered set of semantically distinct operators. For every operator, specify inputs, edit scope, number of LLM proposal calls, expected output schema, failure handling, and whether it uses execution feedback.
- Keep parent selection, survivor selection, population size, and offspring count fixed across all methods.
- Prefer one controller action per generation (select the operator used to produce that generation's offspring batch), so actions alter later population states. If proposing per-offspring actions instead, explain why the problem is not adequately handled by a contextual bandit.
- Define the MDP: observation available at decision time, action, transition, episode boundary, reward, and return horizon.
- State must use only prior/current training episodes and population history. No held-out test outcome, answer, or hidden evaluator state may enter it.
- The design must explain what delayed consequence PPO could learn that a contextual bandit cannot. If no credible explanation exists, recommend STOP before implementation.

### 3. Reward and evaluation semantics

- Primary outcomes must come from actual LLM-agent execution in the environment.
- Define the primary task-success metric and generation-level reward. A recommended starting point is change in best-so-far training-suite success across generations, with all invalid/non-executing candidates counted transparently rather than silently credited as parent reuse.
- Specify how repeated runs, stochastic LLM outputs, ties, invalid offspring, timeouts, and missing outcomes are handled.
- Separate the controller's training reward from validation model selection and final held-out reporting.
- Do not use test data or evaluation-budget savings as the central reward/novelty claim.
- Include a no-execution-features ablation and a fitness-only state ablation.

### 4. Environment and task-family split

Propose a reproducible environment with actual tool calls and task outcomes. Define at least:
- training task families A/B;
- validation instances drawn from the same declared families but with disjoint task IDs/templates;
- a held-out family C that is not used for training, reward shaping, feature design, or hyperparameter selection.
- The task families should share enough interface primitives for transfer to be meaningful, but differ in task structure rather than only random seeds.
- Record how task IDs, templates, seeds, tool schemas, and split manifests will be frozen and hashed before training.
- Consider licenses, reproducibility, and the role of a later external benchmark. Do not assume a public benchmark has a suitable split or reuse license without checking.
- No held-out-family execution or tuning during this design task.

### 5. Baselines and fair comparison

The design must include:
- fixed operator;
- random operator;
- strong hand-designed adaptive rule;
- **non-contextual bandit** (e.g. UCB1 or EXP3);
- **contextual bandit using the same available state features** (e.g. a justified linear/contextual method);
- always-on failure-mode rewrite (FM-rewrite) under the same agent genotype and evaluation protocol;
- PPO ECOS.
- Consider a value-based RL baseline if it is practical and relevant, because RL-based operator selection predates this project.

Match model, operator library, proposal-call protocol, parent/survivor selection, task instances, and number of agent evaluations as closely as possible. Report model calls/tokens/latency as secondary resource measurements, not the main contribution. State how every baseline is tuned without using Family C.

### 6. Feasibility and stop criteria

Give an honest estimate of:
- controller training environment steps;
- candidate evaluations and LLM calls per evolutionary episode;
- likely API/local-inference costs and what must be measured in a pilot before forecasting total cost;
- number of controller seeds and evaluation seeds needed for a useful first test.

No API calls, model training, benchmark runs, or controller implementation in this task.

Define an early stop criterion: if PPO's sequential-control hypothesis is not distinguishable from contextual bandit under the designed state/action/reward, do not proceed to training merely because PPO is preferred.

## Phase 1 acceptance criteria

- M1 is the sole active candidate; M2 is explicitly frozen.
- The genotype, operators, environment, evaluator, split, MDP and reward are precise enough for an independent implementer to build without guessing.
- The contextual-bandit challenge is treated as a core scientific test, not a checkbox.
- Held-out family C is protected by a concrete manifest/hash protocol.
- Baselines and evaluation protocol are pre-specified.
- Clear GO / REVISE / STOP recommendation for the next phase.
- Documentation-only changes; no implementation, no training, no experiment claims.
- Update `status.json` and `planner/latest_plan.md`; commit and push to GLEPPO `main`.
