"""Evaluator: owns gold labels; exposes only allowed observations to controllers.

R1: success is determined by gold checkers (actual answer correctness).
R4: cache keys include replicate_id / seed / runtime revision; cache hits are
    counted separately and never counted as new independent samples.
R8: paired CRN seeds exclude genotype/action identity from the shared RNG seed.
R9: cache hits are BUNDLE-level (one bundle = n_eval replicas); actual CTX
    counts only replica executions that really ran.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .genotype import Genotype, behavior_hash
from .interpreter import Interpreter, ExecutionResult
from .tasks import attach_checker

EVALUATOR_VERSION = "eval-v1.2-crn-accounting"


@dataclass
class EvalResult:
    success: float          # mean over independent replicas
    validity_ok: bool
    failure_category: str   # dominant failure
    turns: float
    tool_calls: float
    replicas: int
    from_cache: bool = False
    replicas_run: int = 0   # R9: actual replica executions (0 on cache hit)
    raw: List[dict] = field(default_factory=list)


class Evaluator:
    """Label isolation: gold never leaves this object.

    Controllers/operators must use only: success, failure_category, turns, tool_calls.
    """

    def __init__(self, interpreter: Optional[Interpreter] = None, n_eval: int = 3,
                 runtime_revision: str = "stub-v1.2"):
        self.interpreter = interpreter or Interpreter()
        self.n_eval = n_eval
        self.runtime_revision = runtime_revision
        self._cache: Dict[str, EvalResult] = {}
        self.cache_hits = 0            # R9: BUNDLE-level hits (one bundle = n_eval replicas)
        self.cache_misses = 0
        self.independent_samples = 0   # never incremented on cache hit
        self.replicas_executed = 0     # R9: total replica executions that actually ran

    # ---- R8 seed hierarchy -------------------------------------------------
    # The effective evaluation seed for a PAIRED comparison must depend on
    # (state_id, task_id, rollout_id, replicate_id, replica_index) and must NOT
    # depend on action or genotype. Genotype/action identity lives only in the
    # cache key and sample metadata.
    @staticmethod
    def effective_seed_parts(state_id: str, task_id: str, rollout_id: str,
                             replicate_id: int, replica_index: int) -> Tuple[str, ...]:
        return ("SEED", state_id, task_id, str(rollout_id), str(replicate_id), str(replica_index))

    def _cache_key(self, g: Genotype, task: dict, replicate_id: int, eval_seed: str) -> str:
        # genotype identity stays in the CACHE key (not in the RNG seed)
        return "|".join([
            behavior_hash(g),
            task["task_id"],
            str(replicate_id),
            eval_seed,
            self.runtime_revision,
            EVALUATOR_VERSION,
            getattr(self.interpreter.llm, "name", "unknown") if hasattr(self.interpreter, "llm") else "unknown",
        ])

    def evaluate(self, g: Genotype, task: dict, allow_family: tuple = ("A", "B"),
                 replicate_id: int = 0, eval_seed: Optional[str] = None,
                 state_id: str = "s0", rollout_id: str = "r0",
                 use_cache: bool = True) -> EvalResult:
        """Evaluate one genotype on one task over n_eval independent replicas.

        R8: when eval_seed / state_id / rollout_id are supplied, the RNG seed
        passed to the interpreter is derived ONLY from
        (state_id, task_id, rollout_id, replicate_id, replica_index) — identical
        for any genotype/action under the same CRN tuple.
        """
        if task["family"] not in allow_family:
            raise PermissionError(
                f"family {task['family']} not allowed in this call (held-out protection)"
            )
        task = attach_checker(dict(task))

        key = self._cache_key(g, task, replicate_id, eval_seed or f"{state_id}|{rollout_id}")
        if use_cache and key in self._cache:
            self.cache_hits += 1   # bundle-level: 1 hit returns n_eval replicas, 0 ran
            cached = self._cache[key]
            return EvalResult(
                success=cached.success, validity_ok=cached.validity_ok,
                failure_category=cached.failure_category, turns=cached.turns,
                tool_calls=cached.tool_calls, replicas=cached.replicas,
                from_cache=True, replicas_run=0,
            )

        self.cache_misses += 1
        reps: List[ExecutionResult] = []
        for r in range(self.n_eval):
            # R8: no genotype / action component in the shared seed
            seed_parts = self.effective_seed_parts(state_id, task["task_id"], rollout_id, replicate_id, r)
            res = self.interpreter.run(g, task, seed_parts=seed_parts)
            reps.append(res)
        self.independent_samples += 1
        self.replicas_executed += self.n_eval   # R9

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
            replicas_run=self.n_eval,
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
