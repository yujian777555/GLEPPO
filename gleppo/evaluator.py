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

EVALUATOR_VERSION = "eval-v1.4-r20-crn-unified"


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
    answer_correct: float = 0.0    # D1: gold checker result (0-1)
    format_compliant: float = 0.0  # D1: format checker result (0-1)


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
        """R20: ONE seed contract. eval_seed_override is a BASE CRN key combined
        with (task_id, state_id, rollout_id, replicate_id, replica_index).
        Action and genotype NEVER enter the seed.
        """
        # R34: collision-free typed encoding — ["none"] vs ["value","NONE"] etc.
        if eval_seed_override is None:
            base_tag = ["none"]
        elif eval_seed_override == "":
            base_tag = ["empty"]
        else:
            base_tag = ["value", eval_seed_override]
        # JSON-serialize all fields for unambiguous encoding
        import json as _json
        encoded = _json.dumps([
            base_tag, task_id, state_id, str(rollout_id), str(replicate_id), str(replica_index)
        ], separators=(",", ":"), ensure_ascii=False)
        return ("SEED", encoded)

    def _cache_key(self, g: Genotype, task: dict, state_id: str, rollout_id: str,
                   replicate_id: int, eval_seed_override: Optional[str]) -> str:
        """R32: cache key uses tagged encoding for eval_seed to distinguish
        None (absent) from "" (explicit empty). Includes all seed-affecting
        fields plus genotype identity, task, runtime, evaluator version."""
        # R34: collision-free typed encoding for eval_seed
        if eval_seed_override is None:
            seed_tag = ["none"]
        elif eval_seed_override == "":
            seed_tag = ["empty"]
        else:
            seed_tag = ["value", eval_seed_override]
        # R34: JSON-array serialization — delimiter-safe for any input
        import json as _json
        key_parts = _json.dumps([
            behavior_hash(g),
            task["task_id"],
            state_id,
            str(rollout_id),
            str(replicate_id),
            seed_tag,
            self.runtime_revision,
            EVALUATOR_VERSION,
            getattr(getattr(self.interpreter, "llm", None), "name", "unknown"),
        ], separators=(",", ":"), ensure_ascii=False)
        return key_parts

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
        # D1: separate answer_correct from format_compliant
        answer_correct = sum(1 for x in reps if x.success) / len(reps)
        format_compliant = sum(1 for x in reps if self._check_format(x.answer)) / len(reps)
        out = EvalResult(
            success=succ, validity_ok=True, failure_category=dom,
            turns=turns, tool_calls=tools, replicas=len(reps),
            from_cache=False, replicas_run=self.n_eval,
            effective_seeds=seeds_used,
            answer_correct=answer_correct,
            format_compliant=format_compliant,
        )
        self._cache[key] = out
        return out

    @staticmethod
    def _check_format(answer: str) -> bool:
        """D1: format compliance — independent of gold checker.

        Rules (frozen protocol):
        - Must contain 'Final answer:' prefix
        - Must have non-empty content after prefix
        - No trailing explanation after the answer value
        """
        if not answer or not answer.strip():
            return False
        if "Final answer:" not in answer:
            return False
        # Extract content after prefix
        idx = answer.index("Final answer:")
        after = answer[idx + len("Final answer:"):].strip()
        if not after:
            return False
        # D1: check for excessive trailing text (more than 20 chars after value)
        # This catches "Final answer: 42. Let me explain..." as non-compliant
        lines = after.split("\n")
        first_line = lines[0].strip()
        # Value should be reasonably short (no long explanations)
        if len(first_line) > 100:
            return False
        return True

    def observe(self, ev: EvalResult) -> dict:
        return {
            "success": ev.success,
            "failure_category": ev.failure_category,
            "turns": ev.turns,
            "tool_calls": ev.tool_calls,
        }
