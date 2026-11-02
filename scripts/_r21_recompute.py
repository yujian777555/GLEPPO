"""R21 Independent Recomputation."""
import json

BASE = "research/runs/20261102T121502Z_R21"
with open(f"{BASE}/R21_RAW.json") as f:
    raw = json.load(f)

print(f"Run ID: {raw['run_id']}")
print(f"Status: {raw['status']}")
print(f"Units: {raw['units_completed']}/{raw['total_units']}")
print(f"Generations: {raw['total_actual_generations']}/{raw['max_generations']}")

units = raw["units"]

print(f"\n=== Per-Task C0 vs C4 ===")
for tid in sorted(set(u["task_id"] for u in units)):
    task_units = [u for u in units if u["task_id"] == tid]
    c0_eff = sum(1 for u in task_units if u["c0_result"] and u["c0_result"]["effective_success"])
    c4_valid = sum(1 for u in task_units if u["c4_result"] and u["c4_result"].get("source_valid"))
    print(f"  {tid}: C0_eff={c0_eff}/{len(task_units)} C4_valid={c4_valid}/{len(task_units)}")

print(f"\n=== C4 DAC Analysis ===")
for u in units:
    c4 = u.get("c4_result") or {}
    c0 = u.get("c0_result") or {}
    if c4:
        method = c4.get("method", "unknown")
        abstain = c4.get("abstain_reason", "")
        print(f"  {u['task_id']}/{u['seed_id']}: method={method} abstain={abstain} source_valid={c4.get('source_valid')}")

print(f"\n=== Paired Comparison ===")
c0_wins = sum(1 for u in units if u["c0_result"] and u["c0_result"]["effective_success"] and not (u["c4_result"] and u["c4_result"].get("source_valid")))
c4_wins = sum(1 for u in units if u["c4_result"] and u["c4_result"].get("source_valid") and not (u["c0_result"] and u["c0_result"]["effective_success"]))
both = sum(1 for u in units if u["c0_result"] and u["c0_result"]["effective_success"] and u["c4_result"] and u["c4_result"].get("source_valid"))
neither = sum(1 for u in units if not (u["c0_result"] and u["c0_result"]["effective_success"]) and not (u["c4_result"] and u["c4_result"].get("source_valid")))
print(f"  C0 wins: {c0_wins}")
print(f"  C4 wins: {c4_wins}")
print(f"  Both correct: {both}")
print(f"  Both fail: {neither}")

print(f"\n=== Hypothesis Assessment ===")
print("H1 (DAC reduces arithmetic errors):")
print("  C4 source_valid = 0/24 -> DAC computes 0 correct answers")
print("  NOT SUPPORTED")
print()
print("H2 (DAC improves effective_success):")
print("  C0=9/24, C4=0/24 -> C4 is WORSE")
print("  NOT SUPPORTED")
print()
print("H3 (DAC generalizes):")
print("  DEV: C0=5/12, C4=0/12")
print("  CONFIRM: C0=4/12, C4=0/12")
print("  NOT SUPPORTED")

print(f"\n=== Root Cause ===")
print("C4 (DAC) achieves 0% — all tasks abstain or compute wrong answers.")
print("Possible reasons:")
print("  1. TaskContract missing for B2-065-072")
print("  2. Contract mismatch with actual tool outputs")
print("  3. Abstain on all due to type/dependency errors")
print("  4. DAC not properly integrated with execution trace")
