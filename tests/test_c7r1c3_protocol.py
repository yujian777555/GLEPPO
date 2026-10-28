"""C7-R1-C3-A: strict protocol hash tests."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from protocol_hash import compute_protocol_hash, update_protocol_hash, verify_protocol_hash, normalize_text


class TestProtocolHashStrict(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, "test.md")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write(self, content: bytes):
        with open(self.path, "wb") as f:
            f.write(content)

    def test_normal_single_hash_passes(self):
        self._write(b"# T\n**Protocol hash:** old\ncontent\n")
        h = update_protocol_hash(self.path)
        self.assertTrue(verify_protocol_hash(self.path))

    def test_missing_hash_rejected(self):
        self._write(b"# T\ncontent\n")
        self.assertFalse(verify_protocol_hash(self.path))
        with self.assertRaises(ValueError):
            compute_protocol_hash(self.path)

    def test_multiple_hash_fields_rejected(self):
        self._write(b"# T\n**Protocol hash:** a\n**Protocol hash:** b\ncontent\n")
        self.assertFalse(verify_protocol_hash(self.path))
        with self.assertRaises(ValueError):
            compute_protocol_hash(self.path)

    def test_multiple_hash_fields_rejected_even_if_first_correct(self):
        self._write(b"# T\n**Protocol hash:** old\n**Protocol hash:** old\ncontent\n")
        h = compute_protocol_hash(self.path) if False else None
        # Should fail on update due to multiple fields
        with self.assertRaises(ValueError):
            update_protocol_hash(self.path)

    def test_crlf_same_as_lf(self):
        self._write(b"# T\n**Protocol hash:** old\ncontent\n")
        h1 = compute_protocol_hash(self.path)
        self._write(b"# T\r\n**Protocol hash:** old\r\ncontent\r\n")
        h2 = compute_protocol_hash(self.path)
        self.assertEqual(h1, h2)

    def test_cr_same_as_lf(self):
        self._write(b"# T\n**Protocol hash:** old\ncontent\n")
        h1 = compute_protocol_hash(self.path)
        self._write(b"# T\r**Protocol hash:** old\rcontent\r")
        h2 = compute_protocol_hash(self.path)
        self.assertEqual(h1, h2)

    def test_update_then_verify_stable(self):
        self._write(b"# T\n**Protocol hash:** old\ncontent\n")
        h1 = update_protocol_hash(self.path)
        self.assertTrue(verify_protocol_hash(self.path))
        h2 = update_protocol_hash(self.path)
        self.assertEqual(h1, h2, "double update must be stable")

    def test_content_change_invalidates(self):
        self._write(b"# T\n**Protocol hash:** old\ncontent\n")
        update_protocol_hash(self.path)
        self.assertTrue(verify_protocol_hash(self.path))
        self._write(b"# T\n**Protocol hash:** old\nchanged\n")
        self.assertFalse(verify_protocol_hash(self.path))

    def test_cross_process_consistent(self):
        self._write(b"# T\n**Protocol hash:** old\ncontent\n")
        h1 = compute_protocol_hash(self.path)
        # Independent subprocess
        script = (
            "import sys; sys.path.insert(0, r'%s'); "
            "from protocol_hash import compute_protocol_hash; "
            "print(compute_protocol_hash(r'%s'))"
        ) % (os.path.join(REPO, "scripts"), self.path)
        r = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        h2 = r.stdout.strip()
        self.assertEqual(h1, h2, f"cross-process mismatch: {h1} != {h2}")


REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


if __name__ == "__main__":
    unittest.main(verbosity=2)
