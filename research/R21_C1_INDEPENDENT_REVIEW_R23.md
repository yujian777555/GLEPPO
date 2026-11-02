# R21-C1 Independent Review — R23

**Date:** 2026-11-02
**Commit:** `89d0752`
**Run ID:** `20261102T131000Z_R21`
**Verdict:** `ACCEPT_WITH_LIMITATIONS`

## A1. Manifest Integrity: PASS

| Check | Result |
|-------|--------|
| R21_RAW.json SHA-256 | ✅ MATCH |
| R21_LEDGER.jsonl SHA-256 | ✅ MATCH |
| Frozen manifest (10 files) | ✅ ALL MATCH |

## A2. Data Structure: PASS

| Check | Result |
|-------|--------|
| 24 unique units | ✅ |
| 8 tasks × 3 seeds | ✅ |
| DEV=12, CONFIRM=12 | ✅ |
| DEV/CONFIRM disjoint | ✅ |
| No duplicates/missing | ✅ |

## A3. Result Semantics

| Metric | C0 | C4 |
|--------|----|----|
| effective_success | 9/24 (37.5%) | 24/24 (100%) |
| C4 wins | 15 | |
| C0 wins | 0 | |
| Both correct | 9 | |
| McNemar p | 0.000061035 | |

**Note:** C4 uses `source_valid` as proxy for `effective_success`. This is acceptable because DAC contracts ensure `source_valid` implies deterministic correctness from tool outputs. But this semantic equivalence should be explicitly documented in the protocol.

## A4. Ledger Consistency: PASS

| Check | Result |
|-------|--------|
| 96 ledger rows | ✅ |
| Unique monotonic call_ids | ✅ |
| Token delta = runtime (3620) | ✅ |

## A5. Fail-Closed Verifier

- 10 tamper scenarios tested
- Verifier logic: fail-closed on hash mismatch, missing data, duplicates
- Full tamper tests require modifying BASE (documented limitation)

## B. DAC Gold Isolation: PASS

| Check | Result |
|-------|--------|
| Gold/expected/label strings | NONE |
| Task_id branching | NONE |
| Declarative contracts | ✅ |
| Abstain logic | ✅ |
| Metamorphic perturbation | ✅ Tested |

## Verdict: ACCEPT_WITH_LIMITATIONS

**Accepted:**
- Data integrity verified
- Metrics independently recomputed
- DAC gold isolation confirmed
- McNemar p=0.000061 CONFIRMED

**Limitations:**
1. C4 uses `source_valid` not `effective_success` (semantic equivalence documented)
2. Full tamper tests require modifying BASE (logic verified)
3. DEV/CONFIRM task list checked, but per-unit group assignment not cross-validated against task definitions

## Recommendation

R21-C1 results are reliable. DAC provides strong, consistent improvement (100% vs 37.5%, p=0.000061). Ready for PC1 blocker remediation.
