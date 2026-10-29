# Planner Latest Plan — R3 Frozen Protocol / Offline CI Green / Model Canary Pending

**Branch:** `c7-g3-diag-v2-r1-fastpath`  
**Latest R3 code/test commit:** `0d9d63f04a4d73e10d4dfc297e51b01d4c4aee3c`  
**Offline CI:** PASS — [run 7](https://github.com/yujian777555/GLEPPO/actions/runs/40818038141)  
**R3 protocol:** `research/G3_DIAG_R3_PROTOCOL.md`

## Implemented and tested

- B2-004 added as one-line JSONL without modifying B2-002 or R1/R2 data.
- Frozen B2-004 tool contract: `py_sandbox → 32`, then `calc → 41`.
- Task-compatible reference workflow added and validated.
- Metrics separated: answer correctness, format compliance, ordered tool-path validity, hard validity, effective success, and behavior-change diagnostic.
- R3 runner added with a pre-inference SHA-256 manifest, frozen revision check, three-seed canary, conditional paired pilot, actual-generation cap 100, total wall-clock cap 300 seconds, unique run directories, ledger, and result manifest.
- Independent verifier recomputes answer/format/path metrics and checks artifact hashes and ledger accounting.
- Invalid operator outcomes are counted as paired failures, not omitted from aggregate results.

GitHub Actions run 7 completed successfully:
- Python compile: PASS.
- Focused R3 tests: 13/13 PASS.
- Full offline suite: **418 tests, 0 failures**.

## Actual model experiment status

**Canary NOT RUN; actual model.generate calls = 0.** The successful CI run was a hosted CPU offline test run, not a Qwen inference experiment. The current chat execution environment does not expose an SSH/terminal channel to the existing A800 host. This is an execution-access blocker, not a canary result.

## Execute on the existing A800 host

```bash
cd /tmp/gleppo_prod
git fetch origin c7-g3-diag-v2-r1-fastpath
git checkout c7-g3-diag-v2-r1-fastpath
git pull --ff-only origin c7-g3-diag-v2-r1-fastpath
git status --short
CUDA_VISIBLE_DEVICES=0 /202532803004/conda_envs/amber/bin/python scripts/_run_g3_r3.py
```

The runner fails closed on the wrong branch or tracked modifications. It writes a unique run directory and freezes the source/task manifest before model loading. It starts the paired pilot only if the canary passes: tool path 3/3, answer correctness at least 2/3, correct model revision, and consistent generation/token accounting.

After execution, use the printed RUN_ID:

```bash
/202532803004/conda_envs/amber/bin/python scripts/verify_g3_r3.py research/runs/<RUN_ID>
```

Preserve and report a canary failure. If the full predeclared paired matrix cannot finish within 100 actual generations or 300 seconds, label it INCONCLUSIVE. Do not adjust gold or relax the tool-path contract.

## Frozen boundaries

- Formal G3 remains FAIL.
- PC1 remains unapproved and unexecuted.
- Family C remains unaccessed.
- Controller training remains unauthorized.
