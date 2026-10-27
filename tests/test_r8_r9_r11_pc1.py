"""Regression tests for R8 (CRN end-to-end), R9 (CTX/cache accounting), R11 (StubLLM templates),
and PC1 runner synthetic-only tests. No PC1 execution, no Family C execution."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gleppo.genotype import make_valid_genotype, behavior_hash
from gleppo.interpreter import Interpreter
from gleppo.evaluator import Evaluator, EVALUATOR_VERSION
from gleppo.evolution import EvolutionConfig, evolve, evolve_generation, stable_seed
from gleppo.operators import OPERATOR_NAMES
from gleppo.tasks import (
    build_task, attach_checker, solve_input,
    TRAIN_TEMPLATES_A, VAL_TEMPLATES_A, TRAIN_TEMPLATES_B, VAL_TEMPLATES_B,
)
from gleppo.pc1 import (
    StateActionRecord, compute_r_hat, compute_q_hat, run_pc1_analysis,
    zero_cost_protocol_check, HARD_CAP_SLOTS, N_ACTIONS, ROLE_Q, ROLE_EXTRA,
)

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# ===== R8: instrumented interpreter records seed_parts =====
class InstrumentedInterpreter(Interpreter):
    """Records every seed_parts passed to run()."""

    def __init__(self):
        super().__init__()
        self.seed_log = []

    def run(self, g, task, seed_parts=None):
        self.seed_log.append(tuple(seed_parts))
        return super().run(g, task, seed_parts=seed_parts)


class TestR8CRNEndToEnd(unittest.TestCase):
    def setUp(self):
        self.interp = InstrumentedInterpreter()
        self.ev = Evaluator(interpreter=self.interp, n_eval=2)
        self.g1 = make_valid_genotype()
        self.g2 = make_valid_genotype()
        self.g2.system_prompt = self.g2.system_prompt + " Different variant."
        self.task = attach_checker(build_task("A-r8", "A", 1, "TA1"))

    def test_same_crn_tuple_gives_identical_seeds_across_genotypes(self):
        """R8 core: two different genotypes under the same CRN tuple get identical seed_parts."""
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0,
                         state_id="sX", rollout_id="rX", eval_seed="CRN|sX|0")
        seeds_g1 = list(self.interp.seed_log)

        self.interp.seed_log = []
        self.ev.evaluate(self.g2, self.task, replicate_id=0,
                         state_id="sX", rollout_id="rX", eval_seed="CRN|sX|0")
        seeds_g2 = list(self.interp.seed_log)

        self.assertEqual(len(seeds_g1), 2)  # n_eval=2 replicas
        self.assertEqual(seeds_g1, seeds_g2,
                         "CRN seeds must be identical across genotypes for the same (state,rollout,replicate)")

    def test_different_replicate_id_gives_different_seeds(self):
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="rX")
        s0 = list(self.interp.seed_log)
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=1, state_id="sX", rollout_id="rX")
        s1 = list(self.interp.seed_log)
        self.assertNotEqual(s0, s1)

    def test_different_rollout_id_gives_different_seeds(self):
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="r0")
        s0 = list(self.interp.seed_log)
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="r1")
        s1 = list(self.interp.seed_log)
        self.assertNotEqual(s0, s1)

    def test_cache_identity_is_genotype_specific(self):
        r1 = self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="rX")
        r2 = self.ev.evaluate(self.g2, self.task, replicate_id=0, state_id="sX", rollout_id="rX")
        self.assertFalse(r1.from_cache)
        self.assertFalse(r2.from_cache, "different genotype must not hit the same cache entry")

    def test_cache_hits_do_not_increment_independent_samples(self):
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="rX")
        n = self.ev.independent_samples
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="rX")
        self.assertEqual(self.ev.independent_samples, n)
        self.assertGreaterEqual(self.ev.cache_hits, 1)


# ===== R9: CTX / cache accounting =====
class TestR9Accounting(unittest.TestCase):
    def setUp(self):
        self.ev = Evaluator(n_eval=2, runtime_revision="test-r9")
        self.g = make_valid_genotype()
        self.task = attach_checker(build_task("A-r9", "A", 1, "TA1"))

    def test_uncached_evaluation_runs_n_eval_replicas(self):
        reps0 = self.ev.replicas_executed
        r = self.ev.evaluate(self.g, self.task, replicate_id=0)
        self.assertEqual(self.ev.replicas_executed - reps0, 2)
        self.assertEqual(r.replicas_run, 2)
        self.assertFalse(r.from_cache)

    def test_cache_hit_adds_zero_actual_ctx_and_one_bundle(self):
        self.ev.evaluate(self.g, self.task, replicate_id=0)
        reps0 = self.ev.replicas_executed
        hits0 = self.ev.cache_hits
        r = self.ev.evaluate(self.g, self.task, replicate_id=0)
        self.assertTrue(r.from_cache)
        self.assertEqual(r.replicas_run, 0)
        self.assertEqual(self.ev.replicas_executed - reps0, 0, "cache hit must add 0 actual CTX")
        self.assertEqual(self.ev.cache_hits - hits0, 1, "cache hit bundles +1")

    def test_different_replicate_no_cache_reuse(self):
        self.ev.evaluate(self.g, self.task, replicate_id=0)
        r = self.ev.evaluate(self.g, self.task, replicate_id=1)
        self.assertFalse(r.from_cache)

    def test_episode_result_reports_own_deltas(self):
        """Reuse one Evaluator across two episodes; each reports only its own deltas."""
        cfg = EvolutionConfig(mu=2, lam=2, T=2, n_eval=2)

        def sched(t, pop, hist):
            return OPERATOR_NAMES[t % 5]

        task = attach_checker(build_task("A-r9b", "A", 2, "TA1"))
        ev = self.ev  # shared evaluator
        e1 = evolve(sched, cfg, ev, task, seed=1, episode_id="ep1")
        cache_after_e1 = ev.cache_hits
        e2 = evolve(sched, cfg, ev, task, seed=2, episode_id="ep2")
        # each EpisodeResult.cache_hits is its own delta, not cumulative
        self.assertGreaterEqual(e1.cache_hits, 0)
        self.assertGreaterEqual(e2.cache_hits, 0)
        self.assertEqual(ev.cache_hits, cache_after_e1 + e2.cache_hits,
                         "episode cache_hits must be per-episode deltas summing to cumulative")

    def test_initialization_slots_included_in_planned(self):
        cfg = EvolutionConfig(mu=3, lam=2, T=2, n_eval=2)

        def sched(t, pop, hist):
            return OPERATOR_NAMES[0]

        task = attach_checker(build_task("A-r9c", "A", 3, "TA1"))
        e = evolve(sched, cfg, Evaluator(n_eval=2), task, seed=1)
        self.assertEqual(e.planned_init_slots, 3 * 2, "init slots = mu * n_eval")
        expected_total = 3 * 2 + 2 * 2 * 2  # init + T*lam*n_eval
        self.assertEqual(e.planned_slots, expected_total)

    def test_invalid_offspring_not_counted_as_evaluated(self):
        cfg = EvolutionConfig(mu=4, lam=4, T=1, n_eval=2)

        def sched(t, pop, hist):
            return "tool_subset_edit"  # drop-mode gen=0 often invalidates

        task = attach_checker(build_task("A-r9d", "A", 4, "TA1"))
        ev = Evaluator(n_eval=2)
        reps0 = ev.replicas_executed
        e = evolve(sched, cfg, ev, task, seed=1)
        # actual CTX only counts valid evaluated offspring + init
        self.assertEqual(e.actual_ctx, ev.replicas_executed - reps0)
        # invalid offspring are reported separately
        self.assertGreaterEqual(e.invalid_offspring, 0)


# ===== R11: StubLLM correct on every template =====
class TestR11StubTemplates(unittest.TestCase):
    def _run_all(self, templates, family, seed=7):
        g = make_valid_genotype()
        interp = Interpreter()
        for tid in templates:
            t = attach_checker(build_task("X", family, seed, tid))
            res = interp.run(g, t, seed_parts=("t", 0, "h"))
            self.assertTrue(res.success,
                            f"{tid} failed: gold={t['gold']} ans={res.answer}")

    def test_all_train_a_templates(self):
        self._run_all(TRAIN_TEMPLATES_A, "A")

    def test_all_val_a_templates(self):
        self._run_all(VAL_TEMPLATES_A, "A")

    def test_all_train_b_templates(self):
        self._run_all(TRAIN_TEMPLATES_B, "B")

    def test_all_val_b_templates(self):
        self._run_all(VAL_TEMPLATES_B, "B")

    def test_solve_input_matches_gold(self):
        """solve_input computes the same answer as gold from input alone."""
        for tid in TRAIN_TEMPLATES_A + VAL_TEMPLATES_A:
            t = build_task("X", "A", 11, tid)
            self.assertEqual(solve_input("A", t["input"]), t["gold"], tid)
        for tid in TRAIN_TEMPLATES_B + VAL_TEMPLATES_B:
            t = build_task("X", "B", 11, tid)
            self.assertEqual(solve_input("B", t["input"]), t["gold"], tid)

    def test_multiple_seeds_all_templates(self):
        for seed in (1, 2, 3):
            self._run_all(TRAIN_TEMPLATES_A + VAL_TEMPLATES_A, "A", seed=seed)
            self._run_all(TRAIN_TEMPLATES_B + VAL_TEMPLATES_B, "B", seed=seed)


# ===== PC1 runner synthetic tests (NO real PC1 execution) =====
class TestPC1RunnerSynthetic(unittest.TestCase):
    def _make_records(self, per_state_action=3, n_states=6, n_actions=5, n_clusters=3):
        """Synthetic records. Actions 0/1 have delayed payoff to create disagreement."""
        recs = []
        for si in range(n_states):
            cid = f"cluster{si % n_clusters}"
            for a in range(n_actions):
                for r in range(per_state_action):
                    # action 0: high immediate, low future; action 1: low immediate, high future
                    if a == 0:
                        gen = [0.10, 0.00, 0.00]
                    elif a == 1:
                        gen = [0.02, 0.08, 0.10]
                    else:
                        gen = [0.05, 0.05, 0.05]
                    recs.append(StateActionRecord(
                        state_id=f"s{si}", cluster_id=cid, action=a,
                        rollout_id=r, replicate_id=0,
                        crn_seed=f"CRN|s{si}|{r}",
                        sample_role=ROLE_Q, task_id="T1", episode_id="col000",
                        effective_seed_parts=("SEED", f"s{si}", "A", str(r), "0", "0"),
                        gen_rewards=gen,
                        planned_slots=4 * 2,
                    ))
        return recs

    def test_r_hat_uses_first_reward_same_as_q_first_term(self):
        recs = self._make_records()
        r_hat = compute_r_hat(recs)
        q_hat = compute_q_hat(recs)
        # Q first term must come from the same gen_rewards[0] as r_hat
        self.assertAlmostEqual(r_hat[("s0", 0)], 0.10)
        # Q(0) = 0.10 + 0.95*0 + 0.95^2*0 = 0.10
        self.assertAlmostEqual(q_hat[("s0", 0)], 0.10)
        # Q(1) = 0.02 + 0.95*0.08 + 0.95^2*0.10 > r_hat(1)
        self.assertGreater(q_hat[("s0", 1)], r_hat[("s0", 1)])

    def test_disagreement_detected(self):
        recs = self._make_records()
        res = run_pc1_analysis(recs, planned_slots_total=50000, require_registered_shape=False)
        # a_r = 0 (highest r_hat=0.10), a_q = 1 (highest Q) -> disagreement expected
        self.assertGreater(res.D, 0.0)
        self.assertGreater(res.advantage, 0.0)

    def test_cluster_bootstrap_keeps_clusters_together(self):
        recs = self._make_records(n_states=6, n_clusters=3)
        res = run_pc1_analysis(recs, planned_slots_total=50000, require_registered_shape=False)
        self.assertEqual(res.n_clusters, 3)
        self.assertEqual(res.n_states, 6)
        self.assertEqual(len(res.D_ci), 2)
        self.assertLessEqual(res.D_ci[0], res.D_ci[1])

    def test_hard_cap_enforced(self):
        recs = self._make_records()
        with self.assertRaises(ValueError):
            run_pc1_analysis(recs, planned_slots_total=HARD_CAP_SLOTS + 1)

    def test_decision_pass_when_clear(self):
        """Construct records where D is high and advantage is high -> PASS."""
        recs = []
        for si in range(20):
            for a in range(5):
                for r in range(3):
                    if a == 0:
                        gen = [0.30, 0.00, 0.00]   # high r_hat, Q=0.30
                    elif a == 1:
                        gen = [0.00, 0.20, 0.25]   # r_hat=0, Q=0.95*0.20+0.95^2*0.25=0.4156
                    else:
                        gen = [0.05, 0.05, 0.05]
                    recs.append(StateActionRecord(
                        state_id=f"s{si}", cluster_id=f"c{si}", action=a,
                        rollout_id=r, replicate_id=0, crn_seed=f"CRN|s{si}|{r}",
                        sample_role=ROLE_Q, task_id="T1", episode_id="col000",
                        effective_seed_parts=("SEED", f"s{si}", "A", str(r), "0", "0"),
                        gen_rewards=gen, planned_slots=8))
        res = run_pc1_analysis(recs, planned_slots_total=45000, require_registered_shape=False)
        self.assertGreaterEqual(res.D, 0.15)
        self.assertGreaterEqual(res.advantage, 0.02)
        self.assertEqual(res.decision, "PASS", f"D={res.D} adv={res.advantage} ci={res.D_ci},{res.adv_ci}")

    def test_decision_inconclusive_when_mixed(self):
        """All actions identical -> D=0, advantage=0 -> not PASS."""
        recs = []
        for si in range(10):
            for a in range(5):
                for r in range(3):
                    recs.append(StateActionRecord(
                        state_id=f"s{si}", cluster_id=f"c{si}", action=a,
                        rollout_id=r, replicate_id=0, crn_seed=f"CRN|s{si}|{r}",
                        sample_role=ROLE_Q, task_id="T1", episode_id="col000",
                        effective_seed_parts=("SEED", f"s{si}", "A", str(r), "0", "0"),
                        gen_rewards=[0.05, 0.05, 0.05], planned_slots=8))
        res = run_pc1_analysis(recs, planned_slots_total=50000, require_registered_shape=False)
        self.assertEqual(res.D, 0.0)
        self.assertEqual(res.advantage, 0.0)
        self.assertIn(res.decision, ("FAIL", "INCONCLUSIVE"))

    def test_raw_evidence_replayable_fields(self):
        recs = self._make_records()
        res = run_pc1_analysis(recs, planned_slots_total=50000, require_registered_shape=False)
        ev = res.raw_evidence
        self.assertIn("protocol_version", ev)
        self.assertIn("r_hat", ev)
        self.assertIn("q_hat", ev)
        self.assertIn("rows", ev)
        self.assertIn("thresholds", ev)
        self.assertIn("decision_rule", ev)

    def test_zero_cost_check_still_passes(self):
        self.assertTrue(zero_cost_protocol_check()["all_pass"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
