"""Add R15 task references to genotype.py."""
content = open("gleppo/genotype.py", encoding="utf-8").read()
marker = '"B2-048":'
idx = content.rfind(marker)
end_idx = content.find("\n}", idx)

new_tasks = '''    "B2-049": {
        "tools": ["calc", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-050": {
        "tools": ["str_ops", "calc", "py_sandbox"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-051": {
        "tools": ["py_sandbox", "calc"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-052": {
        "tools": ["calc", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-053": {
        "tools": ["calc", "py_sandbox"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-054": {
        "tools": ["calc", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
}'''

content = content[:end_idx] + "\n" + new_tasks + content[end_idx+2:]
open("gleppo/genotype.py", "w", encoding="utf-8").write(content)
print("Added B2-049 to B2-054")
