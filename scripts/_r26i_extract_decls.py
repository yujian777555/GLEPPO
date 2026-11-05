"""Extract test declarations with exact line ranges and assertions using AST."""
import ast
import json
import sys
from pathlib import Path

REPO = Path(r"D:\GLEPPO_repo")

TEST_FILES = [
    "tests/test_r8_r9_r11_pc1.py",
    "tests/test_r12_r17.py",
    "tests/test_r19_r25.py",
    "tests/test_r26_r32.py",
    "tests/test_r33_r38.py",
    "tests/test_r39_r42.py",
    "tests/test_r54_r59.py",
]


def extract_declarations(repo_root):
    declarations = {}
    for rel_path in TEST_FILES:
        path = repo_root / rel_path
        if not path.exists():
            print(f"MISSING: {rel_path}")
            continue
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content)
        lines = content.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                        func_name = item.name
                        start_line = item.lineno
                        end_line = item.end_lineno or start_line

                        # Collect assertions
                        assertions = []
                        for sub in ast.walk(item):
                            if isinstance(sub, ast.Assert):
                                assertion_expr = ast.get_source_segment(
                                    content, sub
                                ) or f"assert (line {sub.lineno})"
                                assertions.append({
                                    "line": sub.lineno,
                                    "expr": assertion_expr.strip(),
                                })
                            elif isinstance(sub, ast.Call):
                                # Check for self.assert* calls
                                func = sub.func
                                if isinstance(func, ast.Attribute):
                                    if func.attr.startswith("assert") or func.attr in (
                                        "assertEqual", "assertNotEqual", "assertTrue",
                                        "assertFalse", "assertRaises", "assertIn",
                                        "assertNotIn", "assertIsNone", "assertIsNotNone",
                                        "assertGreater", "assertLess", "assertAlmostEqual",
                                        "assertDictEqual", "assertListEqual", "assertSetEqual",
                                        "assertTupleEqual", "assertCountEqual",
                                        "assertWarns", "assertLogs",
                                    ):
                                        seg = ast.get_source_segment(content, sub)
                                        if seg:
                                            assertions.append({
                                                "line": sub.lineno,
                                                "expr": seg.strip(),
                                            })

                        key = (rel_path, class_name, func_name)
                        declarations[key] = {
                            "file": rel_path,
                            "class": class_name,
                            "function": func_name,
                            "start_line": start_line,
                            "end_line": end_line,
                            "assertions": assertions,
                        }

            # Also capture module-level test functions (if any)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                # Only if not inside a class (top-level)
                pass  # handled by walk from root

    return declarations


def main():
    decls = extract_declarations(REPO)
    print(f"Total declarations: {len(decls)}")

    # Print summary
    for key in sorted(decls.keys()):
        d = decls[key]
        n_assert = len(d["assertions"])
        print(f"  {d['file']}::{d['class']}::{d['function']} [{d['start_line']}-{d['end_line']}] assertions={n_assert}")

    # Save to JSON for later use
    out = []
    for key in sorted(decls.keys()):
        out.append(decls[key])
    out_path = REPO / "scripts" / "_r26i_declarations.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()
