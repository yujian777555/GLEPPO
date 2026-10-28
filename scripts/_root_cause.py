"""Check what operators actually changed in genotypes."""
import json

d = json.load(open('research/G3_DIAGNOSTIC_20261028T090752Z.json', encoding='utf-8'))

# Check hash_changed values - these tell us the genotype changed
print("=== Genotype hash changes ===")
for op_name, r in d['operators'].items():
    print(f"{op_name}: hash_changed={r['hash_changed']}/{r['valid']}")

# The issue: hash changes but behavior doesn't
# This means the genotype edit doesn't affect the execution path
print("\n=== Root cause analysis ===")
print("tool_subset_edit: 2 valid, 2 invalid. Hash changed but behavior identical.")
print("  -> Tool subset changed but workflow still calls same tools.")
print("  -> OR: tasks don't trigger tool-dependent behavior differences.")
print()
print("crossover: 4 valid, 4 hash changed. Behavior identical.")
print("  -> Prompt union preserves strategy keywords.")
print("  -> OR: tasks too easy - all genotypes solve them the same way.")
print()
print("Key insight: ALL parent-child pairs show success=1.0, tools=2.0.")
print("The tasks (A-g3-prod-00, B-g3-prod-00) are solved identically by all genotypes.")
print("This is a TASK DESIGN issue, not necessarily an operator defect.")
