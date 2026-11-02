# R23 Controller Training Preregistration

**Date:** 2026-11-02
**Status:** PREREGISTERED — NOT AUTHORIZED TO EXECUTE

## Research Question

Can an Evolution-Conditioned Operator Selection (ECOS) controller improve operator selection compared to fixed/random/rule-based baselines?

## Training Design

### Control Object
- **NOT Qwen base model** — no SFT/RLHF
- **Evolutionary controller** — selects operators based on state

### DAC Integration
- DAC is a **fixed shared component** across all arms
- DAC improvements must NOT be attributed to PPO
- DAC NOT in action space

### State/Action/Reward

| Component | Definition |
|-----------|-----------|
| State | Task features, operator history, performance metrics |
| Action | Operator selection (5 operators) |
| Reward | effective_success improvement |

### Train/Validation/Confirm Split

| Set | Tasks | Seeds | Purpose |
|-----|-------|-------|---------|
| Train | 4 tasks | 3 seeds | Policy optimization |
| Validation | 4 tasks | 3 seeds | Checkpoint selection |
| Confirm | 4 tasks | 3 seeds | Final evaluation |

**Strict isolation by task/template/seed. No tuning on confirm set.**

### Baselines

| Arm | Description |
|-----|-------------|
| Fixed | Always use best single operator |
| Random | Uniform random selection |
| Rule-based | Heuristic rules |
| PPO | ECOS controller |

### Budget (Pre-registered)

| Resource | Limit |
|----------|-------|
| Training episodes | 1000 |
| GPU hours | 10 |
| Model calls | 5000 |
| Tokens | 1M |
| Wall clock | 24 hours |

### Stop Rules

1. Budget exhausted → stop
2. No improvement after 100 episodes → stop
3. Validation degradation → stop
4. Any gate failure → stop

### Checkpoint Selection

- Best validation effective_success
- Early stopping with patience=20
- Final evaluation on confirm set only

## Prerequisites (ALL must pass)

1. R21-C1 independent review ACCEPT
2. PC1 current-branch audit complete
3. Trusted Planner approval
4. Formal G3 passage
5. PC1 approval and execution

**Current status: NONE MET — training NOT authorized.**
