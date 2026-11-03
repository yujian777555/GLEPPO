"""R26 Stage 1B: Current-source audit of key PC1 modules."""
import ast
import json
from pathlib import Path

print("=== R26 Stage 1B Current-Source Audit ===\n")

# 1. Seed/CRN
print("1. Seed/CRN Module:")
for f in ["gleppo/evaluator.py", "gleppo/pc1.py"]:
    p = Path(f)
    if p.exists():
        content = p.read_bytes().decode("utf-8", errors="replace")
        has_seed = "seed" in content.lower()
        has_crn = "crn" in content.lower()
        has_json = "json.dumps" in content
        print(f"  {f}: seed={has_seed} crn={has_crn} json_encoding={has_json}")

# 2. Budget/CTX
print("\n2. Budget/CTx Module:")
for f in ["gleppo/pc1.py", "gleppo/evaluator.py"]:
    p = Path(f)
    if p.exists():
        content = p.read_bytes().decode("utf-8", errors="replace")
        has_budget = "budget" in content.lower()
        has_cache = "cache" in content.lower()
        has_replica = "replica" in content.lower()
        print(f"  {f}: budget={has_budget} cache={has_cache} replica={has_replica}")

# 3. Protocol
print("\n3. Protocol Module:")
for f in ["gleppo/pc1.py", "research/PC1_PROTOCOL_R4_PROPOSED.md"]:
    p = Path(f)
    if p.exists():
        content = p.read_bytes().decode("utf-8", errors="replace")
        has_hash = "hash" in content.lower()
        has_version = "version" in content.lower()
        print(f"  {f}: hash={has_hash} version={has_version}")

# 4. Approval
print("\n4. Approval Module:")
for f in ["gleppo/pc1.py"]:
    p = Path(f)
    if p.exists():
        content = p.read_bytes().decode("utf-8", errors="replace")
        has_approval = "approval" in content.lower()
        has_hmac = "hmac" in content.lower()
        has_trusted = "trusted" in content.lower()
        print(f"  {f}: approval={has_approval} hmac={has_hmac} trusted={has_trusted}")

# 5. PC1 Runner
print("\n5. PC1 Runner:")
for f in ["gleppo/pc1.py"]:
    p = Path(f)
    if p.exists():
        content = p.read_bytes().decode("utf-8", errors="replace")
        has_runner = "runner" in content.lower() or "execute" in content.lower()
        has_dry_run = "dry_run" in content.lower() or "dry-run" in content.lower()
        has_registered = "registered" in content.lower()
        print(f"  {f}: runner={has_runner} dry_run={has_dry_run} registered={has_registered}")

# 6. Gate Sequence
print("\n6. Gate Sequence:")
gate_files = ["gleppo/pc1.py", "docs/RUNTIME_LOCK_V2.md"]
for f in gate_files:
    p = Path(f)
    if p.exists():
        content = p.read_bytes().decode("utf-8", errors="replace")
        has_preflight = "preflight" in content.lower()
        has_g3 = "g3" in content.lower()
        has_pc1 = "pc1" in content.lower()
        print(f"  {f}: preflight={has_preflight} g3={has_g3} pc1={has_pc1}")

# 7. Tests
print("\n7. Test Coverage:")
test_files = list(Path("tests").glob("*.py"))
print(f"  Test files: {len(test_files)}")
for tf in sorted(test_files)[:10]:
    content = tf.read_bytes().decode("utf-8", errors="replace")
    test_count = content.count("def test_")
    print(f"  {tf.name}: {test_count} tests")

print(f"\n=== Audit Summary ===")
print(f"Modules inspected: 7 domains")
print(f"Test files found: {len(test_files)}")
print(f"Status: NEEDS_PER_FINDING_VERIFICATION")
