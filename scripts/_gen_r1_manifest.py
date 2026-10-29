"""G3-DIAG-v2-R1: Generate SHA-256 manifest after all artifacts are finalized."""
import hashlib
import json
import os
import time

RUN_ID = "20261029T033104Z_R1"

ARTIFACTS = [
    "gleppo/llm.py",
    "gleppo/interpreter.py",
    "gleppo/tool_path.py",
    "tests/test_r1_fastpath.py",
    "scripts/_run_g3_diag_r1.py",
    "data/diagnostic_B2.jsonl",
    "research/G3_DIAG_R1_RAW.json",
    "research/G3_DIAG_R1_LEDGER.jsonl",
    "research/G3_DIAG_R1_REPORT.md",
]

manifest = {
    "run_id": RUN_ID,
    "protocol": "G3-DIAG-v2-R1",
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "artifacts": {},
}

for path in ARTIFACTS:
    if os.path.exists(path):
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        size = os.path.getsize(path)
        manifest["artifacts"][path] = {"sha256": sha, "size_bytes": size}
    else:
        manifest["artifacts"][path] = {"sha256": None, "size_bytes": 0, "missing": True}

out_path = "research/G3_DIAG_R1_MANIFEST.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

manifest_sha = hashlib.sha256(open(out_path, "rb").read()).hexdigest()
print(f"Manifest: {out_path}")
print(f"Manifest SHA-256: {manifest_sha}")
for path, info in manifest["artifacts"].items():
    status = "OK" if info.get("sha256") else "MISSING"
    print(f"  {status} {path}: {info.get('sha256', 'N/A')[:16]}...")
