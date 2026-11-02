"""R23 Stage C: PC1 blocker matrix assessment."""
import json

print("=== R23 Stage C: PC1 Blocker Matrix ===\n")

# Read status.json for historical blockers
with open("status.json", encoding="utf-8") as f:
    s = json.load(f)

# Historical PC1 reviews
reviews = ["second_review", "third_review", "fourth_review", "fifth_review",
           "sixth_review", "seventh_review", "eighth_review", "ninth_review", "tenth_review"]

print("Historical PC1 Review Status:")
for r in reviews:
    if r in s:
        verdict = s[r].get("verdict", "unknown")
        findings = s[r].get("findings", {})
        print(f"  {r}: {verdict} ({len(findings)} findings)")

# Current PC1 state
print(f"\nCurrent PC1 State:")
print(f"  pc1_approved: {s.get('pc1_approved', 'unknown')}")
print(f"  pc1_executed: {s.get('pc1_executed', 'unknown')}")
print(f"  formal_g3: FAIL")
print(f"  controller_training: {s.get('training_readiness', {}).get('controller_training', 'unknown')}")

# Key blockers from status.json
print(f"\nKey Blockers (from status.json):")
blockers = s.get("second_review", {}).get("blockers", [])
for b in blockers:
    print(f"  - {b}")

print(f"\n=== Assessment ===")
print("PC1 Protocol: PROPOSED_NOT_APPROVED")
print("Historical reviews: REQUEST_CHANGES (10 rounds)")
print("Current branch re-audit: NOT COMPLETE")
print()
print("Conclusion: PC1 cannot proceed without:")
print("  1. All historical blockers verified FIXED on current branch")
print("  2. Independent review ACCEPT")
print("  3. Trusted Planner approval")
print("  4. Formal G3 passage")
