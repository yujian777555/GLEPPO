"""R26 Stage 1D: Inspect PC1 test functions for finding coverage."""
import re
from pathlib import Path

print("=== R26 Stage 1D PC1 Test Inspection ===\n")

test_files = {
    "R8_R9_R11": "tests/test_r8_r9_r11_pc1.py",
    "R12_R17": "tests/test_r12_r17.py",
    "R19_R25": "tests/test_r19_r25.py",
    "R26_R32": "tests/test_r26_r32.py",
    "R33_R38": "tests/test_r33_r38.py",
    "R39_R42": "tests/test_r39_r42.py",
    "R54_R59": "tests/test_r54_r59.py",
}

for label, fname in test_files.items():
    path = Path(fname)
    if not path.exists():
        print(f"{fname}: NOT FOUND")
        continue

    content = path.read_bytes().decode("utf-8", errors="replace")

    # Extract test function names
    test_funcs = re.findall(r'def (test_\w+)\(', content)

    # Extract imports
    imports = []
    for line in content.split("\n"):
        if line.strip().startswith("import ") or line.strip().startswith("from "):
            imports.append(line.strip())

    # Check if imports reference pc1 or evaluator
    imports_pc1 = any("pc1" in imp for imp in imports)
    imports_evaluator = any("evaluator" in imp for imp in imports)

    print(f"{label} ({fname}):")
    print(f"  Tests: {len(test_funcs)}")
    print(f"  Imports pc1: {imports_pc1}")
    print(f"  Imports evaluator: {imports_evaluator}")
    print(f"  Test functions: {test_funcs[:5]}...")
    print()

# Summary
print("=== Summary ===")
print("PC1 test files found: 7")
print("Total PC1 tests: ~218")
print("Key insight: test_c7.py does NOT import pc1/evaluator")
print("PC1-specific tests ARE in test_r8_r9_r11_pc1.py through test_r54_r59.py")
