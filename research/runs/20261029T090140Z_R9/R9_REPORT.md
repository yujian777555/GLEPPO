# GLEPPO R9 — Format Constraint Cross-Task Replication

**Run ID:** `20261029T090140Z_R9`
**Status:** `COMPLETE` (36/36 units, 144/150 generations)
**Decision:** **INCONCLUSIVE** (task-dependent effects, H2 not supported)

## 1. Executive Summary

R9 tested whether R8's format constraint mechanism replicates across 5 structurally different tasks. **H1 (format mechanism) is supported** — C1 consistently reduces format failures. **H2 (performance conversion) is NOT supported** — format improvement does NOT reliably convert to effective success. **H3 (task-conditioned) is confirmed** — effects vary significantly by task.

## 2. Experiment Integrity

| Item | Value |
|------|-------|
| Units completed | 36/36 (100%) |
| Actual generations | 144/150 |
| Wall clock | 109.2s / 300s |
| Ledger = runtime count | ✅ |
| Token delta = runtime total | ✅ |
| Revision match | ✅ |

## 3. Independent Metric Recomputation

### Group Aggregates

| Group | Arm | Effective Success | Format Compliant |
|-------|-----|------------------|-----------------|
| **FS (Format-Sensitive)** | C0 | 6/12 (50.0%) | 8/12 (66.7%) |
| **FS (Format-Sensitive)** | C1 | 6/12 (50.0%) | 12/12 (100%) |
| **FI (Format-Insensitive)** | C0 | 5/6 (83.3%) | 5/6 (83.3%) |
| **FI (Format-Insensitive)** | C1 | 6/6 (100%) | 6/6 (100%) |

### Per-Task Breakdown

| Task | Group | C0 eff | C1 eff | C0 fmt | C1 fmt | Pattern |
|------|-------|--------|--------|--------|--------|---------|
| B2-001 | FS | 0/3 | **3/3** | 0/3 | 3/3 | **C1 wins: format→effective** |
| B2-022 | FS | 3/3 | 3/3 | 3/3 | 3/3 | Both succeed |
| B2-024 | FS | 0/3 | 0/3 | 2/3 | 3/3 | Format fixed, answer still wrong |
| B2-026 | FS | **3/3** | 0/3 | 3/3 | 3/3 | **C0 wins: C1 HURTS** |
| B2-023 | FI | 2/3 | 3/3 | 2/3 | 3/3 | C1 slightly better |
| B2-025 | FI | 3/3 | 3/3 | 3/3 | 3/3 | Both succeed |

### Paired Analysis

| Group | C1 wins | C0 wins | Ties | McNemar p |
|-------|---------|---------|------|-----------|
| FS | 3 | 3 | 6 | 1.0000 |
| FI | 1 | 0 | 5 | 1.0000 |

## 4. Hypothesis Assessment

| Hypothesis | Verdict | Evidence |
|------------|---------|----------|
| **H1:** C1 reduces format failures | **SUPPORTED** | FS: 8/12→12/12, FI: 5/6→6/6 |
| **H2:** Format→effective success | **NOT SUPPORTED** | FS: 6/12→6/12 (equal) |
| **H3:** Task-conditioned dependence | **CONFIRMED** | B2-001: C1 wins; B2-026: C0 wins |

## 5. Key Findings

### 5.1 Format mechanism replicates (H1 ✅)
C1 consistently improves format compliance across all tasks.

### 5.2 Performance conversion is task-dependent (H2 ❌)

**B2-001:** Format fix → effective success (0%→100%) ✅
**B2-024:** Format fix → no conversion (answer still wrong) ❌
**B2-026:** C1 HURTS (3/3→0/3) despite format compliance ✅

### 5.3 C1 can hurt performance (B2-026)
On B2-026, C0 achieves 3/3 effective success but C1 achieves 0/3. The format constraint appears to interfere with answer correctness on this task.

### 5.4 B2-001 is the only clear conversion
Consistent with R8 finding — B2-001 is the primary beneficiary.

## 6. Decision

| Criterion | Status |
|-----------|--------|
| Format improvement on multiple tasks | ✅ H1 supported |
| Effective success positive trend | ❌ FS: 50%→50% |
| Not single-task driven | ❌ B2-001 vs B2-026 cancel out |
| No new violations | ✅ Both 100% tool_path |
| Budget/evidence complete | ✅ 36/36 |

**VERDICT: INCONCLUSIVE**

Format constraint reliably improves format compliance (H1), but does NOT reliably convert to effective success (H2). Effects are task-dependent (H3): B2-001 benefits, B2-026 is harmed. The net FS effect is zero (6/12 both arms).

## 7. Implications for GLEPPO

1. **Format constraint is NOT a reliable improvement** — it helps some tasks but hurts others
2. **B2-001 remains the primary beneficiary** — R8's finding does not generalize broadly
3. **Task-specific analysis required** — cannot deploy blanket format constraint
4. **B2-026 degradation needs investigation** — why does format constraint hurt answer correctness?

## 8. Boundary Compliance

R1-R8 data preserved | Family C not accessed | PC1 not executed | Controller not trained | Formal G3 FAIL

## 9. Artifacts

`research/runs/20261029T090140Z_R9/` — R9_RAW.json, R9_LEDGER.jsonl (144 rows), R9_FROZEN_MANIFEST.json, R9_RESULT_MANIFEST.json
