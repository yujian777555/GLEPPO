"""Debug tool_subset_edit."""
import sys
sys.path.insert(0, '.')
from gleppo.genotype import make_valid_genotype, validate_genotype
from gleppo.operators import apply_operator

g = make_valid_genotype()
print("parent tools:", g.tools)
print("parent workflow:", [(s.type, s.tool) for s in g.workflow])

for gen in range(4):
    child, ok, errs = apply_operator("tool_subset_edit", g, {"gen": gen})
    child_tools = child.tools if ok else "N/A"
    print(f"gen={gen}: ok={ok} errs={errs} tools={child_tools}")
