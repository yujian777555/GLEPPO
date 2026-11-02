"""R19 Phase 1: R18 trace audit — B2-055/B2-061 answer source analysis."""
import json

BASE = "research/runs/20261029T132950Z_R18"
with open(f"{BASE}/R18_RAW.json") as f:
    raw = json.load(f)

units = raw["units"]

print("=== R18 Trace Audit: Answer Source Analysis ===")
print()
print("B2-055 task: Compute 19*2-5 using calc (33), transform 'done' to uppercase (DONE).")
print("Expected: DONE-33")
print()

for tid in ["B2-055", "B2-061"]:
    task_units = [u for u in units if u["task_id"] == tid]
    print(f"--- {tid} ---")
    for u in task_units:
        cr = u.get("child_result") or {}
        ans = cr.get("answer_preview", "")
        # Extract answer after "Final answer:"
        if "Final answer:" in ans:
            final = ans[ans.index("Final answer:"):].strip()
        else:
            final = ans[:80]
        print(f"  {u['arm']}/{u['seed_id']}: eff={cr.get('effective_success')} ans_correct={cr.get('answer_correct')}")
        print(f"    answer: {final}")
    print()

print("=== Answer Source Analysis ===")
print()
print("B2-055 expected: DONE-33 (19*2-5=33, 'done'->'DONE')")
print()
print("C0 correct outputs: DONE-33")
print("C0 wrong outputs: DONE-23")
print("C3 wrong outputs: DONE-23")
print()
print("Where does 23 come from?")
print("  19*2-5 = 33 (calc result)")
print("  'done' -> 'DONE' (str_ops result)")
print("  23 = ??? Not a direct tool output")
print()
print("Possible sources of 23:")
print("  - Model arithmetic error")
print("  - Model using wrong intermediate")
print("  - Model hallucinating a number")
print()
print("Key finding: DONE-23 is NOT a direct tool result.")
print("It's an LLM computation error, not a tool result misselection.")
print()
print("=== Implication for TGAB ===")
print("If answer errors are LLM computation errors (not tool misselection),")
print("then answer source verification won't help.")
print("The problem is in LLM reasoning, not in tool result selection.")
