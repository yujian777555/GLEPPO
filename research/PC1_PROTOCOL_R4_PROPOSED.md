# PC1 Canonical Protocol — R4 Proposed Design

**Status: PROPOSED / NOT APPROVED**  
**Document ID:** `PC1_PROTOCOL_R4_PROPOSED`  
**Code version:** `pc1-proposed-v1-r5`  
**Protocol hash:** computed at test time from this document's canonical field block (see §12)  
**Date:** 2026-10-27  
**Approval:** NOT APPROVED. Requires explicit Planner decision after independent review.

---

## 1. Scope

This document defines the proposed PC1 myopia-diagnostic protocol for the GLEPPO project (M1 ECOS). It supersedes the historical v1/v2 sampling designs recorded in `research/PHASE2_PREFLIGHT.md` (retained as archival). It does **not** authorize data collection.

## 2. Sample design

| Parameter | Value |
|---|---|
| States (N_STATES) | 100 |
| Actions (N_ACTIONS) | 5 |
| Q rollouts per (state, action) | 3 |
| Horizon (HORIZON) | 3 |
| Extra immediate draws per (state, action) | 1 |
| Collection episodes (clusters) | 40 |
| Population size (MU) | 8 |
| Offspring per generation (LAMBDA) | 4 |
| Replicas per evaluation (N_EVAL) | 2 (PC1 diagnostic only) |
| Discount factor (GAMMA) | 0.95 |

## 3. Estimator definitions

**Frozen reward function** (single source: `gleppo/reward.py:generation_reward`):

```
r_t = clip(Δbest + 0.1 × valid_rate + 0.25 × Δmean, -0.5, 1.0)
```

**r̂(s,a)** = mean of (Q-rollout first-step rewards + extra immediate rewards) for the (s,a) pair. All rewards computed with the frozen function above.

**Q̂(s,a)** = mean h-step discounted return of **complete q_rollout records only** (never extra_immediate):

```
Q̂(s,a) = E[ r_0 + γ·r_1 + γ²·r_2 ]  under the fixed random continuation policy
```

## 4. Sample roles

| Role | Reward trace length | Used in r̂ | Used in Q̂ |
|---|---|---|---|
| `q_rollout` | 3 (HORIZON) | first reward only | full trace |
| `extra_immediate` | 1 | the single reward | **never** |

## 5. CRN seed contract

Evaluation RNG seed (shared across actions for paired comparison):

```
effective_seed = ("SEED", base_tag, task_id, state_id, rollout_id, replicate_id, replica_index)
```

- `base_tag`: `"NONE"` if no override, `"EMPTY"` if explicit empty, else the override string.
- Action and genotype **never** enter the seed.
- Operator-generation RNG is separate: `operator_rng_seed(operator, state_id, action, rollout_id, draw)`.

## 6. Collection clusters and independence

- 40 independent collection episodes (20 random + 20 heuristic policy).
- Each sampled state is assigned to exactly one episode (state-to-episode mapping in the dry-run plan).
- Bootstrap resamples complete episode clusters (not individual rows).
- Cluster unit = collection episode.

## 7. Statistical thresholds and decision rule

| Threshold | Value |
|---|---|
| D (disagreement rate) | ≥ 0.15 |
| Advantage (mean Q̂ gap) | ≥ 0.02 |
| CI margin D | 0.10 |
| CI margin advantage | 0.01 |

**Decision rule:** PASS if point estimates meet thresholds AND 95% CI lower bounds exclude margins. FAIL if CI upper bounds are below thresholds. Otherwise INCONCLUSIVE → SR1 STOP.

**Bootstrap:** cluster bootstrap by episode, 10,000 resamples, seed 20261027.

## 8. Budget arithmetic

| Component | Formula | Planned slots |
|---|---|---|
| Q rollouts | 100 × 5 × 3 × 3 × 4 × 2 | **36,000** |
| Extra immediate | 100 × 5 × 1 × 1 × 4 × 2 | **4,000** |
| State collection | 40 × (8 × 2 + 15 × 4 × 2) | **5,440** |
| **Total** | | **45,440** |
| **Hard cap** | | **50,000** |
| Headroom | | **4,560** |

## 9. Registered shape requirements

- Exactly 100 states.
- Exactly 40 source collection episodes / clusters.
- Exactly 5 actions per state.
- Exactly 3 Q rollouts + 1 extra immediate per (state, action).
- Every record must match the plan's state-to-episode/task/family mapping.
- All provenance fields (manifest_hash, protocol_hash, runtime_revision, evaluator_version) must be non-empty.

## 10. Authorization gates

Registered PC1 execution requires ALL of:

1. Planner approval of this protocol (status → APPROVED with approval ID and date).
2. Independent review approval.
3. Production runtime lock revision bound and ready.
4. Budget guard passing.

Default is **deny**. Boolean flags alone do not authorize execution.

## 11. Change log

| Version | Date | Change |
|---|---|---|
| R4 proposed | 2026-10-27 | Initial canonical proposed protocol (supersedes v1/v2 archival designs) |

## 12. Canonical field block (for hash computation)

```json
{
  "document_id": "PC1_PROTOCOL_R4_PROPOSED",
  "code_version": "pc1-proposed-v1-r5",
  "status": "PROPOSED_NOT_APPROVED",
  "n_states": 100,
  "n_actions": 5,
  "q_rollouts": 3,
  "horizon": 3,
  "extra_immediate": 1,
  "n_collection_episodes": 40,
  "gamma": 0.95,
  "thresholds": {"D": 0.15, "advantage": 0.02, "margin_D": 0.10, "margin_adv": 0.01},
  "budget": {"q_slots": 36000, "extra_slots": 4000, "collection_slots": 5440, "total": 45440, "hard_cap": 50000},
  "estimator_r_hat": "mean of Q-rollout first rewards + extra immediate rewards",
  "estimator_q_hat": "h-step discounted return of q_rollout records only",
  "cluster_unit": "collection_episode",
  "seed_contract": "crn-v2 typed JSON serialization",
  "reward_formula": "clip(d_best + 0.1*valid_rate + 0.25*d_mean, -0.5, 1.0)",
  "code_version": "pc1-proposed-v1-r5",
  "status": "PROPOSED_NOT_APPROVED"
}
```
