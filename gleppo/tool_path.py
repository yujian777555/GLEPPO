"""G3-DIAG-v2: Tool path verification.

Phase 1 requirement 5-6: evaluator must independently verify tool call paths.
- B2-002: must verify py_sandbox AND calc were actually called
- B2-003: must verify str_ops actually executed string transformation
"""
from typing import Dict, List, Set


def verify_tool_path(trace: List[Dict], required_tools: List[str]) -> Dict:
    """Verify that required tools were actually called in the execution trace.

    Args:
        trace: execution trace from Interpreter.run()
        required_tools: list of tool names that must be called

    Returns:
        dict with 'passed', 'called_tools', 'missing_tools', 'tool_outputs'
    """
    called_tools: Set[str] = set()
    tool_outputs: Dict[str, str] = {}

    for event in trace:
        if event.get("type") == "tool" and event.get("ok"):
            tool_name = event.get("detail", "")
            called_tools.add(tool_name)
            tool_outputs[tool_name] = event.get("output", "")

    missing_tools = [t for t in required_tools if t not in called_tools]

    return {
        "passed": len(missing_tools) == 0,
        "called_tools": sorted(called_tools),
        "missing_tools": missing_tools,
        "tool_outputs": tool_outputs,
    }


def verify_tool_path_b2_001(trace: List[Dict]) -> Dict:
    """B2-001: verify calc AND str_ops were called.

    Expected: calc computes 25*3-11=64, str_ops transforms 'sum'->'SUM'
    """
    result = verify_tool_path(trace, ["calc", "str_ops"])

    # Additional check: verify str_ops output is 'SUM'
    if "str_ops" in result["tool_outputs"]:
        strops_out = result["tool_outputs"]["str_ops"].strip().upper()
        result["strops_output_correct"] = strops_out == "SUM"
    else:
        result["strops_output_correct"] = False

    result["passed"] = result["passed"] and result.get("strops_output_correct", False)
    return result


def verify_tool_path_b2_002(trace: List[Dict]) -> Dict:
    """B2-002: verify py_sandbox AND calc were called.

    Expected: py_sandbox computes 14*3+7=49, calc computes 49-6=43
    """
    result = verify_tool_path(trace, ["py_sandbox", "calc"])

    # Additional check: verify py_sandbox output is 49
    if "py_sandbox" in result["tool_outputs"]:
        ps_out = result["tool_outputs"]["py_sandbox"].strip()
        result["py_sandbox_output_correct"] = ps_out == "49"
    else:
        result["py_sandbox_output_correct"] = False

    result["passed"] = result["passed"] and result.get("py_sandbox_output_correct", False)
    return result


def verify_tool_path_b2_003(trace: List[Dict]) -> Dict:
    """B2-003: verify calc AND str_ops were called.

    Expected: calc computes 8*8-4=60, str_ops transforms 'hi'->'HI'
    """
    result = verify_tool_path(trace, ["calc", "str_ops"])

    # Additional check: verify str_ops output is 'HI'
    if "str_ops" in result["tool_outputs"]:
        strops_out = result["tool_outputs"]["str_ops"].strip().upper()
        result["strops_output_correct"] = strops_out == "HI"
    else:
        result["strops_output_correct"] = False

    result["passed"] = result["passed"] and result.get("strops_output_correct", False)
    return result


# Mapping of task_id to specialized verifier
TOOL_PATH_VERIFIERS = {
    "B2-001": verify_tool_path_b2_001,
    "B2-002": verify_tool_path_b2_002,
    "B2-003": verify_tool_path_b2_003,
}


def verify_tool_path_for_task(task_id: str, trace: List[Dict], required_tools: List[str]) -> Dict:
    """Dispatch to specialized verifier if available, else use generic."""
    if task_id in TOOL_PATH_VERIFIERS:
        return TOOL_PATH_VERIFIERS[task_id](trace)
    return verify_tool_path(trace, required_tools)
