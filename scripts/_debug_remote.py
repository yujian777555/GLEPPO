"""Debug remote tool_subset_edit."""
import sys
sys.path.insert(0, '.')
from gleppo.genotype import make_valid_genotype, validate_genotype
from gleppo.operators import apply_operator

p1 = make_valid_genotype()
print("p1 tools:", p1.tools)
print("p1 workflow:", [(s.type, s.tool) for s in p1.workflow])

child, ok, errs = apply_operator("tool_subset_edit", p1, {"gen": 0})
print("ok:", ok, "errs:", errs)
if ok:
    print("child tools:", child.tools)
    print("child workflow:", [(s.type, s.tool) for s in child.workflow])
    print("child valid:", validate_genotype(child))
