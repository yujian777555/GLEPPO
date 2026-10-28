"""C7-R1-C3-A: strict protocol hash — unique field, file normalization."""
from __future__ import annotations

import hashlib
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOCK_V2_PATH = os.path.join(REPO, "docs", "RUNTIME_LOCK_V2.md")
MARKER = "__PROTOCOL_HASH__"
HASH_PATTERN = re.compile(r"\*\*Protocol hash:\*\* (\S+)")


def normalize_text(text: str) -> str:
    """A1: normalize line endings to LF, then replace unique hash with marker."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    matches = list(HASH_PATTERN.finditer(normalized))
    if len(matches) == 0:
        raise ValueError("A1: no Protocol hash field found")
    if len(matches) > 1:
        raise ValueError(f"A1: multiple Protocol hash fields found ({len(matches)})")
    # Replace the single hash value with marker
    m = matches[0]
    normalized = normalized[:m.start(1)] + MARKER + normalized[m.end(1):]
    return normalized


def compute_protocol_hash(path: str) -> str:
    """A1: deterministic hash — normalize line endings and unique hash field."""
    with open(path, "rb") as f:
        data = f.read()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"A1: UTF-8 decode failed: {e}")
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def update_protocol_hash(path: str) -> str:
    """A1: compute hash, write atomically, re-read and verify."""
    h = compute_protocol_hash(path)
    with open(path, "rb") as f:
        text = f.read().decode("utf-8")
    matches = list(HASH_PATTERN.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"A1: expected exactly 1 hash field, found {len(matches)}")
    m = matches[0]
    new_text = text[:m.start(1)] + h + text[m.end(1):]
    # A2: write atomically (write to temp, then rename)
    tmp_path = path + ".tmp"
    with open(tmp_path, "wb") as f:
        f.write(new_text.encode("utf-8"))
    os.replace(tmp_path, path)
    # A2: re-read and verify
    h2 = compute_protocol_hash(path)
    if h != h2:
        raise ValueError(f"A1: hash unstable after write: {h} != {h2}")
    return h


def verify_protocol_hash(path: str) -> bool:
    """A1: verify — must find exactly one hash field, match computed."""
    try:
        with open(path, "rb") as f:
            text = f.read().decode("utf-8")
        matches = list(HASH_PATTERN.finditer(text))
        if len(matches) != 1:
            return False
        stored = matches[0].group(1)
        if stored == MARKER:
            return False
        computed = compute_protocol_hash(path)
        return stored == computed
    except (ValueError, OSError):
        return False


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "update":
        h = update_protocol_hash(LOCK_V2_PATH)
        print(f"Updated: {h}")
    elif cmd == "verify":
        ok = verify_protocol_hash(LOCK_V2_PATH)
        print(f"Verify: {'OK' if ok else 'FAILED'}")
        sys.exit(0 if ok else 1)
