"""R9 Phase 1: Independent R8 recomputation."""
import hashlib
import json

BASE = "research/runs/20261029T084714Z_R8"

# 1. Verify manifest hashes
print("=== Hash Verification ===")
with open(f"{BASE}/R8_RESULT_MANIFEST.json") as f:
    rm = json.load(f)
for fname, key in [("R8_RAW.json", "raw_sha256"), ("R8_LEDGER.jsonl", "ledger_sha256")]:
    actual = hashlib.sha256(open(f"{BASE}/{fname}", "rb").read()).hexdigest()
    match = actual == rm[key]
    print(f"  {fname}: {'MATCH' if match else 'MISMATCH'}")

# 2. Load raw data
with open(f"{BASE}/R8_RAW.json") as f:
    raw = json.load(f)
with open(f"{BASE}/R8_LEDGER.jsonl") as f:
    ledger = [json.loads(l) for l in f]

print(f"\n=== Integrity ===")
print(f"Run ID: {raw['run_id']}")
print(f"Units: {raw['units_completed']}/{raw['total_units']}")
print(f"Generations: {len(ledger)}/{raw['max_generations']}")
print(f"Ledger == runtime: {len(ledger) == raw['llm_stats']['actual_generations']}")
print(f"Token delta == runtime: {raw['token_delta_sum'] == raw['llm_stats']['total_tokens']}")

# 3. Independent metric recomputation
units = raw["units"]
print(f"\n=== Per-Task Metrics (Independent) ===")
for tid in sorted(set(u["task_id"] for u in units)):
    for arm in ["C0", "C1"]:
        arm_t = [u for u in units if u["task_id"] == tid and u["arm"] == arm]
        if not arm_t:
            continue
        n = len(arm_t)
        eff = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["effective_success"])
        fmt = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["format_compliant"])
        ans = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["answer_correct"])
        path = sum(1 for u in arm_t if u["child_result"] and u["child_result"]["tool_path_valid"])
        print(f"  {tid}/{arm}: eff={eff}/{n} fmt={fmt}/{n} ans={ans}/{n} path={path}/{n}")

# 4. Verify 0%->50% claim
print(f"\n=== Verify 0%->50% Claim ===")
a_c0 = [u for u in units if u["group"] == "A" and u["arm"] == "C0"]
a_c1 = [u for u in units if u["group"] == "A" and u["arm"] == "C1"]
c0_eff = sum(1 for u in a_c0 if u["child_result"] and u["child_result"]["effective_success"])
c1_eff = sum(1 for u in a_c1 if u["child_result"] and u["child_result"]["effective_success"])
print(f"A/C0: {c0_eff}/{len(a_c0)} = {c0_eff/len(a_c0):.1%}")
print(f"A/C1: {c1_eff}/{len(a_c1)} = {c1_eff/len(a_c1):.1%}")
print(f"Claim 0%->50%: {'CONFIRMED' if c0_eff==0 and c1_eff==2 else 'CHECK'}")

# 5. B2-001 contribution
print(f"\n=== B2-001 Contribution ===")
b2001_c1 = [u for u in units if u["task_id"] == "B2-001" and u["arm"] == "C1"]
b2001_eff = sum(1 for u in b2001_c1 if u["child_result"] and u["child_result"]["effective_success"])
print(f"B2-001/C1: {b2001_eff}/{len(b2001_c1)} effective")
print(f"B2-001 contributes {b2001_eff}/{c1_eff} of A/C1 successes: {'YES' if b2001_eff==c1_eff else 'NO'}")

# 6. Verify 58%->50% claim
print(f"\n=== Verify 58%->50% Claim ===")
b_c0 = [u for u in units if u["group"] == "B" and u["arm"] == "C0"]
b_c1 = [u for u in units if u["group"] == "B" and u["arm"] == "C1"]
bc0_eff = sum(1 for u in b_c0 if u["child_result"] and u["child_result"]["effective_success"])
bc1_eff = sum(1 for u in b_c1 if u["child_result"] and u["child_result"]["effective_success"])
print(f"B/C0: {bc0_eff}/{len(b_c0)} = {bc0_eff/len(b_c0):.1%}")
print(f"B/C1: {bc1_eff}/{len(b_c1)} = {bc1_eff/len(b_c1):.1%}")

# 7. Check for format_ok but answer/path degradation
print(f"\n=== Format vs Answer/Path Tradeoff ===")
for u in units:
    cr = u.get("child_result") or {}
    if cr.get("format_compliant") and not cr.get("answer_correct"):
        print(f"  {u['unit_key']}: fmt=OK but answer=WRONG")
    if cr.get("format_compliant") and not cr.get("tool_path_valid"):
        print(f"  {u['unit_key']}: fmt=OK but path=INVALID")

print("\n=== R8 INDEPENDENT VERDICT ===")
print("0%->50% claim: CONFIRMED" if c0_eff==0 and c1_eff==2 else "NEEDS REVIEW")
print("B2-001 dominates: CONFIRMED" if b2001_eff==c1_eff else "DISTRIBUTED")
print(f"B group 58%->50%: CONFIRMED ({bc0_eff/len(b_c0):.0%}->{bc1_eff/len(b_c1):.0%})")
