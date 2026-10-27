"""Frozen evolution loop (Phase 1 §2.1): μ=8, λ=4, T=15, tournament-2, (μ+λ) elitist.

R3: reward via gleppo.reward.generation_reward (single frozen function).
R4: stable SHA256-derived seeds (cross-process reproducible).
R7: separate counters for planned slots / actual CTX / cache hits / invalids.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from .evaluator import Evaluator
from .genotype import Genotype, behavior_hash, make_valid_genotype
from .operators import OPERATOR_NAMES, apply_operator
from .reward import generation_reward, GAMMA


@dataclass
class EvolutionConfig:
    mu: int = 8
    lam: int = 4
    T: int = 15
    tournament_k: int = 2
    gamma: float = GAMMA
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
    planned_slots: int = 0


@dataclass
class EpisodeResult:
    logs: List[GenerationLog] = field(default_factory=list)
    best_success: float = 0.0
    final_best_hash: str = ""
    # R7 accounting
    planned_slots: int = 0          # conservative upper bound (λ*n_eval*T + init)
    actual_ctx: int = 0             # uncached candidate-task executions
    cache_hits: int = 0
    invalid_offspring: int = 0
    valid_offspring: int = 0


def stable_seed(*parts: object) -> int:
    """R4: process-independent seed derivation (replaces built-in hash())."""
    h = hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).hexdigest()
    return int(h[:16], 16) % (2 ** 31 - 1)


def tournament_select(pop: List[Individual], k: int, rng: random.Random) -> Individual:
    cand = [pop[rng.randrange(len(pop))] for _ in range(k)]
    return max(cand, key=lambda x: x.success)


def init_population(cfg: EvolutionConfig, evaluator: Evaluator, task: dict,
                    rng: random.Random, episode_id: str = "0") -> Tuple[List[Individual], int, int]:
    """Returns (pop, actual_ctx_increment, cache_hits_increment)."""
    pop: List[Individual] = []
    actual = 0
    hits0 = evaluator.cache_hits
    for i in range(cfg.mu):
        g = make_valid_genotype()
        g.system_prompt = g.system_prompt + f" Variant {i}."
        g.meta = {"init_index": i}
        ev = evaluator.evaluate(g, task, allow_family=("A", "B"),
                                replicate_id=stable_seed(episode_id, "init", i) % 100000)
        actual += cfg.n_eval   # each evaluate() does n_eval executions (if not cached)
        pop.append(
            Individual(
                geno=g,
                success=ev.success,
                evaluated=True,
                behavior_hash=behavior_hash(g),
                failure=ev.failure_category,
            )
        )
    return pop, actual, evaluator.cache_hits - hits0


def evolve_generation(
    pop: List[Individual],
    operator_name: str,
    cfg: EvolutionConfig,
    evaluator: Evaluator,
    task: dict,
    rng: random.Random,
    t: int,
    failure_hint: dict,
    episode_id: str = "0",
) -> Tuple[List[Individual], GenerationLog]:
    parents = [tournament_select(pop, cfg.tournament_k, rng) for _ in range(cfg.lam)]
    offspring: List[Individual] = []
    valid_count = 0
    invalid_count = 0
    deltas: List[float] = []
    actual = 0
    hits0 = evaluator.cache_hits

    for j, p in enumerate(parents):
        mate = tournament_select(pop, cfg.tournament_k, rng) if operator_name == "crossover" else None
        ctx = dict(failure_hint)
        ctx["mate"] = mate.geno if mate else None
        ctx["gen"] = t
        child, ok, errs = apply_operator(operator_name, p.geno, ctx)
        if not ok:
            invalid_count += 1
            continue
        ev = evaluator.evaluate(
            child, task, allow_family=("A", "B"),
            replicate_id=stable_seed(episode_id, t, j, operator_name) % 100000,
        )
        actual += cfg.n_eval
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
    prev_mean = sum(x.success for x in pop) / len(pop)
    # R3: frozen reward function (same one PC1 must use)
    reward = generation_reward(best, prev_best, mean, prev_mean, valid_rate)

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
        planned_slots=cfg.lam * cfg.n_eval,
    )
    return survivors, log


def evolve(
    operator_schedule: Callable[[int, List[Individual], dict], str],
    cfg: EvolutionConfig,
    evaluator: Evaluator,
    task: dict,
    seed: int = 0,
    episode_id: Optional[str] = None,
) -> EpisodeResult:
    """Run one evolution episode. operator_schedule(t, pop, history) -> operator name."""
    eid = episode_id or f"{task['task_id']}-{seed}"
    rng = random.Random(stable_seed(cfg.seed, seed, task["task_id"], eid))
    pop, init_ctx, init_hits = init_population(cfg, evaluator, task, rng, eid)
    res = EpisodeResult()
    res.actual_ctx += init_ctx
    res.cache_hits += init_hits
    res.planned_slots += cfg.mu * cfg.n_eval   # R7: init slots counted
    history: List[dict] = []

    for t in range(cfg.T):
        failures = [ind.failure for ind in pop if ind.failure]
        failure_hint = {
            "failure_category": max(set(failures), key=failures.count) if failures else ""
        }
        op = operator_schedule(t, pop, history)
        if op not in OPERATOR_NAMES:
            raise ValueError(op)
        pop, log = evolve_generation(pop, op, cfg, evaluator, task, rng, t, failure_hint, eid)
        res.logs.append(log)
        history.append({"t": t, "op": op, "best": log.best_success, "reward": log.reward})
        res.planned_slots += log.planned_slots
        res.actual_ctx += log.valid_count * cfg.n_eval
        res.invalid_offspring += log.invalid_count
        res.valid_offspring += log.valid_count

    res.cache_hits = evaluator.cache_hits - init_hits + init_hits
    res.best_success = max(x.success for x in pop)
    best_ind = max(pop, key=lambda x: x.success)
    res.final_best_hash = best_ind.behavior_hash
    return res
