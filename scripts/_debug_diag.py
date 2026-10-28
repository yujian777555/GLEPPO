"""Debug tool_subset_edit in diagnostic context."""
import sys
sys.path.insert(0, '.')
from gleppo.genotype import make_valid_genotype, validate_genotype
from gleppo.operators import apply_operator

p1 = make_valid_genotype()
p2 = make_valid_genotype()
p2.system_prompt = "Use a different strategy: compute step by step and transform results. Final answer: {{answer}}"
p2.tools = ["calc", "str_ops", "py_sandbox"]
for step in p2.workflow:
    if step.tool and step.tool not in p2.tools:
        step.tool = p2.tools[0]

for p_idx, parent in enumerate([p1, p2]):
    for gen in range(4):
        mate = p2 if parent is p1 else p1
        ctx = {'gen': gen, 'mate': mate, 'failure_category': 'wrong_answer'}
        child, ok, errs = apply_operator("tool_subset_edit", parent, ctx)
        child_tools = child.tools if ok else "N/A"
        child_wf = [(s.type, s.tool) for s in child.workflow] if ok else "N/A"
        valid = validate_genotype(child) if ok else ["invalid"]
        print(f"p{p_idx} gen={gen}: ok={ok} errs={errs} tools={child_tools} wf={child_wf} valid={valid}")
