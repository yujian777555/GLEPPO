"""G3-DIAG-v1: zero-cost identifiability check for failing operators."""
import sys
sys.path.insert(0, '.')
from gleppo.genotype import make_valid_genotype, behavior_hash, validate_genotype
from gleppo.operators import apply_operator, OPERATOR_NAMES

print("=== tool_subset_edit identifiability ===")
g = make_valid_genotype()
print(f"Parent tools: {g.tools}")
print(f"Parent workflow: {[(s.type, s.tool) for s in g.workflow]}")

for gen in range(6):
    child, ok, errs = apply_operator("tool_subset_edit", g, {"gen": gen})
    if ok:
        tools_changed = sorted(child.tools) != sorted(g.tools)
        wf_changed = [(s.type, s.tool) for s in child.workflow] != [(s.type, s.tool) for s in g.workflow]
        print(f"gen={gen}: valid={ok} tools_changed={tools_changed} wf_changed={wf_changed} child_tools={child.tools}")
    else:
        print(f"gen={gen}: INVALID {errs}")

print("\n=== crossover identifiability ===")
p1 = make_valid_genotype()
p2 = make_valid_genotype()
p2.system_prompt = "Use a different strategy: compute step by step and transform results. Final answer: {{answer}}"
p2.tools = ["calc", "str_ops", "py_sandbox"]
# Fix workflow for p2
for step in p2.workflow:
    if step.tool and step.tool not in p2.tools:
        step.tool = p2.tools[0]

print(f"p1 tools: {p1.tools}")
print(f"p2 tools: {p2.tools}")
print(f"p1 prompt hash: {behavior_hash(p1)[:8]}")
print(f"p2 prompt hash: {behavior_hash(p2)[:8]}")
print(f"p1 valid: {validate_genotype(p1)}")
print(f"p2 valid: {validate_genotype(p2)}")

child, ok, errs = apply_operator("crossover", p1, {"mate": p2, "gen": 0})
print(f"\nChild valid: {ok}")
print(f"Child tools: {child.tools}")
print(f"Child prompt hash: {behavior_hash(child)[:8]}")
print(f"p1 hash != child hash: {behavior_hash(p1) != behavior_hash(child)}")
print(f"p2 hash != child hash: {behavior_hash(p2) != behavior_hash(child)}")
inherited = child.meta.get("inherited_strategies", {})
print(f"Inherited parent_unique: {inherited.get('from_parent_unique', [])}")
print(f"Inherited mate_unique: {inherited.get('from_mate_unique', [])}")
print(f"Workflow inheritance: {len(inherited.get('workflow_inheritance', []))} steps")
