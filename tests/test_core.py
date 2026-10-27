"""Unit tests: schema, serialization, hashes, operators, interpreter, evaluator isolation, features, manifest, reward, reproducibility."""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gleppo.genotype import (  # noqa: E402
    Genotype, Step, behavior_hash, canonical_serialize, is_valid, make_valid_genotype, validate_genotype,
)
from gleppo.operators import OPERATOR_NAMES, apply_operator  # noqa: E402
from gleppo.tools import run_tool  # noqa: E402
from gleppo.llm import StubLLM  # noqa: E402
from gleppo.interpreter import Interpreter  # noqa: E402
from gleppo.tasks import build_task, generate_split, attach_checker, SPLIT_SPEC  # noqa: E402
from gleppo.evaluator import Evaluator  # noqa: E402
from gleppo.features import STATE_DIM, FEATURE_NAMES, state_vector, empty_state  # noqa: E402
from gleppo.manifest import build_manifests, verify_manifest, load_split, FamilyCGuard  # noqa: E402
from gleppo.evolution import EvolutionConfig, evolve, evolve_generation, Individual  # noqa: E402


class TestGenotype(unittest.TestCase):
    def test_valid_default(self):
        g = make_valid_genotype()
        self.assertTrue(is_valid(g), validate_genotype(g))

    def test_canonical_serialize_stable(self):
        g = make_valid_genotype()
        s1 = canonical_serialize(g)
        s2 = canonical_serialize(g)
        self.assertEqual(s1, s2)

    def test_hash_excludes_meta(self):
        g = make_valid_genotype()
        h1 = behavior_hash(g)
        g.meta["note"] = "abc"
        self.assertEqual(h1, behavior_hash(g))

    def test_hash_changes_with_prompt(self):
        g1 = make_valid_genotype()
        g2 = make_valid_genotype()
        g2.system_prompt = g2.system_prompt + " Extra."
        self.assertNotEqual(behavior_hash(g1), behavior_hash(g2))

    def test_invalid_tool_rejected(self):
        g = make_valid_genotype()
        g.tools = ["calc", "nope"]
        self.assertFalse(is_valid(g))

    def test_invalid_missing_finalize(self):
        g = make_valid_genotype()
        g.workflow = [Step(type="llm", prompt_slot="a"), Step(type="tool", tool="calc")]
        self.assertFalse(is_valid(g))


class TestTools(unittest.TestCase):
    def test_calc(self):
        ok, out = run_tool("calc", "3*7+2")
        self.assertTrue(ok)
        self.assertEqual(out, "23")

    def test_calc_rejects_names(self):
        ok, _ = run_tool("calc", "__import__('os')")
        self.assertFalse(ok)

    def test_str_ops(self):
        ok, out = run_tool("str_ops", "upper|ab")
        self.assertTrue(ok)
        self.assertEqual(out, "AB")

    def test_py_sandbox_ok(self):
        ok, out = run_tool("py_sandbox", "result = 2 + 3\n")
        self.assertTrue(ok)
        self.assertEqual(out, "5")

    def test_py_sandbox_blocks_import(self):
        ok, _ = run_tool("py_sandbox", "import os\n")
        self.assertFalse(ok)


class TestOperators(unittest.TestCase):
    def setUp(self):
        self.parent = make_valid_genotype()
        self.parent.meta["parent_id"] = "p1"

    def test_all_operators_produce_valid_or_flagged(self):
        for name in OPERATOR_NAMES:
            child, ok, errs = apply_operator(name, self.parent, {"gen": 1, "failure_category": "wrong_answer"})
            self.assertIsInstance(child, Genotype)
            if not ok:
                self.assertTrue(errs)

    def test_prompt_local_edit_changes_hash(self):
        child, ok, _ = apply_operator("prompt_local_edit", self.parent, {})
        self.assertTrue(ok)
        self.assertNotEqual(behavior_hash(self.parent), behavior_hash(child))

    def test_prompt_critique_uses_failure(self):
        c1, _, _ = apply_operator("prompt_critique_rewrite", self.parent, {"failure_category": "tool_error"})
        c2, _, _ = apply_operator("prompt_critique_rewrite", self.parent, {"failure_category": "format_error"})
        self.assertNotEqual(behavior_hash(c1), behavior_hash(c2))

    def test_tool_subset_edit_changes_tools(self):
        # gen=1 prefers add; parent lacks py_sandbox so a valid child must gain it
        child, ok, errs = apply_operator("tool_subset_edit", self.parent, {"gen": 1})
        self.assertTrue(ok, errs)
        self.assertNotEqual(sorted(self.parent.tools), sorted(child.tools))

    def test_workflow_edit_changes_hash(self):
        child, ok, _ = apply_operator("workflow_step_edit", self.parent, {"gen": 2})
        self.assertTrue(ok)
        self.assertNotEqual(behavior_hash(self.parent), behavior_hash(child))

    def test_crossover_uses_mate(self):
        mate = make_valid_genotype()
        mate.system_prompt = "Convert output and format carefully. Final answer: {{answer}}"
        mate.tools = ["py_sandbox"]
        child, ok, _ = apply_operator("crossover", self.parent, {"mate": mate, "gen": 3})
        self.assertTrue(ok)
        self.assertNotEqual(behavior_hash(self.parent), behavior_hash(child))


