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

    def run(self, g: Genotype, task: dict, seed_parts: tuple) -> ExecutionResult:
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
            if step.type == "finalize":
                payload = self._slot_text(step, ctx, task)
                reply = self.llm.reply(g.system_prompt, payload, trace, seed_parts + (turns,))
                turns += 1
                answer = reply.text
                if reply.kind == "call_tool" and turns < MAX_TURNS:
                    ok, out = run_tool(reply.tool, reply.tool_payload) if reply.tool else (False, "no tool")
                    tool_calls += 1
                    trace.append(TraceEvent("tool", ok, reply.tool or "", out).to_dict())
                    answer = self.llm.reply(g.system_prompt, payload, trace, seed_parts + (turns,)).text
                    turns += 1
                i += 1
                continue

            if step.type == "llm":
                payload = self._slot_text(step, ctx, task)
                t0 = time.time()
                reply = self.llm.reply(g.system_prompt, payload, trace, seed_parts + (turns,))
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
                    reply2 = self.llm.reply(g.system_prompt, payload, trace, seed_parts + (turns,))
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
                # R63: extract usable tool payload from LLM natural-language output
                if step.tool == "calc":
                    payload = self._extract_calc_payload(str(payload), task)
                elif step.tool == "str_ops":
                    payload = self._extract_strops_payload(str(payload), task)
                ok, out = run_tool(step.tool or "", str(payload))
                tool_calls += 1
                trace.append(TraceEvent("tool", ok, step.tool or "", out).to_dict())
                if not ok:
                    failure = "tool_error"
                    break
                ctx[step.tool or "out"] = out
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
                            reply = self.llm.reply(g.system_prompt, task["input"], trace, seed_parts + (turns,))
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
        """R63: extract arithmetic expression from LLM output or task input."""
        import re
        # Try to find arithmetic expression in LLM output
        m = re.search(r"([0-9]+\s*[+\-*/\*]\s*[0-9][0-9+\-*/\s]*)", llm_output)
        if m:
            return m.group(1).strip().rstrip(".?, ")
        # Fall back to task input
        return self._extract_calc_payload(task["input"], {"input": ""}) if "input" not in task else self._extract_expr_from_text(task["input"])

    def _extract_strops_payload(self, llm_output: str, task: dict) -> str:
        """R63: extract str_ops command from LLM output or task input."""
        import re
        m = re.search(r"(upper|lower|reverse|split|join|replace)\s*[|:]\s*(.+)", llm_output, re.IGNORECASE)
        if m:
            return f"{m.group(1).lower()}|{m.group(2).strip()}"
        # Fall back to task input
        return self._extract_expr_from_text(task["input"])

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
