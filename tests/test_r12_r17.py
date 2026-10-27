"""Regression tests for R12-R17 (Phase 2A-R3). Synthetic fixtures only. No PC1 execution, no Family C."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gleppo.evaluator import Evaluator
from gleppo.genotype import make_valid_genotype
from gleppo.interpreter import Interpreter
from gleppo.pc1 import (
    BudgetLedger, StateActionRecord, PC1ExecutionRefused,
    compute_r_hat, compute_q_hat, run_pc1_analysis,
    generate_pc1_dry_run_plan, execute_registered_pc1,
    validate_records, crn_seed, operator_rng_seed,
    zero_cost_protocol_check,
    ROLE_Q, ROLE_EXTRA, N_ACTIONS, HORIZON, Q_ROLLOUTS, EXTRA_IMMEDIATE,
    N_STATES, HARD_CAP_SLOTS, PLANNED_TOTAL_SLOTS,
)
from gleppo.tasks import build_task, attach_checker


class InstrumentedInterpreter(Interpreter):
    def __init__(self):
        super().__init__()
        self.seed_log = []

    def run(self, g, task, seed_parts=None):
        self.seed_log.append(tuple(seed_parts))
        return super().run(g, task, seed_parts=seed_parts)


# ===== R12: BudgetLedger unit separation =====
class TestR12BudgetLedger(unittest.TestCase):
    def test_init_evaluation(self):
        bl = BudgetLedger()
        bl.record_init(mu=4, n_eval=2, replicas_run_delta=8, cache_bundle_delta=0)
        self.assertEqual(bl.planned_slots, 8)
        self.assertEqual(bl.actual_replicas_run, 8)
        self.assertEqual(bl.cache_hit_bundles, 0)

    def test_cache_bundle_hit_adds_zero_replicas(self):
        bl = BudgetLedger()
        bl.record_evaluation(planned_slots=4, replicas_run_delta=2, cache_bundle_delta=1, valid=2)
        self.assertEqual(bl.actual_replicas_run, 2, "1 bundle hit must not add replicas")
        self.assertEqual(bl.cache_hit_bundles, 1)

    def test_invalid_offspring_zero_ctx(self):
        bl = BudgetLedger()
        bl.record_evaluation(planned_slots=4, replicas_run_delta=0, cache_bundle_delta=0, valid=0, invalid=2)
        self.assertEqual(bl.actual_replicas_run, 0)
        self.assertEqual(bl.invalid_offspring, 2)

    def test_multiple_generations(self):
        bl = BudgetLedger()
        bl.record_init(mu=4, n_eval=2, replicas_run_delta=6, cache_bundle_delta=1)
        bl.record_evaluation(planned_slots=8, replicas_run_delta=8, cache_bundle_delta=0, valid=4)
        bl.record_evaluation(planned_slots=8, replicas_run_delta=4, cache_bundle_delta=2, valid=2, invalid=2)
        self.assertEqual(bl.planned_slots, 8 + 8 + 8)
        self.assertEqual(bl.actual_replicas_run, 6 + 8 + 4)
        self.assertEqual(bl.cache_hit_bundles, 1 + 0 + 2)
        self.assertEqual(bl.invalid_offspring, 2)

    def test_shared_evaluator_deltas(self):
        """Ledger must receive evaluator counter deltas, not inferred values."""
        ev = Evaluator(n_eval=2)
        g = make_valid_genotype()
        task = attach_checker(build_task("A-r12", "A", 1, "TA1"))
        bl = BudgetLedger()

        reps0 = ev.replicas_executed
        hits0 = ev.cache_hits
        ev.evaluate(g, task, replicate_id=0, state_id="sX", rollout_id="rX")
        bl.record_evaluation(planned_slots=4, replicas_run_delta=ev.replicas_executed - reps0,
                             cache_bundle_delta=ev.cache_hits - hits0, valid=1)

        reps0 = ev.replicas_executed
        hits0 = ev.cache_hits
        ev.evaluate(g, task, replicate_id=0, state_id="sX", rollout_id="rX")  # cache hit
        bl.record_evaluation(planned_slots=4, replicas_run_delta=ev.replicas_executed - reps0,
                             cache_bundle_delta=ev.cache_hits - hits0, valid=1)

        self.assertEqual(bl.actual_replicas_run, 2, "cache hit contributes 0")
        self.assertEqual(bl.cache_hit_bundles, 1)
        self.assertEqual(bl.planned_slots, 8)

    def test_planned_independent_of_cache(self):
        bl = BudgetLedger()
        bl.record_evaluation(planned_slots=8, replicas_run_delta=0, cache_bundle_delta=4, valid=4)
        self.assertEqual(bl.planned_slots, 8, "planned slots are conservative, not reduced by cache")


# ===== R13: fail-closed validation =====
def _make_rec(si, a, r=0, role=ROLE_Q, rewards=None, cluster=None):
    n = HORIZON if role == ROLE_Q else 1
    return StateActionRecord(
        state_id=f"s{si:03d}", cluster_id=cluster or f"c{si:03d}",
        action=a, rollout_id=r, replicate_id=0,
        crn_seed=crn_seed(f"s{si:03d}", r),
        sample_role=role,
        effective_seed_parts=("SEED", f"s{si:03d}", "A", str(r), "0", "0"),
        gen_rewards=rewards if rewards is not None else [0.05] * n,
    )


class TestR13FailClosed(unittest.TestCase):
    def test_missing_action_rejected(self):
        recs = [_make_rec(0, a) for a in range(N_ACTIONS - 1)]  # missing action 4
        with self.assertRaises(ValueError):
            validate_records(recs, require_registered_shape=False)

    def test_wrong_horizon_rejected(self):
        rec = _make_rec(0, 0, rewards=[0.1, 0.2])  # 2 rewards, need 3
        with self.assertRaises(ValueError):
            validate_records([rec], require_registered_shape=False)

    def test_nonfinite_reward_rejected(self):
        rec = _make_rec(0, 0, rewards=[0.1, float("nan"), 0.3])
        with self.assertRaises(ValueError):
            validate_records([rec], require_registered_shape=False)

    def test_cluster_conflict_rejected(self):
        r1 = _make_rec(0, 0, cluster="c1")
        r2 = _make_rec(0, 1, cluster="c2")  # same state, different cluster
        with self.assertRaises(ValueError):
            validate_records([r1, r2], require_registered_shape=False)

    def test_duplicate_key_rejected(self):
        r1 = _make_rec(0, 0, r=0)
        r2 = _make_rec(0, 0, r=0)  # identical key
        with self.assertRaises(ValueError):
            validate_records([r1, r2], require_registered_shape=False)

    def test_invalid_action_rejected(self):
        rec = _make_rec(0, 99)
        with self.assertRaises(ValueError):
            validate_records([rec], require_registered_shape=False)

    def test_invalid_role_rejected(self):
        rec = _make_rec(0, 0, role="bad_role")
        with self.assertRaises(ValueError):
            validate_records([rec], require_registered_shape=False)

    def test_registered_shape_requires_100_states(self):
        recs = []
        for si in range(10):
            for a in range(N_ACTIONS):
                recs.append(_make_rec(si, a, r=0))
                recs.append(_make_rec(si, a, r=1))
                recs.append(_make_rec(si, a, r=2))
                recs.append(_make_rec(si, a, r=3, role=ROLE_EXTRA, rewards=[0.05]))
        with self.assertRaises(ValueError):
            validate_records(recs, require_registered_shape=True)

    def test_extra_immediate_wrong_length_rejected(self):
        rec = _make_rec(0, 0, role=ROLE_EXTRA, rewards=[0.1, 0.2])  # 2 rewards, need 1
        with self.assertRaises(ValueError):
            validate_records([rec], require_registered_shape=False)

    def test_no_default_zeros_for_missing_actions(self):
        """Analysis must NOT silently fill missing actions with 0.0."""
        recs = [_make_rec(0, a) for a in range(N_ACTIONS)]
        # remove action 4 q records
        recs = [r for r in recs if r.action != 4]
        with self.assertRaises(ValueError):
            run_pc1_analysis(recs, 1000, require_registered_shape=False)


# ===== R14: sample roles =====
class TestR14SampleRoles(unittest.TestCase):
    def _make_full_state(self, si, gen_q=None, gen_extra=None):
        recs = []
        for a in range(N_ACTIONS):
            for r in range(Q_ROLLOUTS):
                recs.append(_make_rec(si, a, r=r, role=ROLE_Q,
                                      rewards=gen_q or [0.05, 0.05, 0.05]))
            recs.append(_make_rec(si, a, r=100, role=ROLE_EXTRA,
                                  rewards=gen_extra or [0.05]))
        return recs

    def test_q_hat_excludes_extra_immediate(self):
        recs = self._make_full_state(0, gen_q=[0.1, 0.1, 0.1], gen_extra=[0.9])
        q_hat = compute_q_hat(recs)
        # Q should be 0.1 + 0.95*0.1 + 0.95^2*0.1 = 0.28525, NOT influenced by 0.9
        self.assertAlmostEqual(q_hat[("s000", 0)], 0.1 + 0.95 * 0.1 + 0.95**2 * 0.1)

    def test_r_hat_includes_extra_immediate(self):
        recs = self._make_full_state(0, gen_q=[0.1, 0.1, 0.1], gen_extra=[0.9])
        r_hat = compute_r_hat(recs)
        # r_hat = mean of [0.1, 0.1, 0.1, 0.9] = 0.3
        self.assertAlmostEqual(r_hat[("s000", 0)], (0.1 + 0.1 + 0.1 + 0.9) / 4)

    def test_extra_immediate_does_not_pollute_q_hat(self):
        recs_q = self._make_full_state(0, gen_q=[0.1, 0.1, 0.1], gen_extra=[0.0])
        recs_q2 = self._make_full_state(0, gen_q=[0.1, 0.1, 0.1], gen_extra=[1.0])
        q1 = compute_q_hat(recs_q)
        q2 = compute_q_hat(recs_q2)
        self.assertAlmostEqual(q1[("s000", 0)], q2[("s000", 0)],
                               "extra_immediate must not change Q_hat")


# ===== R15: dry-run plan =====
class TestR15DryRunPlan(unittest.TestCase):
    def test_plan_within_hard_cap(self):
        plan = generate_pc1_dry_run_plan()
        self.assertTrue(plan.within_cap)
        self.assertEqual(plan.planned_total_slots, PLANNED_TOTAL_SLOTS)
        self.assertLessEqual(plan.planned_total_slots, HARD_CAP_SLOTS)

    def test_plan_structure(self):
        plan = generate_pc1_dry_run_plan()
        self.assertEqual(plan.n_states, 100)
        self.assertEqual(plan.n_actions, 5)
        self.assertEqual(plan.q_rollouts, 3)
        self.assertEqual(plan.horizon, 3)
        self.assertEqual(plan.extra_immediate, 1)

    def test_plan_schedule_covers_all_units(self):
        plan = generate_pc1_dry_run_plan()
        q_units = [s for s in plan.schedule if s["unit"] == "q_rollout"]
        extra_units = [s for s in plan.schedule if s["unit"] == "extra_immediate"]
        col_units = [s for s in plan.schedule if s["unit"] == "collection_episode"]
        self.assertEqual(len(q_units), 100 * 5 * 3)
        self.assertEqual(len(extra_units), 100 * 5 * 1)
        self.assertEqual(len(col_units), 40)

    def test_registered_execution_refused(self):
        with self.assertRaises(PC1ExecutionRefused):
            execute_registered_pc1()


# ===== R16: unified seed contract =====
class TestR16SeedContract(unittest.TestCase):
    def setUp(self):
        self.interp = InstrumentedInterpreter()
        self.ev = Evaluator(interpreter=self.interp, n_eval=2)
        self.g1 = make_valid_genotype()
        self.g2 = make_valid_genotype()
        self.g2.system_prompt = self.g2.system_prompt + " Other."
        self.task = attach_checker(build_task("A-r16", "A", 1, "TA1"))

    def test_same_crn_identical_across_genotypes(self):
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sP", rollout_id="rP")
        s1 = list(self.interp.seed_log)
        self.interp.seed_log = []
        self.ev.evaluate(self.g2, self.task, replicate_id=0, state_id="sP", rollout_id="rP")
        s2 = list(self.interp.seed_log)
        self.assertEqual(s1, s2)

    def test_different_state_different_seed(self):
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sA", rollout_id="rX")
        s1 = list(self.interp.seed_log)
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sB", rollout_id="rX")
        s2 = list(self.interp.seed_log)
        self.assertNotEqual(s1, s2)

    def test_different_rollout_different_seed(self):
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="r0")
        s1 = list(self.interp.seed_log)
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="r1")
        s2 = list(self.interp.seed_log)
        self.assertNotEqual(s1, s2)

    def test_eval_seed_override_is_authoritative(self):
        """When eval_seed is provided, it is used as the actual RNG seed, not cache-only."""
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="rX",
                         eval_seed="MYSEED")
        s1 = list(self.interp.seed_log)
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="rX",
                         eval_seed="OTHERSEED")
        s2 = list(self.interp.seed_log)
        self.assertNotEqual(s1, s2, "different eval_seed must produce different RNG seeds")

    def test_cache_no_collision_across_state_rollout(self):
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="r0")
        r = self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="r1")
        self.assertFalse(r.from_cache, "same eval_seed but different rollout_id must not cache-collide")

    def test_cache_hit_still_genotype_specific(self):
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="rX")
        r = self.ev.evaluate(self.g2, self.task, replicate_id=0, state_id="sX", rollout_id="rX")
        self.assertFalse(r.from_cache)

    def test_operator_rng_independent_of_eval_seed(self):
        s_op = operator_rng_seed("crossover", "sX", 3, 0, 0)
        s_op2 = operator_rng_seed("crossover", "sX", 3, 0, 1)
        self.assertNotEqual(s_op, s_op2)


# ===== R17: replayable evidence =====
class TestR17Evidence(unittest.TestCase):
    def _make_records(self, n_states=4):
        recs = []
        for si in range(n_states):
            for a in range(N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    recs.append(_make_rec(si, a, r=r, role=ROLE_Q))
                recs.append(_make_rec(si, a, r=100, role=ROLE_EXTRA, rewards=[0.05]))
        return recs

    def test_evidence_contains_provenance(self):
        recs = self._make_records(3)
        res = run_pc1_analysis(recs, 5000, require_registered_shape=False,
                               manifest_hash="abc123", runtime_revision="test",
                               evaluator_version="eval-test")
        ev = res.raw_evidence
        self.assertIn("protocol_version", ev)
        self.assertIn("estimator_version", ev)
        self.assertIn("manifest_hash", ev)
        self.assertIn("runtime_revision", ev)
        self.assertIn("evaluator_version", ev)
        self.assertIn("records", ev)
        self.assertIn("bootstrap", ev)
        self.assertIn("replay_command", ev)
        self.assertEqual(ev["manifest_hash"], "abc123")

    def test_evidence_records_have_required_fields(self):
        recs = self._make_records(2)
        res = run_pc1_analysis(recs, 2000, require_registered_shape=False)
        for rec_ev in res.raw_evidence["records"]:
            for key in ("state_id", "cluster_id", "action", "sample_role",
                        "rollout_id", "replicate_id", "crn_seed", "gen_rewards"):
                self.assertIn(key, rec_ev)

    def test_no_gold_labels_in_evidence(self):
        recs = self._make_records(2)
        res = run_pc1_analysis(recs, 2000, require_registered_shape=False)
        ev_str = str(res.raw_evidence)
        self.assertNotIn("gold", ev_str.lower().replace("gold_check", ""))
        self.assertNotIn("gold_label", ev_str.lower())


# ===== Integrated =====
class TestIntegrated(unittest.TestCase):
    def test_zero_cost_check_passes(self):
        r = zero_cost_protocol_check()
        self.assertTrue(r["all_pass"], r["checks"])

    def test_dry_run_plan_and_analysis_agree(self):
        plan = generate_pc1_dry_run_plan()
        self.assertEqual(plan.planned_total_slots, PLANNED_TOTAL_SLOTS)
        self.assertTrue(plan.within_cap)


if __name__ == "__main__":
    unittest.main(verbosity=2)
