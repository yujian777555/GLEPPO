"""R2: Tool-path repair regression tests.

Tests:
1. Quoted uppercase extraction: B2-001 'sum'->upper|sum, B2-003 'hi'->upper|hi
2. Explicit command syntax remains supported
3. Missing/ambiguous string operation raises ValueError (no arithmetic fallback)
4. B2-002 calc extraction chooses 49-6, not 14*3+7
5. B2-001/B2-003 still select their intended arithmetic expression
6. Task-compatible reference workflows match frozen B2 contracts
"""
import unittest

from gleppo.interpreter import Interpreter
from gleppo.genotype import make_task_compatible_reference, validate_genotype


class TestStropsQuotedExtraction(unittest.TestCase):
    """Defect A: parse quoted natural-language string transforms."""

    def setUp(self):
        self.interp = Interpreter()

    def test_b2_001_sum_uppercase(self):
        task = {"input": "Compute 25*3-11 using the calc tool, then transform the word 'sum' to uppercase using str_ops. Report as SUM-STRING."}
        result = self.interp._extract_strops_payload("", task)
        self.assertEqual(result, "upper|sum")

    def test_b2_003_hi_uppercase(self):
        task = {"input": "Compute 8*8-4 using calc, then transform 'hi' to uppercase using str_ops. Report as NUMBER-STRING."}
        result = self.interp._extract_strops_payload("", task)
        self.assertEqual(result, "upper|hi")

    def test_transform_word_x_to_uppercase(self):
        result = self.interp._extract_strops_payload(
            "transform the word 'hello' to uppercase", {}
        )
        self.assertEqual(result, "upper|hello")

    def test_make_x_uppercase(self):
        result = self.interp._extract_strops_payload(
            "make 'test' uppercase", {}
        )
        self.assertEqual(result, "upper|test")

    def test_convert_x_to_lowercase(self):
        result = self.interp._extract_strops_payload(
            "convert 'ABC' to lowercase", {}
        )
        self.assertEqual(result, "lower|ABC")

    def test_x_reverse(self):
        result = self.interp._extract_strops_payload(
            "transform 'abc' to reverse", {}
        )
        self.assertEqual(result, "reverse|abc")

    def test_llm_output_takes_priority(self):
        task = {"input": "transform 'sum' to uppercase"}
        result = self.interp._extract_strops_payload("upper|override", task)
        self.assertEqual(result, "upper|override")

    def test_task_input_fallback_when_llm_empty(self):
        task = {"input": "transform 'sum' to uppercase using str_ops"}
        result = self.interp._extract_strops_payload("", task)
        self.assertEqual(result, "upper|sum")


class TestStropsExplicitSyntax(unittest.TestCase):
    """Explicit command syntax remains supported."""

    def setUp(self):
        self.interp = Interpreter()

    def test_explicit_upper(self):
        result = self.interp._extract_strops_payload("upper|abc", {})
        self.assertEqual(result, "upper|abc")

    def test_explicit_lower(self):
        result = self.interp._extract_strops_payload("lower|ABC", {})
        self.assertEqual(result, "lower|ABC")

    def test_explicit_reverse(self):
        result = self.interp._extract_strops_payload("reverse|hello", {})
        self.assertEqual(result, "reverse|hello")

    def test_explicit_colon_separator(self):
        result = self.interp._extract_strops_payload("upper:abc", {})
        self.assertEqual(result, "upper|abc")


class TestStropsFailClosed(unittest.TestCase):
    """Missing/ambiguous string operation raises ValueError, no arithmetic fallback."""

    def setUp(self):
        self.interp = Interpreter()

    def test_no_string_operation_raises(self):
        with self.assertRaises(ValueError):
            self.interp._extract_strops_payload("just some text", {"input": "no string op here"})

    def test_arithmetic_not_fallback(self):
        """Must NOT return '25*3-11' as a str_ops payload."""
        with self.assertRaises(ValueError):
            self.interp._extract_strops_payload("25*3-11", {"input": "25*3-11"})

    def test_empty_inputs_raise(self):
        with self.assertRaises(ValueError):
            self.interp._extract_strops_payload("", {"input": ""})

    def test_b2_002_no_string_transform_raises(self):
        """B2-002 has no string transform; str_ops should fail closed."""
        task = {"input": "Use py_sandbox to compute result = 14*3+7. Then use calc to compute 49-6. Report the final result."}
        with self.assertRaises(ValueError):
            self.interp._extract_strops_payload("", task)


