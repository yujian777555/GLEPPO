"""R20: Regression tests for DAC generic mechanism."""
import unittest

from gleppo.answer_binding import (
    AbstainReason,
    ComputationStep,
    TaskContract,
    compute_answer,
    dac_select_answer,
    extract_tool_outputs,
)


class TestComputeAnswer(unittest.TestCase):
    def test_calc_strops_pattern(self):
        contract = TaskContract(
            task_id="test", 
            steps=[
                ComputationStep("num", "calc", "int"),
                ComputationStep("word", "str_ops", "upper"),
            ],
            final_output="result",
            output_format="{word}-{num}",
        )
        outputs = {"calc": "33", "str_ops": "DONE"}
        answer, err = compute_answer(contract, outputs)
        self.assertEqual(answer, "DONE-33")
        self.assertIsNone(err)

    def test_py_sandbox_calc_pattern(self):
        contract = TaskContract(
            task_id="test",
            steps=[
                ComputationStep("intermediate", "py_sandbox", "int"),
                ComputationStep("result", "calc", "int"),
            ],
            final_output="result",
            output_format="{result}",
        )
        outputs = {"py_sandbox": "26", "calc": "17"}
        answer, err = compute_answer(contract, outputs)
        self.assertEqual(answer, "17")
        self.assertIsNone(err)

    def test_three_tool_pattern(self):
        contract = TaskContract(
            task_id="test",
            steps=[
                ComputationStep("word", "str_ops", "upper"),
                ComputationStep("num", "calc", "int"),
                ComputationStep("result", "py_sandbox", "int"),
            ],
            final_output="result",
            output_format="{word}-{result}",
        )
        outputs = {"str_ops": "BASE", "calc": "11", "py_sandbox": "19"}
        answer, err = compute_answer(contract, outputs)
        self.assertEqual(answer, "BASE-19")
        self.assertIsNone(err)

    def test_arithmetic_operation(self):
        contract = TaskContract(
            task_id="test",
            steps=[
                ComputationStep("a", "calc", "int"),
                ComputationStep("result", "a", "add", ["10"]),
            ],
            final_output="result",
            output_format="{result}",
        )
        outputs = {"calc": "5"}
        answer, err = compute_answer(contract, outputs)
        self.assertEqual(answer, "15")
        self.assertIsNone(err)

    def test_missing_tool(self):
        contract = TaskContract(
            task_id="test",
            steps=[ComputationStep("num", "calc", "int")],
            final_output="num",
            output_format="{num}",
            required_tools=["calc", "str_ops"],
        )
        outputs = {"calc": "33"}  # str_ops missing
        answer, err = compute_answer(contract, outputs)
        self.assertIsNone(answer)
        self.assertEqual(err, AbstainReason.MISSING_TOOL)

    def test_type_mismatch(self):
        contract = TaskContract(
            task_id="test",
            steps=[ComputationStep("num", "calc", "int")],
            final_output="num",
            output_format="{num}",
        )
        outputs = {"calc": "not_a_number"}
        answer, err = compute_answer(contract, outputs)
        self.assertIsNone(answer)
        self.assertEqual(err, AbstainReason.TYPE_MISMATCH)

    def test_incomplete_dependency(self):
        contract = TaskContract(
            task_id="test",
            steps=[
                ComputationStep("a", "calc", "int"),
                ComputationStep("result", "missing_step", "int"),
            ],
            final_output="result",
            output_format="{result}",
        )
        outputs = {"calc": "5"}
        answer, err = compute_answer(contract, outputs)
        self.assertIsNone(answer)
        self.assertEqual(err, AbstainReason.INCOMPLETE_DEPENDENCY)

    def test_identity_operation(self):
        contract = TaskContract(
            task_id="test",
            steps=[ComputationStep("word", "str_ops", "identity")],
            final_output="word",
            output_format="{word}",
        )
        outputs = {"str_ops": "hello"}
        answer, err = compute_answer(contract, outputs)
        self.assertEqual(answer, "hello")
        self.assertIsNone(err)

    def test_no_gold_read(self):
        """Mechanism doesn't read gold answers."""
        contract = TaskContract(
            task_id="test",
            steps=[ComputationStep("num", "calc", "int")],
            final_output="num",
            output_format="{num}",
        )
        outputs = {"calc": "42"}
        # Same outputs -> same answer regardless of any gold
        answer1, _ = compute_answer(contract, outputs)
        answer2, _ = compute_answer(contract, outputs)
        self.assertEqual(answer1, answer2)

    def test_deterministic_reproducible(self):
        contract = TaskContract(
            task_id="test",
            steps=[
                ComputationStep("num", "calc", "int"),
                ComputationStep("word", "str_ops", "upper"),
            ],
            final_output="result",
            output_format="{word}-{num}",
        )
        outputs = {"calc": "33", "str_ops": "DONE"}
        a1, _ = compute_answer(contract, outputs)
        a2, _ = compute_answer(contract, outputs)
        self.assertEqual(a1, a2)


class TestDACSelectAnswer(unittest.TestCase):
    def test_deterministic_wins(self):
        trace = [
            {"type": "tool", "ok": True, "detail": "calc", "output": "33"},
            {"type": "tool", "ok": True, "detail": "str_ops", "output": "DONE"},
        ]
        result = dac_select_answer("B2-055", trace, "Final answer: DONE-23")
        self.assertEqual(result["method"], "deterministic")
        self.assertEqual(result["answer"], "Final answer: DONE-33")
        self.assertTrue(result["computation_valid"])

    def test_abstain_on_missing_tool(self):
        trace = [
            {"type": "tool", "ok": True, "detail": "calc", "output": "33"},
        ]
        result = dac_select_answer("B2-055", trace, "Final answer: X")
        self.assertEqual(result["method"], "abstain")
        self.assertEqual(result["abstain_reason"], "missing_tool")

    def test_abstain_on_type_mismatch(self):
        trace = [
            {"type": "tool", "ok": True, "detail": "calc", "output": "not_number"},
            {"type": "tool", "ok": True, "detail": "str_ops", "output": "DONE"},
        ]
        result = dac_select_answer("B2-055", trace, "Final answer: X")
        self.assertEqual(result["method"], "abstain")
        self.assertEqual(result["abstain_reason"], "type_mismatch")

    def test_llm_fallback_unknown_task(self):
        trace = []
        result = dac_select_answer("UNKNOWN_TASK", trace, "Final answer: 42")
        self.assertEqual(result["method"], "llm_fallback")
        self.assertEqual(result["abstain_reason"], "invalid_contract")


if __name__ == "__main__":
    unittest.main()
