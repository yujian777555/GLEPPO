"""Check StubLLM correctness against every generated template (R11)."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from gleppo.tasks import build_task, attach_checker, TRAIN_TEMPLATES_A, VAL_TEMPLATES_A, TRAIN_TEMPLATES_B, VAL_TEMPLATES_B
from gleppo.genotype import make_valid_genotype
from gleppo.interpreter import Interpreter

g = make_valid_genotype()
interp = Interpreter()
print("=== Family A templates ===")
for tid in TRAIN_TEMPLATES_A + VAL_TEMPLATES_A:
    t = attach_checker(build_task("X", "A", 7, tid))
    res = interp.run(g, t, seed_parts=("t", 0, "h"))
    print(tid, "success=", res.success, "fail=", res.failure_category, "gold=", t["gold"], "ans=", res.answer[:80])
print("=== Family B templates ===")
for tid in TRAIN_TEMPLATES_B + VAL_TEMPLATES_B:
    t = attach_checker(build_task("X", "B", 7, tid))
    res = interp.run(g, t, seed_parts=("t", 0, "h"))
    print(tid, "success=", res.success, "fail=", res.failure_category, "gold=", t["gold"], "ans=", res.answer[:80])
