"""LLM backend interface.

Phase 2A uses StubLLM only (RUNTIME_LOCK §4). Production backend is PENDING_DEPLOYMENT.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import List, Optional


def _seed_int(*parts: object) -> int:
    h = hashlib.sha256(("|".join(map(str, parts))).encode("utf-8")).hexdigest()
    return int(h[:8], 16)


@dataclass
class LLMReply:
    kind: str            # "answer" | "call_tool"
    text: str = ""
    tool: Optional[str] = None
    tool_payload: str = ""


class StubLLM:
    """Deterministic stand-in preserving causal structure (see RUNTIME_LOCK §4).

    Strategy keywords in system_prompt + enabled tools decide success on each family.
    Not a real LLM; token/latency costs are UNMEASURED.
    """

    name = "stub-v1"

    def reply(self, system_prompt: str, user_message: str, trace: List[dict], seed_parts: tuple) -> LLMReply:
        prompt = system_prompt.lower()
        msg = user_message
        tools_hint = next((t.get("tools", []) for t in trace if "tools" in t), [])
        # Infer enabled tools from the interpreter via trace meta if present
        enabled = list(tools_hint)
        numeric = bool(re.search(r"\d", msg))
        wants_transform = bool(re.search(r"upper|lower|reverse|join|split|transform", msg.lower()))
        wants_format = bool(re.search(r"json|format|keys", msg.lower()))

        already_called = any(e.get("type") == "tool" for e in trace)

        if (not already_called) and numeric and enabled and "calc" in enabled and ("compute" in prompt or "step" in prompt):
            expr = self._extract_expr(msg)
            return LLMReply(kind="call_tool", tool="calc", tool_payload=expr)

        if (not already_called) and wants_transform and enabled and "str_ops" in enabled:
            return LLMReply(kind="call_tool", tool="str_ops", tool_payload=self._extract_str_cmd(msg))

        # Direct answer
        return LLMReply(kind="answer", text=self._answer(system_prompt, user_message, trace, enabled, seed_parts))

    @staticmethod
    def _extract_expr(msg: str) -> str:
        m = re.search(r"what is (.+?)\?", msg, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        m = re.search(r"compute\s+([0-9][0-9\+\-\*/\(\)\.\s]*)", msg, re.IGNORECASE)
        if m:
            return m.group(1).strip().rstrip(".?, ")
        m = re.search(r"([0-9]+\s*[\+\-\*/]\s*[0-9][0-9\+\-\*/\(\)\.\s]*)", msg)
        if m:
            return m.group(1).strip().rstrip(".?, ")
        nums = re.findall(r"\d+", msg)
        if len(nums) >= 2:
            return f"{nums[0]}+{nums[1]}"
        return "1+1"

    @staticmethod
    def _extract_str_cmd(msg: str) -> str:
        low = msg.lower()
        m = re.search(r"upper\((.+?)\)", low)
        if m:
            return f"upper|{m.group(1)}"
        m = re.search(r"lower\((.+?)\)", low)
        if m:
            return f"lower|{m.group(1)}"
        if "reverse" in low:
            m = re.search(r"reverse\((.+?)\)", low)
            s = m.group(1) if m else "abc"
            return f"reverse|{s}"
        return "upper|abc"

    @staticmethod
    def _answer(system_prompt: str, user_message: str, trace: List[dict], enabled: List[str], seed_parts: tuple) -> str:
        prompt = system_prompt.lower()
        wf_sig = next((t.get("workflow_sig", "") for t in trace if t.get("type") == "meta"), "")
        digest = hashlib.sha256(
            (system_prompt + "|" + ",".join(sorted(enabled)) + "|" + wf_sig).encode()
        ).hexdigest()[:4]
        tool_outputs = [e.get("output", "") for e in trace if e.get("type") == "tool" and e.get("ok")]
        if tool_outputs:
            return f"Final answer: {tool_outputs[-1]}|g{digest}"
        if "compute" in prompt and "calc" in enabled:
            return f"Final answer: 42|g{digest}"
        if "transform" in prompt and "calc" in enabled and "str_ops" in enabled:
            return f"Final answer: TRANSFORMED|g{digest}"
        if ("format" in prompt or "json" in prompt) and "str_ops" in enabled:
            return f'Final answer: {{"ok": true}}|g{digest}'
        h = hashlib.sha256((system_prompt + user_message).encode("utf-8")).hexdigest()[:6]
        return f"Final answer: X{h}|g{digest}"


class ProductionLLM:
    """Placeholder. Must be implemented only after RUNTIME_LOCK production fields are filled."""

    name = "production-pending"

    def reply(self, system_prompt: str, user_message: str, trace: List[dict], seed_parts: tuple) -> LLMReply:
        raise RuntimeError("ProductionLLM not deployed; see docs/RUNTIME_LOCK.md")
