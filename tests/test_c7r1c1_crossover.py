"""C7-R1-C1-C: crossover inheritance tracking tests."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gleppo.genotype import make_valid_genotype, behavior_hash, validate_genotype
from gleppo.operators import apply_operator


class TestCrossoverInheritance(unittest.TestCase):
    def _make_valid_parent(self, prompt_suffix="", tools=None, workflow_mod=None):
        g = make_valid_genotype()
        if prompt_suffix:
            g.system_prompt = g.system_prompt.replace(
                "Final answer:", f"{prompt_suffix} Final answer:")
        if tools:
            g.tools = tools
        if workflow_mod:
            workflow_mod(g)
        self.assertEqual(validate_genotype(g), [], "parent must be valid")
        return g

    def test_both_parents_valid(self):
        p1 = self._make_valid_parent("Strategy A: compute carefully.")
        p2 = self._make_valid_parent("Strategy B: transform carefully.")
        self.assertEqual(validate_genotype(p1), [])
        self.assertEqual(validate_genotype(p2), [])

    def test_child_inherits_prompt_content(self):
        p1 = self._make_valid_parent("Strategy Alpha: use tools.")
        p2 = self._make_valid_parent("Strategy Beta: format output.")
        child, ok, _ = apply_operator("crossover", p1, {"mate": p2, "gen": 0})
        self.assertTrue(ok)
        self.assertEqual(validate_genotype(child), [])
        # Child should contain content from both parents
        self.assertIn("Strategy Alpha", child.system_prompt)
        self.assertIn("Strategy Beta", child.system_prompt)

    def test_inheritance_metadata_matches_child(self):
        p1 = self._make_valid_parent("Strategy Alpha: use tools.")
        p2 = self._make_valid_parent("Strategy Beta: format output.")
        child, ok, _ = apply_operator("crossover", p1, {"mate": p2, "gen": 0})
        self.assertTrue(ok)
        # Metadata should track actual inherited content
        inherited = child.meta.get("inherited_strategies", {})
        self.assertIn("from_parent_unique", inherited)
        self.assertIn("from_mate_unique", inherited)
        self.assertIn("from_shared", inherited)
        # Verify inherited sentences are actually in child
        for sent in inherited.get("from_parent_unique", []):
            self.assertIn(sent, child.system_prompt, "parent sentence must be in child")
        for sent in inherited.get("from_mate_unique", []):
            self.assertIn(sent, child.system_prompt, "mate sentence must be in child")

    def test_tools_inherited(self):
        p1 = self._make_valid_parent(tools=["calc", "str_ops"])
        p2 = self._make_valid_parent(tools=["calc", "str_ops", "py_sandbox"])
        child, ok, _ = apply_operator("crossover", p1, {"mate": p2, "gen": 0})
        self.assertTrue(ok)
        self.assertEqual(validate_genotype(child), [])
        # Child should have tools from both
        self.assertIn("calc", child.tools)
        # Metadata should track tool inheritance
        inherited = child.meta.get("inherited_strategies", {})
        self.assertIn("from_parent_tools", inherited)
        self.assertIn("from_mate_tools", inherited)

    def test_single_finalize_at_end(self):
        p1 = self._make_valid_parent("Alpha.")
        p2 = self._make_valid_parent("Beta.")
        child, ok, _ = apply_operator("crossover", p1, {"mate": p2, "gen": 0})
        self.assertTrue(ok)
        finalize_steps = [s for s in child.workflow if s.type == "finalize"]
        self.assertEqual(len(finalize_steps), 1, "exactly one finalize")
        self.assertEqual(child.workflow[-1].type, "finalize", "finalize must be last")

    def test_same_parents_deterministic(self):
        p = self._make_valid_parent("Same parent.")
        c1, _, _ = apply_operator("crossover", p, {"mate": p, "gen": 0})
        c2, _, _ = apply_operator("crossover", p, {"mate": p, "gen": 0})
        self.assertEqual(behavior_hash(c1), behavior_hash(c2))

    def test_different_parents_produce_different_child(self):
        p1 = self._make_valid_parent("Strategy Alpha: use tools.")
        p2 = self._make_valid_parent("Strategy Beta: format output.")
        c1, _, _ = apply_operator("crossover", p1, {"mate": p2, "gen": 0})
        self.assertNotEqual(behavior_hash(p1), behavior_hash(c1))
        self.assertNotEqual(behavior_hash(p2), behavior_hash(c1))


if __name__ == "__main__":
    unittest.main(verbosity=2)
