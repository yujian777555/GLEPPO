"""C7-R1-C1-A: evidence verifier negative tests."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from verify_evidence import build_manifest, verify_manifest, _safe_path, REQUIRED_FILES, HISTORICAL_MISSING


class TestEvidenceVerifierNegative(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.manifest_path = os.path.join(self.tmpdir, "manifest.json")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _build_ok(self):
        build_manifest(self.manifest_path)
        return verify_manifest(self.manifest_path)

    def test_normal_manifest_passes(self):
        errors = self._build_ok()
        self.assertEqual(errors, [], f"unexpected errors: {errors}")

    def test_delete_required_entry_fails(self):
        build_manifest(self.manifest_path)
        with open(self.manifest_path, encoding="utf-8") as f:
            m = json.load(f)
        del m["files"]["status.json"]  # delete a required entry
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(m, f)
        errors = verify_manifest(self.manifest_path)
        self.assertTrue(any("REQUIRED_ENTRY_MISSING" in e for e in errors),
                        f"expected REQUIRED_ENTRY_MISSING, got: {errors}")

    def test_delete_all_files_fails(self):
        build_manifest(self.manifest_path)
        with open(self.manifest_path, encoding="utf-8") as f:
            m = json.load(f)
        m["files"] = {}
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(m, f)
        errors = verify_manifest(self.manifest_path)
        self.assertTrue(len(errors) > 0, "deleting all entries must fail")

    def test_unauthorized_entry_fails(self):
        build_manifest(self.manifest_path)
        with open(self.manifest_path, encoding="utf-8") as f:
            m = json.load(f)
        m["files"]["research/FAKE_FILE.json"] = {"status": "present", "sha256": "a" * 64, "size": 1}
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(m, f)
        errors = verify_manifest(self.manifest_path)
        self.assertTrue(any("UNAUTHORIZED_ENTRY" in e for e in errors))

    def test_fake_historical_missing_fails(self):
        build_manifest(self.manifest_path)
        with open(self.manifest_path, encoding="utf-8") as f:
            m = json.load(f)
        m["files"]["research/FAKE_FILE.json"] = {"status": "historical_missing"}
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(m, f)
        errors = verify_manifest(self.manifest_path)
        self.assertTrue(any("FAKE_HISTORICAL_MISSING" in e or "UNAUTHORIZED_ENTRY" in e for e in errors))

    def test_invalid_hash_format_fails(self):
        build_manifest(self.manifest_path)
        with open(self.manifest_path, encoding="utf-8") as f:
            m = json.load(f)
        m["files"]["status.json"]["sha256"] = "zz" * 32  # not hex
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(m, f)
        errors = verify_manifest(self.manifest_path)
        self.assertTrue(any("INVALID_HASH_FORMAT" in e for e in errors))

    def test_path_traversal_rejected(self):
        self.assertFalse(_safe_path("../etc/passwd"))
        self.assertFalse(_safe_path("research/../../etc/passwd"))
        self.assertFalse(_safe_path("/etc/passwd"))
        self.assertTrue(_safe_path("research/test.json"))

    def test_unsafe_path_in_manifest_fails(self):
        build_manifest(self.manifest_path)
        with open(self.manifest_path, encoding="utf-8") as f:
            m = json.load(f)
        m["files"]["../etc/passwd"] = {"status": "present", "sha256": "a" * 64, "size": 100}
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(m, f)
        errors = verify_manifest(self.manifest_path)
        self.assertTrue(any("UNSAFE_PATH" in e or "UNAUTHORIZED_ENTRY" in e for e in errors))

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

    def test_corrupt_json_fails(self):
        with open(self.manifest_path, "w") as f:
            f.write("{invalid")
        errors = verify_manifest(self.manifest_path)
        self.assertTrue(any("MANIFEST_INVALID_JSON" in e for e in errors))


if __name__ == "__main__":
    unittest.main(verbosity=2)
