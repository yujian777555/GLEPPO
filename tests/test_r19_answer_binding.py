"""R19: Regression tests for deterministic answer calculation."""
import unittest

from gleppo.answer_binding import (
    deterministic_answer,
    extract_tool_outputs,
    tgab_answer_selection,
    verify_answer_source,
)


class TestExtractToolOutputs(unittest.TestCase):
    def test_extract_calc_and_strops(self):
        trace = [
            {"type": "meta", "tools": []},
            {"type": "tool", "ok": True, "detail": "calc", "output": "33"},
            {"type": "tool", "ok": True, "detail": "str_ops", "output": "DONE"},
        ]
        outputs = extract_tool_outputs(trace)
        self.assertEqual(outputs["calc"], "33")
        self.assertEqual(outputs["str_ops"], "DONE")

    def test_extract_ignores_failed_tools(self):
        trace = [
            {"type": "tool", "ok": False, "detail": "calc", "output": "error"},
            {"type": "tool", "ok": True, "detail": "str_ops", "output": "DONE"},
        ]
        outputs = extract_tool_outputs(trace)
        self.assertNotIn("calc", outputs)
        self.assertEqual(outputs["str_ops"], "DONE")


class TestDeterministicAnswer(unittest.TestCase):
    def test_calc_strops_pattern(self):
        outputs = {"calc": "33", "str_ops": "DONE"}
        result = deterministic_answer("B2-055", outputs, "")
        self.assertEqual(result, "DONE-33")

    def test_calc_strops_word_case(self):
        outputs = {"calc": "33", "str_ops": "done"}
        result = deterministic_answer("B2-055", outputs, "")
        self.assertEqual(result, "DONE-33")

    def test_py_sandbox_calc_pattern(self):
        outputs = {"py_sandbox": "26", "calc": "17"}
        result = deterministic_answer("B2-062", outputs, "")
        self.assertEqual(result, "17")

    def test_single_calc(self):
        outputs = {"calc": "44"}
        result = deterministic_answer("B2-064", outputs, "")
        self.assertEqual(result, "44")

    def test_no_tools(self):
        result = deterministic_answer("B2-055", {}, "")
        self.assertIsNone(result)

    def test_non_numeric_calc(self):
        outputs = {"calc": "error", "str_ops": "DONE"}
        result = deterministic_answer("B2-055", outputs, "")
        self.assertIsNone(result)


class TestVerifyAnswerSource(unittest.TestCase):
    def test_correct_answer(self):
        outputs = {"calc": "33", "str_ops": "DONE"}
        result = verify_answer_source("Final answer: DONE-33", outputs, "B2-055")
        self.assertTrue(result["source_valid"])

    def test_wrong_answer(self):
        outputs = {"calc": "33", "str_ops": "DONE"}
        result = verify_answer_source("Final answer: DONE-23", outputs, "B2-055")
        self.assertFalse(result["source_valid"])
        self.assertEqual(result["expected"], "DONE-33")
        self.assertEqual(result["actual"], "DONE-23")

    def test_no_final_prefix(self):
        outputs = {"calc": "33", "str_ops": "DONE"}
        result = verify_answer_source("DONE-33", outputs, "B2-055")
        self.assertTrue(result["source_valid"])


class TestTGABSelection(unittest.TestCase):
    def test_deterministic_wins(self):
        trace = [
            {"type": "tool", "ok": True, "detail": "calc", "output": "33"},
            {"type": "tool", "ok": True, "detail": "str_ops", "output": "DONE"},
        ]
        llm_answer = "Final answer: DONE-23"  # LLM is wrong
        result = tgab_answer_selection("B2-055", trace, "", llm_answer)
        self.assertEqual(result["method"], "deterministic")
        self.assertEqual(result["answer"], "Final answer: DONE-33")
        self.assertFalse(result["used_llm"])

    def test_llm_fallback_when_no_deterministic(self):
        trace = [
            {"type": "tool", "ok": True, "detail": "calc", "output": "not_a_number"},
        ]
        llm_answer = "Final answer: 42"
        result = tgab_answer_selection("B2-064", trace, "", llm_answer)
        self.assertEqual(result["method"], "llm_fallback")
        self.assertTrue(result["used_llm"])

    def test_gold_not_used(self):
        """Mechanism doesn't read gold answers."""
        trace = [
            {"type": "tool", "ok": True, "detail": "calc", "output": "33"},
            {"type": "tool", "ok": True, "detail": "str_ops", "output": "DONE"},
        ]
        # Same trace, different gold -> same result
        result1 = tgab_answer_selection("B2-055", trace, "", "Final answer: X")
        result2 = tgab_answer_selection("B2-055", trace, "", "Final answer: Y")
        self.assertEqual(result1["answer"], result2["answer"])

    def test_deterministic_reproducible(self):
        trace = [
            {"type": "tool", "ok": True, "detail": "calc", "output": "33"},
            {"type": "tool", "ok": True, "detail": "str_ops", "output": "DONE"},
        ]
        r1 = tgab_answer_selection("B2-055", trace, "", "Final answer: X")
        r2 = tgab_answer_selection("B2-055", trace, "", "Final answer: X")
        self.assertEqual(r1["answer"], r2["answer"])


if __name__ == "__main__":
    unittest.main()
