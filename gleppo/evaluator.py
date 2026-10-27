"""Evaluator: owns gold labels; exposes only allowed observations to controllers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .genotype import Genotype, behavior_hash
from .interpreter import Interpreter, ExecutionResult
from .tasks import attach_checker


@dataclass
class EvalResult:
    success: float          # mean over replicas
    validity_ok: bool
    failure_category: str   # dominant failure
    turns: float
    tool_calls: float
    replicas: int
    raw: List[dict] = field(default_factory=list)


class Evaluator:
    """Label isolation: gold never leaves this object.

    Controllers/operators must use only: success, failure_category, turns, tool_calls.
    """

    def __init__(self, interpreter: Optional[Interpreter] = None, n_eval: int = 3):
        self.interpreter = interpreter or Interpreter()
        self.n_eval = n_eval
        self._cache: Dict[str, dict] = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def evaluate(self, g: Genotype, task: dict, allow_family: tuple = ("A", "B")) -> EvalResult:
        if task["family"] not in allow_family:
            raise PermissionError(
                f"family {task['family']} not allowed in this call (held-out protection)"
            )
        task = attach_checker(dict(task))
        h = behavior_hash(g)
        key = f"{h}|{task['task_id']}"
        if key in self._cache:
            self.cache_hits += 1
            return EvalResult(**{k: v for k, v in self._cache[key].items() if k != "raw"})

        self.cache_misses += 1
        reps: List[ExecutionResult] = []
        for r in range(self.n_eval):
            res = self.interpreter.run(g, task, seed_parts=(task["task_id"], r, h[:8]))
            reps.append(res)

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
        )
        self._cache[key] = {
            "success": out.success,
            "validity_ok": out.validity_ok,
            "failure_category": out.failure_category,
            "turns": out.turns,
            "tool_calls": out.tool_calls,
            "replicas": out.replicas,
        }
        return out

    def observe(self, ev: EvalResult) -> dict:
        """The ONLY view a controller/operator may consume."""
        return {
            "success": ev.success,
            "failure_category": ev.failure_category,
            "turns": ev.turns,
            "tool_calls": ev.tool_calls,
        }
