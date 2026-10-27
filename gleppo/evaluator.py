"""Evaluator: owns gold labels; exposes only allowed observations to controllers.

R1: success is determined by gold checkers (actual answer correctness).
R4: cache keys include replicate_id / seed / runtime revision; cache hits are
    counted separately and never counted as new independent samples.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .genotype import Genotype, behavior_hash
from .interpreter import Interpreter, ExecutionResult
from .tasks import attach_checker

EVALUATOR_VERSION = "eval-v1.1-correctness"


@dataclass
class EvalResult:
    success: float          # mean over independent replicas
    validity_ok: bool
    failure_category: str   # dominant failure
    turns: float
    tool_calls: float
    replicas: int
    from_cache: bool = False
    raw: List[dict] = field(default_factory=list)


class Evaluator:
    """Label isolation: gold never leaves this object.

    Controllers/operators must use only: success, failure_category, turns, tool_calls.
    """

    def __init__(self, interpreter: Optional[Interpreter] = None, n_eval: int = 3,
                 runtime_revision: str = "stub-v1.1"):
        self.interpreter = interpreter or Interpreter()
        self.n_eval = n_eval
        self.runtime_revision = runtime_revision
        self._cache: Dict[str, EvalResult] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.independent_samples = 0   # R4: never incremented on cache hit

    def _cache_key(self, g: Genotype, task: dict, replicate_id: int, eval_seed: str) -> str:
        return "|".join([
            behavior_hash(g),
            task["task_id"],
            str(replicate_id),
            eval_seed,
            self.runtime_revision,
            EVALUATOR_VERSION,
            self.interpreter.llm.name if hasattr(self.interpreter, "llm") else "unknown",
        ])

    def evaluate(self, g: Genotype, task: dict, allow_family: tuple = ("A", "B"),
                 replicate_id: int = 0, eval_seed: Optional[str] = None,
                 use_cache: bool = True) -> EvalResult:
        """Evaluate one genotype on one task over n_eval independent replicas.

        replicate_id distinguishes Monte Carlo replicates. Distinct replicate_ids
        NEVER share cache entries (R4). eval_seed (if provided) is the CRN seed.
        """
        if task["family"] not in allow_family:
            raise PermissionError(
                f"family {task['family']} not allowed in this call (held-out protection)"
            )
        task = attach_checker(dict(task))
        h = behavior_hash(g)

        # one cache entry per (genotype, task, replicate, seed, runtime)
        key = self._cache_key(g, task, replicate_id, eval_seed or "default")
        if use_cache and key in self._cache:
            self.cache_hits += 1
            cached = self._cache[key]
            return EvalResult(
                success=cached.success, validity_ok=cached.validity_ok,
                failure_category=cached.failure_category, turns=cached.turns,
                tool_calls=cached.tool_calls, replicas=cached.replicas,
                from_cache=True,
            )

        self.cache_misses += 1
        reps: List[ExecutionResult] = []
        for r in range(self.n_eval):
            # per-replica seed: CRN seed shared across actions when eval_seed is
            # declared; replica index r keeps draws independent within a replicate.
            if eval_seed:
                seed_parts = (eval_seed, task["task_id"], r, h[:8])
            else:
                seed_parts = (task["task_id"], replicate_id, r, h[:8])
            res = self.interpreter.run(g, task, seed_parts=seed_parts)
            reps.append(res)
        self.independent_samples += 1

        succ = sum(1 for x in reps if x.success) / len(reps)
        fails = [x.failure_category for x in reps if x.failure_category]
        dom = max(set(fails), key=fails.count) if fails else ""
        turns = sum(x.turns for x in reps) / len(reps)
        tools = sum(x.tool_calls for x in reps) / len(reps)
        out = EvalResult(
            success=succ,
            validity_ok=True,
            failure_category=dom,
            turns=turns,
            tool_calls=tools,
            replicas=len(reps),
            from_cache=False,
        )
        self._cache[key] = out
        return out

    def observe(self, ev: EvalResult) -> dict:
        """The ONLY view a controller/operator may consume."""
        return {
            "success": ev.success,
            "failure_category": ev.failure_category,
            "turns": ev.turns,
            "tool_calls": ev.tool_calls,
        }
