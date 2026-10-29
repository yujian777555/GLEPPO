# GLEPPO R13 — R12 Statistical Audit + C2 Generalization

**Run ID:** `20261029T120036Z_R13`
**Status:** `INCONCLUSIVE` (33/54 units, budget exhausted)
**Decision:** **INCONCLUSIVE** (C2 mechanism not triggered on new tasks)

## 1. R12 Statistical Erratum

R12 report had **inverted metric names**. Corrected values:

| Metric | Correct Value | R12 Claim |
|--------|---------------|-----------|
| Precision | **33.3%** | 100% ❌ |
| Recall | **100%** | 33% ❌ |
| Specificity | **42.9%** | 100% ❌ |
| NPV | **100%** | not reported |
| Accuracy | **55.6%** | not reported |

**Corrected interpretation:**
- Validation catches ALL failures (recall=100%)
- But many false alarms (precision=33.3%, specificity=42.9%)
- When validation says OK, it's ALWAYS correct (NPV=100%)

## 2. C2 Mechanism Re-evaluation

| Proposition | Verdict |
|-------------|---------|
| 1. Validation correlates with final format | PARTIAL (good recall, poor precision) |
| 2. C1 reduces format failures | SUPPORTED (B2-001: 0/3→3/3) |
| 3. C2 improves effective_success | SUPPORTED in R12 (FS: 4/9→5/9) |

## 3. R13 Results (New Tasks B2-039-B2-044)

### Per-Task

| Task | C0 | C1 | C2 | C0 fmt | C1 fmt |
|------|----|----|-----|--------|--------|
| B2-039 | 2/3 | 3/3 | 2/3 | 3/3 | 3/3 |
| B2-040 | 0/3 | 0/3 | 0/3 | 2/3 | 3/3 |
| B2-041 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 |
| B2-042 | 1/3 | 0/3 | — | 3/3 | 3/3 |

### C2 Decisions: **0/9 use_C1** — validation always showed format OK

## 4. Key Finding

**New tasks (B2-039-B2-044) do NOT trigger format failures in validation.** C2's selective intervention cannot be tested without format failures.

This confirms R11's finding and R12's corrected precision=33.3% (many false alarms mean validation rarely says FAIL on new tasks).

## 5. Decision

| Criterion | Status |
|-----------|--------|
| R12 audit complete | ✅ Erratum documented |
| C2 reproduces on new tasks | ❌ C2 never intervenes |
| Format failures present | ❌ New tasks too format-friendly |
| Matrix complete | ❌ 33/54 |

**VERDICT: INCONCLUSIVE** — C2's mechanism requires format-sensitive tasks to trigger.

## 6. Implications

1. **R12's "100% precision" claim is RETRACTED** — actual precision=33.3%
2. **C2 requires format failures to function** — new tasks don't provide this
3. **R10's B2-001 remains the key use case** — format failure → validation detects → C2 intervenes
4. **Need to design tasks with higher format failure rates** to test C2's selectivity

## 7. Boundary Compliance

R1-R12 data preserved | Family C not accessed | PC1 not executed | Controller not trained | Formal G3 FAIL

## 8. Artifacts

- `research/R12_STATISTICAL_ERRATUM.md` — metric correction
- `research/runs/20261029T120036Z_R13/` — R13_RAW.json, R13_LEDGER.jsonl (150 rows)
