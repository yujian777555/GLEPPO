"""C7-E: evidence hash verification tool."""
from __future__ import annotations

import hashlib
import json
import os
import sys

REPO = os.path.join(os.path.dirname(__file__), "..")

def compute_file_hash(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def generate_manifest() -> dict:
    """Generate SHA-256 manifest of all evidence files."""
    evidence_files = [
        "research/PRODUCTION_G3_RAW.json",
        "research/PRODUCTION_G3_REPORT.md",
        "research/PRODUCTION_SMOKE_RAW.json",
        "research/C7_EVIDENCE_RECOVERY.md",
        "docs/RUNTIME_LOCK.md",
        "status.json",
    ]
    manifest = {"files": {}, "generated_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ")}
    for f in evidence_files:
        path = os.path.join(REPO, f)
        if os.path.exists(path):
            manifest["files"][f] = {
                "sha256": compute_file_hash(path),
                "size": os.path.getsize(path),
            }
        else:
            manifest["files"][f] = {"status": "MISSING"}
    return manifest

def verify_manifest(manifest_path: str) -> list:
    """Verify files match manifest. Returns list of errors."""
    errors = []
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    for fname, expected in manifest.get("files", {}).items():
        if expected.get("status") == "MISSING":
            continue
        path = os.path.join(REPO, fname)
        if not os.path.exists(path):
            errors.append(f"MISSING: {fname}")
            continue
        actual = compute_file_hash(path)
        if actual != expected.get("sha256"):
            errors.append(f"HASH_MISMATCH: {fname} expected={expected.get('sha256','')[:16]} actual={actual[:16]}")
    return errors

if __name__ == "__main__":
    manifest = generate_manifest()
    manifest_path = os.path.join(REPO, "research", "EVIDENCE_MANIFEST.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest written to {manifest_path}")
    errors = verify_manifest(manifest_path)
    if errors:
        print("VERIFICATION FAILED:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("VERIFICATION OK: all files match manifest")
