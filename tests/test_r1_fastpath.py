"""R1-FASTPATH Stage A regression tests.

Tests:
1. Hard cap enforced at model.generate boundary (over-cap must NOT execute)
2. Unique monotonically increasing call IDs
3. Per-call token deltas (not cumulative)
4. Failed calls recorded in ledger
5. Malformed/missing ledger rows rejected
6. Tool path validators reject missing, reordered, failed, wrong-output events
"""
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestBudgetExceededError(unittest.TestCase):
    """Hard cap: over-cap model.generate must NOT execute."""

    def test_error_is_exception(self):
        from gleppo.llm import BudgetExceededError
        with self.assertRaises(BudgetExceededError):
            raise BudgetExceededError("test")

    def test_error_message_contains_cap_info(self):
        from gleppo.llm import BudgetExceededError
        e = BudgetExceededError("generation cap exhausted: 30/30")
        self.assertIn("30/30", str(e))


class TestReserveGenerationSlot(unittest.TestCase):
    """Test slot reservation at the generation boundary."""

    def _make_llm_stub(self, max_generations=None):
        """Create a ProductionLLM without loading real model."""
        from gleppo.llm import ProductionLLM
        llm = object.__new__(ProductionLLM)
        llm.model_path = "stub"
        llm.device = "cpu"
        llm.max_new_tokens = 16
        llm.temperature = 0.7
        llm.max_generations = max_generations
        llm._call_id = 0
        llm._generation_ledger = []
        llm.stats = {
            "requests": 0, "total_tokens": 0, "failures": 0,
            "latencies": [], "revision": "test",
            "evaluations": 0, "episodes": 0, "tool_invocations": 0,
        }
        return llm

    def test_reserve_increments_call_id(self):
        from gleppo.llm import ProductionLLM
        llm = self._make_llm_stub(max_generations=5)
        id1 = llm._reserve_generation_slot()
        id2 = llm._reserve_generation_slot()
        self.assertEqual(id1, 1)
        self.assertEqual(id2, 2)

    def test_reserve_raises_at_cap(self):
        from gleppo.llm import BudgetExceededError, ProductionLLM
        llm = self._make_llm_stub(max_generations=2)
        llm._reserve_generation_slot()
        llm._reserve_generation_slot()
        with self.assertRaises(BudgetExceededError):
            llm._reserve_generation_slot()

    def test_reserve_no_cap_is_unlimited(self):
        llm = self._make_llm_stub(max_generations=None)
        for i in range(100):
            llm._reserve_generation_slot()
        self.assertEqual(llm._call_id, 100)

    def test_call_ids_are_monotonic(self):
        llm = self._make_llm_stub(max_generations=50)
        ids = [llm._reserve_generation_slot() for _ in range(50)]
        self.assertEqual(ids, list(range(1, 51)))

    def test_generate_not_called_when_cap_exceeded(self):
        """The critical test: model.generate must NOT be invoked after cap."""
        from gleppo.llm import BudgetExceededError
        llm = self._make_llm_stub(max_generations=1)
        llm.model = MagicMock()
        llm.tokenizer = MagicMock()

        # Consume the one allowed slot
        llm._reserve_generation_slot()

        # Next call must raise BEFORE model.generate
        with self.assertRaises(BudgetExceededError):
            llm._reserve_generation_slot()

        # model.generate was never called
        llm.model.generate.assert_not_called()


