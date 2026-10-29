"""R3 Independent Recomputation — Phase 1: Integrity checks."""
import hashlib
import json

BASE = "research/runs/20261029T052350Z_R3"

# 1. Result manifest SHA-256
with open(f"{BASE}/R3_RESULT_MANIFEST.json", "rb") as f:
    msha = hashlib.sha256(f.read()).hexdigest()
print(f"Result manifest SHA-256: {msha[:16]}...")
assert msha.startswith("cfadb67b37d40c31"), f"MISMATCH: {msha[:16]}"
print("Result manifest hash: MATCH")

# 2. Frozen manifest source hashes
with open(f"{BASE}/R3_FROZEN_MANIFEST.json") as f:
    frozen = json.load(f)
files = frozen.get("files", {})
print(f"\nFrozen manifest entries: {len(files)}")
hash_ok = True
for fname, finfo in files.items():
    try:
        actual = hashlib.sha256(open(fname, "rb").read()).hexdigest()
        if actual != finfo["sha256"]:
            print(f"  HASH MISMATCH: {fname}")
            hash_ok = False
        else:
            print(f"  OK: {fname}")
    except FileNotFoundError:
        print(f"  FILE MISSING: {fname}")
        hash_ok = False
print(f"Source hash check: {'PASS' if hash_ok else 'FAIL'}")

# 3. Raw data + Ledger integrity
with open(f"{BASE}/R3_RAW.json") as f:
    raw = json.load(f)
with open(f"{BASE}/R3_LEDGER.jsonl") as f:
    ledger = [json.loads(l) for l in f]

print(f"\n=== Integrity ===")
print(f"Run ID: {raw['run_id']}")
print(f"Status: {raw['status']}")
print(f"Raw generations: {raw['total_actual_generations']}")
print(f"Ledger rows: {len(ledger)}")
print(f"Ledger == raw count: {len(ledger) == raw['total_actual_generations']}")

ids = [r["call_id"] for r in ledger]
print(f"Unique call IDs: {len(ids) == len(set(ids))}")
print(f"Monotonic call IDs: {ids == sorted(ids)}")

token_delta = sum(r["output_tokens"] for r in ledger)
runtime_tokens = raw["llm_stats"]["total_tokens"]
print(f"Token delta sum: {token_delta}")
print(f"Runtime total_tokens: {runtime_tokens}")
print(f"Token match: {token_delta == runtime_tokens}")

failures_ledger = sum(1 for r in ledger if r.get("status") == "error")
failures_runtime = raw["llm_stats"]["failures"]
print(f"Ledger failures: {failures_ledger}")
print(f"Runtime failures: {failures_runtime}")
print(f"Failure match: {failures_ledger == failures_runtime}")

# 4. Check for duplicate records
pairs_seen = set()
duplicates = []
for r in ledger:
    key = (r.get("task_id",""), r.get("genotype_role",""), r.get("replicate", -1))
    if key in pairs_seen:
        duplicates.append(key)
    pairs_seen.add(key)
print(f"Duplicate records: {len(duplicates)}")

# 5. Paired matrix coverage
print(f"\n=== Paired Matrix Coverage ===")
pilot = raw["pilot"]
print(f"Matrix complete: {pilot['matrix_complete']}")
print(f"Stop reason: {pilot['stop_reason']}")
for op_name in ["tool_subset_edit", "crossover"]:
    agg = pilot["aggregate"][op_name]
    print(f"{op_name}: {agg['paired_comparisons']} paired comparisons")
