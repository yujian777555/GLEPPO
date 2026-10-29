"""R3 metric separation: correctness, output format, and hard tool-path validity.

These metrics intentionally remain independent. A correct answer does not excuse
a broken required tool path, and a path-valid run is not automatically correct.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .tool_path import verify_tool_path_for_task

FORMAT_PREFIX = "Final answer: "
MAX_ANSWER_VALUE_CHARS = 100


def check_format_compliant(answer: str) -> bool:
    """Frozen R3 format: exact prefix, non-empty value, <=100 chars, one line."""
    if not isinstance(answer, str) or not answer.startswith(FORMAT_PREFIX):
        return False
    value = answer[len(FORMAT_PREFIX):]
    if not value.strip() or len(value) > MAX_ANSWER_VALUE_CHARS:
        return False
    if "\n" in value or "\r" in value:
        return False
    return True


def evaluate_r3_metrics(answer: str, task: dict, genotype: Any,
                        trace: List[Dict]) -> Dict[str, Any]:
    """Compute answer correctness independently of execution/path/format flags."""
    try:
        answer_correct = bool(task["gold_check"](answer, genotype))
    except Exception:  # noqa: BLE001 - malformed answer is incorrect, not a crash
        answer_correct = False

    format_ok = check_format_compliant(answer)
    path_details = verify_tool_path_for_task(
        task["task_id"], trace, task.get("required_tools", [])
    )
    path_ok = bool(path_details.get("passed"))
    hard_validity = format_ok and path_ok
    return {
        "answer_correct": answer_correct,
        "format_compliant": format_ok,
        "tool_path_valid": path_ok,
        "hard_validity": hard_validity,
        "effective_success": answer_correct and hard_validity,
        "tool_path_details": path_details,
    }
