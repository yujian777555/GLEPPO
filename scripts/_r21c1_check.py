"""R21-C1: Check and fix TaskContracts."""
content = open("gleppo/answer_binding.py", encoding="utf-8").read()

# Find existing contracts
import re
contracts = re.findall(r'"(B2-\d+)": TaskContract', content)
print("Existing contracts:", contracts)

missing = [f"B2-0{i}" for i in range(65, 73) if f"B2-0{i}" not in contracts]
print("Missing for R21:", missing)

# Check task definitions
for fname in ["data/diagnostic_B2_R21.jsonl"]:
    with open(fname, encoding="utf-8") as f:
        for line in f:
            import json
            t = json.loads(line)
            tid = t["task_id"]
            tools = t.get("required_tools", [])
            gold = t.get("gold", "")
            print(f"  {tid}: tools={tools} gold={gold}")
