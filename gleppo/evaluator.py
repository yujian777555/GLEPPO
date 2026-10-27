"""Evaluator: owns gold labels; exposes only allowed observations to controllers.

R1: success is determined by gold checkers (actual answer correctness).
R4/R8/R16: one authoritative seed contract — effective evaluation seed derived
    from (state_id, task_id, rollout_id, replicate_id, replica_index); cache key
    includes every field that affects the effective seed + genotype identity.
R9: cache hits are BUNDLE-level (1 bundle = n_eval replicas, 0 ran);
    replicas_run reports actual replica executions.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .genotype import Genotype, behavior_hash
from .interpreter import Interpreter, ExecutionResult
from .tasks import attach_checker

EVALUATOR_VERSION = "eval-v1.3-unified-seed"


@dataclass
class EvalResult:
    success: float
    validity_ok: bool
    failure_category: str
    turns: float
    tool_calls: float
    replicas: int
    from_cache: bool = False
    replicas_run: int = 0       # R9/R12: actual replica executions (0 on cache hit)
    effective_seeds: List[Tuple[str, ...]] = field(default_factory=list)


class Evaluator:
    """Label isolation: gold never leaves this object.

    Controllers/operators must use only: success, failure_category, turns, tool_calls.
    """

    def __init__(self, interpreter: Optional[Interpreter] = None, n_eval: int = 3,
                 runtime_revision: str = "stub-v1.3"):
        self.interpreter = interpreter or Interpreter()
        self.n_eval = n_eval
        self.runtime_revision = runtime_revision
        self._cache: Dict[str, EvalResult] = {}
        self.cache_hits = 0            # BUNDLE-level
        self.cache_misses = 0
        self.independent_samples = 0   # never incremented on cache hit
        self.replicas_executed = 0     # total replica executions that actually ran

    # ---- R16: one authoritative seed derivation ---------------------------
    @staticmethod
    def effective_seed_parts(state_id: str, task_id: str, rollout_id: str,
                             replicate_id: int, replica_index: int,
                             eval_seed_override: Optional[str] = None) -> Tuple[str, ...]:
        """The ONE seed contract for paired evaluation RNG.

        When eval_seed_override is provided, it fully replaces the derived tuple
        (the caller is responsible for uniqueness). Otherwise the seed depends on
        (state_id, task_id, rollout_id, replicate_id, replica_index) and NEVER on
        genotype or action.
        """
        if eval_seed_override is not None:
            return ("SEED_OVERRIDE", eval_seed_override, str(replica_index))
        return ("SEED", state_id, task_id, str(rollout_id), str(replicate_id), str(replica_index))

    def _cache_key(self, g: Genotype, task: dict, state_id: str, rollout_id: str,
                   replicate_id: int, eval_seed_override: Optional[str]) -> str:
        """R16: cache key includes every field that affects the effective seed
        PLUS genotype identity, task, runtime, evaluator version."""
        return "|".join([
            behavior_hash(g),
            task["task_id"],
            state_id,
            str(rollout_id),
            str(replicate_id),
            eval_seed_override or "",
            self.runtime_revision,
            EVALUATOR_VERSION,
            getattr(getattr(self.interpreter, "llm", None), "name", "unknown"),
        ])

    def evaluate(self, g: Genotype, task: dict, allow_family: tuple = ("A", "B"),
                 replicate_id: int = 0,
                 state_id: str = "s0", rollout_id: str = "r0",
                 eval_seed: Optional[str] = None,
                 use_cache: bool = True) -> EvalResult:
        """Evaluate one genotype on one task over n_eval independent replicas.

        R16: eval_seed, if provided, is the ACTUAL override for the RNG seed
        (not cache-only). state_id and rollout_id always enter both the seed and
        the cache key.
        """
        if task["family"] not in allow_family:
            raise PermissionError(
                f"family {task['family']} not allowed (held-out protection)")
        task = attach_checker(dict(task))

        key = self._cache_key(g, task, state_id, rollout_id, replicate_id, eval_seed)
        if use_cache and key in self._cache:
            self.cache_hits += 1
            c = self._cache[key]
            return EvalResult(
                success=c.success, validity_ok=c.validity_ok,
                failure_category=c.failure_category, turns=c.turns,
                tool_calls=c.tool_calls, replicas=c.replicas,
                from_cache=True, replicas_run=0,
            )

        self.cache_misses += 1
        reps: List[ExecutionResult] = []
        seeds_used: List[Tuple[str, ...]] = []
        for r in range(self.n_eval):
            seed_parts = self.effective_seed_parts(
                state_id, task["task_id"], rollout_id, replicate_id, r, eval_seed)
            seeds_used.append(seed_parts)
            res = self.interpreter.run(g, task, seed_parts=seed_parts)
            reps.append(res)
        self.independent_samples += 1
        self.replicas_executed += self.n_eval

        succ = sum(1 for x in reps if x.success) / len(reps)
        fails = [x.failure_category for x in reps if x.failure_category]
        dom = max(set(fails), key=fails.count) if fails else ""
        turns = sum(x.turns for x in reps) / len(reps)
        tools = sum(x.tool_calls for x in reps) / len(reps)
        out = EvalResult(
            success=succ, validity_ok=True, failure_category=dom,
            turns=turns, tool_calls=tools, replicas=len(reps),
            from_cache=False, replicas_run=self.n_eval,
            effective_seeds=seeds_used,
        )
        self._cache[key] = out
        return out

    def observe(self, ev: EvalResult) -> dict:
        return {
            "success": ev.success,
            "failure_category": ev.failure_category,
            "turns": ev.turns,
            "tool_calls": ev.tool_calls,
        }
