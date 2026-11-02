# GLEPPO R24 Handoff

**Repository:** `yujian777555/GLEPPO`  
**Branch:** `c7-g3-diag-v2-r1-fastpath`  
**R23 base:** `2c66291ea896246a4f90b1f713c81a7ce931682c`

## Current interpretation

R23 is a meaningful partial audit milestone, but its headline claims need correction:
- R21 review is `ACCEPT_WITH_LIMITATIONS`, not unconditional ACCEPT.
- The ten tamper scenarios in `scripts/_r23_tamper_tests.py` are prepared in temporary copies but never passed to the verifier; `run_verifier()` is never called.
- The R21 verifier leaves seed, group, frozen-manifest hash/size and ledger-provenance checks incomplete; C4 `source_valid` remains a proxy for `effective_success`.
- The DAC AST script inspects one file and prints PASS without executing the claimed metamorphic tests.
- The PC1 matrix is a summary; current-branch finding-by-finding audit is incomplete.
- Formal G3 and training preregistration create a circular gate: G3 report says training is needed for the final G3 rerun, while preregistration requires G3 PASS before training.
- PC1's proposed protocol itself requires independent review, trusted Planner approval, production runtime lock and budget guard; it does not require post-training G3 efficacy passage as a precondition.

## Immediate next task

Read `planner/GLEPPO_R24_CORRECTIVE_AUDIT_PROMPT.md` and `research/R23_STATIC_REASSESSMENT.md`.

Start with:
1. Parameterize R21 verifier input path.
2. Make all tamper tests execute verifier on temp copies and assert non-zero exit.
3. Fix exact seeds, split, unit-key, manifest and ledger provenance checks.
4. Resolve C4 outcome semantics without silently promoting source_valid.
5. Replace DAC print-only audit with real dependency-path and executed metamorphic tests.
6. Audit every historical PC1 finding against current source and tests.
7. Amend gate sequence into G3-PREFLIGHT → approved PC1 → ECOS training → G3-EFFICACY, subject to independent review and approval.
8. Complete executable ECOS preregistration, align reward definitions, and reconcile budget.

## Hard boundaries

- Do not execute PC1.
- Do not run formal G3 efficacy.
- Do not train ECOS.
- Do not access Family C.
- Do not make model/API calls in R24.
- Do not modify historical raw data or manifests.
- Do not claim CI or independent approval without exact evidence.
- DAC must remain a shared fixed component across all controller arms.
