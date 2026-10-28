"""Five frozen evolution operators (K=5).

prompt_local_edit is DETERMINISTIC with 0 LLM calls (RUNTIME_LOCK resolution).
"""
from __future__ import annotations

import copy
import hashlib
import re
from typing import Callable, List, Optional, Tuple

from .genotype import Genotype, Step, is_valid, validate_genotype, behavior_hash

OPERATOR_NAMES = (
    "prompt_local_edit",
    "prompt_critique_rewrite",
    "tool_subset_edit",
    "workflow_step_edit",
    "crossover",
)

# Deterministic synonym table for prompt_local_edit (template paraphrase, 0 LLM).
_SYNONYMS = [
    (r"\bcompute\b", "calculate"),
    (r"\bcalculate\b", "compute"),
    (r"\bstep by step\b", "step-by-step"),
    (r"\bstep-by-step\b", "step by step"),
    (r"\btransform\b", "convert"),
    (r"\bconvert\b", "transform"),
    (r"\bresult\b", "output"),
    (r"\boutput\b", "result"),
    (r"\bformat\b", "structure"),
    (r"\bstructure\b", "format"),
]


def _stable_hash(*parts: object) -> int:
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


def op_prompt_local_edit(parent: Genotype, ctx: dict) -> Genotype:
    child = parent.copy()
    prompt = child.system_prompt
    changed = False
    for pat, repl in _SYNONYMS:
        if re.search(pat, prompt, flags=re.IGNORECASE):
            prompt = re.sub(pat, repl, prompt, count=1, flags=re.IGNORECASE)
            changed = True
            break
    if not changed:
        # guaranteed visible change: append a neutral token (still valid)
        prompt = prompt.replace("Final answer:", "Final answer now:")
    child.system_prompt = prompt
    return child


def op_prompt_critique_rewrite(parent: Genotype, ctx: dict) -> Genotype:
    """Production: 2 LLM calls. Stub mode: deterministic rewrite from failure trace (0 LLM)."""
    child = parent.copy()
    failure = ctx.get("failure_category", "")
    trace_note = ctx.get("failure_detail", "")[:200]
    # Deterministic rebuild that responds to failure category (uses execution feedback).
    base = "Compute step by step and then transform the result. Use tools when needed. Final answer: {{answer}}"
    if failure == "tool_error":
        base = "Compute step by step with careful tool inputs and then transform the result. Final answer: {{answer}}"
    elif failure == "wrong_answer":
        base = "Calculate intermediate values explicitly, compute each sub-expression, then transform. Final answer: {{answer}}"
    elif failure == "format_error":
        base = "Format output as exact JSON keys requested. Transform and structure the answer. Final answer: {{answer}}"
    elif failure == "timeout":
        base = "Compute briefly. Step by step, short turns. Final answer: {{answer}}"
    if trace_note:
        base = base.replace("Final answer:", f"(ref: {trace_note[:40]}) Final answer:")
    child.system_prompt = base
    return child


