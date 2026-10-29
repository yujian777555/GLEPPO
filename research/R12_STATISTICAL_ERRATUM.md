# R12 Statistical Erratum — Confusion Matrix Metric Correction

**Date:** 2026-10-29
**Original Report:** `research/runs/20261029T113122Z_R12/R12_REPORT.md`
**Erratum Type:** Metric name inversion

## Original (Incorrect) Claims

R12 report stated:
- Precision: 100% (val FAIL predicts final FAIL)
- Specificity: 100% (val OK predicts final OK)
- Recall: 33% (val catches 33% of final failures)

## Corrected Values (positive = final format FAILURE)

| Metric | Formula | Correct Value | Original Claim |
|--------|---------|---------------|----------------|
| **Precision** | TP/(TP+FP) | **33.3%** | 100% ❌ |
| **Recall** | TP/(TP+FN) | **100%** | 33% ❌ |
| **Specificity** | TN/(TN+FP) | **42.9%** | 100% ❌ |
| **NPV** | TN/(TN+FN) | **100%** | not reported |
| **Accuracy** | (TP+TN)/N | **55.6%** | not reported |

## Root Cause

The R12 report **inverted the positive class definition** in the metric labels. The confusion matrix counts (TP=2, FP=4, FN=0, TN=3) were correct, but:
- "Precision 100%" was actually **Recall** (TP/(TP+FN) = 2/2 = 100%)
- "Specificity 100%" was actually **NPV** (TN/(TN+FN) = 3/3 = 100%)
- "Recall 33%" was actually **Precision** (TP/(TP+FP) = 2/6 = 33.3%)

## Corrected Interpretation

- **Recall = 100%**: Validation catches ALL format failures (0 FN)
- **Precision = 33.3%**: When validation says FAIL, only 33% actually fail (4/6 are false alarms)
- **Specificity = 42.9%**: When validation says OK, 42.9% are actually OK (many false alarms)
- **NPV = 100%**: When validation says OK, it's ALWAYS correct

## Impact on Conclusions

1. **Validation signal reliability is DIFFERENT than reported:**
   - GOOD: catches all failures (recall=100%), never misses (NPV=100%)
   - POOR: many false alarms (precision=33.3%, specificity=42.9%)

2. **C2 mechanism still valid but with caveats:**
   - C2 will intervene when validation says FAIL (correct behavior)
   - But 4/6 interventions are unnecessary (false positives)
   - C2 achieves C1-level performance despite unnecessary interventions

3. **Original "100% precision/specificity" claim is RETRACTED**

## Corrected Metrics (for reference)

```
Confusion Matrix (positive = format FAILURE):
                 Predict FAIL  Predict OK
Actual FAIL      TP=2          FN=0
Actual OK        FP=4          TN=3

Precision = 2/6 = 33.3%
Recall = 2/2 = 100%
Specificity = 3/7 = 42.9%
NPV = 3/3 = 100%
Accuracy = 5/9 = 55.6%
```