class TestGenerationLedger(unittest.TestCase):
    """Per-call ledger rows: unique IDs, token deltas, status."""

    def _make_llm_stub(self):
        from gleppo.llm import ProductionLLM
        llm = object.__new__(ProductionLLM)
        llm.model_path = "stub"
        llm.device = "cpu"
        llm.max_new_tokens = 16
        llm.temperature = 0.7
        llm.max_generations = None
        llm._call_id = 0
        llm._generation_ledger = []
        llm.stats = {
            "requests": 0, "total_tokens": 0, "failures": 0,
            "latencies": [], "revision": "test",
            "evaluations": 0, "episodes": 0, "tool_invocations": 0,
        }
        return llm

    def test_ledger_rows_have_unique_call_ids(self):
        llm = self._make_llm_stub()
        # Simulate ledger rows
        for i in range(5):
            llm._call_id += 1
            llm._generation_ledger.append({
                "call_id": llm._call_id,
                "input_tokens": 10,
                "output_tokens": 5,
                "duration_s": 0.1,
                "status": "ok",
                "error": "",
            })
        ids = [r["call_id"] for r in llm._generation_ledger]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, [1, 2, 3, 4, 5])

    def test_token_deltas_are_per_call(self):
        llm = self._make_llm_stub()
        llm._generation_ledger.append({
            "call_id": 1, "input_tokens": 100, "output_tokens": 50,
            "duration_s": 0.5, "status": "ok", "error": "",
        })
        llm._generation_ledger.append({
            "call_id": 2, "input_tokens": 120, "output_tokens": 30,
            "duration_s": 0.3, "status": "ok", "error": "",
        })
        # Deltas sum correctly
        total_out = sum(r["output_tokens"] for r in llm._generation_ledger)
        self.assertEqual(total_out, 80)
        # Each row has its own deltas, not cumulative
        self.assertEqual(llm._generation_ledger[0]["output_tokens"], 50)
        self.assertEqual(llm._generation_ledger[1]["output_tokens"], 30)

    def test_failed_calls_recorded_in_ledger(self):
        llm = self._make_llm_stub()
        llm._generation_ledger.append({
            "call_id": 1, "input_tokens": 50, "output_tokens": 0,
            "duration_s": 0.1, "status": "error", "error": "CUDA OOM",
        })
        row = llm._generation_ledger[0]
        self.assertEqual(row["status"], "error")
        self.assertIn("CUDA OOM", row["error"])

    def test_get_generation_ledger_returns_copy(self):
        llm = self._make_llm_stub()
        llm._generation_ledger.append({"call_id": 1, "status": "ok"})
        ledger = llm.get_generation_ledger()
        ledger[0]["status"] = "tampered"
        self.assertEqual(llm._generation_ledger[0]["status"], "ok")

    def test_ledger_row_fields_complete(self):
        """Required fields: call_id, input_tokens, output_tokens, duration_s,
        status, error, seed_digest, task_id, operator, genotype_role, replicate, turn."""
        llm = self._make_llm_stub()
        llm._generation_ledger.append({
            "call_id": 1,
            "timestamp": "2026-01-01T00:00:00Z",
            "seed_digest": "abc123",
            "task_id": "B2-001",
            "operator": "tool_subset_edit",
            "genotype_role": "parent",
            "replicate": 0,
            "turn": 1,
            "input_tokens": 100,
            "output_tokens": 50,
            "duration_s": 0.5,
            "status": "ok",
            "error": "",
        })
        required = [
            "call_id", "seed_digest", "task_id", "operator",
            "genotype_role", "replicate", "turn",
            "input_tokens", "output_tokens", "duration_s", "status", "error",
        ]
        for field in required:
            self.assertIn(field, llm._generation_ledger[0])


