"""Update manifest with freeze information."""
import hashlib
import json
import time

RUN_ID = "20261028T130000Z"

# Load existing manifest
with open("research/G3_DIAG_V2_MANIFEST.json", encoding="utf-8") as f:
    manifest = json.load(f)

# Add freeze information
manifest["freeze"] = {
    "frozen_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "protocol_sha256": hashlib.sha256(open("research/G3_DIAG_V2_PROTOCOL.md", "rb").read()).hexdigest(),
    "model_revision": "a09a35458c702b33eeacc393d103063234e8bc28",
    "operators": ["tool_subset_edit", "crossover", "prompt_critique_rewrite"],
    "max_requests": 60,
    "max_wall_s": 600,
    "n_replicates": 2,
    "paired_seed_rule": "diag-{task_id}-p{parent_idx}",
    "behavior_change_criteria": [
        "success_rate_differs",
        "mean_tool_calls_differs",
        "mean_turns_differs",
        "failure_distribution_differs",
        "trace_differs",
        "answer_differs",
    ],
}

# Write updated manifest
with open("research/G3_DIAG_V2_MANIFEST.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

sha = hashlib.sha256(open("research/G3_DIAG_V2_MANIFEST.json", "rb").read()).hexdigest()
print(f"Manifest updated: sha256={sha[:16]}")
print(f"Protocol sha256: {manifest['freeze']['protocol_sha256'][:16]}")
print(f"Run ID: {manifest['run_id']}")
