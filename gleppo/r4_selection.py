"""R4: Static pre-execution hard constraint filter (S1) and selection (S2).

S1 uses ONLY pre-execution information:
- Tool registry membership
- Workflow references valid tools
- Required tools appear in workflow in correct order (as subsequence)
- Genotype passes structural validation
- Does NOT use gold answers, execution results, or LLM outputs

S2 adds static parent-child comparison (behavior_hash, workflow, tools).
"""
from typing import Dict, List, Optional, Tuple

from .genotype import Genotype, validate_genotype, behavior_hash, ALLOWED_TOOLS

# Frozen task contracts: ordered (tool_name, expected_output) pairs.
# These are the PRE-DECLARED contracts, not execution results.
R4_TOOL_CONTRACTS = {
    "B2-001": [("calc", "64"), ("str_ops", "SUM")],
    "B2-003": [("calc", "60"), ("str_ops", "HI")],
    "B2-004": [("py_sandbox", "32"), ("calc", "41")],
    "B2-005": [("calc", "58"), ("py_sandbox", "71")],
    "B2-006": [("calc", "40"), ("str_ops", "FINAL"), ("py_sandbox", "42")],
}


def _extract_workflow_tool_sequence(g: Genotype) -> List[str]:
    """Extract ordered tool names from workflow steps."""
    return [s.tool for s in g.workflow if s.type == "tool" and s.tool]


def _is_subsequence(sub: List[str], seq: List[str]) -> bool:
    """Check if `sub` appears as an ordered subsequence in `seq`."""
    it = iter(seq)
    return all(item in it for item in sub)


def static_check_s1(g: Genotype, task_id: str) -> Dict:
    """S1: static pre-execution hard constraint filter.

    Returns dict with 'pass', 'violations', 'not_checkable'.
    Uses ONLY pre-execution information.
    """
    violations = []
    not_checkable = []

    # 1. Genotype structural validation
    struct_errors = validate_genotype(g)
    if struct_errors:
        violations.append(f"structural: {struct_errors}")

    # 2. All tools in registry
    for t in g.tools:
        if t not in ALLOWED_TOOLS:
            violations.append(f"tool_not_in_registry: {t}")

    # 3. Workflow references only enabled tools
    for s in g.workflow:
        if s.type == "tool" and s.tool and s.tool not in g.tools:
            violations.append(f"workflow_tool_not_enabled: {s.tool}")

    # 4. Required tools in workflow as ordered subsequence
    contract = R4_TOOL_CONTRACTS.get(task_id)
    if contract:
        required_tools = [t for t, _ in contract]
        wf_tools = _extract_workflow_tool_sequence(g)
        if not _is_subsequence(required_tools, wf_tools):
            violations.append(
                f"required_tools_not_in_order: need {required_tools}, have {wf_tools}"
            )
    else:
        not_checkable.append(f"no_contract_for_{task_id}")

    return {
        "pass": len(violations) == 0,
        "violations": violations,
        "not_checkable": not_checkable,
    }


def static_check_s2(parent: Genotype, child: Genotype, task_id: str) -> Dict:
    """S2: S1 + static parent-child selection.

    Uses ONLY static features:
    - S1 on child (must pass to be accepted)
    - behavior_hash difference (structural change)
    - workflow step count difference
    - tool set difference
    - Does NOT use answer_correct, execution traces, or gold labels
    """
    s1_result = static_check_s1(child, task_id)
    if not s1_result["pass"]:
        return {
            "accepted": False,
            "reason": "S1_failed",
            "s1": s1_result,
            "static_features": {},
        }

    # Static feature comparison
    parent_hash = behavior_hash(parent)
    child_hash = behavior_hash(child)
    parent_wf_len = len(parent.workflow)
    child_wf_len = len(child.workflow)
    parent_tools = set(parent.tools)
    child_tools = set(child.tools)

    # S2 acceptance: child must have structural differences (meaningful change)
    # AND pass S1. If identical, no point accepting.
    has_change = parent_hash != child_hash

    static_features = {
        "hash_changed": parent_hash != child_hash,
        "wf_step_delta": child_wf_len - parent_wf_len,
        "tools_added": sorted(child_tools - parent_tools),
        "tools_removed": sorted(parent_tools - child_tools),
        "parent_hash": parent_hash[:12],
        "child_hash": child_hash[:12],
    }

    return {
        "accepted": has_change,
        "reason": "accepted" if has_change else "no_structural_change",
        "s1": s1_result,
        "static_features": static_features,
    }


def run_selection_mechanisms(
    parent: Genotype,
    child: Genotype,
    task_id: str,
    parent_result: Optional[Dict] = None,
    child_result: Optional[Dict] = None,
) -> Dict:
    """Run all four selection mechanisms on the same frozen candidate pair.

    S0: Unfiltered — accept if structurally valid.
    S1: Static hard constraint filter.
    S2: S1 + static parent-child selection.
    S3: Post-execution diagnostic (requires parent_result, child_result).
    """
    # S0: accept all structurally valid
    s0_valid = len(validate_genotype(child)) == 0

    # S1
    s1 = static_check_s1(child, task_id)

    # S2
    s2 = static_check_s2(parent, child, task_id)

    # S3: post-execution diagnostic
    s3 = {"pass": None, "note": "requires_execution"}
    if child_result is not None:
        s3 = {
            "pass": child_result.get("tool_path_valid", False)
            and child_result.get("format_compliant", False),
            "tool_path_valid": child_result.get("tool_path_valid", False),
            "format_compliant": child_result.get("format_compliant", False),
            "note": "POST_EXECUTION_DIAGNOSTIC",
        }

    return {
        "S0_unfiltered": {"accepted": s0_valid},
        "S1_static_filter": s1,
        "S2_static_select": s2,
        "S3_post_exec_diag": s3,
    }
