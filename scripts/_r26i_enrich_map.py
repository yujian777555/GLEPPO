"""Enrich semantic evidence map test_evidence entries with declaration data."""
import json
from pathlib import Path

REPO = Path(r"D:\GLEPPO_repo")

# Load current map
map_path = REPO / "research" / "R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json"
with open(map_path, encoding="utf-8") as f:
    data = json.load(f)

# Load declarations
decl_path = REPO / "scripts" / "_r26i_declarations.json"
with open(decl_path, encoding="utf-8") as f:
    decls_list = json.load(f)

# Build lookup: (file, class, function) -> declaration
decl_lookup = {}
for d in decls_list:
    key = (d["file"], d["class"], d["function"])
    decl_lookup[key] = d

# Report what we can match
matched = 0
unmatched = 0
for finding in data["findings"]:
    for te in finding.get("test_evidence", []):
        key = (te.get("test_file"), te.get("test_class"), te.get("test_function"))
        if key in decl_lookup:
            matched += 1
        else:
            unmatched += 1
            print(f"UNMATCHED: {finding['id']} -> {key}")

print(f"\nMatched: {matched}, Unmatched: {unmatched}")

# Now enrich
for finding in data["findings"]:
    for te in finding.get("test_evidence", []):
        key = (te.get("test_file"), te.get("test_class"), te.get("test_function"))
        if key in decl_lookup:
            decl = decl_lookup[key]

            # Set declaration start/end lines
            te["declaration_start_line"] = decl["start_line"]
            te["declaration_end_line"] = decl["end_line"]

            # Set assertion expressions with line numbers
            te["assertion_expressions"] = [
                {"line": a["line"], "expression": a["expr"]}
                for a in decl["assertions"]
            ]

            # Keep old fields for backward compat (will be cleaned up later)
            # te["declaration_line"] already exists

# Save enriched map
with open(map_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Enriched map saved.")
