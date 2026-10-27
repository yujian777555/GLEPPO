"""Regression tests for R1-R7 plus core schema/operator/manifest tests."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gleppo.genotype import (
    Genotype, Step, behavior_hash, canonical_serialize, is_valid, make_valid_genotype, validate_genotype,
)
from gleppo.operators import OPERATOR_NAMES, apply_operator
from gleppo.tools import run_tool
from gleppo.llm import StubLLM
from gleppo.interpreter import Interpreter
from gleppo.tasks import (
    build_task, generate_split, attach_checker, SPLIT_SPEC,
    TRAIN_TEMPLATES_A, VAL_TEMPLATES_A, TRAIN_TEMPLATES_B, VAL_TEMPLATES_B,
    _check_family_a, _check_family_b, _check_family_c,
)
from gleppo.evaluator import Evaluator
from gleppo.features import STATE_DIM, FEATURE_NAMES, state_vector, empty_state, jaccard_distance
from gleppo.manifest import build_manifests, verify_manifest, load_split, FamilyCGuard
from gleppo.evolution import EvolutionConfig, evolve, evolve_generation, Individual, stable_seed
from gleppo.reward import generation_reward
from gleppo.pc1 import zero_cost_protocol_check, crn_seed

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# ===== R1: evaluator correctness =====
class TestR1EvaluatorCorrectness(unittest.TestCase):
    def test_family_a_correct_arithmetic_passes(self):
        check = _check_family_a("42")
        g = make_valid_genotype()
        self.assertTrue(check("Final answer: 42", g))
        self.assertTrue(check("Final answer: 42.0", g))

    def test_family_a_wrong_arithmetic_fails_despite_keywords(self):
        check = _check_family_a("42")
        g = make_valid_genotype()  # has compute + calc tools
        self.assertFalse(check("Final answer: 41", g))
        self.assertFalse(check("Final answer: Xabc", g))
        self.assertFalse(check("", g))

    def test_family_b_correct_answer_passes(self):
        check = _check_family_b("27-AB12")
        g = make_valid_genotype()
        self.assertTrue(check("Final answer: 27-AB12", g))
        self.assertTrue(check("Final answer: 27-ab12", g))  # case-insensitive

    def test_family_b_wrong_string_fails(self):
        check = _check_family_b("27-AB12")
        g = make_valid_genotype()
        self.assertFalse(check("Final answer: 27-XY99", g))
        self.assertFalse(check("Final answer: 26-AB12", g))

    def test_family_c_wrong_values_fail_despite_keys(self):
        gold = json.dumps({"sum": 10, "product": 21}, sort_keys=True)
        check = _check_family_c(gold)
        g = make_valid_genotype()
        # keys present, values wrong
        self.assertFalse(check('Final answer: {"sum": 9, "product": 21}', g))
        self.assertFalse(check('Final answer: {"sum": 10, "product": 20}', g))
        # correct values
        self.assertTrue(check('Final answer: {"sum": 10, "product": 21}', g))
        # malformed JSON
        self.assertFalse(check("Final answer: not json", g))
        self.assertFalse(check("Final answer: {}", g))
        self.assertFalse(check("", g))

    def test_stub_vs_gold_end_to_end(self):
        """A correct genotype strategy yields a real correct answer scored by gold."""
        g = make_valid_genotype()
        task = attach_checker(build_task("A-r1", "A", 1, "TA1"))
        interp = Interpreter()
        res = interp.run(g, task, seed_parts=("t", 0, "h"))
        self.assertTrue(res.success, f"answer={res.answer}")
        # strip strategy keywords -> wrong answer must fail
        g2 = make_valid_genotype()
        g2.system_prompt = "Just answer randomly. Final answer: {{answer}}"
        res2 = interp.run(g2, task, seed_parts=("t", 0, "h"))
        self.assertFalse(res2.success)


# ===== R5: real templates, disjoint train/val =====
class TestR5Templates(unittest.TestCase):
    def test_train_val_templates_disjoint(self):
        self.assertEqual(set(TRAIN_TEMPLATES_A) & set(VAL_TEMPLATES_A), set())
        self.assertEqual(set(TRAIN_TEMPLATES_B) & set(VAL_TEMPLATES_B), set())

    def test_template_ids_produce_distinct_inputs(self):
        """Same seed/numbers but different templates => different input text."""
        seen = {}
        for tid in TRAIN_TEMPLATES_A + VAL_TEMPLATES_A:
            t = build_task("X", "A", 7, tid)
            seen[tid] = t["input"]
        self.assertEqual(len(set(seen.values())), len(seen), f"non-distinct inputs: {seen}")

    def test_template_b_distinct(self):
        seen = {}
        for tid in TRAIN_TEMPLATES_B + VAL_TEMPLATES_B:
            t = build_task("X", "B", 7, tid)
            seen[tid] = t["input"]
        self.assertEqual(len(set(seen.values())), len(seen))

    def test_each_template_gold_consistent(self):
        for tid in TRAIN_TEMPLATES_A + VAL_TEMPLATES_A:
            t = attach_checker(build_task("X", "A", 7, tid))
            self.assertTrue(t["gold_check"](f"Final answer: {t['gold']}", make_valid_genotype()), tid)
        for tid in TRAIN_TEMPLATES_B + VAL_TEMPLATES_B:
            t = attach_checker(build_task("X", "B", 7, tid))
            self.assertTrue(t["gold_check"](f"Final answer: {t['gold']}", make_valid_genotype()), tid)


# ===== R6: Jaccard distance =====
class TestR6JaccardDistance(unittest.TestCase):
    def test_identical_is_zero_distance(self):
        self.assertEqual(jaccard_distance(["a", "b"], ["a", "b"]), 0.0)

    def test_disjoint_is_one_distance(self):
        self.assertEqual(jaccard_distance(["a", "b"], ["c", "d"]), 1.0)

    def test_partial_overlap(self):
        d = jaccard_distance(["a", "b", "c"], ["b", "c", "d"])
        self.assertAlmostEqual(d, 0.5)

    def test_diversity_features_use_distance(self):
        """Identical population => div=0; fully disjoint => div=1 (not similarity)."""
        same = state_vector(
            best_success=0, mean_success=0, fail_rates={}, valid_rate=1,
            mean_turns=0, mean_tool_calls=0, parent_last_delta=0, recent_eval_coverage=1,
            tool_sets=[["calc"], ["calc"]], workflows=[["llm", "finalize"], ["llm", "finalize"]],
            prompts=["same prompt here", "same prompt here"],
            op_usage={}, op_mean_delta={},
            age_best=0, pop_size_norm=1, gen_t=0, T=15, stagnation=0,
            best_delta_since_start=0, improve_last_3_frac=0,
            recency_gaps=[], offspring_valid_last=1,
        )
        diff = state_vector(
            best_success=0, mean_success=0, fail_rates={}, valid_rate=1,
            mean_turns=0, mean_tool_calls=0, parent_last_delta=0, recent_eval_coverage=1,
            tool_sets=[["calc"], ["py_sandbox"]], workflows=[["llm", "finalize"], ["tool", "branch"]],
            prompts=["aaaa", "zzzz"],
            op_usage={}, op_mean_delta={},
            age_best=0, pop_size_norm=1, gen_t=0, T=15, stagnation=0,
            best_delta_since_start=0, improve_last_3_frac=0,
            recency_gaps=[], offspring_valid_last=1,
        )
        self.assertEqual(same[12], 0.0)   # div_tools identical -> 0
        self.assertEqual(diff[12], 1.0)   # div_tools disjoint -> 1


# ===== R4: stable seeds, cache, CRN =====
class TestR4SeedsCache(unittest.TestCase):
    def test_stable_seed_process_independent(self):
        """Subprocess test with different PYTHONHASHSEED values."""
        code = (
            "import sys; sys.path.insert(0, r'%s'); "
            "from gleppo.evolution import stable_seed; "
            "print(stable_seed(20261026, 0, 'A-0001', 'ep1'))" % REPO
        )
        out = set()
        for hs in ("0", "1", "42"):
            r = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True, text=True, env={**os.environ, "PYTHONHASHSEED": hs},
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            out.add(r.stdout.strip())
        self.assertEqual(len(out), 1, f"seed varies across PYTHONHASHSEED: {out}")

    def test_cache_key_includes_replicate_and_runtime(self):
        ev1 = Evaluator(n_eval=1, runtime_revision="stub-v1.1")
        ev2 = Evaluator(n_eval=1, runtime_revision="stub-v1.2")
        g = make_valid_genotype()
        task = attach_checker(build_task("A-r4", "A", 1, "TA1"))
        r_a = ev1.evaluate(g, task, replicate_id=0)
        self.assertFalse(r_a.from_cache)
        # same replicate -> cache hit
        r_b = ev1.evaluate(g, task, replicate_id=0)
        self.assertTrue(r_b.from_cache)
        # different replicate -> NOT cache hit
        r_c = ev1.evaluate(g, task, replicate_id=1)
        self.assertFalse(r_c.from_cache)
        # different runtime revision -> not cache hit
        r_d = ev2.evaluate(g, task, replicate_id=0)
        self.assertFalse(r_d.from_cache)

    def test_cache_hits_not_counted_as_samples(self):
        ev = Evaluator(n_eval=1)
        g = make_valid_genotype()
        task = attach_checker(build_task("A-r4b", "A", 2, "TA1"))
        ev.evaluate(g, task, replicate_id=0)
        n = ev.independent_samples
        ev.evaluate(g, task, replicate_id=0)  # cache hit
        self.assertEqual(ev.independent_samples, n, "cache hit must not add sample")
        self.assertGreaterEqual(ev.cache_hits, 1)

    def test_crn_seed_shared_across_actions(self):
        self.assertEqual(crn_seed("s1", 0), crn_seed("s1", 0))
        self.assertNotEqual(crn_seed("s1", 0), crn_seed("s1", 1))

    def test_replicate_seeds_distinct(self):
        self.assertNotEqual(crn_seed("s", 0), crn_seed("s", 1))


# ===== R3: reward identity =====
class TestR3RewardIdentity(unittest.TestCase):
    def test_frozen_reward_clipping(self):
        self.assertEqual(generation_reward(10, 0, 10, 0, 1), 1.0)
        self.assertEqual(generation_reward(0, 10, 0, 10, 0), -0.5)

    def test_frozen_reward_terms(self):
        r = generation_reward(0.5, 0.0, 0.4, 0.0, 1.0)
        self.assertAlmostEqual(r, 0.5 + 0.1 * 1.0 + 0.25 * 0.4)

    def test_pc1_zero_cost_protocol(self):
        report = zero_cost_protocol_check()
        self.assertTrue(report["all_pass"], json.dumps(report["checks"], indent=2))
        self.assertTrue(report["checks"]["q_uses_same_first_term"]["ok"])
        self.assertTrue(report["checks"]["q_uses_same_first_term"]["ok"])


# ===== R7 / R2: budget =====
class TestR7Budget(unittest.TestCase):
    def test_planned_slots_within_cap(self):
        report = zero_cost_protocol_check()
        self.assertTrue(report["checks"]["planned_within_hard_cap"]["ok"], report["budget"])
        self.assertGreaterEqual(report["budget"]["total_planned"], 45000)

    def test_states_at_least_100(self):
        report = zero_cost_protocol_check()
        self.assertTrue(report["checks"]["states_at_least_100"]["ok"])


# ===== Core schema / operators / tools / interpreter =====
class TestGenotype(unittest.TestCase):
    def test_valid_default(self):
        self.assertTrue(is_valid(make_valid_genotype()), validate_genotype(make_valid_genotype()))

    def test_canonical_serialize_stable(self):
        g = make_valid_genotype()
        self.assertEqual(canonical_serialize(g), canonical_serialize(g))

    def test_hash_excludes_meta(self):
        g = make_valid_genotype()
        h1 = behavior_hash(g)
        g.meta["note"] = "abc"
        self.assertEqual(h1, behavior_hash(g))

    def test_invalid_tool_rejected(self):
        g = make_valid_genotype()
        g.tools = ["calc", "nope"]
        self.assertFalse(is_valid(g))


class TestTools(unittest.TestCase):
    def test_calc(self):
        ok, out = run_tool("calc", "3*7+2")
        self.assertTrue(ok)
        self.assertEqual(out, "23")

    def test_calc_rejects_names(self):
        self.assertFalse(run_tool("calc", "__import__('os')")[0])

    def test_py_sandbox(self):
        self.assertEqual(run_tool("py_sandbox", "result = 2 + 3\n"), (True, "5"))
        self.assertFalse(run_tool("py_sandbox", "import os\n")[0])


class TestOperators(unittest.TestCase):
    def setUp(self):
        self.parent = make_valid_genotype()
        self.parent.meta["parent_id"] = "p1"

    def test_all_operators(self):
        for name in OPERATOR_NAMES:
            child, ok, errs = apply_operator(name, self.parent, {"gen": 1, "failure_category": "wrong_answer"})
            self.assertIsInstance(child, Genotype)

    def test_prompt_local_edit_changes_hash(self):
        child, ok, _ = apply_operator("prompt_local_edit", self.parent, {})
        self.assertTrue(ok)
        self.assertNotEqual(behavior_hash(self.parent), behavior_hash(child))

    def test_crossover_uses_mate(self):
        mate = make_valid_genotype()
        mate.system_prompt = "Convert output and format carefully. Final answer: {{answer}}"
        child, ok, _ = apply_operator("crossover", self.parent, {"mate": mate, "gen": 3})
        self.assertTrue(ok)
        self.assertNotEqual(behavior_hash(self.parent), behavior_hash(child))


class TestManifest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_build_verify_and_template_disjoint(self):
        digests = build_manifests(self.dir)
        self.assertEqual(verify_manifest(self.dir), [])
        self.assertEqual(len(digests), 5)
        # train/val templates disjoint in the frozen manifest
        train_templates = set()
        val_templates = set()
        with open(os.path.join(self.dir, "manifest.json"), encoding="utf-8") as f:
            manifest = json.load(f)
        for name, meta in manifest["splits"].items():
            if name.startswith("train"):
                train_templates.update(meta["templates"])
            if name.startswith("val"):
                val_templates.update(meta["templates"])
        self.assertEqual(train_templates & val_templates, set())

    def test_c_guard(self):
        g = FamilyCGuard(enabled=True)
        with self.assertRaises(PermissionError):
            g.check_task(build_task("C-1", "C", 0, "TC1"))


class TestEvolution(unittest.TestCase):
    def test_episode_reproducible_and_accounting(self):
        cfg = EvolutionConfig(mu=4, lam=2, T=3, n_eval=1)

        def sched(t, pop, hist):
            return OPERATOR_NAMES[t % 5]

        task = attach_checker(build_task("A-0004", "A", 4, "TA1"))
        e1 = evolve(sched, cfg, Evaluator(n_eval=1), task, seed=1)
        e2 = evolve(sched, cfg, Evaluator(n_eval=1), task, seed=1)
        self.assertEqual(e1.best_success, e2.best_success)
        # R7 accounting present
        self.assertGreater(e1.planned_slots, 0)
        self.assertGreater(e1.actual_ctx + e1.cache_hits, 0)
        self.assertEqual(len(e1.logs), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
