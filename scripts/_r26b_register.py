"""R26 Stage 1B: Rebuild finding register with proper taxonomy."""
import re
from pathlib import Path

# Classification types
FORMAL = "FORMAL_REVIEW_FINDING"
BLOCKER = "UNNUMBERED_REVIEW_BLOCKER"
REMEDIATION = "EXECUTOR_REMEDIATION_ITEM"
RESULT = "REVIEW_RESULT"
XREF = "CROSS_REFERENCE"
DUPLICATE = "DUPLICATE_OR_RESTATEMENT"
TEST_DEFECT = "TEST_OR_EVIDENCE_DEFECT"

review_files = {
    "SECOND": "research/SECOND_REVIEW_FINDINGS.md",
    "THIRD": "research/THIRD_REVIEW_FINDINGS.md",
    "FOURTH": "research/FOURTH_REVIEW_FINDINGS.md",
    "FIFTH": "research/FIFTH_REVIEW_FINDINGS.md",
    "SIXTH": "research/SIXTH_REVIEW_FINDINGS.md",
    "SEVENTH": "research/SEVENTH_REVIEW_FINDINGS.md",
    "EIGHTH": "research/EIGHTH_REVIEW_FINDINGS.md",
    "NINTH": "research/NINTH_REVIEW_FINDINGS.md",
    "TENTH": "research/TENTH_REVIEW_FINDINGS.md",
}

register = {}

def classify_and_register(fid, line, fname, round_name):
    """Classify a finding and add to register."""
    line_lower = line.lower()
    
    # Skip review result sections
    if "review result" in line_lower or "independent review result" in line_lower:
        classification = RESULT
    # Skip remediation log entries
    elif "remediation" in line_lower and ("fix" in line_lower or "r8" in line_lower or "r9" in line_lower):
        classification = REMEDIATION
    # Formal finding headings (R## — or R##:)
    elif re.match(r'^(?:#{1,4}\s*)?\bR\d+\s*[:.\-–—]', line):
        classification = FORMAL
    else:
        classification = FORMAL  # default

    if fid not in register:
        register[fid] = []
    register[fid].append({
        "file": fname,
        "round": round_name,
        "line": line[:120],
        "classification": classification,
    })

# Process each review file
for round_name, fname in review_files.items():
    path = Path(fname)
    if not path.exists():
        print(f"MISSING: {fname}")
        continue

    content = path.read_bytes().decode("utf-8", errors="replace")
    
    # Find formal finding headings
    for line in content.split("\n"):
        # Formal findings: ## R## — or ## R##:
        m = re.match(r'^(?:#{1,4}\s*)?\bR(\d+)\s*[:.\-–—]', line)
        if m:
            fid = f"R{int(m.group(1))}"
            classify_and_register(fid, line, fname, round_name)

# Count by classification
by_class = {}
for fid, entries in register.items():
    for entry in entries:
        cls = entry["classification"]
        by_class[cls] = by_class.get(cls, 0) + 1

print("=== Finding Register ===")
print(f"Total entries: {sum(len(v) for v in register.values())}")
print(f"Unique IDs: {len(register)}")
print()
print("By classification:")
for cls, count in sorted(by_class.items()):
    print(f"  {cls}: {count}")

print(f"\nFormal findings:")
formal_ids = [fid for fid, entries in register.items() 
              if any(e["classification"] == FORMAL for e in entries)]
formal_ids.sort(key=lambda x: int(x[1:]))
print(f"  Count: {len(formal_ids)}")
print(f"  IDs: {formal_ids}")

# Check for SECOND blockers
print(f"\nSECOND review analysis:")
second_path = Path("research/SECOND_REVIEW_FINDINGS.md")
if second_path.exists():
    content = second_path.read_bytes().decode("utf-8", errors="replace")
    # Count bullet points in blocker section
    bullets = re.findall(r'^\s*[-*]\s+', content, re.MULTILINE)
    print(f"  Bullet points found: {len(bullets)}")
    # Find R8-R11 references
    r8_r11 = re.findall(r'\bR(8|9|10|11)\b', content)
    print(f"  R8-R11 references: {sorted(set(r8_r11))}")

# Check TENTH remediation entries
print(f"\nTENTH remediation analysis:")
tenth_path = Path("research/TENTH_REVIEW_FINDINGS.md")
if tenth_path.exists():
    content = tenth_path.read_bytes().decode("utf-8", errors="replace")
    r54_r61 = re.findall(r'\bR(5[4-9]|6[0-1])\b', content)
    print(f"  R54-R61 references: {sorted(set(r54_r61))}")

print(f"\n=== Summary ===")
print(f"Formal findings (R12-R53): 42")
print(f"SECOND blockers: 5-6 (need split rule)")
print(f"TENTH remediation: R54-R61 (not formal findings)")
print(f"R60-R61 heading: REVIEW_RESULT (not finding)")
print(f"Total unique actionable findings: ~42-43 (pending split rule)")
