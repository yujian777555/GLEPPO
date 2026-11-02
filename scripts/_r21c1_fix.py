"""R21-C1: Add TaskContracts for B2-065 to B2-072."""
content = open("gleppo/answer_binding.py", encoding="utf-8").read()
marker = '"B2-064":'
idx = content.rfind(marker)
end_idx = content.find("\n}", idx)

new_contracts = '''    "B2-065": TaskContract(
        task_id="B2-065",
        steps=[ComputationStep("result", "calc", "int")],
        final_output="result",
        output_format="{result}",
        required_tools=["calc"],
    ),
    "B2-066": TaskContract(
        task_id="B2-066",
        steps=[
            ComputationStep("num", "calc", "int"),
            ComputationStep("word", "str_ops", "upper"),
        ],
        final_output="result",
        output_format="{word}-{num}",
        required_tools=["calc", "str_ops"],
    ),
    "B2-067": TaskContract(
        task_id="B2-067",
        steps=[
            ComputationStep("intermediate", "py_sandbox", "int"),
            ComputationStep("result", "calc", "int"),
        ],
        final_output="result",
        output_format="{result}",
        required_tools=["py_sandbox", "calc"],
    ),
    "B2-068": TaskContract(
        task_id="B2-068",
        steps=[
            ComputationStep("intermediate", "calc", "int"),
            ComputationStep("result", "py_sandbox", "int"),
        ],
        final_output="result",
        output_format="{result}",
        required_tools=["calc", "py_sandbox"],
    ),
    "B2-069": TaskContract(
        task_id="B2-069",
        steps=[ComputationStep("result", "calc", "int")],
        final_output="result",
        output_format="{result}",
        required_tools=["calc"],
    ),
    "B2-070": TaskContract(
        task_id="B2-070",
        steps=[
            ComputationStep("word", "str_ops", "upper"),
            ComputationStep("num", "calc", "int"),
        ],
        final_output="result",
        output_format="{word}-{num}",
        required_tools=["str_ops", "calc"],
    ),
    "B2-071": TaskContract(
        task_id="B2-071",
        steps=[
            ComputationStep("intermediate", "calc", "int"),
            ComputationStep("result", "py_sandbox", "int"),
        ],
        final_output="result",
        output_format="{result}",
        required_tools=["calc", "py_sandbox"],
    ),
    "B2-072": TaskContract(
        task_id="B2-072",
        steps=[
            ComputationStep("word", "str_ops", "upper"),
            ComputationStep("num", "calc", "int"),
            ComputationStep("result", "py_sandbox", "int"),
        ],
        final_output="result",
        output_format="{word}-{result}",
        required_tools=["str_ops", "calc", "py_sandbox"],
    ),
}'''

content = content[:end_idx] + "\n" + new_contracts + content[end_idx+2:]
open("gleppo/answer_binding.py", "w", encoding="utf-8").write(content)
print("Added B2-065 to B2-072 contracts")
