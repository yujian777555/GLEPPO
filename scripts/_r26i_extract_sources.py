"""Extract source symbol line ranges from production source files."""
import ast
import json
from pathlib import Path

REPO = Path(r"D:\GLEPPO_repo")

SOURCE_FILES = [
    "gleppo/pc1.py",
    "gleppo/evaluator.py",
]

def extract_source_symbols(repo_root):
    symbols = {}
    for rel_path in SOURCE_FILES:
        path = repo_root / rel_path
        if not path.exists():
            print(f"MISSING: {rel_path}")
            continue
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                key = f"{rel_path}::{name}"
                symbols[key] = {
                    "file": rel_path,
                    "name": name,
                    "type": "function",
                    "start_line": node.lineno,
                    "end_line": node.end_lineno or node.lineno,
                }
            elif isinstance(node, ast.ClassDef):
                name = node.name
                key = f"{rel_path}::{name}"
                symbols[key] = {
                    "file": rel_path,
                    "name": name,
                    "type": "class",
                    "start_line": node.lineno,
                    "end_line": node.end_lineno or node.lineno,
                }
                # Also get methods
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_key = f"{rel_path}::{name}.{item.name}"
                        symbols[method_key] = {
                            "file": rel_path,
                            "name": f"{name}.{item.name}",
                            "type": "method",
                            "start_line": item.lineno,
                            "end_line": item.end_lineno or item.lineno,
                        }
    return symbols

symbols = extract_source_symbols(REPO)
print(f"Total source symbols: {len(symbols)}")

# Print summary
for key in sorted(symbols.keys()):
    s = symbols[key]
    print(f"  {key} [{s['start_line']}-{s['end_line']}] ({s['type']})")

# Save
out_path = REPO / "scripts" / "_r26i_source_symbols.json"
out_path.write_text(json.dumps(symbols, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nSaved to {out_path}")
