"""Declarative agent genotype: schema, validation, canonical serialization, hashing.

What evolves: system_prompt, tools, workflow.
What is frozen: base model, tool implementations, interpreter, selection rules (elsewhere).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, List, Optional

ALLOWED_TOOLS = ("calc", "py_sandbox", "str_ops")
STEP_TYPES = ("llm", "tool", "branch", "finalize")
MIN_PROMPT_TOKENS = 5          # stub-safe lower bound; production 20 (see RUNTIME_LOCK)
MAX_PROMPT_TOKENS = 800
MIN_STEPS = 2
MAX_STEPS = 6


class InvalidGenotype(Exception):
    pass


@dataclass
class Step:
    type: str
    tool: Optional[str] = None
    prompt_slot: Optional[str] = None
    input_from: Optional[str] = None
    arms: Optional[List[List["Step"]]] = None

    def to_dict(self) -> dict:
        d: dict[str, Any] = {"type": self.type}
        if self.tool is not None:
            d["tool"] = self.tool
        if self.prompt_slot is not None:
            d["prompt_slot"] = self.prompt_slot
        if self.input_from is not None:
            d["input_from"] = self.input_from
        if self.arms is not None:
            d["arms"] = [[s.to_dict() for s in arm] for arm in self.arms]
        return d

    @staticmethod
    def from_dict(d: dict) -> "Step":
        arms = None
        if d.get("arms") is not None:
            arms = [[Step.from_dict(s) for s in arm] for arm in d["arms"]]
        return Step(
            type=d["type"],
            tool=d.get("tool"),
            prompt_slot=d.get("prompt_slot"),
            input_from=d.get("input_from"),
            arms=arms,
        )


@dataclass
class Genotype:
    system_prompt: str
    tools: List[str]
    workflow: List[Step]
    meta: dict = field(default_factory=dict)

    def to_dict(self, include_meta: bool = False) -> dict:
        d = {
            "system_prompt": self.system_prompt,
            "tools": sorted(self.tools),
            "workflow": [s.to_dict() for s in self.workflow],
        }
        if include_meta:
            d["meta"] = self.meta
        return d

    @staticmethod
    def from_dict(d: dict) -> "Genotype":
        return Genotype(
            system_prompt=d["system_prompt"],
            tools=list(d.get("tools", [])),
            workflow=[Step.from_dict(s) for s in d.get("workflow", [])],
            meta=dict(d.get("meta", {})),
        )

    def copy(self) -> "Genotype":
        return Genotype.from_dict(self.to_dict(include_meta=True))


def canonical_serialize(g: Genotype) -> str:
    """Canonical JSON for behavior hashing: sorted keys, compact, meta excluded."""
    payload = g.to_dict(include_meta=False)
    payload["tools"] = sorted(payload["tools"])
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def behavior_hash(g: Genotype) -> str:
    return hashlib.sha256(canonical_serialize(g).encode("utf-8")).hexdigest()


def _prompt_tokens(s: str) -> int:
    return len(re.findall(r"\S+", s))


def validate_genotype(g: Genotype) -> List[str]:
    """Return list of validity errors; empty list means valid."""
    errs: List[str] = []
    if not isinstance(g.system_prompt, str):
        errs.append("system_prompt not str")
    else:
        ntok = _prompt_tokens(g.system_prompt)
        if ntok < MIN_PROMPT_TOKENS:
            errs.append(f"system_prompt too short ({ntok} tokens)")
        if ntok > MAX_PROMPT_TOKENS:
            errs.append(f"system_prompt too long ({ntok} tokens)")
        if "{{answer}}" not in g.system_prompt and "final answer" not in g.system_prompt.lower():
            errs.append("system_prompt missing answer slot or 'final answer'")

    if not g.tools or len(g.tools) > 3:
        errs.append("tools must be 1-3 entries")
    for t in g.tools:
        if t not in ALLOWED_TOOLS:
            errs.append(f"unknown tool: {t}")
    if len(set(g.tools)) != len(g.tools):
        errs.append("duplicate tools")

    if not isinstance(g.workflow, list) or not (MIN_STEPS <= len(g.workflow) <= MAX_STEPS):
        errs.append(f"workflow must have {MIN_STEPS}-{MAX_STEPS} steps")
    else:
        finalize_count = 0
        for i, s in enumerate(g.workflow):
            if s.type not in STEP_TYPES:
                errs.append(f"step {i}: bad type {s.type}")
                continue
            if s.type == "finalize":
                finalize_count += 1
                if i != len(g.workflow) - 1:
                    errs.append("finalize must be the last step")
            if s.type == "tool":
                if s.tool is None or s.tool not in g.tools:
                    errs.append(f"step {i}: tool {s.tool} not in enabled tools")
            if s.type == "branch":
                if not s.arms or len(s.arms) > 2:
                    errs.append(f"step {i}: branch needs 1-2 arms")
                else:
                    for arm in s.arms:
                        if not (1 <= len(arm) <= 2):
                            errs.append(f"step {i}: arm length must be 1-2")
        if finalize_count != 1:
            errs.append("workflow must contain exactly one finalize step")
    return errs


def is_valid(g: Genotype) -> bool:
    return not validate_genotype(g)


def make_valid_genotype(
    system_prompt: str = (
        "Compute step by step and transform the result. "
        "You are a precise task solver. Follow these rules strictly: "
        "(1) Use tools to compute values. "
        "(2) Your FINAL answer MUST start with 'Final answer: ' followed by ONLY the answer value. "
        "(3) For numeric answers, output only the number. "
        "(4) When asked for SUM-STRING format, compute the sum and uppercase the string. Output ONLY the computed result like '25-AB42'. The phrase 'Give as SUM-STRING' means use that FORMAT, not output those words. NEVER include 'SUM-STRING', 'SUM', or 'STRING' in your answer. "
        "(5) Do NOT include markdown, reasoning, or text after the answer. "
        "(6) Do NOT output '{{answer}}' as a literal. "
        "Example: If the answer is 42, output exactly 'Final answer: 42'"
    ),
    tools: Optional[List[str]] = None,
    workflow: Optional[List[Step]] = None,
) -> Genotype:
    if tools is None:
        tools = ["calc", "str_ops"]
    if workflow is None:
        workflow = [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="analyze"),
            Step(type="tool", tool="str_ops", input_from="calc"),
            Step(type="finalize", prompt_slot="answer", input_from="str_ops"),
        ]
    return Genotype(system_prompt=system_prompt, tools=tools, workflow=workflow, meta={})


# R2: task-compatible reference workflows for B2 diagnostic tasks.
# Each reference exposes EXACTLY the tools and ordered steps required by the
# frozen B2 tool-path contract. Labeled 'task_compatible_reference', NOT the
# unmodified default genotype.

_TASK_COMPATIBLE_REFERENCES = {
    "B2-001": {
        "tools": ["calc", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-002": {
        "tools": ["py_sandbox", "calc"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-003": {
        "tools": ["calc", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-004": {
        "tools": ["py_sandbox", "calc"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-005": {
        "tools": ["calc", "py_sandbox"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-006": {
        "tools": ["calc", "str_ops", "py_sandbox"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-007": {
        "tools": ["calc", "py_sandbox"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-008": {
        "tools": ["calc", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-009": {
        "tools": ["str_ops", "calc", "py_sandbox"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-010": {
        "tools": ["calc", "py_sandbox"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-011": {
        "tools": ["py_sandbox", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-012": {
        "tools": ["calc", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-013": {
        "tools": ["py_sandbox", "calc"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-014": {
        "tools": ["str_ops", "calc"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-015": {
        "tools": ["calc", "str_ops", "py_sandbox"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-016": {
        "tools": ["calc", "py_sandbox"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-017": {
        "tools": ["py_sandbox", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-018": {
        "tools": ["calc", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-019": {
        "tools": ["py_sandbox", "calc"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-020": {
        "tools": ["calc", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-021": {
        "tools": ["str_ops", "calc", "py_sandbox"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-022": {
        "tools": ["calc", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-023": {
        "tools": ["py_sandbox", "calc"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-024": {
        "tools": ["str_ops", "calc", "py_sandbox"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-025": {
        "tools": ["calc", "py_sandbox"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-026": {
        "tools": ["calc", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-027": {
        "tools": ["calc", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-028": {
        "tools": ["py_sandbox", "calc"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
}

_TASK_COMPATIBLE_PROMPT = (
    "Compute step by step using the required tools in order. "
    "Use tools to compute values and transform strings. "
    "Your FINAL answer MUST start with 'Final answer: ' followed by ONLY the answer value. "
    "Do NOT include markdown, reasoning, or text after the answer."
)


def make_task_compatible_reference(task_id: str) -> Genotype:
    """R2: create a frozen task-compatible reference genotype for a B2 task.

    The genotype exposes exactly the tools and ordered workflow steps required
    by the frozen B2 tool-path contract. Labeled 'task_compatible_reference'.
    """
    spec = _TASK_COMPATIBLE_REFERENCES.get(task_id)
    if spec is None:
        raise ValueError(f"no task-compatible reference for {task_id}")
    return Genotype(
        system_prompt=_TASK_COMPATIBLE_PROMPT,
        tools=list(spec["tools"]),
        workflow=[Step.from_dict(s.to_dict()) for s in spec["workflow"]],
        meta={"label": "task_compatible_reference", "task_id": task_id},
    )
