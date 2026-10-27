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
    """Real model inference via Transformers + Qwen2.5-7B-Instruct.

    Must be explicitly instantiated and injected via Interpreter(llm=...).
    Records model revision, request counts, tokens, latency in self.stats.
    """

    name = "qwen2.5-7b-instruct"
    version = "a09a35458c702b33eeacc393d103063234e8bc28"

    def __init__(self, model_path: str = "", device: str = "cuda:0",
                 max_new_tokens: int = 512, temperature: float = 0.7):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.model_path = model_path or "/202532803004/datasets/hf/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28"
        self.device = device
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.stats = {
            "requests": 0, "total_tokens": 0, "failures": 0,
            "latencies": [], "revision": self.version,
        }
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path, dtype=torch.bfloat16, device_map=device,
        )
        self.model.eval()

    def reply(self, system_prompt: str, user_message: str, trace: List[dict], seed_parts: tuple) -> LLMReply:
        import time
        import torch
        self.stats["requests"] += 1
        t0 = time.time()

        # Build messages from system_prompt + user_message + trace context
        messages = [{"role": "system", "content": system_prompt}]
        # Include trace context (tool outputs, errors) but NEVER gold labels
        for entry in trace:
            if entry.get("type") == "tool" and entry.get("ok"):
                messages.append({"role": "user", "content": f"[tool:{entry.get('detail','')}] {entry.get('output','')[:200]}"})
            elif entry.get("type") == "tool" and not entry.get("ok"):
                messages.append({"role": "user", "content": f"[tool error: {entry.get('detail','')}] {entry.get('output','')[:200]}"})
        messages.append({"role": "user", "content": user_message})

        try:
            result = self.tokenizer.apply_chat_template(
                messages, add_generation_prompt=True, return_tensors="pt"
            )
            if hasattr(result, 'input_ids'):
                input_ids = result.input_ids.to(self.device)
            elif isinstance(result, dict):
                input_ids = result['input_ids'].to(self.device)
            else:
                input_ids = result.to(self.device)

            # R64: stable SHA256-based seed (not Python hash())
            import hashlib
            import json
            seed_str = json.dumps(list(seed_parts), separators=(",", ":"), ensure_ascii=False)
            seed_val = int(hashlib.sha256(seed_str.encode()).hexdigest()[:8], 16) % (2**31)
            torch.manual_seed(seed_val)

            with torch.no_grad():
                output = self.model.generate(
                    input_ids,
                    max_new_tokens=self.max_new_tokens,
                    temperature=self.temperature,
                    do_sample=True,
                    top_p=0.95,
                    pad_token_id=self.tokenizer.eos_token_id,
                )

            generated = output[0][input_ids.shape[1]:]
            text = self.tokenizer.decode(generated, skip_special_tokens=True).strip()

            latency = time.time() - t0
            self.stats["latencies"].append(latency)
            self.stats["total_tokens"] += len(generated)

            # R63: parse with real tool registry
            return self._parse_response(text)
        except Exception as e:
            self.stats["failures"] += 1
            return LLMReply(kind="answer", text=f"Final answer: ERROR:{str(e)[:50]}")

    def _parse_response(self, text: str) -> LLMReply:
        """R63: parse with real tool registry validation."""
        import json
        import re
        from .tools import TOOL_REGISTRY
        text = text.strip()
        # Try JSON tool call
        if text.startswith("{"):
            try:
                obj = json.loads(text)
                if "tool" in obj and "payload" in obj:
                    tool_name = obj["tool"]
                    if tool_name not in TOOL_REGISTRY:
                        return LLMReply(kind="answer", text=f"ERROR: invalid tool '{tool_name}'")
                    return LLMReply(kind="call_tool", tool=tool_name, tool_payload=str(obj["payload"]))
            except json.JSONDecodeError:
                pass
        # TOOL:name PAYLOAD:xxx
        m = re.match(r"TOOL:(\w+)\s+PAYLOAD:(.+)", text, re.DOTALL)
        if m:
            tool_name = m.group(1)
            if tool_name not in TOOL_REGISTRY:
                return LLMReply(kind="answer", text=f"ERROR: invalid tool '{tool_name}'")
            return LLMReply(kind="call_tool", tool=tool_name, tool_payload=m.group(2).strip())
        return LLMReply(kind="answer", text=text)

    def get_stats(self) -> dict:
        import statistics
        lats = self.stats["latencies"]
        return {
            "model": self.name, "revision": self.version,
            "requests": self.stats["requests"],
            "total_tokens": self.stats["total_tokens"],
            "failures": self.stats["failures"],
            "mean_latency_s": statistics.mean(lats) if lats else 0,
            "max_latency_s": max(lats) if lats else 0,
        }
