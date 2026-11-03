"""R26 Stage 1C: Finding-level verification of R12-R53."""
import re
from pathlib import Path

print("=== R26 Stage 1C Finding-Level Verification ===\n")

# Define finding categories and source locations
findings = {
    "R12": {"cat": "Budget", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R13": {"cat": "Statistics", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R14": {"cat": "Statistics", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R15": {"cat": "Runner", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R16": {"cat": "Seed/CRN", "src": "gleppo/evaluator.py", "test": "tests/test_c7.py"},
    "R17": {"cat": "Evidence", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R18": {"cat": "Cost", "src": "research/COST_BASELINE.md", "test": "tests/test_c7.py"},
    "R19": {"cat": "Protocol", "src": "gleppo/pc1.py", "test": "tests/test_c7r1c2_protocol.py"},
    "R20": {"cat": "Seed/CRN", "src": "gleppo/evaluator.py", "test": "tests/test_c7.py"},
    "R21": {"cat": "Budget", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R22": {"cat": "Provenance", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R23": {"cat": "Evidence", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R24": {"cat": "Cost", "src": "research/COST_BASELINE.md", "test": "tests/test_c7.py"},
    "R25": {"cat": "Runner", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R26": {"cat": "Protocol", "src": "gleppo/pc1.py", "test": "tests/test_c7r1c2_protocol.py"},
    "R27": {"cat": "Budget", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R28": {"cat": "Budget", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R29": {"cat": "Provenance", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R30": {"cat": "Provenance", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R31": {"cat": "Runner", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R32": {"cat": "Seed/CRN", "src": "gleppo/evaluator.py", "test": "tests/test_c7.py"},
    "R33": {"cat": "Budget", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R34": {"cat": "Seed/CRN", "src": "gleppo/evaluator.py", "test": "tests/test_c7.py"},
    "R35": {"cat": "Provenance", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R36": {"cat": "Protocol", "src": "gleppo/pc1.py", "test": "tests/test_c7r1c2_protocol.py"},
    "R37": {"cat": "Provenance", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R38": {"cat": "Approval", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R39": {"cat": "Seed/CRN", "src": "gleppo/evaluator.py", "test": "tests/test_c7.py"},
    "R40": {"cat": "Protocol", "src": "gleppo/pc1.py", "test": "tests/test_c7r1c2_protocol.py"},
    "R41": {"cat": "Provenance", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R42": {"cat": "Approval", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R43": {"cat": "Approval", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R44": {"cat": "Provenance", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R45": {"cat": "Protocol", "src": "gleppo/pc1.py", "test": "tests/test_c7r1c2_protocol.py"},
    "R46": {"cat": "Approval", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R47": {"cat": "Provenance", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R48": {"cat": "Protocol", "src": "gleppo/pc1.py", "test": "tests/test_c7r1c2_protocol.py"},
    "R49": {"cat": "Protocol", "src": "gleppo/pc1.py", "test": "tests/test_c7r1c2_protocol.py"},
    "R50": {"cat": "Approval", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R51": {"cat": "Provenance", "src": "gleppo/pc1.py", "test": "tests/test_c7.py"},
    "R52": {"cat": "Protocol", "src": "gleppo/pc1.py", "test": "tests/test_c7r1c2_protocol.py"},
    "R53": {"cat": "Protocol", "src": "gleppo/pc1.py", "test": "tests/test_c7r1c2_protocol.py"},
}

# Verify source files exist
print("Source File Verification:")
for fid, info in sorted(findings.items(), key=lambda x: int(x[0][1:])):
    src_exists = Path(info["src"]).exists()
    test_exists = Path(info["test"]).exists()
    status = "OK" if src_exists and test_exists else "MISSING"
    print(f"  {fid} ({info['cat']}): src={src_exists} test={test_exists} -> {status}")

# Check test coverage
print("\nTest Coverage Check:")
test_files = {}
for fid, info in findings.items():
    tf = info["test"]
    if tf not in test_files:
        test_files[tf] = []
    test_files[tf].append(fid)

for tf, fids in sorted(test_files.items()):
    p = Path(tf)
    if p.exists():
        content = p.read_bytes().decode("utf-8", errors="replace")
        test_count = content.count("def test_")
        print(f"  {tf}: {test_count} tests, covers {len(fids)} findings")

print(f"\n=== Summary ===")
print(f"Total findings: {len(findings)}")
print(f"Source files verified: {sum(1 for i in findings.values() if Path(i['src']).exists())}")
print(f"Test files verified: {len(test_files)}")
print(f"Status: NEEDS_DETAILED_VERIFICATION")
