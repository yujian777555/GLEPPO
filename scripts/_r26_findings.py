"""R26 Stage 1: Extract finding definitions from historical PC1 reviews."""
import re
from pathlib import Path

review_files = [
    "research/SECOND_REVIEW_FINDINGS.md",
    "research/THIRD_REVIEW_FINDINGS.md",
    "research/FOURTH_REVIEW_FINDINGS.md",
    "research/FIFTH_REVIEW_FINDINGS.md",
    "research/SIXTH_REVIEW_FINDINGS.md",
    "research/SEVENTH_REVIEW_FINDINGS.md",
    "research/EIGHTH_REVIEW_FINDINGS.md",
    "research/NINTH_REVIEW_FINDINGS.md",
    "research/TENTH_REVIEW_FINDINGS.md",
]

finding_defs = {}
for fname in review_files:
    path = Path(fname)
    content = path.read_bytes().decode("utf-8", errors="replace")
    for line in content.split("\n"):
        m = re.match(r"^(?:#{1,4}\s*)?\bR(\d+)\s*[:.\-–—]", line)
        if m:
            fid = f"R{int(m.group(1))}"
            if fid not in finding_defs:
                finding_defs[fid] = []
            finding_defs[fid].append({"file": fname, "line": line[:100]})

print(f"Finding definitions found: {len(finding_defs)}")
print(f"IDs: {sorted(finding_defs.keys(), key=lambda x: int(x[1:]), reverse=True)}")
print()
for fid in sorted(finding_defs.keys(), key=lambda x: int(x[1:]), reverse=True):
    defs = finding_defs[fid]
    print(f"{fid}: {len(defs)} definitions")
    for d in defs[:2]:
        fname = d["file"]
        line = d["line"]
        print(f"  {fname}: {line[:80]}")

# R25 table comparison
r25_table = {
    "R8", "R16", "R20", "R34", "R39",
    "R9", "R21", "R27", "R28", "R33",
    "R19", "R26", "R36", "R40", "R45", "R48", "R49", "R53",
    "R38", "R42", "R43", "R46", "R50", "R54", "R59",
    "R22", "R29", "R35", "R37", "R41", "R44", "R47", "R51", "R55", "R58", "R60",
    "R15", "R25", "R31",
}
found = set(finding_defs.keys())
print(f"\nR25 table count: {len(r25_table)}")
print(f"Actual definitions: {len(found)}")
print(f"In R25 but not defined: {sorted(r25_table - found, key=lambda x: int(x[1:]))}")
print(f"Defined but not in R25: {sorted(found - r25_table, key=lambda x: int(x[1:]))}")
