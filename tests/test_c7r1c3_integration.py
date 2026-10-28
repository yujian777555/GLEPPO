"""C7-R1-C3: comprehensive regression tests."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gleppo.genotype import make_valid_genotype, behavior_hash, validate_genotype
from gleppo.operators import apply_operator
from gleppo.evaluator import Evaluator
from gleppo.interpreter import Interpreter
from gleppo.llm import StubLLM
from gleppo.tasks import build_task, attach_checker


class TestC7R1C3Integration(unittest.TestCase):
    def test_crossover_valid_parents(self):
        p1 = make_valid_genotype()
        p2 = make_valid_genotype()
        p2.system_prompt = "Different strategy here. Final answer: {{answer}}"
        child, ok, errs = apply_operator("crossover", p1, {"mate": p2, "gen": 0})
        self.assertTrue(ok)
        self.assertEqual(validate_genotype(child), [])

    def test_crossover_invalid_mate_rejected(self):
        p1 = make_valid_genotype()
        p2 = make_valid_genotype()
        p2.system_prompt = "bad"  # too short
        with self.assertRaises(ValueError):
            apply_operator("crossover", p1, {"mate": p2, "gen": 0})

    def test_crossover_workflow_inheritance(self):
        p1 = make_valid_genotype()
        p2 = make_valid_genotype()
        p2.system_prompt = "Different strategy here. Final answer: {{answer}}"
        child, ok, _ = apply_operator("crossover", p1, {"mate": p2, "gen": 0})
        self.assertTrue(ok)
        wf_inherit = child.meta.get("inherited_strategies", {}).get("workflow_inheritance", [])
        self.assertGreater(len(wf_inherit), 0)
        # Each entry should have source
        for entry in wf_inherit:
            self.assertIn("source", entry)
            self.assertIn(entry["source"], ("parent", "mate", "shared", "derived"))

    def test_py_sandbox_invalid_input_fails(self):
        interp = Interpreter()
        task = attach_checker(build_task("A-test", "A", 1, "TA1"))
        g = make_valid_genotype()
        # Force py_sandbox with invalid input
        g.tools = ["py_sandbox"]
        g.workflow = [
            __import__("gleppo.genotype", fromlist=["Step"]).Step(type="tool", tool="py_sandbox", input_from="task"),
            __import__("gleppo.genotype", fromlist=["Step"]).Step(type="finalize", prompt_slot="answer", input_from="task"),
        ]
        res = interp.run(g, task, seed_parts=("test", 0, 0))
        # Should fail, not succeed with fake result
        self.assertFalse(res.success)

    def test_format_checker_enhanced(self):
        ev = Evaluator(n_eval=1)
        self.assertTrue(ev._check_format("Final answer: 42"))
        self.assertFalse(ev._check_format(""))
        self.assertFalse(ev._check_format("no prefix here"))
        self.assertFalse(ev._check_format("Final answer: "))  # empty after prefix
        self.assertFalse(ev._check_format("Final answer: " + "x" * 200))  # too long

    def test_answer_correct_independent_of_format(self):
        ev = Evaluator(n_eval=1)
        g = make_valid_genotype()
        task = attach_checker(build_task("A-test", "A", 1, "TA1"))
        result = ev.evaluate(g, task, replicate_id=0)
        # Both metrics should be present
        self.assertIsNotNone(result.answer_correct)
        self.assertIsNotNone(result.format_compliant)


if __name__ == "__main__":
    unittest.main(verbosity=2)
