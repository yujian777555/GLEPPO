# G3-DIAG-v2-R3 Run Report

- Run ID: 20261029T052350Z_R3
- Status: PILOT_COMPLETE_REQUIRES_INDEPENDENT_REVIEW
- Model revision: a09a35458c702b33eeacc393d103063234e8bc28
- Revision match: True
- Actual generations: 54 / 100
- Wall clock: 42.883s / 300s

## Canary gate

- Completed: 3/3
- Tool path: 3/3
- Answer correct: 3/3
- Format compliant: 3/3
- Accounting valid: True
- Canary passed: True

## Paired pilot aggregate

### tool_subset_edit

- Paired comparisons: 9
- Invalid operator outcomes (counted as failures): 0
- Parent/child answer-correct rate: 0.7777777777777778 / 0.7777777777777778
- Parent/child tool-path rate: 1.0 / 0.0
- Parent/child hard-validity rate: 0.8888888888888888 / 0.0
- Parent/child format failures: 1 / 0
- Mean paired correctness delta: 0.0
- Behavior changes (diagnostic only): 9

### crossover

- Paired comparisons: 9
- Invalid operator outcomes (counted as failures): 0
- Parent/child answer-correct rate: 0.7777777777777778 / 0.4444444444444444
- Parent/child tool-path rate: 1.0 / 1.0
- Parent/child hard-validity rate: 0.8888888888888888 / 0.3333333333333333
- Parent/child format failures: 1 / 6
- Mean paired correctness delta: -0.3333333333333333
- Behavior changes (diagnostic only): 6

## Interpretation boundary

- Behavior change is diagnostic only and is not evidence of performance improvement.
- A child violating the required tool path is not an effective success even if its answer matches gold.
- Formal G3 remains FAIL. PC1, controller training, and Family C access remain not authorized/not run.
