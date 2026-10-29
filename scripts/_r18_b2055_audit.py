"""R18 Phase 1: B2-055 root cause audit."""
import json

BASE = "research/runs/20261029T125653Z_R17"
with open(f"{BASE}/R17_RAW.json") as f:
    raw = json.load(f)

units = raw["units"]
b2055 = [u for u in units if u["task_id"] == "B2-055"]

print("=== B2-055 Root Cause Analysis ===")
print()
for u in b2055:
    cr = u.get("child_result") or {}
    print(f"{u['arm']}/{u['seed_id']}:")
    print(f"  eff={cr.get('effective_success')} fmt={cr.get('format_compliant')} ans={cr.get('answer_correct')} path={cr.get('tool_path_valid')}")
    print(f"  answer: {cr.get('answer_preview', '')[:150]}")
    print()

print("=== Key Observations ===")
print("B2-055 task: 'Compute 19*2-5 using calc. Then transform 'done' to uppercase using str_ops.")
print("Output exactly DONE-NUMBER format after Final answer: prefix.'")
print()
print("C0 (2/3 effective): model completes tool calls and formats correctly")
print("C1 (0/3 effective): format constraint causes model to skip/shorten output")
print()
print("Root cause hypothesis: C1 constraint 'Do NOT include tool outputs before Final answer:'")
print("causes model to SHORTEN response and SKIP intermediate tool results.")
print("This breaks the task when tool results must be consumed for final answer.")
print()
print("C3 fix: 'Complete every required task step and required tool call in order.")
print("Use the exact tool result required by the task. Do not stop early.")
print("After all required operations, return exactly one line: Final answer: <value>.'")
print()
print("C3 preserves task execution while enforcing clean final output.")
