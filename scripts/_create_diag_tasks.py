"""G3-DIAG-v1: create diagnostic tasks A2 and B2."""
import json, hashlib, os, time

RUN_ID = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())

# A2: Strategy-sensitive tasks — require multi-step processing
# These tasks can distinguish different prompt strategies
A2_TASKS = [
    {
        "task_id": "A2-001", "family": "A", "template_id": "A2-T1",
        "input": "Solve step by step: (3*7) + (12-4) - (2*3). Show each intermediate result, then give the final answer.",
        "gold": "21",
        "required_tools": ["calc"],
        "description": "Multi-step arithmetic requiring intermediate results — tests step-by-step vs direct computation strategy",
    },
    {
        "task_id": "A2-002", "family": "A", "template_id": "A2-T2",
        "input": "If x=15 and y=8, compute: first find x*y, then subtract x+y from the product. State the intermediate product before the final answer.",
        "gold": "97",
        "required_tools": ["calc"],
        "description": "Two-stage computation — tests whether strategy affects intermediate reporting",
    },
    {
        "task_id": "A2-003", "family": "A", "template_id": "A2-T3",
        "input": "Calculate (100-37)*2 + 5. First report the subtraction result, then the multiplication, then the final sum.",
        "gold": "131",
        "required_tools": ["calc"],
        "description": "Three-stage computation — tests staged strategy compliance",
    },
]

# B2: Tool-dependent tasks — require specific tools for correct execution
B2_TASKS = [
    {
        "task_id": "B2-001", "family": "B", "template_id": "B2-T1",
        "input": "Compute 25*3-11 using the calc tool, then transform the result to a string and make it uppercase. Give as SUM-STRING.",
        "gold": "64-75",
        "required_tools": ["calc", "str_ops"],
        "description": "Requires calc AND str_ops — tool subset changes should affect execution",
    },
    {
        "task_id": "B2-002", "family": "B", "template_id": "B2-T2",
        "input": "Use py_sandbox to compute result = 14*3+7. Then use calc to verify 49-6. Give the final result.",
        "gold": "43",
        "required_tools": ["py_sandbox", "calc"],
        "description": "Requires py_sandbox AND calc — tests tool dependency",
    },
    {
        "task_id": "B2-003", "family": "B", "template_id": "B2-T3",
        "input": "Compute 8*8-4 using calc, then transform 'hi' to uppercase using str_ops. Report as NUMBER-STRING.",
        "gold": "60-HI",
        "required_tools": ["calc", "str_ops"],
        "description": "Requires calc AND str_ops with specific output format",
    },
]

# Create diagnostic task files
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
    "protocol": "G3-DIAG-v1",
    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "tasks": {},
}
for name, tasks in [("diagnostic_A2", A2_TASKS), ("diagnostic_B2", B2_TASKS)]:
    path = f"data/{name}.jsonl"
    manifest["tasks"][name] = {
        "count": len(tasks),
        "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(),
        "task_ids": [t["task_id"] for t in tasks],
    }

with open("research/G3_DIAG_V1_MANIFEST.json", "w") as f:
    json.dump(manifest, f, indent=2)
print(f"Manifest saved: research/G3_DIAG_V1_MANIFEST.json")
print(f"Run ID: {RUN_ID}")
