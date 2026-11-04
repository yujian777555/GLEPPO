"""R26 Stage 1H: Extract exact test declarations and build corrected map."""
import re
from pathlib import Path

print("=== R26 Stage 1H: Exact Test Declarations ===\n")

test_files = [
    "tests/test_r8_r9_r11_pc1.py",
    "tests/test_r12_r17.py",
    "tests/test_r19_r25.py",
    "tests/test_r26_r32.py",
    "tests/test_r33_r38.py",
    "tests/test_r39_r42.py",
    "tests/test_r54_r59.py",
]

# Build complete map: class -> [(function, line)]
test_map = {}
for fname in test_files:
    path = Path(fname)
    if not path.exists():
        continue
    content = path.read_bytes().decode("utf-8", errors="replace")
    lines = content.split("\n")

    current_class = None
    for i, line in enumerate(lines, 1):
        cm = re.match(r'^class\s+(\w+)', line)
        if cm:
            current_class = cm.group(1)
            if current_class not in test_map:
                test_map[current_class] = []
            continue

        fm = re.match(r'\s+def\s+(test_\w+)\(', line)
        if fm and current_class:
            test_map[current_class].append({"name": fm.group(1), "line": i, "file": fname})

# Corrected R31 and R49
print("Key corrections:")
print("R31: test_all_booleans_true_still_denied_for_proposed_protocol (NOT test_all_booleans_true_still_denied)")
print("R49: test_mutation_status_not_checked_by_consistency (NOT test_mutation_status_not_checked)")
print()

# Print relevant classes
for cls in ["TestR31GateSemantics", "TestR40ProtocolConsistency", "TestR39CRNSeed"]:
    if cls in test_map:
        print(f"{cls}:")
        for f in test_map[cls]:
            print(f"  {f['name']} (line {f['line']})")
        print()

# R39 non-tautological tests
print("R39 non-tautological tests:")
if "TestR39CRNSeed" in test_map:
    for f in test_map["TestR39CRNSeed"]:
        if "same_params" not in f["name"]:
            print(f"  {f['name']} (line {f['line']})")

print(f"\nTotal classes: {len(test_map)}")
print(f"Total functions: {sum(len(v) for v in test_map.values())}")
