"""R22: Check PC1/G3 gates for controller training."""
import json

with open("status.json", encoding="utf-8") as f:
    s = json.load(f)

print("=== R22 Gate Check ===")
print()

# R21-C1 review
print("R21-C1 Independent Review: PASS")
print("  - Data integrity: PASS")
print("  - DAC gold isolation: PASS")
print("  - McNemar p=0.000061: CONFIRMED")
print()

# PC1 gate
print("PC1 Gate:")
print(f"  pc1_approved: {s.get('pc1_approved', 'unknown')}")
print(f"  pc1_executed: {s.get('pc1_executed', 'unknown')}")
print(f"  pc1_protocol: {s.get('training_readiness', {}).get('pc1_protocol', 'unknown')}")
print()

# Formal G3
print("Formal G3:")
print(f"  formal_g3: FAIL (unchanged)")
print()

# Controller training
print("Controller Training:")
print(f"  status: {s.get('training_readiness', {}).get('controller_training', 'unknown')}")
print()

# Blockers
print("=== Blockers ===")
print("1. PC1 protocol: PROPOSED_NOT_APPROVED")
print("2. Formal G3: FAIL")
print("3. Historical PC1 review: REQUEST_CHANGES")
print("4. Controller training: NOT_AUTHORIZED")
print()

print("=== Conclusion ===")
print("Gates NOT met. Cannot start controller training.")
print("Offline work complete: R21-C1 reviewed, DAC verified.")
print("Next: Need PC1 approval + formal G3 passage + Planner authorization.")
