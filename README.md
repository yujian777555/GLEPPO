# GLEPPO

**Status:** research bootstrap; no implementation or experimental claim yet.  
**Repository:** https://github.com/yujian777555/GLEPPO  
**Current phase:** P0 — project definition and baseline audit.

## Project idea

GLEPPO investigates whether a **trained reinforcement-learning controller** can learn how to evolve LLM agents more effectively than fixed or hand-designed evolutionary strategies.

The initial methodological reference is GLEET, which uses PPO to adapt exploration–exploitation control in evolutionary computation. GLEPPO will investigate the distinct problem of evolving agents using real task-execution feedback; it is **not** assumed that directly porting GLEET is novel.

## Core research question

Can a PPO-trained controller, conditioned on the evolutionary population and real agent-execution feedback, learn evolution decisions that improve task success and generalize to held-out task families?

The exact state representation, action space, reward, agent genotype, benchmarks, and claimed contribution remain **unsettled research hypotheses** until the baseline and literature audits are complete.

## Project boundaries

- This repository is the sole source of truth for GLEPPO's code, experiments, plans, and status.
- Do not import or conflate code, data, experiment results, plans, or status from unrelated projects.
- Start by training a small controller; do not assume that fine-tuning the base LLM is required.
- Real agent execution outcomes must ground the primary evaluation.
- Evaluation cost may be recorded, but limited-budget allocation is not the intended central contribution.
- No novelty, superiority, or generalization claim is accepted without controlled experiments and strong baselines.

## Immediate next step

Audit the original GLEET paper and official implementation, then map its assumptions to agent evolution. Establish the precise adaptation gap and baseline suite before implementing the controller.

See:
- [Project charter](docs/PROJECT_CHARTER.md)
- [Research plan](docs/RESEARCH_PLAN.md)
- [Literature ledger](docs/LITERATURE_LEDGER.md)
- [Latest executor plan](planner/latest_plan.md)
- [Machine-readable status](status.json)
