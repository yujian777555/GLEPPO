"""R4: Generate frozen task manifest and run offline checks."""
import hashlib
import json
import time

# R4 task definitions
R4_TASKS = {
    "B2-001": {
        "task_id": "B2-001",
        "tools": ["calc", "str_ops"],
        "contract": [("calc", "64"), ("str_ops", "SUM")],
        "structure": "two-tool string-transform SUM-STRING",
    },
    "B2-003": {
        "task_id": "B2-003",
        "tools": ["calc", "str_ops"],
        "contract": [("calc", "60"), ("str_ops", "HI")],
        "structure": "two-tool string-transform NUMBER-STRING",
    },
    "B2-004": {
        "task_id": "B2-004",
        "tools": ["py_sandbox", "calc"],
        "contract": [("py_sandbox", "32"), ("calc", "41")],
        "structure": "two-tool numeric chain intermediate!=final",
    },
    "B2-005": {
        "task_id": "B2-005",
        "tools": ["calc", "py_sandbox"],
        "contract": [("calc", "58"), ("py_sandbox", "71")],
        "structure": "two-tool REVERSED order vs B2-004",
    },
    "B2-006": {
        "task_id": "B2-006",
        "tools": ["calc", "str_ops", "py_sandbox"],
        "contract": [("calc", "40"), ("str_ops", "FINAL"), ("py_sandbox", "42")],
        "structure": "three-tool complex format-degradation-risk",
    },
}

SEEDS = [f"r4-paired-seed-{i:03d}" for i in range(1, 6)]

# Verify gold arithmetic
print("=== Gold Label Verification ===")
checks = [
    ("B2-001", 25*3-11, "64"),
    ("B2-003", 8*8-4, "60"),
    ("B2-004", 5*6+2, "32"),
    ("B2-004-calc", (5*6+2)+9, "41"),
    ("B2-005", 7*9-5, "58"),
    ("B2-005-ps", 58+13, "71"),
    ("B2-006", 12*4-8, "40"),
    ("B2-006-ps", 40+2, "42"),
]
for name, expected, gold in checks:
    ok = str(expected) == gold
    print(f"  {name}: expected={expected} gold={gold} -> {'PASS' if ok else 'FAIL'}")

# Generate manifest
manifest = {
    "protocol_id": "G3-DIAG-v2-R4",
    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "model_revision": "a09a35458c702b33eeacc393d103063234e8bc28",
    "tasks": R4_TASKS,
    "seeds": SEEDS,
    "operators": ["tool_subset_edit", "crossover"],
    "max_generations": 150,
    "max_wall_s": 300,
    "selection_mechanisms": ["S0_unfiltered", "S1_static_filter", "S2_static_select", "S3_post_exec_diag"],
}

# Task file hashes
for fname in ["data/diagnostic_B2.jsonl", "data/diagnostic_B2_R4.jsonl"]:
    with open(fname, "rb") as f:
        manifest[fname] = {"sha256": hashlib.sha256(f.read()).hexdigest()}

with open("research/R4_MANIFEST.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

msha = hashlib.sha256(open("research/R4_MANIFEST.json", "rb").read()).hexdigest()
print(f"\nR4_MANIFEST.json sha256={msha[:16]}")
print(f"Tasks: {len(R4_TASKS)}")
print(f"Seeds: {len(SEEDS)}")
print(f"Units: {len(R4_TASKS) * len(SEEDS) * 2}")
