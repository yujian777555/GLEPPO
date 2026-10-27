"""Build and verify hash-frozen task manifests. Family C is written but never executed."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gleppo.manifest import build_manifests, verify_manifest  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

if __name__ == "__main__":
    digests = build_manifests(DATA_DIR)
    errs = verify_manifest(DATA_DIR)
    print("DIGESTS")
    for k, v in digests.items():
        print(f"  {k}: {v[:16]}...")
    print("VERIFY", "OK" if not errs else errs)
    sys.exit(0 if not errs else 1)
