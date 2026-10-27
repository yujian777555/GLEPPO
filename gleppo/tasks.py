"""Task generators: Family A/B (train+val) and Family C (held-out).

R1: checkers verify ACTUAL answers against gold (evaluator-owned).
R5: template_id maps to a real, distinct generation rule; train/val templates disjoint.
Family C instances may be GENERATED into manifests for freeze, but must never be
executed during Phase 2A development/tuning (scripts enforce this).
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Callable, Dict, List, Tuple

FAMILY_A = "A"
FAMILY_B = "B"
FAMILY_C = "C"

ANSWER_PREFIX = "final answer:"


def _rng(task_id: str, seed: int):
    def _next(salt: int) -> int:
        h = hashlib.sha256(f"{task_id}|{seed}|{salt}".encode("utf-8")).hexdigest()
        return int(h[:8], 16)
    return _next


def _extract_final_answer(ans: str) -> str:
    low = ans.lower()
    if ANSWER_PREFIX in low:
        idx = low.rindex(ANSWER_PREFIX)
        return ans[idx + len(ANSWER_PREFIX):].strip()
    return ans.strip()


def _norm_num_str(s: str) -> str:
    s = s.strip().rstrip(".;,")
    try:
        f = float(s)
        if f.is_integer():
            return str(int(f))
        return f"{f:.6f}".rstrip("0").rstrip(".")
    except ValueError:
        return s


# ---------------------------------------------------------------------------
# R1: gold checkers compare actual answers to gold. Gold stays evaluator-side.
# ---------------------------------------------------------------------------

def _check_family_a(gold: str) -> Callable:
    """Family A: final answer must be the exact arithmetic result (numeric)."""
    gold_n = _norm_num_str(gold)

    def check(ans: str, g) -> bool:
        got = _norm_num_str(_extract_final_answer(ans))
        return got == gold_n
    return check


def _check_family_b(gold: str) -> Callable:
    """Family B: final answer must match gold SUM-STRING exactly (case-insensitive on string part)."""
    gold_norm = gold.strip().lower()

    def check(ans: str, g) -> bool:
        got = _extract_final_answer(ans).strip().lower()
        return got == gold_norm
    return check


def _check_family_c(gold_json: str) -> Callable:
    """Family C: parse JSON and verify BOTH keys and actual values."""
    gold_obj = json.loads(gold_json)

    def check(ans: str, g) -> bool:
        raw = _extract_final_answer(ans)
        try:
            obj = json.loads(raw)
        except Exception:  # noqa: BLE001
            return False
        if not isinstance(obj, dict):
            return False
        for k, v in gold_obj.items():
            if k not in obj:
                return False
            if obj[k] != v:
                return False
        return True
    return check


# ---------------------------------------------------------------------------
# R5: real template-specific generation rules.
# Train templates (TA1-TA7 / TB1-TB5) and val templates (TA8-TA12 / TB6-TB9)
# are DISJOINT sets with different surface forms.
# ---------------------------------------------------------------------------

# Family A templates: arithmetic word problems, distinct wording rules.
# Each template produces input text differently from the same (a,b,c) numbers.
_A_TEMPLATES: Dict[str, Callable[[int, int, int], Tuple[str, str]]] = {
    # returns (input_text, gold_string)
    "TA1": lambda a, b, c: (
        f"If x={a} and y={b}, what is {a}*{c}+{b}?", str(a * c + b)),
    "TA2": lambda a, b, c: (
        f"Calculate {a} times {c}, then add {b}. What do you get?", str(a * c + b)),
    "TA3": lambda a, b, c: (
        f"Compute the value of {a}*{c}+{b}. Give only the number.", str(a * c + b)),
    "TA4": lambda a, b, c: (
        f"A box holds {c} rows of {a} items, plus {b} extras. How many items in total?", str(a * c + b)),
    "TA5": lambda a, b, c: (
        f"What is the result of {c} groups of {a} plus {b} more?", str(a * c + b)),
    "TA6": lambda a, b, c: (
        f"Evaluate: {a}*{c}+{b} = ?", str(a * c + b)),
    "TA7": lambda a, b, c: (
        f"Find {a}*{c}+{b}. Answer with the numeric value only.", str(a * c + b)),
    # --- validation-only templates (disjoint from train) ---
    "TA8": lambda a, b, c: (
        f"Multiply {a} by {c} and then increase the product by {b}. State the number.", str(a * c + b)),
    "TA9": lambda a, b, c: (
        f"First take {a} copies of {c}, then include {b} additional units. Total count?", str(a * c + b)),
    "TA10": lambda a, b, c: (
        f"Express as a single number: {a}×{c}+{b}.", str(a * c + b)),
    "TA11": lambda a, b, c: (
        f"Given x={a}, y={b}, z={c}, report x*z+y.", str(a * c + b)),
    "TA12": lambda a, b, c: (
        f"How many are {c} groups of {a} together with {b}?", str(a * c + b)),
}

# Family B templates: compute then string-transform. Gold is "{sum}-{STRING}".
_B_TEMPLATES: Dict[str, Callable[[int, int, str], Tuple[str, str]]] = {
    "TB1": lambda a, b, s: (
        f"Compute {a}+{b} and then transform the string {s} to upper case. Give as SUM-STRING.",
        f"{a+b}-{s.upper()}"),
    "TB2": lambda a, b, s: (
        f"First calculate {a} plus {b}. Then convert '{s}' to uppercase. Answer in the form N-TEXT.",
        f"{a+b}-{s.upper()}"),
    "TB3": lambda a, b, s: (
        f"Add {a} and {b}. Also make {s} all capitals. Join them with a hyphen, number first.",
        f"{a+b}-{s.upper()}"),
    "TB4": lambda a, b, s: (
        f"Step 1: {a}+{b}. Step 2: upper-case the token {s}. Output SUM-TOKEN.",
        f"{a+b}-{s.upper()}"),
    "TB5": lambda a, b, s: (
        f"Combine the sum of {a} and {b} with the uppercased form of {s}, separated by '-' (sum first).",
        f"{a+b}-{s.upper()}"),
    # --- validation-only templates (disjoint from train) ---
    "TB6": lambda a, b, s: (
        f"Take {a} and {b}, add them, then rewrite {s} in capitals. Present as SUM-WORD.",
        f"{a+b}-{s.upper()}"),
    "TB7": lambda a, b, s: (
        f"What is {a}+{b}? And what is {s} in upper case? Reply as SUM-UPPER.",
        f"{a+b}-{s.upper()}"),
    "TB8": lambda a, b, s: (
        f"Total of {a} and {b}, hyphen, then {s} shouted (uppercase).",
        f"{a+b}-{s.upper()}"),
    "TB9": lambda a, b, s: (
        f"Report two things joined by '-': the sum {a}+{b}, and {s} upper-cased.",
        f"{a+b}-{s.upper()}"),
}

# Family C templates: structured JSON output. Gold values checked (R1).
_C_TEMPLATES: Dict[str, Callable[[int, int], Tuple[str, dict]]] = {
    "TC1": lambda a, b: (
        f"Output JSON with keys sum and product for numbers {a} and {b}.",
        {"sum": a + b, "product": a * b}),
    "TC2": lambda a, b: (
        f"Return a JSON object containing 'sum' ({a}+{b}) and 'product' ({a}*{b}).",
        {"sum": a + b, "product": a * b}),
    "TC3": lambda a, b: (
        f"Give JSON with fields sum and product computed from {a} and {b}.",
        {"sum": a + b, "product": a * b}),
    "TC4": lambda a, b: (
        f"For the pair ({a},{b}) produce JSON: sum and product.",
        {"sum": a + b, "product": a * b}),
    "TC5": lambda a, b: (
        f"Compute sum={a}+{b} and product={a}*{b}; write the answer as JSON.",
        {"sum": a + b, "product": a * b}),
}

TRAIN_TEMPLATES_A = ["TA1", "TA2", "TA3", "TA4", "TA5", "TA6", "TA7"]
VAL_TEMPLATES_A = ["TA8", "TA9", "TA10", "TA11", "TA12"]
TRAIN_TEMPLATES_B = ["TB1", "TB2", "TB3", "TB4", "TB5"]
VAL_TEMPLATES_B = ["TB6", "TB7", "TB8", "TB9"]
TEST_TEMPLATES_C = ["TC1", "TC2", "TC3", "TC4", "TC5"]


def build_task(task_id: str, family: str, seed: int, template_id: str) -> dict:
    nxt = _rng(task_id, seed)
    if family == FAMILY_A:
        if template_id not in _A_TEMPLATES:
            raise ValueError(f"unknown A template {template_id}")
        a = 2 + nxt(1) % 30
        b = 2 + nxt(2) % 30
        c = 2 + nxt(3) % 10
        input_text, gold = _A_TEMPLATES[template_id](a, b, c)
        return {
            "task_id": task_id, "family": family, "seed": seed, "template_id": template_id,
            "input": input_text, "gold": gold,
            "gold_check": _check_family_a(gold),
            "required_tools": ["calc"], "required_prompt_keywords": ["compute"],
        }
    if family == FAMILY_B:
        if template_id not in _B_TEMPLATES:
            raise ValueError(f"unknown B template {template_id}")
        a = 2 + nxt(1) % 20
        b = 2 + nxt(2) % 20
        s = "ab" + str(nxt(3) % 100)
        input_text, gold = _B_TEMPLATES[template_id](a, b, s)
        return {
            "task_id": task_id, "family": family, "seed": seed, "template_id": template_id,
            "input": input_text, "gold": gold,
            "gold_check": _check_family_b(gold),
            "required_tools": ["calc", "str_ops"], "required_prompt_keywords": ["transform"],
        }
    if family == FAMILY_C:
        if template_id not in _C_TEMPLATES:
            raise ValueError(f"unknown C template {template_id}")
        a = 1 + nxt(1) % 9
        b = 1 + nxt(2) % 9
        input_text, gold_obj = _C_TEMPLATES[template_id](a, b)
        gold = json.dumps(gold_obj, sort_keys=True)
        return {
            "task_id": task_id, "family": family, "seed": seed, "template_id": template_id,
            "input": input_text, "gold": gold,
            "gold_check": _check_family_c(gold),
            "required_tools": ["str_ops"], "required_prompt_keywords": ["format", "json"],
        }
    raise ValueError(f"unknown family {family}")


def generate_split(
    family: str,
    prefix: str,
    n: int,
    seed_start: int,
    templates: List[str],
) -> List[dict]:
    tasks = []
    for i in range(n):
        tid = f"{prefix}-{i:04d}"
        seed = seed_start + i
        t = build_task(tid, family, seed, templates[i % len(templates)])
        tasks.append(_serializable(t))
    return tasks


def _serializable(t: dict) -> dict:
    return {
        "task_id": t["task_id"],
        "family": t["family"],
        "seed": t["seed"],
        "template_id": t["template_id"],
        "input": t["input"],
        "gold": t["gold"],
        "required_tools": t["required_tools"],
        "required_prompt_keywords": t["required_prompt_keywords"],
    }


def attach_checker(t: dict) -> dict:
    """Re-attach gold_check from serializable fields (evaluator-side)."""
    fam = t["family"]
    if fam == FAMILY_A:
        t["gold_check"] = _check_family_a(t["gold"])
    elif fam == FAMILY_B:
        t["gold_check"] = _check_family_b(t["gold"])
    elif fam == FAMILY_C:
        t["gold_check"] = _check_family_c(t["gold"])
    else:
        raise ValueError(fam)
    return t


SPLIT_SPEC = {
    "train_A": {"family": FAMILY_A, "prefix": "A", "n": 200, "seed_start": 0, "templates": TRAIN_TEMPLATES_A},
    "train_B": {"family": FAMILY_B, "prefix": "B", "n": 200, "seed_start": 0, "templates": TRAIN_TEMPLATES_B},
    "val_A": {"family": FAMILY_A, "prefix": "Av", "n": 50, "seed_start": 1000, "templates": VAL_TEMPLATES_A},
    "val_B": {"family": FAMILY_B, "prefix": "Bv", "n": 50, "seed_start": 1000, "templates": VAL_TEMPLATES_B},
    "test_C": {"family": FAMILY_C, "prefix": "C", "n": 100, "seed_start": 0, "templates": TEST_TEMPLATES_C},
}
