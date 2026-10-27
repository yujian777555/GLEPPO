"""Canonical 32-dim state vector (PHASE2_PREFLIGHT §4). Tested for shape/order/finiteness."""
from __future__ import annotations

import math
from typing import List, Sequence

STATE_DIM = 32
GAMMA = 0.95

# block A: 0-11, block B: 12-23, block C: 24-31
FEATURE_NAMES = [
    "best_success", "mean_success", "succ_gap",
    "fail_format_rate", "fail_tool_rate", "fail_wrong_rate", "fail_timeout_rate",
    "valid_rate", "mean_turns", "mean_tool_calls", "parent_last_delta", "recent_eval_coverage",
    "div_tools", "div_workflow", "div_prompt",
    "op_usage_entropy", "op_mean_delta_1", "op_mean_delta_2", "op_mean_delta_3",
    "op_mean_delta_4", "op_mean_delta_5", "op_unobserved_frac", "age_best", "pop_size_norm",
    "gen_frac", "stagnation_frac", "budget_used_frac", "best_delta_since_start",
    "improve_last_3_frac", "recency_top1", "recency_top2", "offspring_valid_last",
]

assert len(FEATURE_NAMES) == STATE_DIM


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _jaccard(a: Sequence, b: Sequence) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / max(1, len(sa | sb))


def _ngrams(s: str, n: int = 8) -> set:
    s = s.lower()
    return {s[i:i + n] for i in range(max(0, len(s) - n + 1))} or {s}


def state_vector(
    *,
    best_success: float,
    mean_success: float,
    fail_rates: dict,
    valid_rate: float,
    mean_turns: float,
    mean_tool_calls: float,
    parent_last_delta: float,
    recent_eval_coverage: float,
    tool_sets: List[List[str]],
    workflows: List[List[str]],
    prompts: List[str],
    op_usage: dict,          # name -> count
    op_mean_delta: dict,     # name -> mean delta or None
    age_best: float,
    pop_size_norm: float,
    gen_t: int,
    T: int,
    stagnation: int,
    best_delta_since_start: float,
    improve_last_3_frac: float,
    recency_gaps: List[int],  # gaps of last operators (1 = just used)
    offspring_valid_last: float,
) -> List[float]:
    """Return exactly STATE_DIM floats in the frozen feature order."""
    gaps = sorted([g for g in recency_gaps if g >= 1])[:2]
    rec1 = _clip01((1.0 / gaps[0]) / T) if len(gaps) > 0 else 0.0
    rec2 = _clip01((1.0 / gaps[1]) / T) if len(gaps) > 1 else 0.0

    div_tools = 0.0
    div_wf = 0.0
    div_pr = 0.0
    if len(tool_sets) >= 2:
        pairs = 0
        for i in range(len(tool_sets)):
            for j in range(i + 1, len(tool_sets)):
                div_tools += _jaccard(tool_sets[i], tool_sets[j])
                div_wf += _jaccard(workflows[i], workflows[j])
                div_pr += _jaccard(_ngrams(prompts[i]), _ngrams(prompts[j]))
                pairs += 1
        div_tools /= pairs
        div_wf /= pairs
        div_pr /= pairs

    counts = list(op_usage.values())
    total = sum(counts)
    ent = 0.0
    if total > 0 and counts:
        for c in counts:
            if c > 0:
                p = c / total
                ent -= p * math.log(p)
        ent /= math.log(5.0) if 5.0 > 1 else 1.0

    op_names = [
        "prompt_local_edit", "prompt_critique_rewrite", "tool_subset_edit",
        "workflow_step_edit", "crossover",
    ]
    deltas = []
    unobs = 0
    for name in op_names:
        v = op_mean_delta.get(name)
        if v is None:
            deltas.append(0.0)
            unobs += 1
        else:
            deltas.append(max(-1.0, min(1.0, float(v))))

    vec = [
        _clip01(best_success),
        _clip01(mean_success),
        _clip01(best_success - mean_success),
        _clip01(fail_rates.get("format_error", 0.0)),
        _clip01(fail_rates.get("tool_error", 0.0)),
        _clip01(fail_rates.get("wrong_answer", 0.0)),
        _clip01(fail_rates.get("timeout", 0.0)),
        _clip01(valid_rate),
        _clip01(mean_turns / 24.0),
        _clip01(mean_tool_calls / 8.0),
        max(-1.0, min(1.0, parent_last_delta)),
        _clip01(recent_eval_coverage),
        _clip01(div_tools),
        _clip01(div_wf),
        _clip01(div_pr),
        _clip01(ent),
        deltas[0], deltas[1], deltas[2], deltas[3], deltas[4],
        _clip01(unobs / 5.0),
        _clip01(age_best / max(1, T)),
        _clip01(pop_size_norm),
        _clip01(gen_t / max(1, T)),
        _clip01(stagnation / max(1, T)),
        _clip01(gen_t / max(1, T)),
        max(-1.0, min(1.0, best_delta_since_start)),
        _clip01(improve_last_3_frac),
        rec1,
        rec2,
        _clip01(offspring_valid_last),
    ]
    assert len(vec) == STATE_DIM
    out = [float(x) for x in vec]
    if not all(math.isfinite(x) for x in out):
        raise ValueError("non-finite state feature")
    return out


def empty_state() -> List[float]:
    return [0.0] * STATE_DIM
