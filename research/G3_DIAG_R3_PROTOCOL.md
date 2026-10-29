# G3-DIAG-v2-R3 — Performance-Validity Pilot

**Status:** Protocol frozen; no model calls are authorized until this exact revision is checked out and its pre-run manifest is written.  
**Parent evidence:** R2 `20261029T040254Z_R2`; R2 remains immutable.  
**Model:** Qwen2.5-7B-Instruct, revision `a09a35458c702b33eeacc393d103063234e8bc28`.  
**Hard caps:** 100 actual `model.generate` calls and 300 seconds total wall-clock, including model loading.

## 1. Frozen tasks

- Reuse B2-001 and B2-003 from the immutable `data/diagnostic_B2.jsonl`.
- Add B2-004 in `data/diagnostic_B2_R3.jsonl`; do not modify or relabel B2-002.
- B2-004 input requires `py_sandbox` to compute `5*6+2`, followed by `calc` to compute `32+9`. Gold is `41`, held in the evaluator-side task record. Required ordered tool-path contract: `py_sandbox → 32`, then `calc → 41`.
- The final answer must copy the second tool output, not the first intermediate result. The prompt does not state the gold answer directly.

## 2. Frozen seed plan

Use exactly these predeclared paired seed IDs, in order:

- `r3-paired-seed-001`
- `r3-paired-seed-002`
- `r3-paired-seed-003`

The effective seed input is derived only from protocol ID, task ID, and seed ID. It must not include genotype identity, operator name, or genotype hash. The reference and both children for a task/seed use the same seed input.

The three B2-004 reference canary episodes are reused as the B2-004 reference rows in the paired pilot; do not spend extra generations repeating them.

## 3. Metrics (kept separate)

- **`answer_correct`:** independently evaluate the final answer using the evaluator-owned gold checker, regardless of interpreter failure flags or tool-path outcome.
- **`format_compliant`:** answer starts with exact prefix `Final answer: `, has a non-empty value of at most 100 characters, and contains no additional line.
- **`tool_path_valid`:** the frozen ordered tool-path contract succeeds with exact expected outputs.
- **`hard_validity`:** `format_compliant AND tool_path_valid`.
- **`effective_success`:** `answer_correct AND hard_validity`.
- **`behavior_changed`:** diagnostic only; never a performance success criterion.

A child violating the required tool path is invalid even if its answer string matches gold. Do not collapse the metrics into a single opaque score.

## 4. Stage A — baseline canary

Run B2-004 reference genotype on the three frozen seeds.

Proceed to the paired pilot only if all conditions hold:

1. Tool-path compliance is 3/3.
2. Answer correctness is at least 2/3.
3. The loaded model revision matches the frozen revision.
4. Generation count equals ledger rows, call IDs are unique and monotonic, and the sum of per-call output-token deltas equals the runtime output-token total.
5. No model-generation failure is hidden or dropped from the ledger.

If any condition fails, stop immediately, save artifacts, and label `CANARY_FAIL_STOP`. Do not adjust the gold answer, loosen the tool-path contract, or inspect the gold from model-facing inputs to force a pass.

## 5. Stage B — paired performance pilot

Only after Stage A passes, compare the task-compatible reference, `tool_subset_edit`, and `crossover` on B2-001, B2-003, and B2-004, each with the three paired seed IDs.

For B2-001 and B2-003, run each reference once per seed and evaluate both children against that same paired reference. For B2-004, reuse the canary reference outcomes and evaluate both children on the same seed IDs.

Report per-task and aggregate values for:
- parent and child answer correctness;
- parent and child tool-path validity;
- parent and child format compliance and format-failure counts;
- hard-validity and effective-success rates;
- paired correctness delta (child minus parent);
- behavior-change rate, explicitly diagnostic only.

If the complete predeclared matrix cannot finish within 100 actual generations or 300 seconds, stop and label the pilot `INCONCLUSIVE`. Do not silently drop seeds or tasks and do not call a partial matrix a pass.

## 6. Artifacts and integrity

Every run writes to a unique `research/runs/<RUN_ID>/` directory; never overwrite R1, R2, or a prior R3 run. Before loading the model or making any model call, write `R3_FROZEN_MANIFEST.json` with SHA-256 and size for the frozen protocol, task files, runner, verifier, and relevant implementation sources. The final result manifest records hashes for the frozen manifest, raw results, ledger, and report.

Required artifacts:
- `R3_FROZEN_MANIFEST.json` (created before model load);
- `R3_RAW.json`;
- `R3_LEDGER.jsonl`;
- `R3_REPORT.md`;
- `R3_RESULT_MANIFEST.json`;
- independent verification output.

## 7. Decision boundary

This is a diagnostic performance-validity pilot, not formal G3. Formal G3 remains **FAIL** unless a separate review approves a complete protocol. PC1, controller training, and Family C access remain **NOT AUTHORIZED / NOT RUN**, regardless of the R3 outcome.
