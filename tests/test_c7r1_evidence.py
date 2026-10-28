"""C7-R1-A: evidence verifier tests."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from verify_evidence import build_manifest, verify_manifest, _safe_path


class TestEvidenceVerifier(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.manifest_path = os.path.join(self.tmpdir, "manifest.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_build_then_verify_passes(self):
        build_manifest(self.manifest_path)
        errors = verify_manifest(self.manifest_path)
        self.assertEqual(errors, [], f"errors: {errors}")

    def test_verify_read_only(self):
        build_manifest(self.manifest_path)
        with open(self.manifest_path, "rb") as f:
            before = f.read()
        verify_manifest(self.manifest_path)
        with open(self.manifest_path, "rb") as f:
            after = f.read()
        self.assertEqual(before, after, "verify must not modify manifest")

    def test_file_modification_detected(self):
        build_manifest(self.manifest_path)
        # Temporarily modify a file
        target = os.path.join(os.path.dirname(__file__), "..", "status.json")
        with open(target, "rb") as f:
            original = f.read()
        try:
            with open(target, "ab") as f:
                f.write(b"\n# modified")
            errors = verify_manifest(self.manifest_path)
            self.assertTrue(any("HASH_MISMATCH" in e for e in errors))
        finally:
            with open(target, "wb") as f:
                f.write(original)

    def test_corrupt_manifest_json(self):
        with open(self.manifest_path, "w") as f:
            f.write("{invalid json")
        errors = verify_manifest(self.manifest_path)
        self.assertTrue(any("MANIFEST_INVALID_JSON" in e for e in errors))

    def test_missing_manifest(self):
        errors = verify_manifest(os.path.join(self.tmpdir, "nonexistent.json"))
        self.assertEqual(errors, ["MANIFEST_NOT_FOUND"])

    def test_path_traversal_rejected(self):
        self.assertFalse(_safe_path("../etc/passwd"))
        self.assertFalse(_safe_path("research/../../etc/passwd"))
        self.assertFalse(_safe_path("/etc/passwd"))
        self.assertTrue(_safe_path("research/test.json"))

    def test_unsafe_path_in_manifest(self):
        manifest = {
            "version": "2.0",
            "files": {
                "../etc/passwd": {"status": "present", "sha256": "a" * 64, "size": 100},
            },
        }
        with open(self.manifest_path, "w") as f:
            json.dump(manifest, f)
        errors = verify_manifest(self.manifest_path)
        self.assertTrue(any("UNSAFE_PATH" in e for e in errors))

    def test_invalid_hash_format(self):
        manifest = {
            "version": "2.0",
            "files": {
                "status.json": {"status": "present", "sha256": "short", "size": 100},
            },
        }
        with open(self.manifest_path, "w") as f:
            json.dump(manifest, f)
        errors = verify_manifest(self.manifest_path)
        self.assertTrue(any("INVALID_HASH_FORMAT" in e for e in errors))

    def test_historical_missing_ok(self):
        build_manifest(self.manifest_path)
        errors = verify_manifest(self.manifest_path)
        self.assertEqual(errors, [], "historical_missing should not fail verification")

    def test_required_file_missing_fails(self):
        build_manifest(self.manifest_path)
        with open(self.manifest_path, encoding="utf-8") as f:
            m = json.load(f)
        m["files"]["status.json"]["status"] = "required_missing"
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(m, f)
        errors = verify_manifest(self.manifest_path)
        self.assertTrue(any("REQUIRED_FILE_MISSING" in e for e in errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