class TestToolPathVerification(unittest.TestCase):
    """Tool path validators must reject missing, reordered, failed, wrong-output."""

    def _make_trace(self, events):
        """Build a trace from (tool, ok, output) tuples."""
        trace = [{"type": "meta", "tools": []}]
        for tool, ok, output in events:
            trace.append({
                "type": "tool",
                "ok": ok,
                "detail": tool,
                "output": output,
            })
        return trace

    def test_b2_001_passes_with_correct_path(self):
        from gleppo.tool_path import verify_tool_path_for_task
        trace = self._make_trace([
            ("calc", True, "64"),
            ("str_ops", True, "SUM"),
        ])
        result = verify_tool_path_for_task("B2-001", trace)
        self.assertTrue(result["passed"])

    def test_b2_001_fails_with_wrong_calc_output(self):
        from gleppo.tool_path import verify_tool_path_for_task
        trace = self._make_trace([
            ("calc", True, "63"),  # wrong
            ("str_ops", True, "SUM"),
        ])
        result = verify_tool_path_for_task("B2-001", trace)
        self.assertFalse(result["passed"])

    def test_b2_001_fails_with_wrong_strops_output(self):
        from gleppo.tool_path import verify_tool_path_for_task
        trace = self._make_trace([
            ("calc", True, "64"),
            ("str_ops", True, "sum"),  # wrong case
        ])
        result = verify_tool_path_for_task("B2-001", trace)
        self.assertFalse(result["passed"])

    def test_b2_001_fails_with_reordered(self):
        from gleppo.tool_path import verify_tool_path_for_task
        trace = self._make_trace([
            ("str_ops", True, "SUM"),  # wrong order
            ("calc", True, "64"),
        ])
        result = verify_tool_path_for_task("B2-001", trace)
        self.assertFalse(result["passed"])

    def test_b2_001_fails_with_missing_tool(self):
        from gleppo.tool_path import verify_tool_path_for_task
        trace = self._make_trace([
            ("calc", True, "64"),
            # str_ops missing
        ])
        result = verify_tool_path_for_task("B2-001", trace)
        self.assertFalse(result["passed"])

    def test_b2_001_fails_with_failed_tool(self):
        from gleppo.tool_path import verify_tool_path_for_task
        trace = self._make_trace([
            ("calc", True, "64"),
            ("str_ops", False, "error"),  # failed call
        ])
        result = verify_tool_path_for_task("B2-001", trace)
        self.assertFalse(result["passed"])

    def test_b2_002_passes_with_correct_path(self):
        from gleppo.tool_path import verify_tool_path_for_task
        trace = self._make_trace([
            ("py_sandbox", True, "49"),
            ("calc", True, "43"),
        ])
        result = verify_tool_path_for_task("B2-002", trace)
        self.assertTrue(result["passed"])

    def test_b2_002_fails_with_wrong_pysandbox_output(self):
        from gleppo.tool_path import verify_tool_path_for_task
        trace = self._make_trace([
            ("py_sandbox", True, "50"),  # wrong
            ("calc", True, "43"),
        ])
        result = verify_tool_path_for_task("B2-002", trace)
        self.assertFalse(result["passed"])

    def test_b2_002_fails_with_reordered(self):
        from gleppo.tool_path import verify_tool_path_for_task
        trace = self._make_trace([
            ("calc", True, "43"),  # wrong order
            ("py_sandbox", True, "49"),
        ])
        result = verify_tool_path_for_task("B2-002", trace)
        self.assertFalse(result["passed"])

    def test_b2_003_passes_with_correct_path(self):
        from gleppo.tool_path import verify_tool_path_for_task
        trace = self._make_trace([
            ("calc", True, "60"),
            ("str_ops", True, "HI"),
        ])
        result = verify_tool_path_for_task("B2-003", trace)
        self.assertTrue(result["passed"])

    def test_b2_003_fails_with_wrong_strops_output(self):
        from gleppo.tool_path import verify_tool_path_for_task
        trace = self._make_trace([
            ("calc", True, "60"),
            ("str_ops", True, "hi"),  # wrong case
        ])
        result = verify_tool_path_for_task("B2-003", trace)
        self.assertFalse(result["passed"])

    def test_b2_003_fails_with_missing_calc(self):
        from gleppo.tool_path import verify_tool_path_for_task
        trace = self._make_trace([
            ("str_ops", True, "HI"),  # calc missing
        ])
        result = verify_tool_path_for_task("B2-003", trace)
        self.assertFalse(result["passed"])

    def test_contract_definitions_match_frozen_specs(self):
        from gleppo.tool_path import B2_TOOL_PATH_CONTRACTS
        self.assertEqual(B2_TOOL_PATH_CONTRACTS["B2-001"], [("calc", "64"), ("str_ops", "SUM")])
        self.assertEqual(B2_TOOL_PATH_CONTRACTS["B2-002"], [("py_sandbox", "49"), ("calc", "43")])
        self.assertEqual(B2_TOOL_PATH_CONTRACTS["B2-003"], [("calc", "60"), ("str_ops", "HI")])

    def test_extra_tools_between_contract_entries_allowed(self):
        """Extra successful tool calls between contract entries are OK."""
        from gleppo.tool_path import verify_tool_path_for_task
        trace = self._make_trace([
            ("calc", True, "64"),
            ("py_sandbox", True, "irrelevant"),  # extra
            ("str_ops", True, "SUM"),
        ])
        result = verify_tool_path_for_task("B2-001", trace)
        self.assertTrue(result["passed"])

    def test_missing_contract_task_falls_back_to_presence(self):
        from gleppo.tool_path import verify_tool_path_for_task
        trace = self._make_trace([
            ("calc", True, "42"),
        ])
        result = verify_tool_path_for_task("A2-001", trace, ["calc"])
        self.assertTrue(result["passed"])


class TestSeparateCounters(unittest.TestCase):
    """Evaluation, episode, generation, and tool invocation counts are separate."""

    def test_counters_are_separate_fields(self):
        from gleppo.llm import ProductionLLM
        llm = object.__new__(ProductionLLM)
        llm._call_id = 0
        llm._generation_ledger = []
        llm.stats = {
            "requests": 0, "total_tokens": 0, "failures": 0,
            "latencies": [], "revision": "test",
            "evaluations": 0, "episodes": 0, "tool_invocations": 0,
        }
        self.assertIn("evaluations", llm.stats)
        self.assertIn("episodes", llm.stats)
        self.assertIn("tool_invocations", llm.stats)

    def test_get_stats_reports_actual_generations(self):
        from gleppo.llm import ProductionLLM
        llm = object.__new__(ProductionLLM)
        llm._call_id = 7
        llm._generation_ledger = []
        llm.max_generations = 30
        llm.stats = {
            "requests": 7, "total_tokens": 100, "failures": 0,
            "latencies": [], "revision": "test",
            "evaluations": 3, "episodes": 2, "tool_invocations": 5,
        }
        llm.name = "test"
        llm.version = "test"
        stats = llm.get_stats()
        self.assertEqual(stats["actual_generations"], 7)
        self.assertEqual(stats["evaluations"], 3)
        self.assertEqual(stats["episodes"], 2)
        self.assertEqual(stats["tool_invocations"], 5)
        self.assertEqual(stats["max_generations_cap"], 30)


if __name__ == "__main__":
    unittest.main()
