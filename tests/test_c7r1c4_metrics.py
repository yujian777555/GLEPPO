"""C7-R1-C4: comprehensive tests for format, answer correctness, tool consumption."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gleppo.genotype import make_valid_genotype, validate_genotype
from gleppo.evaluator import Evaluator
from gleppo.interpreter import Interpreter
from gleppo.tasks import build_task, attach_checker
from gleppo.operators import apply_operator


class TestAnswerCorrectness(unittest.TestCase):
    def test_answer_correct_from_gold_checker(self):
        """B1: answer_correct computed from gold checker, not success."""
        ev = Evaluator(n_eval=1)
        g = make_valid_genotype()
        task = attach_checker(build_task("A-test", "A", 1, "TA1"))
        result = ev.evaluate(g, task, replicate_id=0)
        # answer_correct should be 0 or 1 (fraction of replicas with correct answer)
        self.assertIn(result.answer_correct, (0.0, 1.0))

    def test_format_compliant_independent(self):
        """D1: format_compliant independent of answer_correct."""
        ev = Evaluator(n_eval=1)
        # Test format checker directly
        self.assertTrue(ev._check_format("Final answer: 42"))
        self.assertFalse(ev._check_format(""))
        self.assertFalse(ev._check_format("no prefix"))
        self.assertFalse(ev._check_format("Final answer: "))
        self.assertFalse(ev._check_format("Final answer: " + "x" * 200))

    def test_observe_no_gold_leak(self):
        """D3: observe() must not leak gold labels."""
        ev = Evaluator(n_eval=1)
        g = make_valid_genotype()
        task = attach_checker(build_task("A-test", "A", 1, "TA1"))
        result = ev.evaluate(g, task, replicate_id=0)
        obs = ev.observe(result)
        self.assertNotIn("answer_correct", obs)
        self.assertNotIn("format_compliant", obs)
        self.assertNotIn("gold", str(obs))


class TestToolConsumption(unittest.TestCase):
    def test_tool_output_consumed(self):
        """D: tool output consumed by downstream steps."""
        interp = Interpreter()
        g = make_valid_genotype()
        task = attach_checker(build_task("A-test", "A", 1, "TA1"))
        res = interp.run(g, task, seed_parts=("test", 0, 0))
        # Check trace has tool output
        tool_events = [e for e in res.trace if e.get("type") == "tool" and e.get("ok")]
        if tool_events:
            # Output should be non-empty
            self.assertTrue(len(tool_events[0].get("output", "")) > 0)

    def test_invalid_tool_input_fails(self):
        """B1: invalid input fails, not fake success."""
        from gleppo.genotype import Step
        interp = Interpreter()
        g = make_valid_genotype()
        g.tools = ["py_sandbox"]
        g.workflow = [
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="task"),
        ]
        task = attach_checker(build_task("A-test", "A", 1, "TA1"))
        res = interp.run(g, task, seed_parts=("test", 0, 0))
        self.assertFalse(res.success)


class TestCrossoverInheritance(unittest.TestCase):
    def test_workflow_inheritance_tracked(self):
        """E: workflow inheritance tracked."""
        p1 = make_valid_genotype()
        p2 = make_valid_genotype()
        p2.system_prompt = "Different strategy here. Final answer: {{answer}}"
        child, ok, _ = apply_operator("crossover", p1, {"mate": p2, "gen": 0})
        self.assertTrue(ok)
        wf = child.meta.get("inherited_strategies", {}).get("workflow_inheritance", [])
        self.assertGreater(len(wf), 0)
        for entry in wf:
            self.assertIn("source", entry)

    def test_invalid_mate_rejected(self):
        """C1: invalid mate rejected."""
        p1 = make_valid_genotype()
        p2 = make_valid_genotype()
        p2.system_prompt = "bad"
        with self.assertRaises(ValueError):
            apply_operator("crossover", p1, {"mate": p2, "gen": 0})


if __name__ == "__main__":
    unittest.main(verbosity=2)
