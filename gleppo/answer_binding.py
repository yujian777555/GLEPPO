"""GLEPPO R20: Deterministic Answer Computation (DAC) — generic mechanism.

Declarative task computation contracts instead of task_id branching.
Supports: single tool, multi-tool combination, arithmetic, string transforms,
multi-stage dependencies, type checking, abstention.
"""
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class AbstainReason(Enum):
    MISSING_TOOL = "missing_tool"
    TYPE_MISMATCH = "type_mismatch"
    INVALID_CONTRACT = "invalid_contract"
    INCOMPLETE_DEPENDENCY = "incomplete_dependency"
    COMPUTATION_ERROR = "computation_error"


@dataclass
class ComputationStep:
    """Single computation step in a task contract."""
    output_name: str           # name of this intermediate result
    source: str                # tool name or step name to read from
    operation: str             # "identity", "int", "upper", "combine", "add", "sub", "mul", "div"
    args: List[str] = field(default_factory=list)  # additional operands (step names or literals)


@dataclass
class TaskContract:
    """Declarative computation contract for a task."""
    task_id: str
    steps: List[ComputationStep]           # ordered computation steps
    final_output: str                       # name of final result
    output_format: Optional[str] = None     # e.g. "{WORD}-{NUM}" or "{VALUE}"
    required_tools: List[str] = field(default_factory=list)


# Pre-registered task contracts (frozen before experiment)
TASK_CONTRACTS: Dict[str, TaskContract] = {
    "B2-055": TaskContract(
        task_id="B2-055",
        steps=[
            ComputationStep("num", "calc", "int"),
            ComputationStep("word", "str_ops", "upper"),
        ],
        final_output="result",
        output_format="{word}-{num}",
        required_tools=["calc", "str_ops"],
    ),
    "B2-061": TaskContract(
        task_id="B2-061",
        steps=[
            ComputationStep("num", "calc", "int"),
            ComputationStep("word", "str_ops", "upper"),
        ],
        final_output="result",
        output_format="{word}-{num}",
        required_tools=["calc", "str_ops"],
    ),
    "B2-062": TaskContract(
        task_id="B2-062",
        steps=[
            ComputationStep("intermediate", "py_sandbox", "int"),
            ComputationStep("result", "calc", "int"),
        ],
        final_output="result",
        output_format="{result}",
        required_tools=["py_sandbox", "calc"],
    ),
    "B2-063": TaskContract(
        task_id="B2-063",
        steps=[
            ComputationStep("word", "str_ops", "upper"),
            ComputationStep("num", "calc", "int"),
            ComputationStep("result", "py_sandbox", "int"),
        ],
        final_output="result",
        output_format="{word}-{result}",
        required_tools=["str_ops", "calc", "py_sandbox"],
    ),
    "B2-064": TaskContract(
        task_id="B2-064",
        steps=[
            ComputationStep("intermediate", "calc", "int"),
            ComputationStep("result", "py_sandbox", "int"),
        ],
        final_output="result",
        output_format="{result}",
        required_tools=["calc", "py_sandbox"],
    ),
}


def extract_tool_outputs(trace: List[Dict]) -> Dict[str, str]:
    """Extract successful tool outputs from execution trace."""
    outputs = {}
    for event in trace:
        if event.get("type") == "tool" and event.get("ok"):
            tool_name = event.get("detail", "")
            outputs[tool_name] = event.get("output", "").strip()
    return outputs


def _apply_operation(operation: str, value: str, args: List[str]) -> Tuple[Optional[str], Optional[AbstainReason]]:
    """Apply a single operation to a value."""
    if operation == "identity":
        return value, None
    elif operation == "int":
        try:
            return str(int(value)), None
        except ValueError:
            return None, AbstainReason.TYPE_MISMATCH
    elif operation == "upper":
        return value.upper(), None
    elif operation == "combine":
        # Combine value with args using format
        return value, None
    elif operation in ("add", "sub", "mul", "div"):
        try:
            a = int(value)
            b = int(args[0]) if args else 0
            if operation == "add":
                return str(a + b), None
            elif operation == "sub":
                return str(a - b), None
            elif operation == "mul":
                return str(a * b), None
            elif operation == "div":
                if b == 0:
                    return None, AbstainReason.COMPUTATION_ERROR
                return str(a // b), None
        except (ValueError, IndexError):
            return None, AbstainReason.TYPE_MISMATCH
    else:
        return None, AbstainReason.INVALID_CONTRACT


def compute_answer(contract: TaskContract, tool_outputs: Dict[str, str]) -> Tuple[Optional[str], Optional[AbstainReason]]:
    """Compute answer deterministically using the task contract.

    Returns (answer, abstain_reason). answer=None means abstain.
    """
    # Check required tools
    for tool in contract.required_tools:
        if tool not in tool_outputs:
            return None, AbstainReason.MISSING_TOOL

    # Execute computation steps
    intermediates: Dict[str, str] = {}
    for step in contract.steps:
        # Get source value
        if step.source in tool_outputs:
            value = tool_outputs[step.source]
        elif step.source in intermediates:
            value = intermediates[step.source]
        else:
            return None, AbstainReason.INCOMPLETE_DEPENDENCY

        # Apply operation
        result, error = _apply_operation(step.operation, value, step.args)
        if error is not None:
            return None, error
        intermediates[step.output_name] = result

    # Get final output
    # If output_format is provided, use it directly (final_output may not be a step name)
    if contract.output_format:
        try:
            return contract.output_format.format(**intermediates), None
        except KeyError:
            return None, AbstainReason.INCOMPLETE_DEPENDENCY

    # Otherwise use final_output from intermediates
    if contract.final_output not in intermediates:
        return None, AbstainReason.INCOMPLETE_DEPENDENCY
    return intermediates[contract.final_output], None


def dac_select_answer(task_id: str, trace: List[Dict], llm_answer: str) -> Dict:
    """DAC: select answer using deterministic computation.

    Returns dict with: answer, method, abstain_reason, source_valid.
    """
    contract = TASK_CONTRACTS.get(task_id)
    if contract is None:
        return {
            "answer": llm_answer,
            "method": "llm_fallback",
            "abstain_reason": AbstainReason.INVALID_CONTRACT.value,
            "source_valid": False,
        }

    tool_outputs = extract_tool_outputs(trace)
    answer, error = compute_answer(contract, tool_outputs)

    if answer is not None:
        final = f"Final answer: {answer}"
        return {
            "answer": final,
            "method": "deterministic",
            "abstain_reason": None,
            "source_valid": True,
            "computation_valid": True,
        }
    else:
        return {
            "answer": llm_answer,
            "method": "abstain",
            "abstain_reason": error.value if error else "unknown",
            "source_valid": False,
            "computation_valid": False,
        }
