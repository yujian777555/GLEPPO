# GLEPPO R17 — M2 Structural Signal & C2 Performance

**Run ID:** `20261029T125653Z_R17`
**Status:** `INCONCLUSIVE` (37/54 units, budget exhausted)
**Decision:** **NO-GO for H3** (C1 hurts M2_POS tasks)

## 1. Hypothesis Assessment

| Hypothesis | Verdict | Evidence |
|------------|---------|----------|
| H1: M2 has predictive value | ✅ SUPPORTED | M2 correctly splits risk groups (6/6 each) |
| H2: M2 reduces unnecessary interventions | ✅ SUPPORTED | C2 use_C1 only for M2_POS |
| **H3: C2 improves effective_success** | **❌ NOT SUPPORTED** | M2_POS: C0=28.6%, C2=0% |
| H4: Not task-selection artifact | ⚠️ PARTIAL | 6 independent tasks |

## 2. M2 Risk Group Results

| Group | Arm | Effective | Format |
|-------|-----|-----------|--------|
| **M2_POS** | C0 | **2/7 (28.6%)** | 4/7 (57%) |
| **M2_POS** | C1 | **0/6 (0%)** | 5/6 (83%) |
| **M2_POS** | C2 | **0/6 (0%)** | 5/6 (83%) |
| M2_NEG | C0 | 5/6 (83.3%) | 6/6 (100%) |
| M2_NEG | C1 | 5/6 (83.3%) | 6/6 (100%) |
| M2_NEG | C2 | 5/6 (83.3%) | 6/6 (100%) |

## 3. Critical Finding: C1 Hurts M2_POS

| Task | C0 | C1 | C2 | Pattern |
|------|----|----|-----|---------|
| B2-055 | **2/3** | **0/3** | 0/3 | **C1 destroys performance** |
| B2-056 | 0/3 | 0/3 | 0/3 | Both fail (hard task) |
| B2-057 | 2/3 | 2/3 | 2/3 | M2_NEG, no difference |
| B2-058 | 3/3 | 3/3 | 3/3 | M2_NEG, no difference |

**B2-055 shows the problem:** C0 achieves 2/3 but C1/C2 achieve 0/3. The format constraint degrades answer correctness.

## 4. M2 Decision Analysis

| Task | M2 Risk | C2 Action | Result |
|------|---------|-----------|--------|
| B2-055 | True | use_C1 | 0/3 eff (worse than C0's 2/3) |
| B2-056 | True | use_C1 | 0/3 eff |
| B2-057 | False | use_C0 | 2/3 eff |
| B2-058 | False | use_C0 | 3/3 eff |

M2 correctly identifies risk, but C1 intervention HURTS on risk-positive tasks.

## 5. Root Cause

**Format constraint interferes with answer generation** on M2_POS tasks. The constraint "Do NOT include tool outputs before 'Final answer:'" may cause the model to produce shorter but incorrect answers.

## 6. Decision

| Criterion | Status |
|-----------|--------|
| M2 predictive value | ✅ Supported |
| M2 reduces unnecessary interventions | ✅ Supported |
| C2 improves effective_success | ❌ NOT supported |
| No systematic degradation | ❌ C1 hurts M2_POS |
| Matrix complete | ❌ 37/54 |

**VERDICT: NO-GO for H3** — C2 does not improve effective_success. C1 format constraint degrades performance on M2_POS tasks (B2-055: 2/3→0/3).

## 7. Implications

1. **M2 structural signal works** for risk identification
2. **C1 format constraint is harmful** on some format-sensitive tasks
3. **C2 inherits C1's harm** when M2 says intervene
4. **Need to rethink format constraint** — it's not universally beneficial

## 8. Boundary Compliance

R1-R16 data preserved | Family C not accessed | PC1 not executed | Controller not trained | Formal G3 FAIL

## 9. Artifacts

`research/runs/20261029T125653Z_R17/` — R17_RAW.json, R17_LEDGER.jsonl (150 rows)
