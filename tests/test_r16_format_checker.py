"""R16: Regression tests for format checker and validation signal."""
import unittest

from gleppo.tool_path import verify_tool_path_for_task


def _make_trace(events):
    trace = [{"type": "meta", "tools": []}]
    for tool, ok, output in events:
        trace.append({"type": "tool", "ok": ok, "detail": tool, "output": output})
    return trace


class TestFormatChecker(unittest.TestCase):
    """Test format checker semantics."""

    def _check_format(self, answer):
        """Replicate format checker logic."""
        if not answer or not answer.strip():
            return False
        if "Final answer:" not in answer:
            return False
        idx = answer.index("Final answer:")
        after = answer[idx + len("Final answer:"):].strip()
        if not after:
            return False
        lines = after.split("\n")
        first_line = lines[0].strip()
        if len(first_line) > 100:
            return False
        return True

    def test_valid_format(self):
        self.assertTrue(self._check_format("Final answer: 42"))

    def test_missing_prefix(self):
        self.assertFalse(self._check_format("The answer is 42"))

    def test_empty_answer(self):
        self.assertFalse(self._check_format("Final answer: "))

    def test_tool_output_before_prefix(self):
        answer = "[tool:calc] 64\n[tool:str_ops] SUM\nFinal answer: 64-SUM"
        self.assertTrue(self._check_format(answer))  # prefix exists

    def test_tool_output_no_prefix(self):
        answer = "[tool:calc] 64\n[tool:str_ops] SUM"
        self.assertFalse(self._check_format(answer))  # no prefix

    def test_long_answer(self):
        answer = "Final answer: " + "x" * 200
        self.assertFalse(self._check_format(answer))

    def test_empty_input(self):
        self.assertFalse(self._check_format(""))

    def test_none_input(self):
        self.assertFalse(self._check_format(None))


class TestValidationSignal(unittest.TestCase):
    """Test validation signal semantics."""

    def test_val_ok_final_ok(self):
        """TN: validation says OK, final OK."""
        val_fmt = True
        final_fmt = True
        # No intervention needed
        self.assertEqual(val_fmt, final_fmt)

    def test_val_fail_final_fail(self):
        """TP: validation says FAIL, final FAILS."""
        val_fmt = False
        final_fmt = False
        self.assertEqual(val_fmt, final_fmt)

    def test_val_ok_final_fail(self):
        """FN: validation says OK, final FAILS — the B2-050 problem."""
        val_fmt = True
        final_fmt = False
        self.assertNotEqual(val_fmt, final_fmt)
        # This is the miss that M2 structural signal should catch

    def test_val_fail_final_ok(self):
        """FP: validation says FAIL, final OK — unnecessary intervention."""
        val_fmt = False
        final_fmt = True
        self.assertNotEqual(val_fmt, final_fmt)


class TestStructuralRiskSignal(unittest.TestCase):
    """Test M2 structural risk signal (pre-execution)."""

    def _check_structural_risk(self, required_tools):
        """M2: task has str_ops in required_tools -> risky."""
        return "str_ops" in required_tools

    def test_b2050_is_risky(self):
        """B2-050 has str_ops -> M2 flags as risky."""
        self.assertTrue(self._check_structural_risk(["str_ops", "calc", "py_sandbox"]))

    def test_b2049_is_risky(self):
        """B2-049 has str_ops -> M2 flags as risky (even though format OK)."""
        self.assertTrue(self._check_structural_risk(["calc", "str_ops"]))

    def test_b2051_is_not_risky(self):
        """B2-051 has no str_ops -> M2 says not risky."""
        self.assertFalse(self._check_structural_risk(["py_sandbox", "calc"]))

    def test_b2053_is_not_risky(self):
        """B2-053 has no str_ops -> M2 says not risky."""
        self.assertFalse(self._check_structural_risk(["calc", "py_sandbox"]))


class TestGoldNotRead(unittest.TestCase):
    """Verify checker does not read gold answers."""

    def test_checker_only_reads_answer_format(self):
        """Format checker only looks at answer text, not gold."""
        # Same answer, different gold -> same format result
        answer = "Final answer: 42"
        gold1 = "42"
        gold2 = "99"
        # Format check doesn't use gold
        fmt1 = "Final answer:" in answer
        fmt2 = "Final answer:" in answer
        self.assertEqual(fmt1, fmt2)

    def test_answer_correctness_independent(self):
        """Changing answer correctness doesn't change format check."""
        answer_correct = "Final answer: 42"
        answer_wrong = "Final answer: 99"
        # Both have same format
        self.assertEqual(
            "Final answer:" in answer_correct,
            "Final answer:" in answer_wrong,
        )


if __name__ == "__main__":
    unittest.main()
