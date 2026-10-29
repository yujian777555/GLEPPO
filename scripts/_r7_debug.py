"""R7 audit: check exact prompt differences."""
import sys
sys.path.insert(0, ".")

from gleppo.operators import apply_operator
from gleppo.genotype import make_task_compatible_reference

parent = make_task_compatible_reference("B2-007")
mate = make_task_compatible_reference("B2-007")
mate.system_prompt += " Alternative."
ctx = {"gen": 0, "mate": mate, "failure_category": "wrong_answer"}

c0, _, _ = apply_operator("crossover", parent, ctx)
c1, _, _ = apply_operator("crossover_format_only", parent, ctx)

print("C0 system_prompt:")
print(repr(c0.system_prompt))
print()
print("C1 system_prompt:")
print(repr(c1.system_prompt))
print()
print("C0 workflow:", [s.to_dict() for s in c0.workflow])
print("C1 workflow:", [s.to_dict() for s in c1.workflow])
print()
print("C0 tools:", c0.tools)
print("C1 tools:", c1.tools)
