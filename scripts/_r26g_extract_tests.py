"""R26 Stage 1G: Extract actual test declarations and build exact map."""
import re
from pathlib import Path

print("=== R26 Stage 1G: Actual Test Declarations ===\n")

test_files = [
    "tests/test_r8_r9_r11_pc1.py",
    "tests/test_r12_r17.py",
    "tests/test_r19_r25.py",
    "tests/test_r26_r32.py",
    "tests/test_r33_r38.py",
    "tests/test_r39_r42.py",
    "tests/test_r54_r59.py",
]

# Build complete test map: class -> {functions: [(name, line)]}
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
                test_map[current_class] = {"file": fname, "functions": []}
            continue

        fm = re.match(r'\s+def\s+(test_\w+)\(', line)
        if fm and current_class:
            test_map[current_class]["functions"].append({
                "name": fm.group(1),
                "line": i,
            })

# Print complete map
for cls, info in sorted(test_map.items()):
    print(f"{cls} ({info['file']}):")
    for f in info["functions"]:
        print(f"  {f['name']} (line {f['line']})")
    print()

print(f"Total classes: {len(test_map)}")
print(f"Total functions: {sum(len(v['functions']) for v in test_map.values())}")
