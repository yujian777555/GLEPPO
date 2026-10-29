"""R2: Generate SHA-256 manifest."""
import hashlib
import json
import os
import time

RUN_ID = "20261029T040254Z_R2"

ARTIFACTS = [
    "gleppo/interpreter.py",
    "gleppo/genotype.py",
    "gleppo/tool_path.py",
    "gleppo/llm.py",
    "tests/test_r2_tool_path.py",
    "tests/test_r1_fastpath.py",
    "scripts/_run_g3_diag_r2.py",
    "data/diagnostic_B2.jsonl",
    "research/G3_DIAG_R2_RAW.json",
    "research/G3_DIAG_R2_LEDGER.jsonl",
    "research/G3_DIAG_R2_REPORT.md",
]

manifest = {
    "run_id": RUN_ID,
    "protocol": "G3-DIAG-v2-R2",
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "artifacts": {},
}

for path in ARTIFACTS:
    if os.path.exists(path):
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        manifest["artifacts"][path] = {"sha256": sha, "size_bytes": os.path.getsize(path)}
    else:
        manifest["artifacts"][path] = {"sha256": None, "size_bytes": 0, "missing": True}

out = "research/G3_DIAG_R2_MANIFEST.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

msha = hashlib.sha256(open(out, "rb").read()).hexdigest()
print(f"Manifest: {out} sha256={msha}")
for p, i in manifest["artifacts"].items():
    s = "OK" if i.get("sha256") else "MISSING"
    print(f"  {s} {p}: {(i.get('sha256') or 'N/A')[:16]}")