def op_tool_subset_edit(parent: Genotype, ctx: dict) -> Genotype:
    """C7-B: tool subset mutation with workflow dependency handling.

    Guarantees:
    - All children pass validate_genotype.
    - Workflow steps only reference enabled tools.
    - Adding a tool may or may not enter the execution path (documented).
    - Dropping a tool safely handles workflow references.
    """
    child = parent.copy()
    all_tools = ["calc", "py_sandbox", "str_ops"]
    current = sorted(child.tools)
    missing = [t for t in all_tools if t not in current]
    present = [t for t in all_tools if t in current]

    # Find tools referenced in workflow
    workflow_tools = set()
    for step in child.workflow:
        if step.tool:
            workflow_tools.add(step.tool)

    gen = int(ctx.get("gen", 0))

    if gen % 2 == 0 and len(current) > 1:
        # Drop mode: prefer dropping tools NOT referenced in workflow
        droppable = [t for t in present if t not in workflow_tools]
        if droppable:
            child.tools = sorted(set(current) - {droppable[-1]})
        else:
            # All tools referenced — drop one and fix ALL workflow references
            drop_tool = present[-1]
            child.tools = sorted(set(current) - {drop_tool})
            replacement = child.tools[0] if child.tools else "calc"
            for step in child.workflow:
                if step.tool == drop_tool:
                    step.tool = replacement
    elif missing:
        # C7-R1-C1-B: add missing tool AND add workflow step with valid input
        new_tool = missing[0]
        child.tools = sorted(set(current) | {new_tool})
        # Add a tool step before finalize with tool-appropriate input
        finalize_idx = None
        for idx, step in enumerate(child.workflow):
            if step.type == "finalize":
                finalize_idx = idx
                break
        if finalize_idx is not None and len(child.workflow) < 6:
            tool_step = Step(type="tool", tool=new_tool, input_from="task")
            child.workflow.insert(finalize_idx, tool_step)
        child.meta["added_tool"] = new_tool
        child.meta["added_tool_in_workflow"] = True
    elif len(current) > 1:
        droppable = [t for t in present if t not in workflow_tools]
        if droppable:
            child.tools = sorted(set(current) - {droppable[-1]})
        else:
            drop_tool = present[-1]
            child.tools = sorted(set(current) - {drop_tool})
            replacement = child.tools[0] if child.tools else "calc"
            for step in child.workflow:
                if step.tool == drop_tool:
                    step.tool = replacement
    else:
        if missing:
            child.tools = sorted(set(current) | {missing[0]})
            child.meta["added_tool"] = missing[0]

    # C7-B: ensure ALL workflow tool references are valid
    for step in child.workflow:
        if step.tool and step.tool not in child.tools:
            step.tool = child.tools[0] if child.tools else "calc"
    return child


_STEP_TEMPLATES = [
    Step(type="llm", prompt_slot="analyze", input_from="task"),
    Step(type="tool", tool="calc", input_from="analyze"),
    Step(type="tool", tool="str_ops", input_from="calc"),
    Step(type="tool", tool="py_sandbox", input_from="analyze"),
    Step(type="llm", prompt_slot="plan", input_from="task"),
]


def op_workflow_step_edit(parent: Genotype, ctx: dict) -> Genotype:
    child = parent.copy()
    wf = [copy.deepcopy(s) for s in child.workflow if s.type != "finalize"]
    if not wf:
        return child
    idx = _stable_hash(parent.meta.get("parent_id", ""), ctx.get("gen", 0), "wf") % len(wf)
    cand = _STEP_TEMPLATES[_stable_hash("tpl", idx, ctx.get("gen", 0)) % len(_STEP_TEMPLATES)]
    # ensure tool step's tool is enabled
    step = copy.deepcopy(cand)
    if step.type == "tool" and step.tool not in child.tools:
        step.tool = child.tools[0]
    wf[idx] = step
    finalize = [copy.deepcopy(s) for s in child.workflow if s.type == "finalize"]
    child.workflow = wf + finalize
    return child


