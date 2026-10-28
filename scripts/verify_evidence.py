"""C7-R1-C1-A: evidence manifest builder and verifier — strict integrity.

Required files must all be present. Removing any required entry fails.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# R1-A3: required files (must all be present in manifest and on disk)
REQUIRED_FILES = {
    "research/PRODUCTION_G3_RAW.json",
    "research/PRODUCTION_G3_REPORT.md",
    "research/PRODUCTION_SMOKE_RAW.json",
    "research/C7_EVIDENCE_RECOVERY.md",
    "research/PHASE2A_R10_C7_R1_REPORT.md",
    "docs/RUNTIME_LOCK.md",
    "docs/RUNTIME_LOCK_V2.md",
    "status.json",
    "scripts/verify_evidence.py",
    "gleppo/operators.py",
    "gleppo/genotype.py",
    "gleppo/interpreter.py",
    "gleppo/tasks.py",
    "gleppo/evaluator.py",
}

# R1-A3: historical missing (allowed but must be explicitly marked)
HISTORICAL_MISSING = {
    "research/PHASE2A_R10_C6_RAW.json",
    "research/PHASE2A_R10_C6_CANARY_RAW.json",
}

# R1-A2: allowed directory prefixes
ALLOWED_PREFIXES = ("research/", "docs/", "scripts/", "gleppo/", "tests/")
ALLOWED_ROOT_FILES = {"status.json"}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _safe_path(filename: str) -> bool:
    """R1-A2: reject traversal, absolute paths, and paths outside allowed roots."""
    if not filename or os.path.isabs(filename):
        return False
    normalized = os.path.normpath(filename)
    if normalized.startswith("..") or ".." in normalized.split(os.sep):
        return False
    # Must be under allowed prefix or be an allowed root file
    if filename in ALLOWED_ROOT_FILES:
        return True
    return any(filename.startswith(p) for p in ALLOWED_PREFIXES)


def _real_path_in_repo(filename: str) -> bool:
    """R1-A2: check resolved real path is inside REPO (symlink safety)."""
    full = os.path.join(REPO, filename)
    try:
        real = os.path.realpath(full)
        repo_real = os.path.realpath(REPO)
        return real.startswith(repo_real + os.sep) or real == repo_real
    except (OSError, ValueError):
        return False


def build_manifest(output_path: str) -> dict:
    """R1-A: explicitly generate new manifest. Does NOT verify."""
    manifest = {
        "version": "3.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files": {},
    }
    all_files = REQUIRED_FILES | HISTORICAL_MISSING
    for fname in sorted(all_files):
        if not _safe_path(fname) or not _real_path_in_repo(fname):
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
            status = "historical_missing" if fname in HISTORICAL_MISSING else "required_missing"
            manifest["files"][fname] = {"status": status}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    return manifest


def verify_manifest(manifest_path: str) -> list:
    """R1-A: read-only verification. Does NOT write or regenerate manifest."""
    errors = []
    if not os.path.exists(manifest_path):
        return ["MANIFEST_NOT_FOUND"]

    with open(manifest_path, "rb") as f:
        original_bytes = f.read()

    try:
        manifest = json.loads(original_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return [f"MANIFEST_INVALID_JSON: {e}"]

    if not isinstance(manifest, dict):
        return ["MANIFEST_NOT_OBJECT"]
    if "files" not in manifest or not isinstance(manifest["files"], dict):
        return ["MANIFEST_MISSING_FILES_KEY"]

    # R1-A1: required files must all be present in manifest
    manifest_keys = set(manifest["files"].keys())
    missing_required = REQUIRED_FILES - manifest_keys
    for fname in sorted(missing_required):
        errors.append(f"REQUIRED_ENTRY_MISSING: {fname}")

    # R1-A1: unauthorized entries
    allowed_entries = REQUIRED_FILES | HISTORICAL_MISSING
    unauthorized = manifest_keys - allowed_entries
    for fname in sorted(unauthorized):
        errors.append(f"UNAUTHORIZED_ENTRY: {fname}")

    # R1-A1: validate each entry
    for fname, entry in manifest["files"].items():
        if not isinstance(entry, dict):
            errors.append(f"INVALID_ENTRY_TYPE: {fname}")
            continue

        status = entry.get("status", "")
        if status not in ("present", "historical_missing", "required_missing"):
            errors.append(f"INVALID_STATUS: {fname} status={status}")
            continue

        # R1-A1: historical_missing only for registered files
        if status == "historical_missing" and fname not in HISTORICAL_MISSING:
            errors.append(f"FAKE_HISTORICAL_MISSING: {fname}")
            continue

        if status == "REJECTED_UNSAFE_PATH":
            errors.append(f"UNSAFE_PATH_IN_MANIFEST: {fname}")
            continue

        if not _safe_path(fname) or not _real_path_in_repo(fname):
            errors.append(f"UNSAFE_PATH: {fname}")
            continue

        if status == "present":
            # R1-A1: SHA-256 must be 64 hex chars
            sha = entry.get("sha256", "")
            if not isinstance(sha, str) or not SHA256_RE.match(sha):
                errors.append(f"INVALID_HASH_FORMAT: {fname}")
                continue

            path = os.path.join(REPO, fname)
            if not os.path.exists(path):
                errors.append(f"FILE_MISSING: {fname}")
                continue

            with open(path, "rb") as f:
                data = f.read()
            actual_hash = hashlib.sha256(data).hexdigest()
            if actual_hash != sha:
                errors.append(f"HASH_MISMATCH: {fname}")
            if len(data) != entry.get("size"):
                errors.append(f"SIZE_MISMATCH: {fname}")

        elif status == "required_missing":
            errors.append(f"REQUIRED_FILE_MISSING: {fname}")

        elif status == "historical_missing":
            if os.path.exists(os.path.join(REPO, fname)):
                errors.append(f"HISTORICAL_MISSING_BUT_EXISTS: {fname}")

    # R1-A1: verify manifest not modified during verification
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
        for fname, entry in sorted(manifest["files"].items()):
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
