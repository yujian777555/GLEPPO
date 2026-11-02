# R24 ECOS Controller Preregistration

**Date:** 2026-11-02
**Status:** PREREGISTERED — NOT AUTHORIZED TO EXECUTE

## Research Question

Can an Evolution-Conditioned Operator Selection (ECOS) controller improve operator selection compared to baselines?

## Controller Design

### State Vector
- Task features (tool count, dependency depth)
- Operator history (recent selections, success rates)
- Performance metrics (effective_success trend)

### Actions (5 operators)
1. prompt_local_edit
2. prompt_critique_rewrite
3. tool_subset_edit
4. workflow_step_edit
5. crossover

### Reward Function

R = effective_success(child) - effective_success(parent)

Attribution: immediate (per episode)

### PPO Configuration

| Parameter | Value |
|-----------|-------|
| Algorithm | PPO |
| Learning rate | 3e-4 |
| Clip epsilon | 0.2 |
| Entropy coefficient | 0.01 |
| Value coefficient | 0.5 |
| Max grad norm | 0.5 |
| Gamma | 0.99 |
| Lambda | 0.95 |

### Data Isolation

| Set | Tasks | Seeds | Purpose |
|-----|-------|-------|---------|
| Train | 4 | 3 | Optimization |
| Validation | 4 | 3 | Checkpoint selection |
| Confirm | 4 | 3 | Final evaluation |

**Strict isolation. No tuning on confirm set.**

### Baselines

| Arm | Description |
|-----|-------------|
| Fixed | Best single operator |
| Random | Uniform random |
| Rule-based | Heuristic rules |
| PPO | ECOS controller |

### Budget (Pre-registered)

| Resource | Limit |
|----------|-------|
| Episodes | 1000 |
| GPU hours | 10 |
| Model calls | 5000 |
| Tokens | 1M |
| Wall clock | 24 hours |

### Stop Rules

1. Budget exhausted
2. No improvement after 100 episodes
3. Validation degradation
4. Any gate failure

### DAC Integration

- DAC is shared across ALL arms
- DAC improvements NOT attributed to PPO
- DAC NOT in action space

## Prerequisites (ALL must pass)

1. R21-C1 independent review ACCEPT
2. PC1 current-branch audit complete
3. Trusted Planner approval
4. Formal G3 passage
5. PC1 approval and execution

**Current status: NONE MET — training NOT authorized.**
