"""R19-R25 regression tests. Synthetic only. No PC1 execution, no Family C."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gleppo.evaluator import Evaluator
from gleppo.genotype import make_valid_genotype
from gleppo.interpreter import Interpreter
from gleppo.pc1 import (
    PlannerApprovalRecord, parse_protocol_document, compute_protocol_hash,
    BudgetLedger, StateActionRecord, PC1ExecutionRefused,
    ApprovalGate, ProductionRuntimeGate, ProtocolVersionGate,
    SyntheticGateHarness, create_default_gated_runner,
    CANONICAL_PROTOCOL, PROTOCOL_VERSION, PROTOCOL_STATUS,
    protocol_consistency_check,
    compute_r_hat, compute_q_hat, run_pc1_analysis,
    generate_pc1_dry_run_plan, execute_registered_pc1,
    validate_records, crn_seed, operator_rng_seed,
    save_evidence_artifact, load_evidence_artifact,
    deserialize_records, replay_from_artifact,
    ROLE_Q, ROLE_EXTRA, N_ACTIONS, HORIZON, Q_ROLLOUTS, EXTRA_IMMEDIATE,
    N_STATES, HARD_CAP_SLOTS, PLANNED_TOTAL_SLOTS,
    N_STATE_COLLECTION_EPISODES,
)
from gleppo.tasks import build_task, attach_checker


class InstrumentedInterpreter(Interpreter):
    def __init__(self):
        super().__init__()
        self.seed_log = []

    def run(self, g, task, seed_parts=None):
        self.seed_log.append(tuple(seed_parts))
        return super().run(g, task, seed_parts=seed_parts)


def _make_rec(si, a, r=0, role=ROLE_Q, rewards=None, cluster=None,
              task_id="T1", episode_id="col000"):
    n = HORIZON if role == ROLE_Q else 1
    rec = StateActionRecord(
        state_id=f"s{si:03d}", cluster_id=cluster or f"c{si:03d}",
        action=a, rollout_id=r, replicate_id=0,
        crn_seed=crn_seed(task_id, f"s{si:03d}", r),
        sample_role=role, task_id=task_id, episode_id=episode_id,
        effective_seed_parts=("SEED", "AUTO", task_id, f"s{si:03d}", str(r), "0", "0"),
        gen_rewards=rewards if rewards is not None else [0.05] * n,
    )
    rec.planned_slots = 24 if role == ROLE_Q else 8
    return rec
    rec.planned_slots = 24 if role == ROLE_Q else 8
    return rec


# ===== R19: protocol consistency =====
class TestR19ProtocolFreeze(unittest.TestCase):
    def test_consistency_check_passes(self):
        r = protocol_consistency_check()
        self.assertTrue(r["all_pass"], r["checks"])

    def test_canonical_matches_code(self):
        self.assertEqual(CANONICAL_PROTOCOL["protocol_version"], PROTOCOL_VERSION)
        self.assertEqual(CANONICAL_PROTOCOL["n_states"], 100)
        self.assertEqual(CANONICAL_PROTOCOL["n_actions"], 5)
        self.assertEqual(CANONICAL_PROTOCOL["q_rollouts"], 3)
        self.assertEqual(CANONICAL_PROTOCOL["horizon"], 3)
        self.assertEqual(CANONICAL_PROTOCOL["extra_immediate"], 1)

    def test_budget_arithmetic(self):
        self.assertEqual(PLANNED_TOTAL_SLOTS, 45440)
        self.assertEqual(HARD_CAP_SLOTS, 50000)

    def test_protocol_status_not_approved(self):
        self.assertIn("PROPOSED", PROTOCOL_STATUS)

    def test_estimator_definition_present(self):
        est = CANONICAL_PROTOCOL["estimator"]
        self.assertIn("r_hat", est)
        self.assertIn("q_hat", est)
        self.assertIn("Q-rollout first rewards + extra_immediate", est["r_hat"])


# ===== R20: CRN seed contract =====
class TestR20CRNContract(unittest.TestCase):
    def setUp(self):
        self.interp = InstrumentedInterpreter()
        self.ev = Evaluator(interpreter=self.interp, n_eval=2)
        self.g1 = make_valid_genotype()
        self.g2 = make_valid_genotype()
        self.g2.system_prompt += " Other."
        self.task = attach_checker(build_task("A-r20", "A", 1, "TA1"))

    def test_same_crn_identical_across_genotypes(self):
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sP", rollout_id="rP")
        s1 = list(self.interp.seed_log)
        self.interp.seed_log = []
        self.ev.evaluate(self.g2, self.task, replicate_id=0, state_id="sP", rollout_id="rP")
        s2 = list(self.interp.seed_log)
        self.assertEqual(s1, s2)

    def test_different_task_isolated(self):
        task2 = attach_checker(build_task("B-r20", "B", 2, "TB1"))
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="rX")
        s1 = list(self.interp.seed_log)
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, task2, replicate_id=0, state_id="sX", rollout_id="rX")
        s2 = list(self.interp.seed_log)
        self.assertNotEqual(s1, s2)

    def test_different_rollout_isolated(self):
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="r0")
        s1 = list(self.interp.seed_log)
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="r1")
        s2 = list(self.interp.seed_log)
        self.assertNotEqual(s1, s2)

    def test_different_replicate_isolated(self):
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="rX")
        s1 = list(self.interp.seed_log)
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=1, state_id="sX", rollout_id="rX")
        s2 = list(self.interp.seed_log)
        self.assertNotEqual(s1, s2)

    def test_override_path_preserves_task_replicate_isolation(self):
        """R20: eval_seed is a BASE key; task/replicate still isolate."""
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="rX",
                         eval_seed="BASE1")
        s1 = list(self.interp.seed_log)
        self.interp.seed_log = []
        self.ev.evaluate(self.g1, self.task, replicate_id=1, state_id="sX", rollout_id="rX",
                         eval_seed="BASE1")
        s2 = list(self.interp.seed_log)
        self.assertNotEqual(s1, s2, "different replicate under same override must differ")

    def test_cache_hit_for_identical_key(self):
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="rX")
        r = self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="rX")
        self.assertTrue(r.from_cache)

    def test_cache_no_hit_for_different_rollout(self):
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="r0")
        r = self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="r1")
        self.assertFalse(r.from_cache)

    def test_cache_no_hit_for_different_genotype(self):
        self.ev.evaluate(self.g1, self.task, replicate_id=0, state_id="sX", rollout_id="rX")
        r = self.ev.evaluate(self.g2, self.task, replicate_id=0, state_id="sX", rollout_id="rX")
        self.assertFalse(r.from_cache)


# ===== R21: budget fail-closed =====
class TestR21BudgetFailClosed(unittest.TestCase):
    def _make_full_state(self, si, cluster=None):
        recs = []
        for a in range(N_ACTIONS):
            for r in range(Q_ROLLOUTS):
                recs.append(_make_rec(si, a, r=r, role=ROLE_Q, cluster=cluster))
            recs.append(_make_rec(si, a, r=100, role=ROLE_EXTRA, rewards=[0.05], cluster=cluster))
        return recs

    def test_negative_total_rejected(self):
        recs = self._make_full_state(0)
        with self.assertRaises(ValueError):
            run_pc1_analysis(recs, -1, require_registered_shape=False)

    def test_over_cap_total_rejected(self):
        recs = self._make_full_state(0)
        with self.assertRaises(ValueError):
            run_pc1_analysis(recs, HARD_CAP_SLOTS + 1, require_registered_shape=False)

    def test_understated_total_rejected(self):
        """R21: caller cannot low-ball the budget."""
        recs = []
        for si in range(3):
            recs.extend(self._make_full_state(si))
        # records have planned_slots=0 (default), so record_planned=0
        # but we set explicit planned_slots
        for r in recs:
            r.planned_slots = 100
        total_record_planned = sum(r.planned_slots for r in recs)
        with self.assertRaises(ValueError):
            run_pc1_analysis(recs, total_record_planned - 100, require_registered_shape=False)

    def test_surplus_samples_rejected_in_registered_mode(self):
        """R21: registered mode requires exact counts."""
        recs = []
        for si in range(2):
            recs.extend(self._make_full_state(si))
        # add surplus Q record
        recs.append(_make_rec(0, 0, r=99, role=ROLE_Q))
        with self.assertRaises(ValueError):
            validate_records(recs, require_registered_shape=True)

    def test_collection_slots_tracked_separately(self):
        bl = BudgetLedger()
        bl.record_collection(planned_slots=5440, replicas_run_delta=4000, cache_bundle_delta=0)
        bl.record_q_slot(planned_slots=36000, replicas_run_delta=30000, cache_bundle_delta=0)
        bl.record_extra_slot(planned_slots=4000, replicas_run_delta=3500, cache_bundle_delta=0)
        self.assertEqual(bl.planned_collection_slots, 5440)
        self.assertEqual(bl.planned_q_slots, 36000)
        self.assertEqual(bl.planned_extra_slots, 4000)
        self.assertEqual(bl.planned_slots, 45440)
        self.assertEqual(bl.reconcile(45440), [])

    def test_reconcile_detects_inconsistency(self):
        bl = BudgetLedger()
        bl.record_q_slot(planned_slots=100, replicas_run_delta=80, cache_bundle_delta=0)
        errors = bl.reconcile(200)  # wrong expected total
        self.assertTrue(any("!= expected" in e for e in errors))

    def test_cache_hit_not_new_sample(self):
        bl = BudgetLedger()
        bl.record_evaluation(planned_slots=4, replicas_run_delta=0, cache_bundle_delta=1, valid=1)
        self.assertEqual(bl.actual_replicas_run, 0)
        self.assertEqual(bl.cache_hit_bundles, 1)


# ===== R22: cluster provenance =====
class TestR22ClusterProvenance(unittest.TestCase):
    def _make_records_with_episodes(self, n_states=3):
        recs = []
        for si in range(n_states):
            ep = f"col{si:03d}"
            for a in range(N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    recs.append(_make_rec(si, a, r=r, role=ROLE_Q,
                                          cluster=ep, episode_id=ep, task_id=f"task-{ep}"))
                recs.append(_make_rec(si, a, r=100, role=ROLE_EXTRA,
                                      rewards=[0.05], cluster=ep, episode_id=ep,
                                      task_id=f"task-{ep}"))
        return recs

    def test_missing_episode_id_rejected_in_registered(self):
        recs = self._make_records_with_episodes(2)
        recs[0].episode_id = ""
        with self.assertRaises(ValueError):
            validate_records(recs, require_registered_shape=True)

    def test_missing_task_id_rejected_in_registered(self):
        recs = self._make_records_with_episodes(2)
        recs[0].task_id = ""
        with self.assertRaises(ValueError):
            validate_records(recs, require_registered_shape=True)

    def test_unknown_episode_in_registered(self):
        recs = self._make_records_with_episodes(2)
        recs[0].episode_id = "unknown_ep"
        recs[0].cluster_id = "unknown_ep"
        # In registered mode, need >= 40 clusters; this should fail
        with self.assertRaises(ValueError):
            validate_records(recs, require_registered_shape=True)

    def test_dry_run_maps_states_to_episodes(self):
        plan = generate_pc1_dry_run_plan()
        ep_units = [s for s in plan.schedule if s["unit"] == "collection_episode"]
        self.assertEqual(len(ep_units), 40)
        # each episode has assigned_states
        for eu in ep_units:
            self.assertIn("assigned_states", eu)
            self.assertTrue(len(eu["assigned_states"]) > 0)

    def test_cluster_bootstrap_preserves_clusters(self):
        recs = self._make_records_with_episodes(3)
        res = run_pc1_analysis(recs, 50000, require_registered_shape=False)
        self.assertGreaterEqual(res.n_clusters, 3)


# ===== R23: replayable evidence =====
class TestR23EvidenceReplay(unittest.TestCase):
    def _make_records(self, n_states=3):
        recs = []
        for si in range(n_states):
            ep = f"col{si:03d}"
            for a in range(N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    recs.append(_make_rec(si, a, r=r, role=ROLE_Q, cluster=ep,
                                          episode_id=ep, task_id=f"task-{ep}"))
                recs.append(_make_rec(si, a, r=100, role=ROLE_EXTRA, rewards=[0.05],
                                      cluster=ep, episode_id=ep, task_id=f"task-{ep}"))
        return recs

    def test_evidence_contains_D_adv_CIs(self):
        recs = self._make_records(2)
        res = run_pc1_analysis(recs, 50000, require_registered_shape=False,
                               manifest_hash="mh123", runtime_revision="rt",
                               evaluator_version="ev")
        ev = res.raw_evidence
        self.assertIn("D", ev)
        self.assertIn("advantage", ev)
        self.assertIn("D_ci", ev)
        self.assertIn("adv_ci", ev)
        self.assertIn("decision", ev)
        self.assertIn("input_record_hash", ev)
        self.assertIn("bootstrap", ev)
        self.assertIn("budget_components", ev)

    def test_round_trip_serialize_replay(self):
        """R23: save -> load -> replay -> compare."""
        recs = self._make_records(3)
        res1 = run_pc1_analysis(recs, 50000, require_registered_shape=False,
                                manifest_hash="mh", runtime_revision="rt",
                                evaluator_version="ev")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        save_evidence_artifact(res1, path)
        res2 = replay_from_artifact(path)
        self.assertAlmostEqual(res1.D, res2.D, places=10)
        self.assertAlmostEqual(res1.advantage, res2.advantage, places=10)
        self.assertEqual(res1.D_ci, res2.D_ci)
        self.assertEqual(res1.adv_ci, res2.adv_ci)
        self.assertEqual(res1.decision, res2.decision)
        self.assertEqual(res1.n_states, res2.n_states)
        self.assertEqual(res1.n_clusters, res2.n_clusters)
        os.unlink(path)

    def test_synthetic_marked(self):
        recs = self._make_records(2)
        res = run_pc1_analysis(recs, 50000, require_registered_shape=False)
        self.assertTrue(res.raw_evidence["is_synthetic"])

    def test_registered_requires_provenance(self):
        recs = self._make_records(2)
        with self.assertRaises(ValueError):
            run_pc1_analysis(recs, 50000, require_registered_shape=True,
                             manifest_hash="", runtime_revision="")


# ===== R24: cost consistency =====
class TestR24CostConsistency(unittest.TestCase):
    def test_smoke_raw_matches_cost_baseline(self):
        smoke_path = os.path.join(os.path.dirname(__file__), "..", "research", "SMOKE_RAW.json")
        cost_path = os.path.join(os.path.dirname(__file__), "..", "research", "COST_BASELINE.md")
        if not os.path.exists(smoke_path):
            self.skipTest("SMOKE_RAW.json not found")
        smoke = json.load(open(smoke_path, encoding="utf-8"))
        cost = open(cost_path, encoding="utf-8", errors="replace").read()
        t = smoke["totals"]
        # R24: wall_clock from raw must appear in cost report
        wc = str(t["wall_clock_s"])
        self.assertIn(wc[:5], cost, f"smoke wall_clock {wc} not in COST_BASELINE")
        # planned slots
        self.assertEqual(t["planned_init_slots"], 32)
        self.assertEqual(t["planned_offspring_slots"], 96)
        self.assertEqual(t["planned_total_slots"], 128)
        self.assertEqual(t["actual_replicas_run"], 112)


# ===== R25: gated runner =====
class TestR25GatedRunner(unittest.TestCase):
    _real_hash = compute_protocol_hash(parse_protocol_document())
    def test_default_deny(self):
        runner = create_default_gated_runner()
        with self.assertRaises(PC1ExecutionRefused):
            runner.execute_unit("u1", PROTOCOL_VERSION, 10, 8, 0)

    def test_unauthorized_approval_denied(self):
        runner = create_default_gated_runner()
        runner.production_gate.ready = True
        with self.assertRaises(PC1ExecutionRefused):
            runner.execute_unit("u1", PROTOCOL_VERSION, 10, 8, 0)

    def test_missing_production_denied(self):
        runner = create_default_gated_runner()
        runner.approval_gate.approved = True
        with self.assertRaises(PC1ExecutionRefused):
            runner.execute_unit("u1", PROTOCOL_VERSION, 10, 8, 0)

    def test_wrong_protocol_version_denied(self):
        runner = create_default_gated_runner()
        runner.approval_gate.approved = True
        runner.production_gate.ready = True
        with self.assertRaises(PC1ExecutionRefused):
            runner.execute_unit("u1", "wrong-version", 10, 8, 0)

    def test_over_budget_denied(self):
        runner = SyntheticGateHarness(
            approval_gate=ApprovalGate(approved=True, protocol_status="APPROVED", protocol_hash=self._real_hash, expected_protocol_hash=self._real_hash, approval_record=PlannerApprovalRecord(approval_id="A1", approver="test", approval_date="2026-01-01", protocol_hash=self._real_hash, protocol_status="APPROVED", protocol_version=PROTOCOL_VERSION)),
            production_gate=ProductionRuntimeGate(ready=True, runtime_revision="r1", required_revision="r1"),
            protocol_gate=ProtocolVersionGate(),
        )
        with self.assertRaises(PC1ExecutionRefused):
            runner.execute_unit("u1", PROTOCOL_VERSION, HARD_CAP_SLOTS + 1, 0, 0)

    def test_synthetic_execution_with_all_gates(self):
        """R43: even with all fields set, PROPOSED protocol must be rejected."""
        runner = SyntheticGateHarness(
            approval_gate=ApprovalGate(approved=True, protocol_status="APPROVED", protocol_hash=self._real_hash, expected_protocol_hash=self._real_hash, approval_record=PlannerApprovalRecord(approval_id="A1", approver="test", approval_date="2026-01-01", protocol_hash=self._real_hash, protocol_status="APPROVED", protocol_version=PROTOCOL_VERSION)),
            production_gate=ProductionRuntimeGate(ready=True, runtime_revision="r1", required_revision="r1"),
            protocol_gate=ProtocolVersionGate(),
        )
        # R43: canonical protocol is PROPOSED, so this must fail
        with self.assertRaises(PC1ExecutionRefused):
            runner.execute_unit("u1", PROTOCOL_VERSION, 10, 8, 0)

    def test_collection_episode_budget_check(self):
        runner = SyntheticGateHarness(
            approval_gate=ApprovalGate(approved=True, protocol_status="APPROVED", protocol_hash=self._real_hash, expected_protocol_hash=self._real_hash, approval_record=PlannerApprovalRecord(approval_id="A1", approver="test", approval_date="2026-01-01", protocol_hash=self._real_hash, protocol_status="APPROVED", protocol_version=PROTOCOL_VERSION)),
            production_gate=ProductionRuntimeGate(ready=True, runtime_revision="r1", required_revision="r1"),
            protocol_gate=ProtocolVersionGate(),
        )
        with self.assertRaises(PC1ExecutionRefused):
            runner.execute_collection_episode("col000", PROTOCOL_VERSION, HARD_CAP_SLOTS + 1, 0, 0)

    def test_registered_execution_still_refused(self):
        with self.assertRaises(PC1ExecutionRefused):
            execute_registered_pc1()


if __name__ == "__main__":
    unittest.main(verbosity=2)
