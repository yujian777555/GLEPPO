# GLEPPO Project Charter

**Last updated:** 2026-10-26  
**State:** hypothesis stage; not yet validated.

## 1. Mission

Investigate a trainable controller for evolutionary improvement of LLM agents. The controller should learn from actual task-execution feedback to decide how the evolutionary process proceeds, and should be evaluated on whether its learned decisions outperform credible alternatives and transfer to unseen tasks.

## 2. Working hypothesis

A controller trained over multiple task instances can learn useful, state-dependent evolution decisions from agent execution and population-history signals. If the learned policy captures reusable relationships between evolutionary context and offspring outcomes, it may improve task success and generalize beyond its training instances.

This is a hypothesis, not a result.

## 3. Primary research question

What controller state, action space, reward signal, and training-task distribution allow a learned policy to improve the evolution of LLM agents, rather than merely overfit a particular task set or reproduce a hand-designed heuristic?

## 4. Initial methodological reference

GLEET (Ma et al., GECCO 2024) uses deep reinforcement learning/PPO to configure the exploration–exploitation tradeoff of evolutionary computation. Its official implementation describes training and rollout with PSO/DMSPSO on CEC2021 numerical-optimization functions.

GLEPPO's research challenge is not simply to replace a numerical objective with an agent score. We must identify and validate the agent-evolution-specific decision problem, execution feedback, training protocol, and generalization claim.

## 5. Candidate design dimensions — not yet selected

- **State:** population fitness and diversity; parent/offspring history; recent gains or stagnation; operator outcomes; agent task-execution signals such as success/failure patterns. Only signals available at decision time may be used.
- **Action:** one deliberately limited decision family at first, such as evolutionary operator choice, mutation intensity, or parent-pair choice. Do not learn every decision simultaneously in the first prototype.
- **Reward:** grounded in actual task outcomes and relative offspring improvement. Avoid reward definitions that leak test labels or reward proxy signals unrelated to final task success.
- **Training:** PPO is the initial candidate because it is the user's preferred trainable direction and aligns with GLEET as a reference; it must still be compared with non-RL alternatives.
- **Generalization:** separate training, validation, and held-out test task instances/families before tuning the controller.

## 6. Evidence required for a credible contribution

1. A precise mechanism-level gap relative to GLEET and existing RL-assisted EA / agent-evolution methods.
2. A reproducible agent-evolution environment in which genotype changes demonstrably alter execution behavior.
3. A primary metric based on real task execution, not only a proxy score.
4. Comparisons against fixed operators, random decisions, a strong hand-designed adaptive baseline, and a suitable non-RL learned or adaptive baseline where feasible.
5. Multiple seeds, uncertainty reporting, ablations, and held-out generalization tests.
6. A negative-result gate: if PPO does not beat credible baselines or does not generalize, revise or stop the current hypothesis.

## 7. Non-goals for the initial phase

- Fine-tuning the base LLM before demonstrating that controller training is the relevant bottleneck.
- Making limited evaluation budget the central research contribution.
- Combining multiple unvalidated mechanisms merely to increase complexity.
- Claiming novelty from applying PPO to a new application domain alone.
- Importing code, results, data, plans, or status from any unrelated project.

## 8. Decision gates

- **G0 — Project isolation:** repository and source-of-truth rules established.
- **G1 — Baseline audit:** inspect the GLEET paper/code and record assumptions, algorithm flow, implementation details, and license.
- **G2 — Novelty gate:** map the proposed mechanism against related work and state what is materially different.
- **G3 — Environment gate:** verify genotype-to-behavior causality and real outcome evaluation.
- **G4 — Training gate:** compare PPO with strong controls and verify stable training.
- **G5 — Generalization gate:** evaluate on held-out tasks and decide whether the contribution merits a paper.

Do not skip a gate because an implementation is convenient.
