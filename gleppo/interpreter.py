"""Fixed workflow interpreter (RUNTIME_LOCK §5)."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from .genotype import Genotype
from .llm import StubLLM
from .tools import run_tool

MAX_ITER = 8
MAX_TURNS = 24
TOOL_TIMEOUT_S = 2.0


@dataclass
class TraceEvent:
    type: str
    ok: bool = True
    detail: str = ""
    output: str = ""

    def to_dict(self) -> dict:
        return {"type": self.type, "ok": self.ok, "detail": self.detail, "output": self.output}


@dataclass
class ExecutionResult:
    success: bool
    answer: str
    failure_category: str   # "" | format_error | tool_error | wrong_answer | timeout | invalid_genotype
    turns: int
    tool_calls: int
    trace: List[dict] = field(default_factory=list)


class Interpreter:
    def __init__(self, llm: Optional[StubLLM] = None):
        self.llm = llm or StubLLM()

    def run(self, g: Genotype, task: dict, seed_parts: tuple,
            provenance: Optional[dict] = None) -> ExecutionResult:
        trace: List[dict] = []
        turns = 0
        tool_calls = 0
        ctx: dict = {"task": task["input"]}
        answer = ""
        failure = ""

        trace.append({
            "type": "meta",
            "tools": list(g.tools),
            "workflow_sig": "|".join(s.type + (s.tool or "") for s in g.workflow),
            "prompt_sig": __import__("hashlib").sha256(g.system_prompt.encode("utf-8")).hexdigest()[:8],
        })

        steps = g.workflow
        i = 0
        iterations = 0
        while i < len(steps) and iterations < MAX_ITER:
            iterations += 1
            step = steps[i]
            # Build per-turn provenance
            turn_prov = dict(provenance or {})
            turn_prov["turn"] = turns

            if step.type == "finalize":
                payload = self._slot_text(step, ctx, task)
                reply = self.llm.reply(g.system_prompt, payload, trace, seed_parts + (turns,), provenance=turn_prov)
                turns += 1
                answer = reply.text
                if reply.kind == "call_tool" and turns < MAX_TURNS:
                    ok, out = run_tool(reply.tool, reply.tool_payload) if reply.tool else (False, "no tool")
                    tool_calls += 1
                    trace.append(TraceEvent("tool", ok, reply.tool or "", out).to_dict())
                    answer = self.llm.reply(g.system_prompt, payload, trace, seed_parts + (turns,), provenance=turn_prov).text
                    turns += 1
                i += 1
                continue

            if step.type == "llm":
                payload = self._slot_text(step, ctx, task)
                t0 = time.time()
                reply = self.llm.reply(g.system_prompt, payload, trace, seed_parts + (turns,), provenance=turn_prov)
                turns += 1
                if time.time() - t0 > TOOL_TIMEOUT_S * 20:
                    failure = "timeout"
                    break
                if reply.kind == "call_tool":
                    ok, out = run_tool(reply.tool or "", reply.tool_payload) if reply.tool else (False, "no tool")
                    tool_calls += 1
                    trace.append(TraceEvent("tool", ok, reply.tool or "", out).to_dict())
                    if not ok:
                        failure = "tool_error"
                        break
                    # keep the tool output as the slot value so downstream tool steps can consume it
                    ctx[step.prompt_slot or "llm"] = out
                    # one follow-up turn consuming tool result (text kept for trace only)
                    reply2 = self.llm.reply(g.system_prompt, payload, trace, seed_parts + (turns,), provenance=turn_prov)
                    turns += 1
                    trace.append(TraceEvent("llm", True, step.prompt_slot or "llm", reply2.text[:200]).to_dict())
                else:
                    ctx[step.prompt_slot or "llm"] = reply.text
                    trace.append(TraceEvent("llm", True, step.prompt_slot or "llm", reply.text[:200]).to_dict())
                i += 1
                continue

            if step.type == "tool":
                src = step.input_from or "task"
                payload = ctx.get(src, task["input"])
                # B1: extract usable tool payload; raise on invalid input
                try:
                    if step.tool == "calc":
                        payload = self._extract_calc_payload(str(payload), task)
                    elif step.tool == "str_ops":
                        payload = self._extract_strops_payload(str(payload), task)
                    elif step.tool == "py_sandbox":
                        payload = self._extract_pysandbox_payload(str(payload), task)
                except ValueError as e:
                    # R2: if the task doesn't require this tool, skip the step
                    # (e.g. str_ops on Family A tasks). Otherwise fail closed.
                    if step.tool == "str_ops" and "str_ops" not in task.get("required_tools", []):
                        i += 1
                        continue
                    trace.append(TraceEvent("tool", False, step.tool or "", f"input_error: {e}").to_dict())
                    failure = "tool_error"
                    break
                ok, out = run_tool(step.tool or "", str(payload))
                tool_calls += 1
                trace.append(TraceEvent("tool", ok, step.tool or "", out).to_dict())
                if not ok:
                    failure = "tool_error"
                    break
                # B2: store output for downstream consumption
                ctx[step.tool or "out"] = out
                # Also store in generic "last_tool_output" for finalize step
                ctx["last_tool_output"] = out
                i += 1
                continue

            if step.type == "branch":
                cond_src = step.input_from or "task"
                cond = str(ctx.get(cond_src, task["input"]))
                arm = 0 if len(cond) % 2 == 0 else 1
                if step.arms and arm < len(step.arms):
                    for sub in step.arms[arm]:
                        if sub.type == "tool":
                            ok, out = run_tool(sub.tool or "", str(ctx.get(sub.input_from or "task", task["input"])))
                            tool_calls += 1
                            trace.append(TraceEvent("tool", ok, sub.tool or "", out).to_dict())
                            if not ok:
                                failure = "tool_error"
                                break
                            ctx[sub.tool or "out"] = out
                        elif sub.type == "llm":
                            reply = self.llm.reply(g.system_prompt, task["input"], trace, seed_parts + (turns,), provenance=turn_prov)
                            turns += 1
                            ctx[sub.prompt_slot or "branch"] = reply.text
                    if failure:
                        break
                i += 1
                continue

            i += 1

        if turns > MAX_TURNS and not failure:
            failure = "timeout"

        if not answer and not failure:
            answer = "Final answer: "
            failure = "format_error"

        success = False
        if not failure:
            success = self._score(answer, task, g)
            if not success:
                failure = "wrong_answer"

        return ExecutionResult(
            success=success,
            answer=answer,
            failure_category=failure,
            turns=min(turns, MAX_TURNS),
            tool_calls=tool_calls,
            trace=trace,
        )

    def _extract_calc_payload(self, llm_output: str, task: dict) -> str:
        """R2: extract arithmetic expression, preferring tool-directed expressions.

        Priority:
        1. Explicit tool-directed: "use calc to compute X-Y" / "calc: X-Y"
        2. First arithmetic expression in LLM output
        3. First arithmetic expression in task input
        """
        import re

        def _tool_directed(text: str) -> Optional[str]:
            # "use calc to compute 49-6" / "calc to compute X+Y" / "calc: X*Y"
            m = re.search(
                r"(?:use\s+)?calc(?:\s+tool)?\s+to\s+(?:compute|calculate|evaluate|verify|find)\s+"
                r"([0-9]+\s*[+\-*/]\s*[0-9][0-9+\-*/\s]*?)(?=[.\s,]|$)",
                text, re.IGNORECASE,
            )
            if m:
                return m.group(1).strip().rstrip(".?, ")
            # "calc: 49-6" or "calc: X*Y"
            m = re.search(
                r"calc(?:\s+tool)?\s*[:=]\s*([0-9]+\s*[+\-*/]\s*[0-9][0-9+\-*/\s]*?)(?=[.\s,]|$)",
                text, re.IGNORECASE,
            )
            if m:
                return m.group(1).strip().rstrip(".?, ")
            return None

        def _first_expr(text: str) -> Optional[str]:
            m = re.search(r"([0-9]+\s*[+\-*/]\s*[0-9][0-9+\-*/\s]*)", text)
            if m:
                return m.group(1).strip().rstrip(".?, ")
            return None

        # Priority 1: tool-directed in LLM output
        result = _tool_directed(llm_output)
        if result:
            return result

        # Priority 2: tool-directed in task input (e.g. "Then use calc to compute 49-6")
        result = _tool_directed(task.get("input", ""))
        if result:
            return result

        # Priority 3: first expression in LLM output
        result = _first_expr(llm_output)
        if result:
            return result

        # Priority 4: first expression in task input
        result = _first_expr(task.get("input", ""))
        if result:
            return result

        # Ultimate fallback: derive from numbers
        return self._extract_expr_from_text(task.get("input", ""))

    def _extract_pysandbox_payload(self, llm_output: str, task: dict) -> str:
        """B1: extract Python code from LLM output or task input.

        Raises ValueError if no valid input found — never returns fake success.
        """
        import re

        def _try_expr(text: str) -> Optional[str]:
            # Explicit result assignment: "result = EXPR" (capture only the expression)
            m = re.search(r"(?:result|out|answer)\s*=\s*([0-9+\-*/().\s]+?)(?:[.;,\n]|$)", text)
            if m:
                expr = m.group(1).strip().rstrip(".;, ")
                if expr:
                    return f"result = {expr}"
            # Arithmetic expression
            m = re.search(r"([0-9]+\s*[+\-*/]\s*[0-9][0-9+\-*/\s]*?)(?=[.;,\n]|$)", text)
            if m:
                return f"result = {m.group(1).strip().rstrip('.;, ')}"
            return None

        # LLM output first
        result = _try_expr(llm_output)
        if result:
            return result

        # Task input
        result = _try_expr(task.get("input", ""))
        if result:
            return result

        raise ValueError("B1: no valid Python input extracted for py_sandbox")

    def _extract_strops_payload(self, llm_output: str, task: dict) -> str:
        """R2: extract str_ops command from LLM output or task input.

        Supports:
        - Explicit syntax: upper|X, lower|X, reverse|X, split|X, join|X, replace|...
        - Quoted natural language: transform 'X' to uppercase / lowercase / reverse
        - Searches LLM output first, then task input.
        Raises ValueError if no valid string operation found (never arithmetic fallback).
        """
        import re

        def _try_extract(text: str) -> Optional[str]:
            # Explicit command syntax: op|payload or op:payload
            m = re.search(
                r"(upper|lower|reverse|split|join|replace)\s*[|:]\s*(.+)",
                text, re.IGNORECASE,
            )
            if m:
                return f"{m.group(1).lower()}|{m.group(2).strip()}"

            # Quoted natural language: transform/make/convert 'X' to uppercase/lowercase/reverse
            m = re.search(
                r"(?:transform|make|convert|rewrite|turn)\s+(?:the\s+word\s+)?['\"](\w+)['\"]\s+"
                r"(?:to\s+|into\s+)?(uppercase|lowercase|upper\s*case|lower\s*case|capitals?|reverse)",
                text, re.IGNORECASE,
            )
            if m:
                word = m.group(1)
                op = m.group(2).lower().replace(" ", "")
                if op in ("uppercase", "uppercase", "capitals", "capital"):
                    return f"upper|{word}"
                if op in ("lowercase",):
                    return f"lower|{word}"
                if op == "reverse":
                    return f"reverse|{word}"
                return f"upper|{word}"

            # Unquoted natural language: transform the string X to upper case
            m = re.search(
                r"(?:transform|make|convert|rewrite|turn)\s+(?:the\s+)?(?:string\s+|word\s+|token\s+)?(\w+)\s+"
                r"(?:to\s+|into\s+)?(uppercase|lowercase|upper\s*case|lower\s*case|capitals?|reverse)",
                text, re.IGNORECASE,
            )
            if m:
                word = m.group(1)
                op = m.group(2).lower().replace(" ", "")
                if op in ("uppercase", "capitals", "capital"):
                    return f"upper|{word}"
                if op in ("lowercase",):
                    return f"lower|{word}"
                if op == "reverse":
                    return f"reverse|{word}"
                return f"upper|{word}"

            # "make X all capitals" / "rewrite X in capitals" / "X shouted"
            m = re.search(
                r"(?:make|rewrite|turn|convert)\s+(\w+)\s+(?:all\s+)?(?:in\s+)?capitals?",
                text, re.IGNORECASE,
            )
            if m:
                return f"upper|{m.group(1)}"

            # "upper-case the token X" / "upper-case X"
            m = re.search(
                r"upper[\s-]case\s+(?:the\s+)?(?:token\s+|string\s+|word\s+)?(\w+)",
                text, re.IGNORECASE,
            )
            if m:
                return f"upper|{m.group(1)}"

            # "the uppercased form of X" / "uppercased X"
            m = re.search(
                r"uppercased?\s+(?:form\s+of\s+)?(\w+)",
                text, re.IGNORECASE,
            )
            if m:
                return f"upper|{m.group(1)}"

            # "X in upper case" / "X upper-cased" / "X in capitals"
            m = re.search(
                r"(\w+)\s+(?:in\s+)?(?:upper[\s-]?case|upper[\s-]?cased|capitals?)",
                text, re.IGNORECASE,
            )
            if m:
                return f"upper|{m.group(1)}"

            # "X ... uppercase/capitals" near end of phrase
            m = re.search(
                r"(\w+)\s+(?:shouted|yelled|all\s+caps|in\s+caps)",
                text, re.IGNORECASE,
            )
            if m:
                return f"upper|{m.group(1)}"

            # Quoted natural language without "the word": 'X' ... uppercase
            m = re.search(
                r"['\"](\w+)['\"].*?(uppercase|lowercase|capitals?|reverse)",
                text, re.IGNORECASE,
            )
            if m:
                word = m.group(1)
                op = m.group(2).lower()
                if op in ("uppercase", "capital", "capitals"):
                    return f"upper|{word}"
                if op == "lowercase":
                    return f"lower|{word}"
                if op == "reverse":
                    return f"reverse|{word}"

            return None

        # Search LLM output first
        result = _try_extract(llm_output)
        if result:
            return result

        # Then task input
        result = _try_extract(task.get("input", ""))
        if result:
            return result

        # Fail closed: no valid string operation found
        raise ValueError("R2: no valid string operation extracted for str_ops")

    def _extract_expr_from_text(self, text: str) -> str:
        import re
        m = re.search(r"([0-9]+\s*[+\-*/]\s*[0-9][0-9+\-*/\s]*)", text)
        if m:
            return m.group(1).strip().rstrip(".?, ")
        nums = re.findall(r"\d+", text)
        if len(nums) >= 2:
            return f"{nums[0]}+{nums[1]}"
        return "1+1"

    def _slot_text(self, step, ctx, task) -> str:
        if step.input_from and step.input_from in ctx:
            return f"{task['input']}\nContext: {ctx[step.input_from]}"
        return task["input"]

    @staticmethod
    def _score(answer: str, task: dict, g: Genotype) -> bool:
        """Strategy-aware stub scoring aligned with RUNTIME_LOCK §4.4.

        Real evaluator compares against gold; here gold semantics are encoded in task['gold_check']
        so the evaluator module owns scoring. Interpreter delegates.
        """
        checker = task.get("gold_check")
        if checker is None:
            return False
        return bool(checker(answer, g))
