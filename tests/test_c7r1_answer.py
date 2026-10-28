"""C7-R1-D: separate answer correctness from format compliance."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gleppo.tasks import _check_family_a, _check_family_b, _extract_final_answer


class TestAnswerCorrectnessVsFormat(unittest.TestCase):
    """Separate answer_correct from format_compliant."""

    def test_family_a_correct_and_format(self):
        check = _check_family_a("42")
        ans = "Final answer: 42"
        self.assertTrue(check(ans, None))  # answer_correct
        self.assertIn("Final answer:", ans)  # format_compliant

    def test_family_a_correct_no_prefix(self):
        check = _check_family_a("42")
        ans = "42"
        self.assertTrue(check(ans, None))  # answer_correct
        self.assertNotIn("Final answer:", ans)  # format NOT compliant

    def test_family_a_wrong_but_format(self):
        check = _check_family_a("42")
        ans = "Final answer: 41"
        self.assertFalse(check(ans, None))  # NOT answer_correct
        self.assertIn("Final answer:", ans)  # format_compliant

    def test_family_a_wrong_and_no_format(self):
        check = _check_family_a("42")
        ans = "The answer is 41"
        self.assertFalse(check(ans, None))
        self.assertNotIn("Final answer:", ans)

    def test_family_a_extra_text(self):
        check = _check_family_a("42")
        ans = "Final answer: 42. Let me explain why."
        self.assertFalse(check(ans, None))  # extra text makes extracted value wrong
        # format: has prefix but also extra text
        extracted = _extract_final_answer(ans)
        self.assertIn("Let me explain", extracted)  # extra text after value

    def test_family_b_correct_and_format(self):
        check = _check_family_b("25-AB42")
        ans = "Final answer: 25-AB42"
        self.assertTrue(check(ans, None))
        self.assertIn("Final answer:", ans)

    def test_family_b_correct_no_prefix(self):
        check = _check_family_b("25-AB42")
        ans = "25-AB42"
        self.assertTrue(check(ans, None))
        self.assertNotIn("Final answer:", ans)

    def test_family_b_wrong_but_format(self):
        check = _check_family_b("25-AB42")
        ans = "Final answer: 26-AB42"
        self.assertFalse(check(ans, None))
        self.assertIn("Final answer:", ans)

    def test_family_b_string_format_correctness(self):
        """Family B: string part case-insensitive, number must match."""
        check = _check_family_b("25-AB42")
        self.assertTrue(check("Final answer: 25-ab42", None))  # case insensitive string
        self.assertFalse(check("Final answer: 25-XY99", None))  # wrong string


if __name__ == "__main__":
    unittest.main(verbosity=2)
