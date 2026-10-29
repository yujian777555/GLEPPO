"""R3 tests: frozen task, ordered tool contract, and independent metrics."""
import json
import unittest
from pathlib import Path

from gleppo.genotype import make_task_compatible_reference, validate_genotype
from gleppo.r3_metrics import check_format_compliant, evaluate_r3_metrics
from gleppo.tool_path import verify_tool_path_for_task


ROOT = Path(__file__).resolve().parents[1]


def load_r3_task():
    path = ROOT / "data" / "diagnostic_B2_R3.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 1:
        raise AssertionError(f"expected exactly one R3 task, got {len(rows)}")
    return rows[0]


class TestR3TaskAndReference(unittest.TestCase):
    def test_b2_004_frozen_identity_and_gold(self):
        task = load_r3_task()
        self.assertEqual(task["task_id"], "B2-004")
        self.assertEqual(task["family"], "B")
        self.assertEqual(task["gold"], "41")
        self.assertEqual(task["required_tools"], ["py_sandbox", "calc"])
        self.assertIn("5*6+2", task["input"])
        self.assertIn("32+9", task["input"])
        self.assertNotIn("Final answer: 41", task["input"])

    def test_reference_workflow_matches_required_order(self):
        task = load_r3_task()
        g = make_task_compatible_reference("B2-004")
        self.assertEqual(validate_genotype(g), [])
        self.assertEqual(sorted(g.tools), ["calc", "py_sandbox"])
        self.assertEqual(
            [s.tool for s in g.workflow if s.type == "tool"],
            ["py_sandbox", "calc"],
        )
        self.assertEqual(g.meta.get("label"), "task_compatible_reference")
        self.assertEqual(task["required_tools"], ["py_sandbox", "calc"])

    def test_gold_checker_checks_answer_not_tool_path(self):
        task = load_r3_task()
        from gleppo.tasks import attach_checker
        task = attach_checker(task)
        self.assertTrue(task["gold_check"]("Final answer: 41", None))
        self.assertFalse(task["gold_check"]("Final answer: 32", None))


class TestR3ToolPathContract(unittest.TestCase):
    def setUp(self):
        self.task = load_r3_task()
        self.good_trace = [
            {"type": "tool", "ok": True, "detail": "py_sandbox", "output": "32"},
            {"type": "tool", "ok": True, "detail": "calc", "output": "41"},
        ]

    def test_correct_order_and_outputs_pass(self):
        result = verify_tool_path_for_task("B2-004", self.good_trace, self.task["required_tools"])
        self.assertTrue(result["passed"])

    def test_wrong_output_fails(self):
        trace = [
            {"type": "tool", "ok": True, "detail": "py_sandbox", "output": "30"},
            {"type": "tool", "ok": True, "detail": "calc", "output": "41"},
        ]
        self.assertFalse(verify_tool_path_for_task("B2-004", trace)["passed"])

    def test_reversed_order_fails(self):
        trace = [
            {"type": "tool", "ok": True, "detail": "calc", "output": "41"},
            {"type": "tool", "ok": True, "detail": "py_sandbox", "output": "32"},
        ]
        self.assertFalse(verify_tool_path_for_task("B2-004", trace)["passed"])

    def test_missing_required_tool_fails(self):
        trace = [{"type": "tool", "ok": True, "detail": "calc", "output": "41"}]
        self.assertFalse(verify_tool_path_for_task("B2-004", trace)["passed"])


class TestR3MetricSeparation(unittest.TestCase):
    def setUp(self):
        from gleppo.tasks import attach_checker
        self.task = attach_checker(load_r3_task())
        self.genotype = make_task_compatible_reference("B2-004")
        self.good_trace = [
            {"type": "tool", "ok": True, "detail": "py_sandbox", "output": "32"},
            {"type": "tool", "ok": True, "detail": "calc", "output": "41"},
        ]

    def test_format_contract(self):
        self.assertTrue(check_format_compliant("Final answer: 41"))
        self.assertFalse(check_format_compliant("41"))
        self.assertFalse(check_format_compliant("Final answer: "))
        self.assertFalse(check_format_compliant("Final answer: " + "x" * 101))
        self.assertFalse(check_format_compliant("Final answer: 41\\nextra"))

    def test_correct_answer_with_broken_path_is_not_effective_success(self):
        metrics = evaluate_r3_metrics(
            "Final answer: 41", self.task, self.genotype,
            [{"type": "tool", "ok": True, "detail": "calc", "output": "41"}],
        )
        self.assertTrue(metrics["answer_correct"])
        self.assertTrue(metrics["format_compliant"])
        self.assertFalse(metrics["tool_path_valid"])
        self.assertFalse(metrics["hard_validity"])
        self.assertFalse(metrics["effective_success"])

    def test_valid_path_with_wrong_answer_is_not_effective_success(self):
        metrics = evaluate_r3_metrics(
            "Final answer: 32", self.task, self.genotype, self.good_trace
        )
        self.assertFalse(metrics["answer_correct"])
        self.assertTrue(metrics["format_compliant"])
        self.assertTrue(metrics["tool_path_valid"])
        self.assertTrue(metrics["hard_validity"])
        self.assertFalse(metrics["effective_success"])

    def test_answer_correctness_is_independent_of_format(self):
        metrics = evaluate_r3_metrics("41", self.task, self.genotype, self.good_trace)
        self.assertTrue(metrics["answer_correct"])
        self.assertFalse(metrics["format_compliant"])
        self.assertTrue(metrics["tool_path_valid"])
        self.assertFalse(metrics["hard_validity"])
        self.assertFalse(metrics["effective_success"])


if __name__ == "__main__":
    unittest.main()
