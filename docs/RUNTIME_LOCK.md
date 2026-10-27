# GLEPPO Runtime Lock

**Locked:** 2026-10-27 (Phase 2A)  
**Scope:** all GLEPPO experiments (G3, smoke, PC1, baselines, PPO, final eval) must use this lock. Any change requires a new lock file version and invalidates comparability.

---

## 1. Base model

| Field | Value |
|---|---|
| Model id | `Qwen2.5-7B-Instruct` |
| Checkpoint / revision | `Qwen/Qwen2.5-7B-Instruct` @ pinned revision **PENDING_DEPLOYMENT** |
| Tokenizer | model-bundled tokenizer of the same revision |
| Inference backend | **Phase 2A: `StubLLM` (deterministic, offline)** — see §4 |
| Production backend | **PENDING_DEPLOYMENT** — must record: backend name+version (e.g. vLLM x.y / transformers x.y), dtype (bfloat16), quantization (none), device, max context, batch size |
| Substitute policy | exactly one substitute model allowed; must be written into a new `RUNTIME_LOCK.md` revision **before** any effectiveness experiment; no silent swaps |

> **Why StubLLM in Phase 2A:** G3 causality, manifest freeze, interpreter/tool tests and smoke-cost scaffolding do not require a 7B model. StubLLM preserves the *causal structure* (genotype edits → observable trace changes) so operators and evaluator can be verified now. LLM token/latency costs are recorded as **UNMEASURED** in `research/COST_BASELINE.md` until a real-model smoke run is approved.

## 2. Decoding profiles (frozen)

| Profile | Use | temperature | top_p | max_tokens | seed rule |
|---|---|---|---|---|---|
| `agent` | agent execution turns | 0.7 | 0.95 | 512 | `hash("agent", task_id, eval_rep, agent_id, turn)` |
| `op_proposal` | operator LLM proposals (op2 real mode) | 0.8 | 0.95 | 640 | `hash("op", operator_name, parent_hash, gen, draw)` |
| `fm_rewrite` | baseline B5 only | 0.8 | 0.95 | 800 | `hash("fm", parent_hash, gen, draw)` |

StubLLM is fully deterministic given the same seed inputs; temperature settings apply only in production mode.

## 3. Tools (deterministic)

| Tool | Spec | Timeout | Notes |
|---|---|---|---|
| `calc` | arithmetic on whitelist grammar: `+ - * / // % **` , parentheses, numeric literals, `abs/min/max/round` | 1s | no names, no attributes, no calls except the 4 builtins above |
| `py_sandbox` | AST-whitelisted expression/statements subset: assignments of arithmetic/str expressions, `if/else`, `for` over `range(n≤100)` | 2s | no imports, no filesystem, no network, no `eval/exec/open` |
| `str_ops` | `lower, upper, strip, split, join, replace, reverse, lstrip, rstrip` | 1s | string-only |

Tool errors are classified `tool_error` with a truncated message (≤200 chars) in the failure trace.

## 4. StubLLM contract (Phase 2A development mode)

Deterministic function `f(system_prompt, user_message, trace_so_far, seed) -> {action: answer|call_tool, ...}`.

Behavioral rules (fixed; unit-tested):

1. If any tool is available **and** the user message matches a numeric pattern and `system_prompt` contains `compute` or `step`, the stub calls `calc` first, then answers using the tool result.
2. Otherwise if `str_ops` is available and the message contains `upper|lower|reverse|join|split`, the stub calls `str_ops`.
3. Otherwise it answers directly.
4. **Answer correctness (stub oracle):** a task is marked solved iff the stub's strategy matches the task type's required strategy keywords in `system_prompt` **and** the required tools are enabled:
   - Family A requires `calc` in tools and prompt contains `compute` or `step`.
   - Family B requires `calc` **and** `str_ops` and prompt contains `transform`.
   - Family C requires `str_ops` and prompt contains `format` or `json`.
5. The final answer string is computed deterministically from the true task computation when the strategy matches; otherwise it is a deterministic wrong answer derived from the prompt hash.

This makes prompt/tool/workflow edits **causally effective** for G3 and for the structural cost/causality work, without pretending to be a real LLM. Production experiments must re-run G3 under the production backend.

## 5. Interpreter rules

- Workflow max 6 steps; max 8 interpreter iterations; max 24 agent turns per episode.
- Step types: `llm`, `tool`, `branch`, `finalize`. `finalize` exactly once, last.
- Branch: ≤2 arms, each 1–2 steps.
- Timeouts → `timeout` failure. Uncaught tool failure → `tool_error`. Unparseable final answer → `format_error` (Family C schema check) or `wrong_answer`.
- Episode ends at `finalize` answer, iteration cap, or turn cap.

## 6. Operator call protocol (frozen counts)

| Operator | LLM proposal calls (production) | Stub-mode calls | Notes |
|---|---|---|---|
| `prompt_local_edit` | **0** | 0 | deterministic template paraphrase |
| `prompt_critique_rewrite` | **2** (critique + rewrite) | 0 (deterministic rewrite) | failure trace excludes gold |
| `tool_subset_edit` | **0** | 0 | alternating add/drop |
| `workflow_step_edit` | **0** | 0 | fixed template set |
| `crossover` | **0** | 0 | mate from frozen tournament-2 |

No per-run variation of these counts is allowed.

## 7. Hardware / environment (Phase 2A)

| Field | Value |
|---|---|
| OS | Windows (as recorded by executor host) |
| Python | 3.10.1 (`C:\Program Files\Python310\python.exe`) |
| Third-party deps | **stdlib only** for the ECOS core (no torch/numpy required) |
| Parallelism | single-process; no distributed runs |
| Network | **none** in Phase 2A (StubLLM) |

Production hardware/quantization must be appended to this file when the real backend is deployed.

## 8. Cache

In-memory dict keyed by `sha256(genotype_behavior_hash + task_id + eval_rep + decoding_profile)`.  
Process-local; never written to disk in 2A; never includes Family C keys (C is never executed).  
Cache hits are counted in cost reports.

## 9. Immutability

Changes to any row above require a new `RUNTIME_LOCK.md` revision, a note in `research/COST_BASELINE.md`, and re-running G3 for operators whose causal effects could change.