class TestInterpreterAndEvaluator(unittest.TestCase):
    def test_family_a_success_with_strategy(self):
        g = make_valid_genotype()
        task = attach_checker(build_task("A-0001", "A", 1))
        ev = Evaluator(n_eval=2)
        res = ev.evaluate(g, task, allow_family=("A", "B"))
        self.assertGreater(res.success, 0.0)

    def test_label_isolation_observe_view(self):
        g = make_valid_genotype()
        task = attach_checker(build_task("A-0001", "A", 1))
        ev = Evaluator(n_eval=1)
        res = ev.evaluate(g, task)
        obs = ev.observe(res)
        self.assertNotIn("gold", obs)
        self.assertNotIn("gold_check", obs)
        self.assertEqual(set(obs), {"success", "failure_category", "turns", "tool_calls"})

    def test_family_c_blocked(self):
        g = make_valid_genotype()
        task = attach_checker(build_task("C-0001", "C", 1))
        ev = Evaluator(n_eval=1)
        with self.assertRaises(PermissionError):
            ev.evaluate(g, task, allow_family=("A", "B"))

    def test_reproducible(self):
        g = make_valid_genotype()
        task = attach_checker(build_task("A-0002", "A", 2))
        e1 = Evaluator(n_eval=2).evaluate(g, task)
        e2 = Evaluator(n_eval=2).evaluate(g, task)
        self.assertEqual(e1.success, e2.success)
        self.assertEqual(e1.failure_category, e2.failure_category)


class TestFeatures(unittest.TestCase):
    def test_shape_and_names(self):
        self.assertEqual(len(FEATURE_NAMES), STATE_DIM)
        vec = state_vector(
            best_success=0.5, mean_success=0.2,
            fail_rates={"wrong_answer": 0.5}, valid_rate=1.0,
            mean_turns=4, mean_tool_calls=2, parent_last_delta=0.1,
            recent_eval_coverage=1.0,
            tool_sets=[["calc"], ["calc", "str_ops"]],
            workflows=[["llm", "finalize"], ["llm", "tool", "finalize"]],
            prompts=["compute step by step final answer: {{answer}}"] * 2,
            op_usage={"prompt_local_edit": 2}, op_mean_delta={"prompt_local_edit": 0.1},
            age_best=1, pop_size_norm=1.0, gen_t=3, T=15, stagnation=1,
            best_delta_since_start=0.2, improve_last_3_frac=0.5,
            recency_gaps=[1, 3], offspring_valid_last=1.0,
        )
        self.assertEqual(len(vec), STATE_DIM)
        self.assertTrue(all(isinstance(x, float) for x in vec))

    def test_unobserved_operator_zero(self):
        vec = state_vector(
            best_success=0, mean_success=0, fail_rates={}, valid_rate=1,
            mean_turns=0, mean_tool_calls=0, parent_last_delta=0, recent_eval_coverage=1,
            tool_sets=[["calc"]], workflows=[["llm"]], prompts=["x"],
            op_usage={}, op_mean_delta={},
            age_best=0, pop_size_norm=1, gen_t=0, T=15, stagnation=0,
            best_delta_since_start=0, improve_last_3_frac=0,
            recency_gaps=[], offspring_valid_last=1,
        )
        self.assertEqual(vec[16], 0.0)  # op_mean_delta_1
        self.assertEqual(vec[21], 1.0)  # all unobserved

    def test_empty_state(self):
        self.assertEqual(len(empty_state()), STATE_DIM)


class TestManifest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_build_and_verify(self):
        build_manifests(self.dir)
        errs = verify_manifest(self.dir)
        self.assertEqual(errs, [])

    def test_tamper_detected(self):
        build_manifests(self.dir)
        path = os.path.join(self.dir, "train_A.jsonl")
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n")
        errs = verify_manifest(self.dir)
        self.assertTrue(any("sha256" in e or "line count" in e for e in errs))

    def test_c_guard(self):
        g = FamilyCGuard(enabled=True)
        t = build_task("C-1", "C", 0)
        with self.assertRaises(PermissionError):
            g.check_task(t)


class TestEvolution(unittest.TestCase):
    def test_reward_arithmetic_and_invalid_accounting(self):
        cfg = EvolutionConfig(mu=4, lam=2, T=2, n_eval=1)
        task = attach_checker(build_task("A-0003", "A", 3))
        ev = Evaluator(n_eval=1)

        class DummyInd(Individual):
            pass

        pop = [
            Individual(geno=make_valid_genotype(), success=0.5, evaluated=True, behavior_hash="a"),
            Individual(geno=make_valid_genotype(), success=0.2, evaluated=True, behavior_hash="b"),
        ]
        import random
        rng = random.Random(0)
        survivors, log = evolve_generation(pop, "prompt_local_edit", cfg, ev, task, rng, 0, {"failure_category": ""})
        self.assertEqual(len(survivors), cfg.mu)
        self.assertGreaterEqual(log.valid_count + log.invalid_count, 1)
        self.assertGreaterEqual(log.reward, -0.5)
        self.assertLessEqual(log.reward, 1.0)

    def test_episode_reproducible(self):
        cfg = EvolutionConfig(mu=4, lam=2, T=3, n_eval=1)

        def sched(t, pop, hist):
            return OPERATOR_NAMES[t % 5]

        task = attach_checker(build_task("A-0004", "A", 4))
        e1 = evolve(sched, cfg, Evaluator(n_eval=1), task, seed=1)
        e2 = evolve(sched, cfg, Evaluator(n_eval=1), task, seed=1)
        self.assertEqual(e1.best_success, e2.best_success)
        self.assertEqual(len(e1.logs), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