class TestCalcToolDirected(unittest.TestCase):
    """B2-002 calc extraction chooses 49-6, not 14*3+7."""

    def setUp(self):
        self.interp = Interpreter()

    def test_b2_002_chooses_49_minus_6(self):
        task = {"input": "Use py_sandbox to compute result = 14*3+7. Then use calc to compute 49-6. Report the final result."}
        result = self.interp._extract_calc_payload("", task)
        self.assertEqual(result, "49-6")

    def test_b2_001_chooses_first_expr(self):
        task = {"input": "Compute 25*3-11 using the calc tool, then transform the word 'sum' to uppercase using str_ops. Report as SUM-STRING."}
        result = self.interp._extract_calc_payload("", task)
        self.assertEqual(result, "25*3-11")

    def test_b2_003_chooses_first_expr(self):
        task = {"input": "Compute 8*8-4 using calc, then transform 'hi' to uppercase using str_ops. Report as NUMBER-STRING."}
        result = self.interp._extract_calc_payload("", task)
        self.assertEqual(result, "8*8-4")

    def test_tool_directed_in_llm_output(self):
        result = self.interp._extract_calc_payload("Then use calc to compute 49-6.", {})
        self.assertEqual(result, "49-6")

    def test_explicit_calc_colon(self):
        result = self.interp._extract_calc_payload("calc: 3*4", {})
        self.assertEqual(result, "3*4")

    def test_fallback_to_first_expr(self):
        result = self.interp._extract_calc_payload("some text 10+5 more", {})
        self.assertEqual(result, "10+5")


class TestTaskCompatibleReferences(unittest.TestCase):
    """Task-compatible reference workflows match frozen B2 contracts."""

    def test_b2_001_tools_and_workflow(self):
        g = make_task_compatible_reference("B2-001")
        self.assertEqual(sorted(g.tools), ["calc", "str_ops"])
        tool_steps = [s for s in g.workflow if s.type == "tool"]
        tool_names = [s.tool for s in tool_steps]
        self.assertEqual(tool_names, ["calc", "str_ops"])

    def test_b2_002_tools_and_workflow(self):
        g = make_task_compatible_reference("B2-002")
        self.assertEqual(sorted(g.tools), ["calc", "py_sandbox"])
        tool_steps = [s for s in g.workflow if s.type == "tool"]
        tool_names = [s.tool for s in tool_steps]
        self.assertEqual(tool_names, ["py_sandbox", "calc"])

    def test_b2_003_tools_and_workflow(self):
        g = make_task_compatible_reference("B2-003")
        self.assertEqual(sorted(g.tools), ["calc", "str_ops"])
        tool_steps = [s for s in g.workflow if s.type == "tool"]
        tool_names = [s.tool for s in tool_steps]
        self.assertEqual(tool_names, ["calc", "str_ops"])

    def test_references_are_valid_genotypes(self):
        for tid in ["B2-001", "B2-002", "B2-003"]:
            g = make_task_compatible_reference(tid)
            errors = validate_genotype(g)
            self.assertEqual(errors, [], f"{tid}: {errors}")

    def test_references_have_llm_step(self):
        """Each reference must keep a model turn in its workflow."""
        for tid in ["B2-001", "B2-002", "B2-003"]:
            g = make_task_compatible_reference(tid)
            has_llm = any(s.type == "llm" for s in g.workflow)
            self.assertTrue(has_llm, f"{tid}: missing llm step")

    def test_reference_label(self):
        g = make_task_compatible_reference("B2-001")
        self.assertEqual(g.meta.get("label"), "task_compatible_reference")

    def test_unknown_task_raises(self):
        with self.assertRaises(ValueError):
            make_task_compatible_reference("UNKNOWN-999")

    def test_tool_steps_before_finalize(self):
        """All tool steps must come before finalize."""
        for tid in ["B2-001", "B2-002", "B2-003"]:
            g = make_task_compatible_reference(tid)
            finalize_idx = next(i for i, s in enumerate(g.workflow) if s.type == "finalize")
            for i, s in enumerate(g.workflow):
                if s.type == "tool":
                    self.assertLess(i, finalize_idx, f"{tid}: tool step {i} after finalize")


if __name__ == "__main__":
    unittest.main()
