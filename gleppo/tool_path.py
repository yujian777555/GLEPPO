"""G3-DIAG-v2-R1: Tool path verification with order and expected outputs.

Gate requirement: required tools must SUCCEED in the REQUIRED ORDER and return
the frozen expected outputs. Missing, reordered, failed, or wrong-output
events must cause verification to FAIL.
"""
from typing import Any, Dict, List, Optional, Tuple


# Frozen tool-path contracts for B2 tasks: ordered (tool_name, expected_output) pairs.
B2_TOOL_PATH_CONTRACTS: Dict[str, List[Tuple[str, str]]] = {
    "B2-001": [("calc", "64"), ("str_ops", "SUM")],
    "B2-002": [("py_sandbox", "49"), ("calc", "43")],
    "B2-003": [("calc", "60"), ("str_ops", "HI")],
    "B2-004": [("py_sandbox", "32"), ("calc", "41")],
}


def _extract_successful_tool_sequence(trace: List[Dict]) -> List[Tuple[str, str]]:
    """Extract ordered (tool_name, output) pairs for successful tool events."""
    seq = []
    for event in trace:
        if event.get("type") == "tool" and event.get("ok"):
            tool_name = event.get("detail", "")
            output = str(event.get("output", "")).strip()
            seq.append((tool_name, output))
    return seq


def _extract_all_tool_events(trace: List[Dict]) -> List[Dict]:
    """Extract all tool events (including failures) for diagnostics."""
    return [e for e in trace if e.get("type") == "tool"]


def verify_tool_path_ordered(trace: List[Dict],
                             contract: List[Tuple[str, str]]) -> Dict:
    """Verify tool path against an ordered contract of (tool, expected_output).

    A passing path must have successful tool calls matching the contract in
    the SAME ORDER with EXACT outputs. Extra successful tool calls before,
    between, or after the contract entries are allowed (they may come from
    other workflow steps), but the contract entries must appear as an ordered
    subsequence of the successful tool calls.
    """
    success_seq = _extract_successful_tool_sequence(trace)
    all_events = _extract_all_tool_events(trace)

    # Check each contract entry in order
    matched_indices = []
    contract_idx = 0
    for seq_idx, (tool_name, output) in enumerate(success_seq):
        if contract_idx >= len(contract):
            break
        expected_tool, expected_output = contract[contract_idx]
        if tool_name == expected_tool and output == expected_output:
            matched_indices.append(seq_idx)
            contract_idx += 1

    all_matched = contract_idx == len(contract)

    # Diagnostics
    called_success = [t for t, _ in success_seq]
    expected_tools = [t for t, _ in contract]
    expected_outputs = [o for _, o in contract]

    result = {
        "passed": all_matched,
        "contract": [{"tool": t, "expected_output": o} for t, o in contract],
        "successful_sequence": [{"tool": t, "output": o} for t, o in success_seq],
        "matched_contract_entries": contract_idx,
        "total_contract_entries": len(contract),
        "matched_indices": matched_indices,
        "all_tool_events": [
            {"tool": e.get("detail", ""), "ok": bool(e.get("ok")),
             "output": str(e.get("output", ""))[:100]}
            for e in all_events
        ],
    }

    if not all_matched:
        # Identify which entries failed
        missing = []
        for i in range(contract_idx, len(contract)):
            missing.append({"tool": contract[i][0], "expected_output": contract[i][1]})
        result["missing_or_wrong"] = missing

    return result


def verify_tool_path_for_task(task_id: str, trace: List[Dict],
                              required_tools: Optional[List[str]] = None) -> Dict:
    """Dispatch to the frozen contract for the given task_id.

    Falls back to presence-only check for tasks without a frozen contract.
    """
    if task_id in B2_TOOL_PATH_CONTRACTS:
        return verify_tool_path_ordered(trace, B2_TOOL_PATH_CONTRACTS[task_id])

    # Fallback: presence-only (for non-B2 tasks)
    tools = required_tools or []
    success_seq = _extract_successful_tool_sequence(trace)
    called = [t for t, _ in success_seq]
    missing = [t for t in tools if t not in called]
    return {
        "passed": len(missing) == 0,
        "contract": [{"tool": t, "expected_output": "(any)"} for t in tools],
        "successful_sequence": [{"tool": t, "output": o} for t, o in success_seq],
        "missing_tools": missing,
    }