def op_crossover(parent: Genotype, ctx: dict) -> Genotype:
    """C7-R1-C2-C: meaningful strategy recombination with strict validation.

    C1: validates both parents before crossover.
    C2: tracks actual inherited content from final child.
    """
    mate: Optional[Genotype] = ctx.get("mate")
    if mate is None or mate is parent:
        mate = parent
    # C1: validate both parents
    p_errors = validate_genotype(parent)
    m_errors = validate_genotype(mate)
    if p_errors:
        raise ValueError(f"C1: invalid parent: {p_errors}")
    if m_errors:
        raise ValueError(f"C1: invalid mate: {m_errors}")
    child = parent.copy()

    # 1. Prompt strategy recombination: take strategy keywords from both
    p_prompt = parent.system_prompt
    m_prompt = mate.system_prompt
    # Extract strategy sentences (those containing key words)
    strategy_words = {"compute", "transform", "step", "tool", "final", "answer", "format"}
    p_strat = [s for s in re.split(r"(?<=[.!?])\s+", p_prompt) if any(w in s.lower() for w in strategy_words)]
    m_strat = [s for s in re.split(r"(?<=[.!?])\s+", m_prompt) if any(w in s.lower() for w in strategy_words)]
    # Take half from each parent
    half = max(1, len(p_strat) // 2)
    mixed_strat = p_strat[:half] + m_strat[:half]
    if not mixed_strat:
        mixed_strat = p_strat or m_strat or [p_prompt]
    child.system_prompt = " ".join(mixed_strat)
    if "{{answer}}" not in child.system_prompt and "final answer" not in child.system_prompt.lower():
        child.system_prompt += " Final answer: {{answer}}"

    # 2. Tool subset: union with cap, ensure workflow compatibility
    tools = sorted(set(parent.tools) | set(mate.tools))
    if len(tools) > 3:
        # Prefer tools used in either workflow
        wf_tools = set()
        for g in [parent, mate]:
            for s in g.workflow:
                if s.tool:
                    wf_tools.add(s.tool)
        priority = [t for t in tools if t in wf_tools] + [t for t in tools if t not in wf_tools]
        tools = sorted(priority[:3])
    child.tools = tools

    # 3. Workflow recombination: alternate steps, ensure validity
    wf = []
    max_len = max(len(parent.workflow), len(mate.workflow))
    for i in range(max_len):
        src = parent.workflow if i % 2 == 0 else mate.workflow
        if i < len(src):
            step = copy.deepcopy(src[i])
            # Fix tool references to match child's tools
            if step.tool and step.tool not in child.tools:
                step.tool = child.tools[0] if child.tools else "calc"
            wf.append(step)
    # Ensure exactly one finalize at end
    fin = [s for s in wf if s.type == "finalize"]
    body = [s for s in wf if s.type != "finalize"]
    if not fin:
        fin = [Step(type="finalize", prompt_slot="answer", input_from="task")]
    child.workflow = body + [fin[0]]

    # C2: record ACTUAL inherited content based on final child
    # Distinguish parent-unique, mate-unique, shared, and selected
    p_unique = [s for s in p_strat if s not in m_strat]
    m_unique = [s for s in m_strat if s not in p_strat]
    shared = [s for s in p_strat if s in m_strat]
    selected_from_parent = [s for s in p_unique if s in child.system_prompt]
    selected_from_mate = [s for s in m_unique if s in child.system_prompt]
    selected_shared = [s for s in shared if s in child.system_prompt]

    p_tools_unique = sorted(set(parent.tools) - set(mate.tools))
    m_tools_unique = sorted(set(mate.tools) - set(parent.tools))
    shared_tools = sorted(set(parent.tools) & set(mate.tools))

    child.meta["crossover_parent"] = behavior_hash(parent)[:8]
    child.meta["crossover_mate"] = behavior_hash(mate)[:8]
    child.meta["inherited_strategies"] = {
        "from_parent_unique": selected_from_parent,
        "from_mate_unique": selected_from_mate,
        "from_shared": selected_shared,
        "from_parent_tools": [t for t in p_tools_unique if t in child.tools],
        "from_mate_tools": [t for t in m_tools_unique if t in child.tools],
        "from_shared_tools": [t for t in shared_tools if t in child.tools],
    }
    # C2: final child behavior hash for verification
    child.meta["crossover_child_hash"] = behavior_hash(child)[:8]
    return child


_OPS: dict[str, Callable[[Genotype, dict], Genotype]] = {
    "prompt_local_edit": op_prompt_local_edit,
    "prompt_critique_rewrite": op_prompt_critique_rewrite,
    "tool_subset_edit": op_tool_subset_edit,
    "workflow_step_edit": op_workflow_step_edit,
    "crossover": op_crossover,
}

OPERATORS = _OPS


def apply_operator(name: str, parent: Genotype, ctx: Optional[dict] = None) -> Tuple[Genotype, bool, List[str]]:
    """Return (child, valid, errors). Invalid children are dropped (never parent-cloned)."""
    if name not in _OPS:
        raise KeyError(name)
    ctx = ctx or {}
    raw = _OPS[name](parent, ctx)
    errs = validate_genotype(raw)
    if errs:
        return raw, False, errs
    return raw, True, []
