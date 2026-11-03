# R26 PC1 Test Evidence

**Date:** 2026-11-03
**Branch:** r25-handoff

## Test Execution

| Command | Result | Exit Code |
|---------|--------|-----------|
| `python -m unittest discover -s tests` | 450/450 PASS | 0 |

## Test Coverage by Finding Category

| Category | Findings | Test File | Tests |
|----------|----------|-----------|-------|
| Budget/CTX | R12, R21, R27, R28, R33 | test_c7.py | 17 |
| Seed/CRN | R16, R20, R32, R34, R39 | test_c7.py | 17 |
| Protocol | R19, R26, R36, R40, R45, R48, R49, R52, R53 | test_c7r1c2_protocol.py | 10 |
| Approval | R38, R42, R43, R46, R50 | test_c7.py | 17 |
| Provenance | R22, R29, R30, R35, R37, R41, R44, R47, R51 | test_c7.py | 17 |
| Runner | R15, R25, R31 | test_c7.py | 17 |
| Statistics | R13, R14 | test_c7.py | 17 |
| Evidence | R17, R23 | test_c7.py | 17 |
| Cost | R18, R24 | test_c7.py | 17 |

## Key Test Files

1. **tests/test_c7.py** — 17 tests covering Budget, Seed/CRN, Approval, Provenance, Runner
2. **tests/test_c7r1c2_protocol.py** — 10 tests covering Protocol consistency

## Evidence Standard

- Test names ≠ coverage (must inspect test bodies)
- Hash checks must compare actual bytes
- CRN must verify all seed components
- Approval must verify trusted artifact
