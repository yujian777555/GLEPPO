# GLEPPO R26 Stage 1I-R2.1.1 — Evidence and Provenance Closeout

**Role:** Executor under independent Planner review  
**Repository:** yujian777555/GLEPPO  
**Branch:** r25-handoff only  
**Reviewed R2.1 work commit:** 5cbd5f605ac6d1df2e6f46e25c76f939163371ab  
**R2.1 parent:** f0569b1e0ab97372f5ae0bf86e564ae17bdca61f  
**Planner review:** research/R26_STAGE1I_R2_1_PLANNER_REVIEW.md  
**Planner decision:** REQUEST_CHANGES — narrow R2.1.1 only

## 1. Scope

Do not restart R1/R2 or repeat the 42-row semantic audit. Correct only:

1. Persist the actual 21-case validator self-test stdout and exit code.
2. Remove one unsupported R41 item from `uncovered_acceptance_conditions`.
3. Complete R2.1 work-commit provenance and refresh the stale branch/main relation in `status.json`.

No other changes are authorized.

## 2. Persist actual validator output

Run exactly:

```bash
python scripts/_r26i_validator.py --self-test
```

Capture the actual stdout verbatim and the actual process exit code. Append them to `research/R26_STAGE1I_TEST_EVIDENCE.md` under a clearly dated R2.1.1 subsection. The output must show all 21 named cases, the total (21 tests, 21 passed, 0 failed), the overall result, and exit code.

Do not hand-construct, infer, or fabricate output. If the command does not pass, report the actual failure and stop; do not modify the test suite or weaken the check.

The exact new adversarial case must remain:
- existing source file;
- valid start line within the file;
- end line beyond EOF;
- rejection specifically with `SRC_RANGE_END_OUT_OF_FILE`.

Do not claim the Planner independently executed the test. The record must distinguish Executor-captured output from Planner static review.

## 3. Correct the R41 acceptance-condition list

In `research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json` and its Markdown rendering:

- Keep R41 = PARTIALLY_FIXED.
- Keep the four artifact lifecycle tests and the uncovered end-to-end registered-analysis artifact-consumption condition.
- Remove `Record artifact hash/path/identity in raw evidence` from `uncovered_acceptance_conditions`. It is not one of the five original R41 acceptance criteria in `SEVENTH_REVIEW_FINDINGS.md`.
- If useful, retain that idea only as a separately labelled future recommendation in the rationale/report, not as an original unmet acceptance condition.
- Do not alter the five original acceptance criteria or the other R41 evidence.

Counts must remain mechanically derived from JSON and unchanged at 25/15/1/1 = 42. JSON/Markdown row dispositions must remain synchronized.

## 4. Provenance correction

Update `status.json` to record these as distinct historical facts:

- R2 work commit: `34ba848c4b8cf4fa07c9583e049b0bb7b0635aab`
- R2 provenance follow-up: `da7a6c7bbd09f1ebca5bf6080dffc78e15615115`
- R2 Planner review parent / R2.1 parent: `f0569b1e0ab97372f5ae0bf86e564ae17bdca61f`
- R2.1 work commit: `5cbd5f605ac6d1df2e6f46e25c76f939163371ab`
- Main: `6bad0b77835a2d00c62287c0c7d9d91d1d186d5e`

Refresh the pre-provenance-follow-up relation:
- branch head before follow-up: `5cbd5f605ac6d1df2e6f46e25c76f939163371ab`
- ahead of main: 234
- behind main: 0
- main modified: false

If a provenance follow-up commit is created, record the R2.1 work commit in it. Do not overwrite historical R2 refs, and do not modify main. The Planner review commit is `3fb54584a914e880f0b48896883a14e43a162217`; fetch the remote branch again before editing and use its current HEAD as the parent.

## 5. Required verification

- Actual self-test stdout is captured verbatim and exit code is recorded.
- The new EOF test still checks the specific diagnostic.
- R41 no longer lists unsupported raw-evidence identity as an original uncovered acceptance condition.
- JSON: exactly 42 unique IDs R12-R53.
- Dispositions remain 25/15/1/1 = 42.
- Markdown: 42 matching rows; summary equals JSON.
- UTF-8 valid; no replacement characters or mojibake.
- Only the three scoped evidence/provenance files and their necessary report/status records change.
- No production source or `tests/` changes.
- No model/API calls, production runtime, signing-key access, PC1, Family C, or controller training.
- Main unchanged.
- Branch pushed and clean.

## 6. Stop condition

After the R2.1.1 evidence/provenance closeout is committed and all durable records are updated, stop and wait for Planner independent review.

If accepted, the next task is **R26_ECOS_PROTOCOL_RECONCILIATION**. That phase must resolve reward/state/gamma/split/budget/seed-contract drift and prepare the fastest safe baseline experiment. It does not authorize registered PC1 execution, Family C access, Formal G3 efficacy claims, or controller training.

Do not begin protocol reconciliation during R2.1.1.
