# Planner Latest Plan — R3 Frozen Protocol / Offline Validation Passed

**Branch:** `c7-g3-diag-v2-r1-fastpath`  
**R3 implementation baseline:** `a5c6f14b1b33ef062c8d5180d764580542c97f1e`  
**Offline CI:** PASS — [run 6](https://github.com/yujian777555/GLEPPO/actions/runs/40817885049)  
**R3 protocol:** `research/G3_DIAG_R3_PROTOCOL.md`  
**Independent verifier:** `scripts/verify_g3_r3.py`

## What is implemented

- Added independent task B2-004 in `data/diagnostic_B2_R3.jsonl` as one-line JSONL.
- Added frozen ordered path contract: `py_sandbox → 32`, then `calc → 41`.
- Added task-compatible B2-004 reference workflow.
- Added independent metrics for answer correctness, format compliance, tool-path validity, hard validity, and effective success.
- Added gated R3 runner with pre-inference SHA-256 source/task manifest, exact model-revision check, 3-seed canary, paired reference/operator pilot, generation cap 100, wall-clock cap 300s, per-generation ledger, run-specific artifacts, and no overwrite of R1/R2.
- Added independent artifact/metric verifier.
- Invalid operator outcomes are counted as failures in paired aggregates, not silently dropped.
- Formal G3 remains FAIL. PC1, Family C, and controller training remain unauthorized.

## Offline validation evidence

GitHub Actions run `40817885049` completed successfully:
- R3 scripts and metric module: `py_compile` PASS.
- Focused R3 tests: PASS.
- Full offline suite: **416 tests, all passed**.
- This CI run used a hosted CPU runner for offline tests only. It did not load Qwen and did not run the R3 model canary.

## Experiment status — important distinction

**Actual R3 model calls: 0. Canary: NOT RUN.** The current chat execution environment has no SSH/terminal channel to the A800 host at `/tmp/gleppo_prod`. Do not describe the offline CI pass as an experiment result. The runner is committed and ready for execution on the existing A800 environment.

## Immediate execution on the existing A800 host

Run on the host that already has the frozen Qwen snapshot and the project's conda environment:

```bash
cd /tmp/gleppo_prod
git fetch origin c7-g3-diag-v2-r1-fastpath
git checkout c7-g3-diag-v2-r1-fastpath
git pull --ff-only origin c7-g3-diag-v2-r1-fastpath
git status --short
CUDA_VISIBLE_DEVICES=0 /202532803004/conda_envs/amber/bin/python scripts/_run_g3_r3.py
```

The runner fails closed if the tracked tree is dirty or the branch is wrong. It writes a unique `research/runs/<RUN_ID>/` directory and freezes the manifest before model loading. It runs the paired pilot only if the B2-004 canary passes all frozen gates.

After the run, use the printed RUN_ID:

```bash
/202532803004/conda_envs/amber/bin/python scripts/verify_g3_r3.py research/runs/<RUN_ID>
```

Inspect the verifier result, then commit the run artifacts and update `status.json`. If the canary fails, preserve and report the failure; do not relax the gold, task contract, or gate.

## Acceptance boundary

- Canary must pass: tool path 3/3, answer correctness at least 2/3, correct revision, and consistent generation/token accounting.
- Full pilot: B2-001, B2-003, B2-004 × three paired seeds × reference / `tool_subset_edit` / `crossover`.
- If the predeclared matrix cannot finish within 100 actual generations / 300 seconds, label INCONCLUSIVE.
- Behavior change is diagnostic only, never a success criterion.
- Formal G3 remains FAIL pending separate independent review; no PC1 or controller training.
