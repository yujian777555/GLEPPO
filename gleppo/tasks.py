"""Task generators: Family A/B (train+val) and Family C (held-out).

Family C instances may be GENERATED into manifests for freeze, but must never be
executed during Phase 2A development/tuning (scripts enforce this).
"""
from __future__ import annotations

import hashlib
import json
from typing import Callable, Dict, List, Tuple

FAMILY_A = "A"
FAMILY_B = "B"
FAMILY_C = "C"


def _rng(task_id: str, seed: int):
    """Deterministic pseudo-random stream from (task_id, seed)."""

    def _next(salt: int) -> int:
        h = hashlib.sha256(f"{task_id}|{seed}|{salt}".encode("utf-8")).hexdigest()
        return int(h[:8], 16)

    return _next


# --- Gold checks (evaluator-owned).
# Phase 2A / StubLLM mode: success = strategy match (RUNTIME_LOCK §4.4).
# The `gold` field is recorded for the production evaluator (string/JSON match)
# and is never exposed to controllers or operators. ---

def _check_family_a(answer: str, gold: str) -> Callable:
    def check(ans: str, g) -> bool:
        if "calc" not in g.tools:
            return False
        prompt = g.system_prompt.lower()
        return "compute" in prompt
    return check


def _check_family_b(answer: str, gold: str) -> Callable:
    def check(ans: str, g) -> bool:
        if "calc" not in g.tools or "str_ops" not in g.tools:
            return False
        return "transform" in g.system_prompt.lower()
    return check


def _check_family_c(gold_keys: List[str]) -> Callable:
    def check(ans: str, g) -> bool:
        if "str_ops" not in g.tools:
            return False
        prompt = g.system_prompt.lower()
        if "format" not in prompt and "json" not in prompt:
            return False
        try:
            s = ans.split("Final answer:", 1)[-1].strip()
            obj = json.loads(s)
            return all(k in obj for k in gold_keys)
        except Exception:  # noqa: BLE001
            return False
    return check


def build_task(task_id: str, family: str, seed: int) -> dict:
    nxt = _rng(task_id, seed)
    if family == FAMILY_A:
        a = 2 + nxt(1) % 30
        b = 2 + nxt(2) % 30
        c = 2 + nxt(3) % 10
        gold = a * c + b
        expr = f"{a}*{c}+{b}"
        input_text = f"If x={a} and y={b}, what is {expr}?"
        return {
            "task_id": task_id,
            "family": family,
            "seed": seed,
            "input": input_text,
            "gold": str(gold),
            "gold_check": _check_family_a(input_text, str(gold)),
            "required_tools": ["calc"],
            "required_prompt_keywords": ["compute", "step"],
        }
    if family == FAMILY_B:
        a = 2 + nxt(1) % 20
        b = 2 + nxt(2) % 20
        s = "ab" + str(nxt(3) % 100)
        gold = f"{a + b}-{s.upper()}"
        input_text = f"Compute {a}+{b} and then transform the string {s} to upper case. Give as SUM-STRING."
        return {
            "task_id": task_id,
            "family": family,
            "seed": seed,
            "input": input_text,
            "gold": gold,
            "gold_check": _check_family_b(input_text, gold),
            "required_tools": ["calc", "str_ops"],
            "required_prompt_keywords": ["transform"],
        }
    if family == FAMILY_C:
        a = 1 + nxt(1) % 9
        b = 1 + nxt(2) % 9
        keys = ["sum", "product"]
        gold = {"sum": a + b, "product": a * b}
        input_text = f"Output JSON with keys sum and product for numbers {a} and {b}."
        return {
            "task_id": task_id,
            "family": family,
            "seed": seed,
            "input": input_text,
            "gold": json.dumps(gold),
            "gold_check": _check_family_c(keys),
            "required_tools": ["str_ops"],
            "required_prompt_keywords": ["format", "json"],
        }
    raise ValueError(f"unknown family {family}")


def generate_split(
    family: str,
    prefix: str,
    n: int,
    seed_start: int,
    templates: List[str],
) -> List[dict]:
    """Generate n tasks. template_id is recorded for manifest but gold logic is generator-owned."""
    tasks = []
    for i in range(n):
        tid = f"{prefix}-{i:04d}"
        seed = seed_start + i
        t = build_task(tid, family, seed)
        t["template_id"] = templates[i % len(templates)]
        # strip non-serializable checker before persisting
        tasks.append(_serializable(t))
    return tasks


def _serializable(t: dict) -> dict:
    return {
        "task_id": t["task_id"],
        "family": t["family"],
        "seed": t["seed"],
        "template_id": t.get("template_id", "T0"),
        "input": t["input"],
        "gold": t["gold"],
        "required_tools": t["required_tools"],
        "required_prompt_keywords": t["required_prompt_keywords"],
    }


def attach_checker(t: dict) -> dict:
    """Re-attach gold_check from serializable fields (evaluator-side)."""
    fam = t["family"]
    if fam == FAMILY_A:
        t["gold_check"] = _check_family_a(t["input"], t["gold"])
    elif fam == FAMILY_B:
        t["gold_check"] = _check_family_b(t["input"], t["gold"])
    elif fam == FAMILY_C:
        t["gold_check"] = _check_family_c(["sum", "product"])
    else:
        raise ValueError(fam)
    return t


# Declared split parameters (Phase 1 §5.2). Family C is generated for freeze only.
TEMPLATES_A = ["TA1", "TA2", "TA3", "TA4", "TA5", "TA6", "TA7"]          # TA8 held out of val
TEMPLATES_A_VAL = ["TA1", "TA2", "TA3", "TA4", "TA5", "TA6", "TA7"]
TEMPLATES_B = ["TB1", "TB2", "TB3", "TB4", "TB5"]                        # TB6 held out of val
TEMPLATES_B_VAL = ["TB1", "TB2", "TB3", "TB4", "TB5"]
TEMPLATES_C = ["TC1", "TC2", "TC3", "TC4", "TC5"]

SPLIT_SPEC = {
    "train_A": {"family": FAMILY_A, "prefix": "A", "n": 200, "seed_start": 0, "templates": TEMPLATES_A},
    "train_B": {"family": FAMILY_B, "prefix": "B", "n": 200, "seed_start": 0, "templates": TEMPLATES_B},
    "val_A": {"family": FAMILY_A, "prefix": "Av", "n": 50, "seed_start": 1000, "templates": TEMPLATES_A_VAL},
    "val_B": {"family": FAMILY_B, "prefix": "Bv", "n": 50, "seed_start": 1000, "templates": TEMPLATES_B_VAL},
    "test_C": {"family": FAMILY_C, "prefix": "C", "n": 100, "seed_start": 0, "templates": TEMPLATES_C},
}
