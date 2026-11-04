"""R26 Stage 1I: Declaration map validator (non-production audit helper)."""
import re
from pathlib import Path


def parse_test_declarations(test_files):
    """Parse test class/function declarations from source."""
    declarations = {}
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
                if current_class not in declarations:
                    declarations[current_class] = []
                continue
            fm = re.match(r'\s+def\s+(test_\w+)\(', line)
            if fm and current_class:
                declarations[current_class].append({
                    "name": fm.group(1),
                    "line": i,
                    "file": fname,
                })
    return declarations


def validate_report_map(report_rows, declarations):
    """Validate 42-row report map against actual declarations.

    Returns list of issues found.
    """
    issues = []
    seen_ids = set()

    for row in report_rows:
        fid = row.get("id")
        if fid in seen_ids:
            issues.append(f"Duplicate ID: {fid}")
        seen_ids.add(fid)

        test_file = row.get("test_file")
        test_class = row.get("test_class")
        test_function = row.get("test_function")
        test_line = row.get("test_line")

        if test_file == "NONE":
            continue

        # Check class exists
        if test_class not in declarations:
            issues.append(f"{fid}: class {test_class} not found")
            continue

        # Check function exists in class
        funcs = declarations[test_class]
        matching = [f for f in funcs if f["name"] == test_function]
        if not matching:
            issues.append(f"{fid}: function {test_function} not in {test_class}")
            continue

        # Check line number
        actual_line = matching[0]["line"]
        if test_line and test_line != actual_line:
            issues.append(f"{fid}: line mismatch (reported={test_line}, actual={actual_line})")

    # Check for missing IDs
    expected_ids = {f"R{i}" for i in range(12, 54)}
    missing = expected_ids - seen_ids
    if missing:
        issues.append(f"Missing IDs: {sorted(missing, key=lambda x: int(x[1:]))}")

    return issues


if __name__ == "__main__":
    test_files = [
        "tests/test_r8_r9_r11_pc1.py",
        "tests/test_r12_r17.py",
        "tests/test_r19_r25.py",
        "tests/test_r26_r32.py",
        "tests/test_r33_r38.py",
        "tests/test_r39_r42.py",
        "tests/test_r54_r59.py",
    ]

    declarations = parse_test_declarations(test_files)
    print(f"Total classes: {len(declarations)}")
    print(f"Total functions: {sum(len(v) for v in declarations.values())}")
    print("\nNote: This helper validates DECLARATION existence only.")
    print("Semantic evidence review requires manual assertion/call-path analysis.")
