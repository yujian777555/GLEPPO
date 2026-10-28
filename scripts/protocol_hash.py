"""C7-R1-C1-E: protocol hash — simple line-based."""
from __future__ import annotations

import hashlib
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOCK_V2_PATH = os.path.join(REPO, "docs", "RUNTIME_LOCK_V2.md")
MARKER = "__PROTOCOL_HASH__"


def compute_protocol_hash(path: str) -> str:
    with open(path, "rb") as f:
        text = f.read().decode("utf-8")
    # Replace hash value with marker (always, regardless of current value)
    text2 = re.sub(r"\*\*Protocol hash:\*\* \S+", f"**Protocol hash:** {MARKER}", text)
    return hashlib.sha256(text2.encode("utf-8")).hexdigest()


def update_protocol_hash(path: str) -> str:
    h = compute_protocol_hash(path)
    with open(path, "rb") as f:
        text = f.read().decode("utf-8")
    text2 = re.sub(r"\*\*Protocol hash:\*\* \S+", f"**Protocol hash:** {h}", text)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text2)
    return h


def verify_protocol_hash(path: str) -> bool:
    with open(path, "rb") as f:
        text = f.read().decode("utf-8")
    m = re.search(r"\*\*Protocol hash:\*\* (\S+)", text)
    if not m:
        return False
    stored = m.group(1)
    if stored == MARKER:
        return False
    return stored == compute_protocol_hash(path)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "update":
        h = update_protocol_hash(LOCK_V2_PATH)
        print(f"Updated: {h}")
    elif cmd == "verify":
        ok = verify_protocol_hash(LOCK_V2_PATH)
        print(f"Verify: {'OK' if ok else 'FAILED'}")
        sys.exit(0 if ok else 1)
