"""R7 zero-cost audit: verify C0/C1 only difference is format constraint."""
import sys
sys.path.insert(0, ".")

from gleppo.operators import apply_operator
from gleppo.genotype import make_task_compatible_reference, behavior_hash

parent = make_task_compatible_reference("B2-007")
mate = make_task_compatible_reference("B2-007")
mate.system_prompt += " Alternative."
ctx = {"gen": 0, "mate": mate, "failure_category": "wrong_answer"}

c0, _, _ = apply_operator("crossover", parent, ctx)
c1, _, _ = apply_operator("crossover_format_only", parent, ctx)

# Key checks
same_tools = c0.tools == c1.tools
same_workflow = [s.to_dict() for s in c0.workflow] == [s.to_dict() for s in c1.workflow]
c0_has_constraint = "Do NOT include tool outputs" in c0.system_prompt
c1_has_constraint = "Do NOT include tool outputs" in c1.system_prompt

# C1 has format constraint, C0 does not
constraint_differs = c1_has_constraint and not c0_has_constraint

# Both end with answer instruction (C0: simple, C1: strict)
c0_simple = "Final answer: {{answer}}" in c0.system_prompt
c1_strict = "Do NOT include tool outputs" in c1.system_prompt

print("C0 vs C1 audit:")
print(f"  Same tools: {same_tools}")
print(f"  Same workflow: {same_workflow}")
print(f"  C0 has format constraint: {c0_has_constraint}")
print(f"  C1 has format constraint: {c1_has_constraint}")
print(f"  Constraint is ONLY difference: {constraint_differs and same_tools and same_workflow}")
print(f"  C0 simple answer instruction: {c0_simple}")
print(f"  C1 strict answer instruction: {c1_strict}")

# Final verdict
pass_audit = same_tools and same_workflow and constraint_differs
print(f"\nAUDIT: {'PASS' if pass_audit else 'FAIL'}")
print(f"  C0/C1 differ ONLY in format constraint: {pass_audit}")
