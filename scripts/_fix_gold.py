"""Fix diagnostic task gold labels."""
import json, hashlib, os, time

RUN_ID = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

# A2: Strategy-sensitive tasks — corrected gold
A2_TASKS = [
    {
        "task_id": "A2-001", "family": "A", "template_id": "A2-T1",
        "input": "Solve step by step: (3*7) + (12-4) - (2*3). Show each intermediate result, then give the final answer.",
        "gold": "23",
        "required_tools": ["calc"],
        "description": "Multi-step arithmetic requiring intermediate results",
    },
    {
        "task_id": "A2-002", "family": "A", "template_id": "A2-T2",
        "input": "If x=15 and y=8, compute: first find x*y, then subtract x+y from the product. State the intermediate product before the final answer.",
        "gold": "97",
        "required_tools": ["calc"],
        "description": "Two-stage computation",
    },
    {
        "task_id": "A2-003", "family": "A", "template_id": "A2-T3",
        "input": "Calculate (100-37)*2 + 5. First report the subtraction result, then the multiplication, then the final sum.",
        "gold": "131",
        "required_tools": ["calc"],
        "description": "Three-stage computation",
    },
]

# B2: Tool-dependent tasks — corrected gold
B2_TASKS = [
    {
        "task_id": "B2-001", "family": "B", "template_id": "B2-T1",
        "input": "Compute 25*3-11 using the calc tool, then transform the result to a string and make it uppercase. Give as SUM-STRING.",
        "gold": "64-64",
        "required_tools": ["calc", "str_ops"],
        "description": "Requires calc AND str_ops — result 64, string '64' uppercased is '64', format is SUM-STRING",
    },
    {
        "task_id": "B2-002", "family": "B", "template_id": "B2-T2",
        "input": "Use py_sandbox to compute result = 14*3+7. Then use calc to verify 49-6. Give the final result.",
        "gold": "43",
        "required_tools": ["py_sandbox", "calc"],
        "description": "Requires py_sandbox AND calc",
    },
    {
        "task_id": "B2-003", "family": "B", "template_id": "B2-T3",
        "input": "Compute 8*8-4 using calc, then transform 'hi' to uppercase using str_ops. Report as NUMBER-STRING.",
        "gold": "60-HI",
        "required_tools": ["calc", "str_ops"],
        "description": "Requires calc AND str_ops with specific output format",
    },
]

# Write corrected tasks
os.makedirs("data", exist_ok=True)
for name, tasks in [("diagnostic_A2", A2_TASKS), ("diagnostic_B2", B2_TASKS)]:
    path = f"data/{name}.jsonl"
    with open(path, "w") as f:
        for t in tasks:
            f.write(json.dumps(t, sort_keys=True) + "\n")
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print(f"{path}: {len(tasks)} tasks, sha256={sha[:16]}")

# Create manifest
manifest = {
    "run_id": RUN_ID,
    "protocol": "G3-DIAG-v2",
    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "gold_corrections": {
        "A2-001": "21 -> 23 (arithmetic error)",
        "B2-001": "64-75 -> 64-64 (phantom 75)",
    },
    "tasks": {},
}
for name, tasks in [("diagnostic_A2", A2_TASKS), ("diagnostic_B2", B2_TASKS)]:
    path = f"data/{name}.jsonl"
    manifest["tasks"][name] = {
        "count": len(tasks),
        "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(),
        "task_ids": [t["task_id"] for t in tasks],
    }

with open("research/G3_DIAG_V2_MANIFEST.json", "w") as f:
    json.dump(manifest, f, indent=2)
print(f"Manifest saved: research/G3_DIAG_V2_MANIFEST.json")
print(f"Run ID: {RUN_ID}")

# Verify gold labels
print("\n=== Gold verification ===")
for t in A2_TASKS:
    if t["task_id"] == "A2-001":
        expected = (3*7) + (12-4) - (2*3)
        print(f"A2-001: gold={t['gold']} expected={expected} match={t['gold']==str(expected)}")
for t in B2_TASKS:
    if t["task_id"] == "B2-001":
        expected = 25*3-11
        print(f"B2-001: gold={t['gold']} calc_result={expected}")
