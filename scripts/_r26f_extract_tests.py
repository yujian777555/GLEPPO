"""R26 Stage 1F: Extract actual test class/function declarations from PC1 test files."""
import re
from pathlib import Path

print("=== R26 Stage 1F: Actual Test Declarations ===\n")

test_files = [
    "tests/test_r8_r9_r11_pc1.py",
    "tests/test_r12_r17.py",
    "tests/test_r19_r25.py",
    "tests/test_r26_r32.py",
    "tests/test_r33_r38.py",
    "tests/test_r39_r42.py",
    "tests/test_r54_r59.py",
]

for fname in test_files:
    path = Path(fname)
    if not path.exists():
        print(f"{fname}: NOT FOUND")
        continue

    content = path.read_bytes().decode("utf-8", errors="replace")
    lines = content.split("\n")

    # Extract class declarations
    classes = []
    for i, line in enumerate(lines, 1):
        m = re.match(r'^class\s+(\w+)', line)
        if m:
            classes.append({"name": m.group(1), "line": i})

    # Extract test function declarations
    functions = []
    for i, line in enumerate(lines, 1):
        m = re.match(r'\s+def\s+(test_\w+)\(', line)
        if m:
            functions.append({"name": m.group(1), "line": i})

    print(f"{fname}:")
    print(f"  Classes: {[c['name'] for c in classes]}")
    print(f"  Test functions: {len(functions)}")
    for f in functions[:3]:
        print(f"    {f['name']} (line {f['line']})")
    print()

print("=== Summary ===")
print("Total test files: 7")
print("Key finding: Stage 1E class/function names were NOT verified against actual declarations")
print("Stage 1F must rebuild the map from actual declarations")
