"""Debug tool_subset_edit with p2 parent."""
import sys
sys.path.insert(0, '.')
from gleppo.genotype import make_valid_genotype, validate_genotype
from gleppo.operators import apply_operator

p2 = make_valid_genotype()
p2.system_prompt = "Use a different strategy: compute step by step and transform results. Final answer: {{answer}}"
p2.tools = ["calc", "str_ops", "py_sandbox"]
for step in p2.workflow:
    if step.tool and step.tool not in p2.tools:
        step.tool = p2.tools[0]

print("p2 tools:", p2.tools)
print("p2 workflow:", [(s.type, s.tool) for s in p2.workflow])
print("p2 valid:", validate_genotype(p2))

for gen in range(4):
    child, ok, errs = apply_operator("tool_subset_edit", p2, {"gen": gen})
    child_tools = child.tools if ok else "N/A"
    child_wf = [(s.type, s.tool) for s in child.workflow] if ok else "N/A"
    print(f"gen={gen}: ok={ok} errs={errs} tools={child_tools} wf={child_wf}")
