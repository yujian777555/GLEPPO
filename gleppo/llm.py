"""LLM backend interface.

Phase 2A uses StubLLM only (RUNTIME_LOCK §4). Production backend is PENDING_DEPLOYMENT.

R1 separation: StubLLM *attempts* to solve the task (computes the real answer when its
strategy matches the genotype). Success is determined ONLY by the evaluator's
gold checkers. Strategy keywords alone never grant success.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import List, Optional


def _seed_int(*parts: object) -> int:
    h = hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).hexdigest()
    return int(h[:8], 16)


@dataclass
class LLMReply:
    kind: str            # "answer" | "call_tool"
    text: str = ""
    tool: Optional[str] = None
    tool_payload: str = ""


class StubLLM:
    """Deterministic stand-in (RUNTIME_LOCK §4).

    Computes the actual answer when the genotype's strategy fits the task;
    otherwise emits a deterministic wrong answer. The evaluator compares to gold.
    """

    name = "stub-v1"
    version = "stub-v1.1-correctness"

    def reply(self, system_prompt: str, user_message: str, trace: List[dict], seed_parts: tuple) -> LLMReply:
        prompt = system_prompt.lower()
        enabled = self._enabled_tools(trace)
        numeric = bool(re.search(r"\d", msg := user_message))
        wants_transform = bool(re.search(r"upper|lower|reverse|join|split|transform|capitals|uppercase", msg.lower()))
        wants_format = bool(re.search(r"json|format|keys|fields|object", msg.lower()))
        already_called = any(e.get("type") == "tool" and e.get("ok") for e in trace)

        if (not already_called) and numeric and "calc" in enabled and "compute" in prompt:
            expr = self._extract_expr(msg)
            return LLMReply(kind="call_tool", tool="calc", tool_payload=expr)

        if (not already_called) and wants_transform and "str_ops" in enabled and "transform" in prompt:
            return LLMReply(kind="call_tool", tool="str_ops", tool_payload=self._extract_str_cmd(msg))

        return LLMReply(kind="answer", text=self._answer(system_prompt, user_message, trace, enabled, seed_parts))

    @staticmethod
    def _enabled_tools(trace: List[dict]) -> List[str]:
        return next((t.get("tools", []) for t in trace if t.get("type") == "meta"), [])

    @staticmethod
    def _extract_expr(msg: str) -> str:
        # order matters: try operation phrases before bare "what is"
        m = re.search(r"(\d+)\s*times\s*(\d+).*?(?:add|plus)\s*(\d+)", msg, re.IGNORECASE)
        if m:
            return f"{m.group(1)}*{m.group(2)}+{m.group(3)}"
        m = re.search(r"(\d+)\s*by\s*(\d+).*?(?:increase|product|add|plus).*?(\d+)", msg, re.IGNORECASE)
        if m:
            return f"{m.group(1)}*{m.group(2)}+{m.group(3)}"
        m = re.search(r"(\d+)\s*(?:copies of|rows of|groups of)\s*(\d+)", msg, re.IGNORECASE)
        if m:
            m2 = re.search(r"(?:plus|include|together with|additional)\s*(\d+)", msg, re.IGNORECASE)
            if m2:
                return f"{m.group(1)}*{m.group(2)}+{m2.group(1)}"
            return f"{m.group(1)}*{m.group(2)}"
        m = re.search(r"x\s*=\s*(\d+).*?y\s*=\s*(\d+).*?z\s*=\s*(\d+)", msg, re.IGNORECASE)
        if m:
            return f"{m.group(1)}*{m.group(3)}+{m.group(2)}"
        m = re.search(r"what is\s+([0-9\+\-\*/\(\)\s]+)\??", msg, re.IGNORECASE)
        if m:
            return m.group(1).strip().rstrip(".?")
        m = re.search(r"(?:value of|find|evaluate)\s*:?\s*([0-9\+\-\*/\(\)\s]+)", msg, re.IGNORECASE)
        if m:
            return m.group(1).strip().rstrip(".?=")
        m = re.search(r"([0-9]+\s*[+\-*/]\s*[0-9][0-9\+\-\*/\(\)\s]*)", msg)
        if m:
            return m.group(1).strip().rstrip(".?, ")
        nums = re.findall(r"\d+", msg)
        if len(nums) >= 3:
            return f"{nums[0]}*{nums[2]}+{nums[1]}"
        if len(nums) >= 2:
            return f"{nums[0]}+{nums[1]}"
        return "1+1"

    @staticmethod
    def _extract_str_cmd(msg: str) -> str:
        m = re.search(r"'([^']+)'", msg)
        token = m.group(1) if m else None
        if token is None:
            m = re.search(r"\b([a-z]{2,}\d*)\b(?=.*(?:upper|capitals|uppercase|shouted))", msg.lower())
            token = m.group(1) if m else "ab"
        return f"upper|{token}"

    @staticmethod
    def _answer(system_prompt: str, user_message: str, trace: List[dict], enabled: List[str], seed_parts: tuple) -> str:
        """Strategy gates *whether* to solve; solve_input computes the answer from
        the task INPUT only (no gold). Correctness is decided by the evaluator."""
        from .tasks import solve_input
        prompt = system_prompt.lower()
        msg = user_message

        def _wrong() -> str:
            h = hashlib.sha256((system_prompt + user_message).encode("utf-8")).hexdigest()[:6]
            return f"Final answer: X{h}"

        # Family detection by MESSAGE content first (B/C messages may also contain "compute")
        wants_transform = bool(re.search(r"transform|upper|capitals|uppercase|shouted|SUM-STRING|SUM-TOKEN|SUM-WORD|SUM-UPPER", msg, re.IGNORECASE))
        wants_json = bool(re.search(r"json|keys sum|fields sum|sum and product|object", msg, re.IGNORECASE))

        if wants_json and ("format" in prompt or "json" in prompt) and "str_ops" in enabled:
            val = solve_input("C", msg)
            return f"Final answer: {val}" if val else _wrong()

        if wants_transform and "transform" in prompt and "calc" in enabled and "str_ops" in enabled:
            val = solve_input("B", msg)
            return f"Final answer: {val}" if val else _wrong()

        if "compute" in prompt and "calc" in enabled:
            val = solve_input("A", msg)
            return f"Final answer: {val}" if val else _wrong()

        return _wrong()


class ProductionLLM:
    """Placeholder. Must be implemented only after RUNTIME_LOCK production fields are filled."""

    name = "production-pending"
    version = "production-pending"

    def reply(self, system_prompt: str, user_message: str, trace: List[dict], seed_parts: tuple) -> LLMReply:
        raise RuntimeError("ProductionLLM not deployed; see docs/RUNTIME_LOCK.md")
