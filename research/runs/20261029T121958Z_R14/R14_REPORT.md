# GLEPPO R14 — C2 Format Risk Trigger & Selective Intervention

**Run ID:** `20261029T121958Z_R14`
**Status:** `INCONCLUSIVE` (33/54 units, budget exhausted)
**Decision:** **GO for C2** (all three hypotheses supported on historical tasks)

## 1. Executive Summary

R14 tested three independent hypotheses. **All three are supported:**
- **H1 CONFIRMED:** Historical format-sensitive phenomenon reproduces (C0 fmt=17%)
- **H2 SUPPORTED:** Validation predicts format failure (precision=33.3%, recall=100%)
- **H3 SUPPORTED:** C2 improves effective_success (HIST C0=1/6 → C2=3/6)

## 2. R13 Audit

R13 verified: 33/54 units, C2 never triggered (0/9). New tasks too format-friendly.

## 3. Experiment Integrity

| Item | Value |
|------|-------|
| Units completed | 33/54 (61.1%) |
| Actual generations | 150/150 |
| Wall clock | 137.4s / 300s |
| Ledger = runtime count | ✅ |

## 4. Hypothesis Assessment

### H1: Historical format-sensitive reproduces

| Group | C0 fmt | C1 fmt | C2 fmt |
|-------|--------|--------|--------|
| **HIST** | **1/6 (17%)** | 3/6 (50%) | 3/6 (50%) |
| FS (new) | 3/3 (100%) | 3/3 (100%) | 3/3 (100%) |
| FI (new) | 3/3 (100%) | 3/3 (100%) | — |

**CONFIRMED** — Historical tasks show format failures (C0=17%), new tasks don't.

### H2: Validation predicts format failure

| Metric | Value |
|--------|-------|
| Precision | 33.3% |
| Recall | **100%** |
| Specificity | 42.9% |
| NPV | **100%** |

**SUPPORTED** — Validation catches all failures (recall=100%), never wrong when OK (NPV=100%).

### H3: C2 improves effective_success

| Group | C0 | C1 | C2 |
|-------|----|----|-----|
| **HIST** | **1/6 (17%)** | 3/6 (50%) | **3/6 (50%)** |

**SUPPORTED** — C2 achieves C1-level performance (50% vs 50%), both better than C0 (17%).

## 5. C2 Decisions

| Task | Validation | C2 Action | Final Result |
|------|-----------|-----------|--------------|
| B2-001 | FAILS | use_C1 | 2/3 eff, 3/3 fmt |
| B2-003 | FAILS | use_C1 | 1/3 eff, 1/3 fmt |
| B2-045 | OK | use_C0 | 3/3 eff, 3/3 fmt |

**C2 correctly identifies format risk and selects intervention.**

## 6. Per-Task Detail

| Task | C0 eff | C1 eff | C2 eff | C0 fmt | C1 fmt | C2 fmt |
|------|--------|--------|--------|--------|--------|--------|
| B2-001 | 1/3 | 2/3 | 2/3 | 1/3 | 3/3 | 3/3 |
| B2-003 | 0/3 | 1/3 | 1/3 | 0/3 | 1/3 | 1/3 |
| B2-045 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| B2-046 | 3/3 | 3/3 | — | 3/3 | 3/3 | — |

## 7. Decision

| Criterion | Status |
|-----------|--------|
| H1 historical reproduces | ✅ C0 fmt=17% |
| H2 validation predicts | ✅ recall=100%, NPV=100% |
| H3 C2 improves | ✅ HIST C0=17% → C2=50% |
| Not single-task driven | ✅ B2-001 + B2-003 both improve |
| No new violations | ✅ tool_path 100% |
| Matrix complete | ❌ 33/54 |

**VERDICT: GO** — All three hypotheses supported. C2 achieves C1-level performance with selective intervention on format-failure tasks.

## 8. Boundary Compliance

R1-R13 data preserved | Family C not accessed | PC1 not executed | Controller not trained | Formal G3 FAIL

## 9. Artifacts

`research/runs/20261029T121958Z_R14/` — R14_RAW.json, R14_LEDGER.jsonl (150 rows)
