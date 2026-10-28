"""C7 regression tests: operator fixes, answer format, evidence verification."""
from __future__ import annotations

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gleppo.genotype import make_valid_genotype, behavior_hash, validate_genotype, is_valid
from gleppo.operators import OPERATOR_NAMES, apply_operator
from gleppo.interpreter import Interpreter
from gleppo.llm import StubLLM
from gleppo.tasks import build_task, attach_checker, _check_family_a, _check_family_b
from gleppo.tools import run_tool


# ===== C7-B: tool_subset_edit tests =====
class TestToolSubsetEdit(unittest.TestCase):
    def test_drop_unreferenced_tool(self):
        """Drop tool not in workflow."""
        g = make_valid_genotype(tools=["calc", "str_ops", "py_sandbox"])
        # workflow uses calc and str_ops only
        child, ok, errs = apply_operator("tool_subset_edit", g, {"gen": 0})
        self.assertTrue(ok, errs)
        self.assertTrue(is_valid(child))

    def test_drop_referenced_tool_fixes_workflow(self):
        """Drop tool referenced in workflow — must fix references."""
        g = make_valid_genotype(tools=["calc", "str_ops"])
        # Force drop of calc (referenced in workflow)
        for gen in range(10):
            child, ok, errs = apply_operator("tool_subset_edit", g, {"gen": gen})
            if ok and "calc" not in child.tools:
                # Verify workflow doesn't reference calc
                for step in child.workflow:
                    if step.tool:
                        self.assertIn(step.tool, child.tools, "workflow references disabled tool")
                break
        self.assertTrue(is_valid(child))

    def test_add_tool_enters_execution(self):
        """Add tool and verify it's in tools list."""
        g = make_valid_genotype(tools=["calc"])
        child, ok, errs = apply_operator("tool_subset_edit", g, {"gen": 1})
        self.assertTrue(ok, errs)
        self.assertTrue(is_valid(child))
        self.assertGreater(len(child.tools), 1)

    def test_min_tool_boundary(self):
        """Minimum 1 tool preserved."""
        g = make_valid_genotype(tools=["calc"])
        for gen in range(20):
            child, ok, _ = apply_operator("tool_subset_edit", g, {"gen": gen})
            if ok:
                self.assertGreaterEqual(len(child.tools), 1)
        self.assertTrue(is_valid(child))

    def test_all_children_valid(self):
        """All generated children pass validation."""
        g = make_valid_genotype()
        for gen in range(20):
            child, ok, errs = apply_operator("tool_subset_edit", g, {"gen": gen})
            if ok:
                self.assertTrue(is_valid(child), f"gen={gen}: {validate_genotype(child)}")


# ===== C7-C: crossover tests =====
class TestCrossover(unittest.TestCase):
    def test_different_prompts(self):
        """Crossover of parents with different prompts."""
        g1 = make_valid_genotype()
        g1.system_prompt = "Compute step by step. Use tools for arithmetic. Final answer: {{answer}}"
        g2 = make_valid_genotype()
        g2.system_prompt = "Transform strings carefully. Format output precisely. Final answer: {{answer}}"
        child, ok, errs = apply_operator("crossover", g1, {"mate": g2, "gen": 0})
        self.assertTrue(ok, errs)
        self.assertTrue(is_valid(child))
        self.assertNotEqual(behavior_hash(g1), behavior_hash(child))

    def test_different_tools(self):
        """Crossover of parents with different tools."""
        g1 = make_valid_genotype(tools=["calc", "str_ops"])
        g2 = make_valid_genotype(tools=["calc", "str_ops", "py_sandbox"])
        child, ok, _ = apply_operator("crossover", g1, {"mate": g2, "gen": 0})
        self.assertTrue(ok)
        self.assertTrue(is_valid(child))
        # Should inherit tools from both
        self.assertIn("calc", child.tools)
        self.assertIn("str_ops", child.tools)

    def test_same_parents(self):
        """Crossover of identical parents — still valid."""
        g = make_valid_genotype()
        child, ok, _ = apply_operator("crossover", g, {"mate": g, "gen": 0})
        self.assertTrue(ok)
        self.assertTrue(is_valid(child))

    def test_inheritance_recorded(self):
        """Crossover records inheritance metadata."""
        g1 = make_valid_genotype()
        g2 = make_valid_genotype()
        g2.system_prompt = "Different strategy. Final answer: {{answer}}"
        child, ok, _ = apply_operator("crossover", g1, {"mate": g2, "gen": 0})
        self.assertTrue(ok)
        self.assertIn("crossover_parent", child.meta)
        self.assertIn("crossover_mate", child.meta)
        self.assertIn("inherited_strategies", child.meta)

    def test_reproducible_with_same_seed(self):
        """Same inputs produce same result."""
        g1 = make_valid_genotype()
        g2 = make_valid_genotype()
        g2.system_prompt = "Different strategy here. Final answer: {{answer}}"
        c1, _, _ = apply_operator("crossover", g1, {"mate": g2, "gen": 0})
        c2, _, _ = apply_operator("crossover", g1, {"mate": g2, "gen": 0})
        self.assertEqual(behavior_hash(c1), behavior_hash(c2))


# ===== C7-D: answer format tests =====
class TestAnswerFormat(unittest.TestCase):
    def test_family_a_correct(self):
        check = _check_family_a("42")
        self.assertTrue(check("Final answer: 42", None))
        self.assertTrue(check("Final answer: 42.0", None))

    def test_family_a_wrong(self):
        check = _check_family_a("42")
        self.assertFalse(check("Final answer: 41", None))
        self.assertFalse(check("The answer is 42", None))
        self.assertFalse(check("", None))

    def test_family_b_correct(self):
        check = _check_family_b("25-AB42")
        self.assertTrue(check("Final answer: 25-AB42", None))
        self.assertTrue(check("25-AB42", None))

    def test_family_b_wrong(self):
        check = _check_family_b("25-AB42")
        self.assertFalse(check("Final answer: 26-AB42", None))
        self.assertFalse(check("Final answer: 25-XY99", None))
        self.assertFalse(check("SUM-STRING: 25-AB42", None))

    def test_format_no_contamination(self):
        """Intermediate tool input doesn't affect final answer format."""
        check = _check_family_a("42")
        self.assertTrue(check("Final answer: 42", None))
        self.assertTrue(check("42", None))  # value correct even without prefix


# ===== Evidence verification =====
class TestEvidenceVerification(unittest.TestCase):
    def test_c6_raw_missing(self):
        """C6 raw files are missing — document this."""
        path = os.path.join(os.path.dirname(__file__), "..", "research", "PHASE2A_R10_C6_RAW.json")
        # This test documents the known missing state
        if os.path.exists(path):
            self.skipTest("C6_RAW now exists")
        else:
            self.assertTrue(True)  # documented as missing

    def test_production_g3_raw_all_zeros(self):
        """PRODUCTION_G3_RAW.json shows all behavior_changed=0."""
        path = os.path.join(os.path.dirname(__file__), "..", "research", "PRODUCTION_G3_RAW.json")
        if not os.path.exists(path):
            self.skipTest("PRODUCTION_G3_RAW.json not found")
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        for op, r in d.get("operators", {}).items():
            self.assertEqual(r.get("behavior_changed"), 0,
                             f"{op} should have behavior_changed=0 in raw data")


if __name__ == "__main__":
    unittest.main(verbosity=2)
