"""C7-R1-A: evidence manifest builder and verifier — strictly separated.

build: generates new manifest (explicit write).
verify: read-only validation against existing manifest.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# R1-A3: allowed files with explicit status
ALLOWED_FILES = {
    "research/PRODUCTION_G3_RAW.json": "required",
    "research/PRODUCTION_G3_REPORT.md": "required",
    "research/PRODUCTION_SMOKE_RAW.json": "required",
    "research/C7_EVIDENCE_RECOVERY.md": "required",
    "research/PHASE2A_R10_C7_REPORT.md": "required",
    "docs/RUNTIME_LOCK.md": "required",
    "status.json": "required",
    "research/PHASE2A_R10_C6_RAW.json": "historical_missing",
    "research/PHASE2A_R10_C6_CANARY_RAW.json": "historical_missing",
}


def _safe_path(filename: str) -> bool:
    """R1-A2: reject path traversal and absolute paths."""
    if os.path.isabs(filename):
        return False
    if ".." in filename.split(os.sep) or ".." in filename.split("/"):
        return False
    if not filename.startswith("research/") and not filename.startswith("docs/") and filename != "status.json":
        return False
    return True


def build_manifest(output_path: str) -> dict:
    """R1-A: explicitly generate new manifest. Does NOT verify."""
    manifest = {
        "version": "2.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files": {},
    }
    for fname, status in ALLOWED_FILES.items():
        if not _safe_path(fname):
            manifest["files"][fname] = {"status": "REJECTED_UNSAFE_PATH"}
            continue
        path = os.path.join(REPO, fname)
        if os.path.exists(path):
            with open(path, "rb") as f:
                data = f.read()
            manifest["files"][fname] = {
                "status": "present",
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
            }
        else:
            manifest["files"][fname] = {"status": status}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    return manifest


def verify_manifest(manifest_path: str) -> list:
    """R1-A: read-only verification. Does NOT write or regenerate manifest."""
    errors = []
    if not os.path.exists(manifest_path):
        return ["MANIFEST_NOT_FOUND"]

    # R1-A2: verify manifest is not modified during verification
    with open(manifest_path, "rb") as f:
        original_bytes = f.read()

    try:
        manifest = json.loads(original_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return [f"MANIFEST_INVALID_JSON: {e}"]

    if "files" not in manifest:
        return ["MANIFEST_MISSING_FILES_KEY"]

    for fname, entry in manifest["files"].items():
        # R1-A2: reject unsafe paths
        if not _safe_path(fname):
            errors.append(f"UNSAFE_PATH: {fname}")
            continue

        status = entry.get("status", "")
        path = os.path.join(REPO, fname)

        if status == "historical_missing":
            if os.path.exists(path):
                errors.append(f"HISTORICAL_MISSING_BUT_EXISTS: {fname}")
            continue

        if status == "REJECTED_UNSAFE_PATH":
            continue

        if status != "present":
            # Required file is missing
            if status == "required":
                errors.append(f"REQUIRED_FILE_MISSING: {fname}")
            continue

        # R1-A2: verify file exists and matches
        if not os.path.exists(path):
            errors.append(f"FILE_MISSING: {fname}")
            continue

        with open(path, "rb") as f:
            data = f.read()
        actual_hash = hashlib.sha256(data).hexdigest()
        expected_hash = entry.get("sha256", "")

        if not expected_hash or len(expected_hash) != 64:
            errors.append(f"INVALID_HASH_FORMAT: {fname}")
            continue

        if actual_hash != expected_hash:
            errors.append(f"HASH_MISMATCH: {fname}")
            continue

        if len(data) != entry.get("size", -1):
            errors.append(f"SIZE_MISMATCH: {fname}")

    # R1-A2: verify manifest not modified
    with open(manifest_path, "rb") as f:
        after_bytes = f.read()
    if original_bytes != after_bytes:
        errors.append("MANIFEST_MODIFIED_DURING_VERIFICATION")

    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: verify_evidence.py <build|verify> [manifest_path]")
        sys.exit(1)

    cmd = sys.argv[1]
    manifest_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "research", "EVIDENCE_MANIFEST.json")

    if cmd == "build":
        manifest = build_manifest(manifest_path)
        print(f"Manifest built: {manifest_path}")
        for fname, entry in manifest["files"].items():
            print(f"  {fname}: {entry.get('status', 'present')}")
    elif cmd == "verify":
        errors = verify_manifest(manifest_path)
        if errors:
            print("VERIFICATION FAILED:")
            for e in errors:
                print(f"  {e}")
            sys.exit(1)
        else:
            print("VERIFICATION OK: all files match manifest")
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
