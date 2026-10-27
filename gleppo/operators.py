"""Five frozen evolution operators (K=5).

prompt_local_edit is DETERMINISTIC with 0 LLM calls (RUNTIME_LOCK resolution).
"""
from __future__ import annotations

import copy
import hashlib
import re
from typing import Callable, List, Optional, Tuple

from .genotype import Genotype, Step, is_valid, validate_genotype

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
    child = parent.copy()
    all_tools = ["calc", "py_sandbox", "str_ops"]
    current = sorted(child.tools)
    missing = [t for t in all_tools if t not in current]
    present = [t for t in all_tools if t in current]
    # Deterministic alternation by generation parity: even -> drop if possible, odd -> add if possible.
    gen = int(ctx.get("gen", 0))
    if gen % 2 == 0 and len(current) > 1:
        child.tools = sorted(set(current) - {present[-1]})
    elif missing:
        child.tools = sorted(set(current) | {missing[0]})
    elif len(current) > 1:
        child.tools = sorted(set(current) - {present[-1]})
    else:
        child.tools = sorted(set(current) | {missing[0]}) if missing else current
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
    mate: Optional[Genotype] = ctx.get("mate")
    if mate is None:
        mate = parent
    child = parent.copy()
    p_sent = [s for s in re.split(r"(?<=[.!?])\s+", parent.system_prompt.strip()) if s]
    m_sent = [s for s in re.split(r"(?<=[.!?])\s+", mate.system_prompt.strip()) if s]
    # Union preserving parent order first, then mate-only sentences.
    # Guarantees the child differs from the parent whenever the mate contributes
    # any sentence the parent lacks (G3-visible causality).
    mixed = list(p_sent)
    for s in m_sent:
        if s not in mixed:
            mixed.append(s)
    child.system_prompt = " ".join(mixed) if mixed else parent.system_prompt
    if "{{answer}}" not in child.system_prompt and "final answer" not in child.system_prompt.lower():
        child.system_prompt = child.system_prompt + " Final answer: {{answer}}"
    tools = sorted(set(parent.tools) | set(mate.tools))
    if len(tools) > 3:
        tools = tools[:3]
    child.tools = tools
    # workflow alternation
    wf = []
    for i in range(max(len(parent.workflow), len(mate.workflow))):
        src = parent.workflow if i % 2 == 0 else mate.workflow
        if i < len(src):
            wf.append(copy.deepcopy(src[i]))
    # keep only one finalize at end
    fin = [s for s in wf if s.type == "finalize"]
    body = [s for s in wf if s.type != "finalize"]
    if not fin:
        fin = [Step(type="finalize", prompt_slot="answer", input_from="task")]
    child.workflow = body + [fin[0]]
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
