"""C7-R1-C4-A: RUNTIME_LOCK_V2 formatting tests."""
from __future__ import annotations

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOCK_PATH = os.path.join(REPO, "docs", "RUNTIME_LOCK_V2.md")


class TestRuntimeLockFormat(unittest.TestCase):
    def test_no_cr_bytes(self):
        with open(LOCK_PATH, "rb") as f:
            data = f.read()
        self.assertEqual(data.count(b"\r"), 0, "no CR bytes allowed")

    def test_no_massive_blank_runs(self):
        with open(LOCK_PATH, "rb") as f:
            text = f.read().decode("utf-8")
        # No more than 2 consecutive newlines
        self.assertNotIn("\n\n\n", text, "no 3+ consecutive newlines")

    def test_key_sections_present(self):
        with open(LOCK_PATH, "rb") as f:
            text = f.read().decode("utf-8")
        for section in ["Model", "Inference Backend", "Decoding", "Random Seeds", "Task Protocol", "G3 Pass", "Budget"]:
            self.assertIn(section, text, f"section '{section}' missing")

    def test_single_hash_field(self):
        with open(LOCK_PATH, "rb") as f:
            text = f.read().decode("utf-8")
        matches = re.findall(r"\*\*Protocol hash:\*\*", text)
        self.assertEqual(len(matches), 1, "exactly one hash field")

    def test_line_count_reasonable(self):
        with open(LOCK_PATH, "rb") as f:
            text = f.read().decode("utf-8")
        lines = text.split("\n")
        self.assertGreater(len(lines), 50, "file should have substantial content")
        self.assertLess(len(lines), 500, "file should not be bloated with empty lines")


if __name__ == "__main__":
    unittest.main(verbosity=2)
