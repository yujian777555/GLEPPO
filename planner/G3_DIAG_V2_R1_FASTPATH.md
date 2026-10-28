# GLEPPO G3-DIAG-v2-R1 Fast Path

**Branch:** `c7-g3-diag-v2-r1-fastpath`  
**Base commit:** `7b0017fee427a49f3f9eb34532bc447f4c2bb7cd`  
**Purpose:** unblock a small, credible real-model diagnostic quickly. This is NOT formal G3, NOT PC1, and NOT controller training.

## Decision

The v2 report is not accepted as proof that tool-path checks passed. The current ledger counts evaluation bundles, not actual model generations; cumulative token totals are repeatedly summed; the run's own model counter reports 240 generations against a stated 60-request cap. Historical v2 evidence must remain immutable and be labelled budget-noncompliant under the actual-generation interpretation.

Proceed in two short stages. Do not add unrelated architecture or protocol-hardening work.

## Stage A — Offline fixes only

1. Instrument the lowest common model-generation boundary in `ProductionLLM`. Every call to `model.generate` must atomically reserve one actual-call slot BEFORE generation. If the next call would exceed the configured cap, raise a dedicated budget exception before invoking the model.
2. Add one monotonically increasing call ID per actual generation. Record per-call input tokens, generated tokens, duration, status/error, task/operator/genotype role/replicate/turn and seed digest. Token counts must be deltas for that call, never cumulative totals.
3. Keep evaluation count, episode count, actual generation count and tool invocation count as separate fields. Never label an evaluation as a model request.
4. Fix `scripts/_run_g3_diag_v2.py`: do not hardcode `success=True`; aggregate real per-call ledger rows; ensure tool-path verification results are preserved in raw output and gate the experiment's tool-path claim.
5. Make offline validation fail if required runtime tool paths are absent or outputs differ from the frozen task contracts. Specifically:
   - B2-001: calc output `64`, str_ops output `SUM`.
   - B2-002: py_sandbox output `49`, calc output `43`.
   - B2-003: calc output `60`, str_ops output `HI`.
   Validate both the presence and order of successful calls, not just task metadata.
6. Add regression tests for hard cap (the over-cap model.generate must not execute), unique call IDs, per-call token deltas, failed calls, malformed/missing ledger rows, and all three tool paths. Run offline tests only. Do not alter or overwrite the v2 raw data, ledger, protocol, or manifest.

**Stage A acceptance:** tests demonstrate the cap is enforced at the actual generation boundary; reported actual-call count equals call-ledger row count and runtime counter; per-call token deltas sum to the runtime total; tool-path validators reject missing, reordered, failed or wrong-output events. Any failed check stops here.

## Stage B — Conditional small real-model diagnostic

Planner authorizes this narrow diagnostic only after Stage A acceptance is evidenced in the executor report. No additional approval round is required for this limited diagnostic; this authorization does NOT extend to formal G3 or PC1.

- Use the frozen Qwen2.5-7B-Instruct revision from `docs/RUNTIME_LOCK_V2.md` / the existing diagnostic protocol; verify the actual loaded revision before running.
- Generate a fresh timestamped run ID and new artifact filenames with suffix `_R1`. Never overwrite v2 artifacts.
- **Hard cap: 30 actual model.generate calls**, enforced in code at the generation boundary; also use a 300-second wall-clock cap.
- First evaluate the unmodified baseline on B2-001, B2-002 and B2-003. If the required tool path or output fails, STOP the run immediately and report which task/tool failed. Do not spend the remaining budget on operator comparisons.
- Only if all three baseline paths pass, compare one child from `tool_subset_edit` and one from `crossover` on the same frozen B2 tasks with paired seeds, within the same 30-call cap. Record partial completion honestly if the cap is reached.
- Include a positive-control operator only if the hard cap has remaining budget; never exceed the cap to complete a matrix.
- No Family C loading/access; no formal G3 status change; no PC1; no controller implementation/training; no tuning against held-out data.
- Report actual model generations, evaluations, episodes, tool calls, input/output tokens, elapsed time, task success, exact tool-path pass/fail and paired behavior differences separately. If the cap prevents a complete comparison, mark INCONCLUSIVE rather than changing the budget.

## Required deliverables

1. Code diff and tests.
2. Actual command lines, exit codes and test logs.
3. Immutable per-generation ledger and raw trajectories for the R1 run.
4. SHA-256 manifest generated only after all artifacts are finalized, plus an independent verifier.
5. A short decision table: baseline path validity; operator behavior differences; task success; budget compliance; next gate.

## Explicit non-claims

- A behavior difference is not performance improvement.
- Passing synthetic tests is not real-model evidence.
- Passing this diagnostic does not make formal G3 pass.
- This plan does not authorize PC1 or controller training.

## Stop condition

If Stage A cannot enforce the generation cap or cannot validate real tool paths, do not launch the model. Submit the exact failing test and smallest proposed fix; do not begin another broad audit cycle.
