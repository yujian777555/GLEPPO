"""Frozen evolution loop (Phase 1 §2.1): μ=8, λ=4, T=15, tournament-2, (μ+λ) elitist.

One operator per generation. No controller is called here — operator choice is an input.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from .evaluator import Evaluator
from .genotype import Genotype, behavior_hash, is_valid, make_valid_genotype
from .operators import OPERATOR_NAMES, apply_operator


@dataclass
class EvolutionConfig:
    mu: int = 8
    lam: int = 4
    T: int = 15
    tournament_k: int = 2
    gamma: float = 0.95
    n_eval: int = 3
    seed: int = 20261026


@dataclass
class Individual:
    geno: Genotype
    success: float = 0.0
    evaluated: bool = False
    behavior_hash: str = ""
    failure: str = ""


@dataclass
class GenerationLog:
    t: int
    operator: str
    parent_hashes: List[str]
    offspring_hashes: List[str]
    valid_count: int
    invalid_count: int
    best_success: float
    mean_success: float
    reward: float
    op_delta_mean: float


@dataclass
class EpisodeResult:
    logs: List[GenerationLog] = field(default_factory=list)
    best_success: float = 0.0
    final_best_hash: str = ""
    total_ctx: int = 0


def tournament_select(pop: List[Individual], k: int, rng: random.Random) -> Individual:
    cand = [pop[rng.randrange(len(pop))] for _ in range(k)]
    return max(cand, key=lambda x: x.success)


def init_population(cfg: EvolutionConfig, evaluator: Evaluator, task: dict, rng: random.Random) -> List[Individual]:
    pop: List[Individual] = []
    for i in range(cfg.mu):
        g = make_valid_genotype()
        # deterministic diversification of prompts at init
        g.system_prompt = g.system_prompt + f" Variant {i}."
        g.meta = {"init_index": i}
        ev = evaluator.evaluate(g, task, allow_family=("A", "B"))
        pop.append(
            Individual(
                geno=g,
                success=ev.success,
                evaluated=True,
                behavior_hash=behavior_hash(g),
                failure=ev.failure_category,
            )
        )
    return pop


def evolve_generation(
    pop: List[Individual],
    operator_name: str,
    cfg: EvolutionConfig,
    evaluator: Evaluator,
    task: dict,
    rng: random.Random,
    t: int,
    failure_hint: dict,
) -> Tuple[List[Individual], GenerationLog]:
    parents = [tournament_select(pop, cfg.tournament_k, rng) for _ in range(cfg.lam)]
    offspring: List[Individual] = []
    valid_count = 0
    invalid_count = 0
    deltas: List[float] = []

    for p in parents:
        mate = tournament_select(pop, cfg.tournament_k, rng) if operator_name == "crossover" else None
        ctx = dict(failure_hint)
        ctx["mate"] = mate.geno if mate else None
        ctx["gen"] = t
        child, ok, errs = apply_operator(operator_name, p.geno, ctx)
        if not ok:
            invalid_count += 1
            continue
        ev = evaluator.evaluate(child, task, allow_family=("A", "B"))
        valid_count += 1
        deltas.append(ev.success - p.success)
        offspring.append(
            Individual(
                geno=child,
                success=ev.success,
                evaluated=True,
                behavior_hash=behavior_hash(child),
                failure=ev.failure_category,
            )
        )

    merged = pop + offspring
    merged.sort(key=lambda x: x.success, reverse=True)
    survivors = merged[: cfg.mu]

    best = survivors[0].success
    mean = sum(x.success for x in survivors) / len(survivors)
    valid_rate = valid_count / max(1, valid_count + invalid_count)
    op_delta = sum(deltas) / len(deltas) if deltas else 0.0

    prev_best = max((x.success for x in pop), default=0.0)
    reward = float(best - prev_best) + 0.1 * valid_rate + 0.25 * (mean - sum(x.success for x in pop) / len(pop))
    reward = max(-0.5, min(1.0, reward))

    log = GenerationLog(
        t=t,
        operator=operator_name,
        parent_hashes=[p.behavior_hash for p in parents],
        offspring_hashes=[o.behavior_hash for o in offspring],
        valid_count=valid_count,
        invalid_count=invalid_count,
        best_success=best,
        mean_success=mean,
        reward=reward,
        op_delta_mean=op_delta,
    )
    return survivors, log


def evolve(
    operator_schedule: Callable[[int, List[Individual], dict], str],
    cfg: EvolutionConfig,
    evaluator: Evaluator,
    task: dict,
    seed: int = 0,
) -> EpisodeResult:
    """Run one evolution episode. operator_schedule(t, pop, history) -> operator name."""
    rng = random.Random(cfg.seed + seed + hash(task["task_id"]) % 100000)
    pop = init_population(cfg, evaluator, task, rng)
    res = EpisodeResult()
    history: List[dict] = []
    prev_best = max(x.success for x in pop)

    for t in range(cfg.T):
        failure_hint = {
            "failure_category": max(
                ([ind.failure for ind in pop if ind.failure] or [""]),
                key=[ind.failure for ind in pop].count,
            )
        }
        op = operator_schedule(t, pop, history)
        if op not in OPERATOR_NAMES:
            raise ValueError(op)
        pop, log = evolve_generation(pop, op, cfg, evaluator, task, rng, t, failure_hint)
        res.logs.append(log)
        history.append({"t": t, "op": op, "best": log.best_success, "reward": log.reward})
        res.total_ctx += cfg.lam * cfg.n_eval

    res.best_success = max(x.success for x in pop)
    best_ind = max(pop, key=lambda x: x.success)
    res.final_best_hash = best_ind.behavior_hash
    return res
