"""Add R8 task references to genotype.py."""
content = open("gleppo/genotype.py", encoding="utf-8").read()

# Find the closing brace of _TASK_COMPATIBLE_REFERENCES
marker = '"B2-017":'
idx = content.rfind(marker)
# Find the closing } after B2-017
end_idx = content.find("\n}", idx)
print(f"B2-017 at {idx}, closing at {end_idx}")

# Insert new tasks before the closing brace
new_tasks = '''    "B2-018": {
        "tools": ["calc", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-019": {
        "tools": ["py_sandbox", "calc"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-020": {
        "tools": ["calc", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-021": {
        "tools": ["str_ops", "calc", "py_sandbox"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
}'''

# Replace the closing brace with new tasks + closing brace
content = content[:end_idx] + "\n" + new_tasks + content[end_idx+2:]
open("gleppo/genotype.py", "w", encoding="utf-8").write(content)
print("Added B2-018 to B2-021")
