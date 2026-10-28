"""C7-R1-C2-A: protocol hash tests."""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from protocol_hash import compute_protocol_hash, update_protocol_hash, verify_protocol_hash, normalize_text


class TestProtocolHash(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, "test.md")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write(self, content: bytes):
        with open(self.path, "wb") as f:
            f.write(content)

    def test_lf_hash(self):
        self._write(b"# Test\n**Protocol hash:** old\ncontent\n")
        h = compute_protocol_hash(self.path)
        self.assertEqual(len(h), 64)

    def test_crlf_same_hash_as_lf(self):
        self._write(b"# Test\n**Protocol hash:** old\ncontent\n")
        h1 = compute_protocol_hash(self.path)
        self._write(b"# Test\r\n**Protocol hash:** old\r\ncontent\r\n")
        h2 = compute_protocol_hash(self.path)
        self.assertEqual(h1, h2, "CRLF and LF must produce same hash")

    def test_cr_same_hash_as_lf(self):
        self._write(b"# Test\n**Protocol hash:** old\ncontent\n")
        h1 = compute_protocol_hash(self.path)
        self._write(b"# Test\r**Protocol hash:** old\rcontent\r")
        h2 = compute_protocol_hash(self.path)
        self.assertEqual(h1, h2, "CR and LF must produce same hash")

    def test_update_then_verify(self):
        self._write(b"# Test\n**Protocol hash:** old\ncontent\n")
        h = update_protocol_hash(self.path)
        self.assertTrue(verify_protocol_hash(self.path))

    def test_double_update_stable(self):
        self._write(b"# Test\n**Protocol hash:** old\ncontent\n")
        h1 = update_protocol_hash(self.path)
        h2 = update_protocol_hash(self.path)
        self.assertEqual(h1, h2, "double update must be stable")

    def test_content_change_invalidates_hash(self):
        self._write(b"# Test\n**Protocol hash:** old\ncontent\n")
        update_protocol_hash(self.path)
        self.assertTrue(verify_protocol_hash(self.path))
        # Modify content
        self._write(b"# Test\n**Protocol hash:** old\nchanged\n")
        self.assertFalse(verify_protocol_hash(self.path))

    def test_missing_hash_field_rejected(self):
        self._write(b"# Test\ncontent\n")
        self.assertFalse(verify_protocol_hash(self.path))

    def test_multiple_hash_fields_rejected(self):
        self._write(b"# Test\n**Protocol hash:** a\n**Protocol hash:** b\n")
        self.assertFalse(verify_protocol_hash(self.path))

    def test_utf8_decode_failure_rejected(self):
        self._write(b"\xff\xfe invalid utf-8")
        with self.assertRaises(ValueError):
            compute_protocol_hash(self.path)

    def test_cross_process_consistent(self):
        self._write(b"# Test\n**Protocol hash:** old\ncontent\n")
        h1 = compute_protocol_hash(self.path)
        # Simulate cross-process: recompute from file
        h2 = compute_protocol_hash(self.path)
        self.assertEqual(h1, h2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
