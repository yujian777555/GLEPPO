# GLEPPO R26 Stage 1B — Planner Independent Review

**Review date:** 2026-11-03  
**Repository:** yujian777555/GLEPPO  
**Continuation branch:** r25-handoff  
**Stage 1B result commit:** bcdc24f4d3c7bbaf390678670c54f642b9948a99  
**Stage 1B audited source snapshot stated in report:** a1940a220bc2b7cdc4e6ba4fe0c723fbfb33c4ec  
**Current branch HEAD at review:** bcdc24f4d3c7bbaf390678670c54f642b9948a99  
**main HEAD at review:** 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e  
**R25 base:** a8ff1827434a88b2fef02a89aaf3e120e0a017a7  
**Planner decision:** ACCEPT_TAXONOMY_MILESTONE; REQUEST_CHANGES_FOR_FINDING_LEVEL_SOURCE_VERIFICATION  
**Next stage:** R26 Stage 1C

---

## 1. Executive decision

Stage 1B correctly narrows the formal numbered review headings to **42 headings, R12–R53**, and separates the TENTH review-result heading from the formal finding count. It also preserves the conservative disposition that all 42 formal findings remain UNVERIFIABLE.

Planner accepts the Stage 1B work as a **historical taxonomy/register milestone only**.

Planner does **not** accept the current-source audit as complete. The report's seven-domain checks are lexical presence checks, not semantic verification of code paths. The 450/450 test result is reported, but the report does not attach raw test output or a CI run reference, and a passing suite does not automatically establish coverage of each historical finding.

Correct state:

**R26_STAGE1B_TAXONOMY_MILESTONE_ACCEPTED; FINDING_LEVEL_SOURCE_AUDIT_REQUIRED; PC1_BLOCKED.**

## 2. Remote reference verification

GitHub branch API confirmed:
- r25-handoff HEAD = bcdc24f4d3c7bbaf390678670c54f642b9948a99;
- main HEAD = 6bad0b77835a2d00c62287c0c7d9d91d1d186d5e;
- Stage 1B commit parent = a1940a220bc2b7cdc4e6ba4fe0c723fbfb33c4ec.

GitHub compare confirmed:
- main → Stage 1B commit: ahead_by=104, behind_by=0;
- R25 base → Stage 1B commit: ahead_by=23, behind_by=0.

Thus r25-handoff contains the R25 base and Stage 1B, while main is an ancestor and is 104 commits behind this branch. Continue only on r25-handoff. Do not merge or update main automatically.

The audit file identifies a1940a2 as the source snapshot. The Stage 1B report itself was committed later at bcdc24f. Preserve both provenance fields; do not describe a1940a2 as the current report commit.

## 3. What Stage 1B established

The Finding Register records:
- 42 formal review-finding headings, R12–R53;
- 5–6 unnumbered SECOND review blockers;
- 8 TENTH remediation entries, R54–R61;
- one R60–R61 review-result heading, not a formal finding.

The formal heading count is defensible as a count of formal numbered headings. It is **not yet proof of 42 distinct underlying actionable issue clusters**. Cross-round restatements, splits, merges, and the SECOND 5-versus-6 blocker ambiguity still require an explicit crosswalk.

The Stage 1B register has a row for each R12–R53 ID and a disposition column, but it does not include all required fields: exact original wording, source report section/line, historical reviewed commit, current source symbol/line, actual test function, reproduction command/output, residual risk, and acceptance test.

The FIRST review search is also not reported as complete. Stage 1B must not imply that all historical rounds are accounted for unless the FIRST report search is completed or the source absence is explicitly bounded.

## 4. Why the seven-domain source audit is insufficient

The committed helper scripts/_r26b_source_audit.py checks for the presence of strings such as seed, crn, budget, cache, replica, hash, approval, hmac, trusted, runner, dry_run, and registered.

These checks establish only that relevant words occur in files. They do not establish:
- that the correct function is called on the registered path;
- that all required fields participate in seed derivation and cache identity;
- that counters use consistent units and reconcile;
- that approval keys come from a genuine external trust anchor;
- that registered execution exists;
- that the tests actually exercise the historical failure mode.

The source-level review by Planner confirms concrete distinctions that Stage 1C must investigate:

### 4.1 PC1 runner is explicitly a synthetic harness, not a registered runner

In gleppo/pc1.py:
- lines 1111–1117: execute_registered_pc1() unconditionally raises PC1ExecutionRefused;
- lines 1400–1411: SyntheticGateHarness explicitly states it does not load tasks, invoke evaluators, execute rollouts, or write raw artifacts, and that the full collection/rollout runner is not yet implemented.

Therefore the domain status must not be summarized as “runner has implementation” without this distinction. If the original R15/R25/R31 requirements demand a full registered runner, this is an explicit open implementation gap, not merely an unverifiable keyword-presence check. Keep registered PC1 blocked.

### 4.2 Approval cryptography is not the same as a trusted authorization source

