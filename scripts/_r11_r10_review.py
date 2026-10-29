"""R11 Phase 1: Independent R10 recomputation."""
import hashlib
import json

BASE = "research/runs/20261029T110437Z_R10"

# 1. Verify manifest hashes
print("=== Hash Verification ===")
with open(f"{BASE}/R10_RESULT_MANIFEST.json") as f:
    rm = json.load(f)
for fname, key in [("R10_RAW.json", "raw_sha256"), ("R10_LEDGER.jsonl", "ledger_sha256")]:
    actual = hashlib.sha256(open(f"{BASE}/{fname}", "rb").read()).hexdigest()
    match = actual == rm[key]
    print(f"  {fname}: {'MATCH' if match else 'MISMATCH'}")

with open(f"{BASE}/R10_RAW.json") as f:
    raw = json.load(f)
with open(f"{BASE}/R10_LEDGER.jsonl") as f:
    ledger = [json.loads(l) for l in f]

print(f"\n=== Integrity ===")
print(f"Units: {raw['units_completed']}/{raw['total_units']}")
print(f"Generations: {len(ledger)}/{raw['max_generations']}")
print(f"Ledger == runtime: {len(ledger) == raw['llm_stats']['actual_generations']}")
print(f"Token delta == runtime: {raw['token_delta_sum'] == raw['llm_stats']['total_tokens']}")

# 2. Verify reported values
units = raw["units"]
print(f"\n=== Verify Reported Values ===")

# FS C0=2/6, C1=3/6, C2=4/6
for arm, expected in [("C0", 2), ("C1", 3), ("C2", 4)]:
    fs = [u for u in units if u["group"] == "FS" and u["arm"] == arm]
    eff = sum(1 for u in fs if u["child_result"] and u["child_result"]["effective_success"])
    match = eff == expected
    print(f"  FS/{arm}: {eff}/{len(fs)} expected={expected} -> {'MATCH' if match else 'MISMATCH'}")

# B2-001: C2 use_C1, 3/3 effective
b2001_c2 = [u for u in units if u["task_id"] == "B2-001" and u["arm"] == "C2"]
b2001_eff = sum(1 for u in b2001_c2 if u["child_result"] and u["child_result"]["effective_success"])
b2001_c1_decision = all(u.get("c2_decision", {}).get("action") == "use_C1" for u in b2001_c2)
print(f"  B2-001/C2: eff={b2001_eff}/{len(b2001_c2)}, use_C1={b2001_c1_decision}")

# B2-024: C2 use_C0, 1/3 effective; C1=0/3
b2024_c2 = [u for u in units if u["task_id"] == "B2-024" and u["arm"] == "C2"]
b2024_c2_eff = sum(1 for u in b2024_c2 if u["child_result"] and u["child_result"]["effective_success"])
b2024_c1 = [u for u in units if u["task_id"] == "B2-024" and u["arm"] == "C1"]
b2024_c1_eff = sum(1 for u in b2024_c1 if u["child_result"] and u["child_result"]["effective_success"])
print(f"  B2-024/C2: eff={b2024_c2_eff}/{len(b2024_c2)}, C1: eff={b2024_c1_eff}/{len(b2024_c1)}")

# B2-025: C2 use_C0, 3/3 effective
b2025_c2 = [u for u in units if u["task_id"] == "B2-025" and u["arm"] == "C2"]
b2025_c2_eff = sum(1 for u in b2025_c2 if u["child_result"] and u["child_result"]["effective_success"])
print(f"  B2-025/C2: eff={b2025_c2_eff}/{len(b2025_c2)}")

# FI "all 100%"
print(f"\n=== FI Group Verification ===")
for arm in ["C0", "C1", "C2"]:
    fi = [u for u in units if u["group"] == "FI" and u["arm"] == arm]
    eff = sum(1 for u in fi if u["child_result"] and u["child_result"]["effective_success"])
    fmt = sum(1 for u in fi if u["child_result"] and u["child_result"]["format_compliant"])
    print(f"  FI/{arm}: eff={eff}/{len(fi)} fmt={fmt}/{len(fi)}")

# 3. Verify C2 uses only validation format signal
print(f"\n=== C2 Decision Verification ===")
c2_units = [u for u in units if u["arm"] == "C2" and u.get("c2_decision")]
for u in c2_units:
    d = u["c2_decision"]
    print(f"  {u['task_id']}/{u['seed_id']}: {d['action']} ({d['reason']})")

# 4. Verify C0/C1 use same child
print(f"\n=== C0/C1 Child Identity Check ===")
# C0 and C1 should use same crossover child
# C1 only adds format constraint
for tid in sorted(set(u["task_id"] for u in units)):
    c0 = [u for u in units if u["task_id"] == tid and u["arm"] == "C0"]
    c1 = [u for u in units if u["task_id"] == tid and u["arm"] == "C1"]
    if c0 and c1:
        print(f"  {tid}: C0 units={len(c0)}, C1 units={len(c1)}")

print(f"\n=== R10 INDEPENDENT VERDICT ===")
print("FS C0=2/6 C1=3/6 C2=4/6: CHECK ABOVE")
print("B2-001 C2 use_C1 3/3: CHECK ABOVE")
print("B2-024 C2 use_C0 1/3, C1 0/3: CHECK ABOVE")
print("FI all 100%: CHECK ABOVE")
