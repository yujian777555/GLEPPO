"""Frozen reward function shared by evolution and PC1 (R3: reward identity)."""
from __future__ import annotations

from typing import Sequence

# Frozen reward weights and clip (Phase 1 §3.4). Do not change without amendment.
W_BEST = 1.0
W_VALID = 0.1
W_MEAN = 0.25
REWARD_CLIP_LO = -0.5
REWARD_CLIP_HI = 1.0
GAMMA = 0.95


def generation_reward(
    best_now: float,
    best_prev: float,
    mean_now: float,
    mean_prev: float,
    valid_rate: float,
) -> float:
    """The ONE frozen reward used by r_hat and the first step of Q_hat (R3).

    reward = clip( Δbest + 0.1*valid_rate + 0.25*Δmean , -0.5, 1.0 )
    """
    r = (best_now - best_prev) + W_VALID * valid_rate + W_MEAN * (mean_now - mean_prev)
    return max(REWARD_CLIP_LO, min(REWARD_CLIP_HI, r))


def discounted_return(rewards: Sequence[float], gamma: float = GAMMA) -> float:
    total = 0.0
    for i, r in enumerate(rewards):
        total += (gamma ** i) * r
    return total