In gleppo/pc1.py:
- lines 1176–1206 define an HMAC artifact and a signing function;
- lines 1208–1259 verify the supplied key, signature, protocol hash/version, action, status and document ID;
- lines 1320–1365 require a trusted artifact and an injected approval_key, then verify the artifact.

The code comments say the key must come from an external trusted source, but the gate accepts the key as a caller-supplied byte value. The test file tests/test_r54_r59.py defines TEST_KEY = b"test-approval-key-not-for-production" and uses it to test cryptographic behavior. This demonstrates test-only HMAC verification, not a production trust-anchor provisioning or identity-verification system. Stage 1C must audit provenance and trust-boundary semantics without creating or loading a production key.

The canonical protocol is currently PROPOSED_NOT_APPROVED, and ApprovalGate.check() rejects that state. This is correct default-deny behavior; it is not authorization to change the protocol state.

### 4.3 CRN tests need semantic coverage analysis

gleppo/evaluator.py lines 57–76 include task, state, rollout, replicate and replica index in effective seed parts while excluding action/genotype. tests/test_r8_r9_r11_pc1.py lines 50–64 exercises two different genotypes through an instrumented interpreter under the same CRN tuple.

However, tests/test_r39_r42.py lines 96–100 labels a test as action/genotype exclusion while comparing the same crn_seed(...) call with itself. That individual test is tautological. Stage 1C must assess the stronger end-to-end test as well, and must not mark an entire finding fixed or open based on one test in isolation.

gleppo/pc1.py lines 230–239 exposes a separate crn_seed() helper that has no replica-index argument, whereas the evaluator's effective seed includes replica index. Determine whether this helper is a base/summary seed or is used as the effective seed in PC1 records; do not assume these functions are interchangeable.

### 4.4 Budget and plan checks require behavior-level verification

BudgetLedger has explicit atomic validation paths in gleppo/pc1.py lines 253–368. load_plan_artifact() has stored-versus-computed plan hash checks, registered plan identity/version checks and three-way protocol hash checks at lines 1027–1082.

These are promising implementation elements, but presence is not proof. Stage 1C must inspect call sites and tests for partial mutation, missing accounting components, stale artifacts, altered plan mappings, path safety, and registered-vs-synthetic execution semantics.

## 5. Test result interpretation

Stage 1B reports:

python -m unittest discover -s tests

450/450 PASS, exit code 0.

Planner has not independently reproduced this command in this review. The report does not provide raw stdout/stderr or a workflow run URL. Do not call it independently verified by Planner.

Stage 1C must inspect test imports and side effects before execution. Run only targeted offline tests that cannot load Family C, call external APIs, start a production runtime, execute registered PC1, or train/load a controller. Save exact command, output, exit code, test count and skips. A passing suite is supporting evidence only for behaviors actually exercised.

## 6. Status and provenance issue

At Stage 1B, status.json top-level fields still include:
- reviewed_commit = e6ae41...;
- implementation_status = R3_EXECUTED_VERIFIED_REVIEWED;
- experimental_status = R3_PILOT_COMPLETE_NEGATIVE_BOTH_OPERATORS.

These may be historical R3 fields, but they are not aligned with the current R26 review state unless explicitly scoped. Stage 1C must inspect the schema and history, preserve historical R3 facts, and add or correct clearly scoped R26 provenance fields. Do not silently overwrite prior experiment history or let a stale reviewed_commit appear to identify the R26 audit snapshot.

## 7. Stage 1C acceptance criteria

The next Executor task must:
1. Recover exact refs and record source snapshot, report commit and current HEAD separately.
2. Complete the FIRST review history search and bound any missing-source conclusion.
3. Build an explicit crosswalk for all 42 formal IDs, SECOND blockers and R54–R61 remediation items.
4. For each formal finding, quote the original issue briefly and map current source symbols/line ranges, test functions, actual coverage, safe reproduction, disposition, residual risk and acceptance criteria.
5. Distinguish a synthetic harness from a registered execution runner.
6. Distinguish HMAC correctness from external trust-anchor provenance.
7. Inspect seed helper versus effective evaluator seed semantics.
8. Verify budget, protocol, plan, provenance and statistical-analysis behavior through actual tests and call paths.
9. Inspect test bodies and run only safe offline targeted tests.
10. Keep production source unchanged. Document defects for a later separately authorized remediation stage.
11. Update status.json, latest_plan.md, R26 handoff and next-session prompt with exact evidence.

## 8. Hard boundaries

No registered PC1 execution. No Family C access. No ECOS/PPO training. No Formal G3 efficacy rerun. No new model/API calls. No production runtime calls. No production source fixes in Stage 1C. No changes to frozen R1–R25 evidence or manifests. No merge/reset/force-push of main.

**Planner disposition:** Stage 1B taxonomy milestone accepted. The 42 formal heading count is accepted; the count of distinct actionable issue clusters remains unresolved. The seven-domain lexical scan and 450/450 claim do not constitute finding-level verification. PC1 remains BLOCKED.
