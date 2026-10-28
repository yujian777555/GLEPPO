"""C7-R1-C2-A: protocol hash with proper line-ending normalization."""
from __future__ import annotations

import hashlib
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOCK_V2_PATH = os.path.join(REPO, "docs", "RUNTIME_LOCK_V2.md")
MARKER = "__PROTOCOL_HASH__"


def normalize_text(text: str) -> str:
    """A1: normalize line endings to LF, then normalize hash field."""
    # Convert CRLF and CR to LF
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace hash field value with fixed marker
    normalized = re.sub(
        r"(\*\*Protocol hash:\*\* )\S+",
        lambda m: m.group(1) + MARKER,
        normalized,
    )
    return normalized


def compute_protocol_hash(path: str) -> str:
    """A1: deterministic hash — normalize line endings and hash field."""
    with open(path, "rb") as f:
        data = f.read()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"UTF-8 decode failed: {e}")
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def update_protocol_hash(path: str) -> str:
    """A2: compute hash, write it, re-read and verify."""
    h = compute_protocol_hash(path)
    with open(path, "rb") as f:
        text = f.read().decode("utf-8")
    # Replace hash value (keep original line endings)
    new_text = re.sub(
        r"(\*\*Protocol hash:\*\* )\S+",
        lambda m: m.group(1) + h,
        text,
    )
    # Write in binary to preserve line endings
    with open(path, "wb") as f:
        f.write(new_text.encode("utf-8"))
    # A2: re-read and verify
    h2 = compute_protocol_hash(path)
    if h != h2:
        raise ValueError(f"Hash unstable after write: {h} != {h2}")
    return h


def verify_protocol_hash(path: str) -> bool:
    """A2: verify stored hash matches independent recomputation."""
    with open(path, "rb") as f:
        text = f.read().decode("utf-8")
    m = re.search(r"\*\*Protocol hash:\*\* (\S+)", text)
    if not m:
        return False
    stored = m.group(1)
    if stored == MARKER:
        return False
    computed = compute_protocol_hash(path)
    return stored == computed


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "update":
        h = update_protocol_hash(LOCK_V2_PATH)
        print(f"Updated: {h}")
    elif cmd == "verify":
        ok = verify_protocol_hash(LOCK_V2_PATH)
        print(f"Verify: {'OK' if ok else 'FAILED'}")
        sys.exit(0 if ok else 1)
