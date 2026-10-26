# GLEPPO Research Plan

## Phase 0 — Scope lock and source audit (current)

### Task 0.1: Audit GLEET
- Read the GLEET paper and the official `MetaEvo/GLEET` implementation.
- Record exact source paths, algorithm flow, state/action/reward definitions, PPO training loop, task distribution, evaluation protocol, baselines, and limitations.
- Check the official repository's license and identify any reuse constraints before copying or adapting code.
- Distinguish facts visible in the paper, facts verified in code, and assumptions that still need reproduction.
- Do not implement a GLEPPO controller yet.

### Task 0.2: Review the neighboring literature
Build a paper-by-paper comparison for:
- RL-assisted evolutionary computation and adaptive operator/parameter control;
- LLM-agent evolution and prompt/workflow evolution;
- learned or meta-learned controllers for search;
- strong reproducible baselines with source code.

For each work, record its actual mechanism, training signal, search object, state/action/reward, benchmark, generalization test, code availability, and overlap with GLEPPO. A title/abstract-level similarity judgment is not enough.

### Phase 0 exit criteria
- A traceable literature ledger with stable paper links and verified bibliographic metadata.
- A code-grounded GLEET baseline audit.
- A short list of at most two candidate contributions, each with an explicit overlap/risk statement.
- A go / revise / stop recommendation before implementation.

## Phase 1 — Define the agent-evolution problem

Choose a small, reproducible agent genotype and task environment only after Phase 0. Verify that changing the genotype changes observable execution behavior. Fix the evaluator and data splits before controller training.

Decide on one primary controller decision family first:
1. evolutionary operator selection;
2. mutation/recombination intensity; or
3. parent-pair selection.

Do not combine all three in the first experiment.

## Phase 2 — Build the minimal environment and baselines

Minimum comparison set:
- fixed evolutionary strategy;
- random controller with the same action set;
- a strong hand-designed adaptive strategy;
- PPO-trained controller;
- an existing method that is a fair, reproducible match to the selected decision problem.

Track task success, offspring validity, population diversity, per-generation improvement, seeds, inference/training costs, and failures. Costs are secondary measurements, not the central novelty.

## Phase 3 — Train and test the controller

- Train PPO only on declared training task instances.
- Use validation tasks for model selection and hyperparameter tuning.
- Freeze the controller before held-out testing.
- Prevent answer, label, or test-result leakage into the controller state, reward, retrieval, or selection logic.
- Compare across multiple seeds and report uncertainty, not just the best run.
- Include ablations that isolate the proposed mechanism.

## Phase 4 — Research viability decision

Continue toward a paper only if the method:
- differs materially from existing methods at the mechanism level;
- improves over strong baselines on real task outcomes;
- does not rely on a flawed evaluator or leakage;
- shows evidence of transfer to held-out tasks.

If the result is negative, document it and revise or stop rather than stacking extra modules.

## Project hygiene

- This plan applies only to GLEPPO.
- Keep the experiment protocol, paper ledger, implementation, results, and `status.json` in this repository.
- Each executor handoff must include a concrete prompt, expected artifacts, acceptance criteria, and explicit out-of-scope actions.
