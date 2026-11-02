# R25 ECOS Scientific Review

**Date:** 2026-11-02
**Reviewer:** Independent

## Verdict: ACCEPT_WITH_LIMITATIONS

## Key Questions

| Question | Assessment |
|----------|------------|
| PPO necessary? | MAYBE — rule-based could suffice for 5 operators |
| Fixed strategy enough? | UNLIKELY — R21-C1 shows operator matters |
| Random beats PPO? | UNLIKELY — but must test |
| State vector useful? | YES — task features + operator history |
| Action space effective? | YES — 5 operators with clear effects |
| Reward reflects quality? | YES — effective_success |
| Reward hacking? | POSSIBLE — monitor format/path violations |
| DAC separated? | YES — shared component |
| Train overfitting? | RISK — need validation monitoring |
| 1000 episodes enough? | PROBABLY — but uncertain |

## Baselines Required

- A0: Fixed Strategy
- A1: Random Intervention
- A2: Rule-based Controller
- A3: PPO ECOS

## Metrics Required

- effective_success_rate
- answer_accuracy
- tool_path_validity
- format_compliance
- constraint_violation_rate
- hypervolume
- inference_cost

## Limitations

- PPO necessity not proven (rule-based may suffice)
- 1000 episodes uncertain for convergence
- Reward hacking possible

## Verdict: ACCEPT_WITH_LIMITATIONS

ECOS is scientifically sound but PPO necessity should be validated against rule-based first.
