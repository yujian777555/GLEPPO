"""Add R17 task references to genotype.py."""
content = open("gleppo/genotype.py", encoding="utf-8").read()
marker = '"B2-054":'
idx = content.rfind(marker)
end_idx = content.find("\n}", idx)

new_tasks = '''    "B2-055": {
        "tools": ["calc", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-056": {
        "tools": ["str_ops", "calc", "py_sandbox"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-057": {
        "tools": ["py_sandbox", "calc"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-058": {
        "tools": ["calc", "py_sandbox"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-059": {
        "tools": ["calc", "str_ops"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="str_ops", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
    "B2-060": {
        "tools": ["calc", "py_sandbox"],
        "workflow": [
            Step(type="llm", prompt_slot="analyze", input_from="task"),
            Step(type="tool", tool="calc", input_from="task"),
            Step(type="tool", tool="py_sandbox", input_from="task"),
            Step(type="finalize", prompt_slot="answer", input_from="last_tool_output"),
        ],
    },
}'''

content = content[:end_idx] + "\n" + new_tasks + content[end_idx+2:]
open("gleppo/genotype.py", "w", encoding="utf-8").write(content)
print("Added B2-055 to B2-060")
