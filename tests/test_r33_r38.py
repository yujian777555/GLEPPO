"""R33-R38 regression tests + synthetic experiments. No PC1 execution, no Family C."""
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
    BudgetLedger, StateActionRecord, PC1ExecutionRefused,
    ApprovalGate, ProductionRuntimeGate, ProtocolVersionGate,
    SyntheticGateHarness, create_default_gated_runner,
    CANONICAL_PROTOCOL, PROTOCOL_VERSION, PROTOCOL_STATUS,
    protocol_consistency_check, parse_protocol_document, compute_protocol_hash,
    generate_plan_mapping, get_plan_mapping, validate_provenance_against_plan,
    compute_r_hat, compute_q_hat, run_pc1_analysis,
    generate_pc1_dry_run_plan, execute_registered_pc1,
    validate_records, crn_seed,
    save_evidence_artifact, load_evidence_artifact,
    deserialize_records, replay_from_artifact,
    ROLE_Q, ROLE_EXTRA, N_ACTIONS, HORIZON, Q_ROLLOUTS, EXTRA_IMMEDIATE,
    N_STATES, HARD_CAP_SLOTS, PLANNED_TOTAL_SLOTS,
    PLANNED_COLLECTION_SLOTS, PLANNED_Q_SLOTS, PLANNED_EXTRA_SLOTS,
    N_STATE_COLLECTION_EPISODES,
)
from gleppo.tasks import build_task, attach_checker

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class InstrumentedInterpreter(Interpreter):
    def __init__(self):
        super().__init__()
        self.seed_log = []

    def run(self, g, task, seed_parts=None):
        self.seed_log.append(tuple(seed_parts))
        return super().run(g, task, seed_parts=seed_parts)


def _make_rec(si, a, r=0, role=ROLE_Q, rewards=None):
    """Create record matching the plan mapping for state si."""
    mapping, _ = get_plan_mapping()
    sid = f"s{si:03d}"
    ep = mapping[sid]
    n = HORIZON if role == ROLE_Q else 1
    rec = StateActionRecord(
        state_id=sid, cluster_id=ep["cluster_id"],
        action=a, rollout_id=r, replicate_id=0,
        crn_seed=crn_seed(ep["task_id"], sid, r),
        sample_role=role, task_id=ep["task_id"], episode_id=ep["episode_id"],
        family=ep["family"],
        effective_seed_parts=("SEED", "json", ep["task_id"], sid, str(r), "0", "0"),
        gen_rewards=rewards if rewards is not None else [0.05] * n,
    )
    rec.planned_slots = 24 if role == ROLE_Q else 8
    return rec


# ===== R33: budget atomicity =====
class TestR33Atomicity(unittest.TestCase):
    def test_q_slot_negative_replicas_no_mutation(self):
        bl = BudgetLedger()
        with self.assertRaises(ValueError):
            bl.record_q_slot(24, -1, 0)
        self.assertEqual(bl.planned_q_slots, 0)
        self.assertEqual(bl.planned_slots, 0)
        self.assertEqual(bl.actual_replicas_run, 0)

    def test_extra_slot_negative_cache_no_mutation(self):
        bl = BudgetLedger()
        with self.assertRaises(ValueError):
            bl.record_extra_slot(8, 0, -1)
        self.assertEqual(bl.planned_extra_slots, 0)
        self.assertEqual(bl.planned_slots, 0)

    def test_q_slot_over_budget_no_mutation(self):
        bl = BudgetLedger()
        bl.record_q_slot(45000, 0, 0)
        with self.assertRaises(ValueError):
            bl.record_q_slot(6000, 0, 0)  # would exceed 50000
        self.assertEqual(bl.planned_q_slots, 45000)
        self.assertEqual(bl.planned_slots, 45000)

    def test_compensating_slot_errors_rejected(self):
        """R33: records with wrong individual planned_slots must be rejected."""
        recs = []
        for si in range(3):
            for a in range(N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    rec = _make_rec(si, a, r=r)
                    rec.planned_slots = 23  # wrong: should be 24
                    recs.append(rec)
                rec = _make_rec(si, a, r=100, role=ROLE_EXTRA, rewards=[0.05])
                rec.planned_slots = 9  # wrong: should be 8
                recs.append(rec)
        with self.assertRaises(ValueError) as ctx:
            validate_records(recs, require_registered_shape=False)
        self.assertIn("planned_slots", str(ctx.exception))

    def test_snapshot_unchanged_after_rejection(self):
        bl = BudgetLedger()
        bl.record_q_slot(24, 10, 2)
        snap = (bl.planned_slots, bl.planned_q_slots, bl.actual_replicas_run,
                bl.cache_hit_bundles, bl.valid_offspring)
        with self.assertRaises(ValueError):
            bl.record_q_slot(24, -5, 0)
        self.assertEqual(snap, (bl.planned_slots, bl.planned_q_slots,
                                bl.actual_replicas_run, bl.cache_hit_bundles,
                                bl.valid_offspring))


# ===== R34: seed collision-free encoding =====
class TestR34SeedCollision(unittest.TestCase):
    def setUp(self):
        self.interp = InstrumentedInterpreter()
        self.ev = Evaluator(interpreter=self.interp, n_eval=2)
        self.g = make_valid_genotype()
        self.task = attach_checker(build_task("A-r34", "A", 1, "TA1"))

    def test_none_vs_literal_NONE_distinct(self):
        self.interp.seed_log = []
        self.ev.evaluate(self.g, self.task, replicate_id=0, state_id="sX",
                         rollout_id="rX", eval_seed=None)
        s1 = list(self.interp.seed_log)
        self.interp.seed_log = []
        self.ev.evaluate(self.g, self.task, replicate_id=0, state_id="sX",
                         rollout_id="rX", eval_seed="NONE")
        s2 = list(self.interp.seed_log)
        self.assertNotEqual(s1, s2, "None and literal 'NONE' must differ")

    def test_empty_vs_literal_EMPTY_distinct(self):
        self.interp.seed_log = []
        self.ev.evaluate(self.g, self.task, replicate_id=0, state_id="sX",
                         rollout_id="rX", eval_seed="")
        s1 = list(self.interp.seed_log)
        self.interp.seed_log = []
        self.ev.evaluate(self.g, self.task, replicate_id=0, state_id="sX",
                         rollout_id="rX", eval_seed="EMPTY")
        s2 = list(self.interp.seed_log)
        self.assertNotEqual(s1, s2, "'' and literal 'EMPTY' must differ")

    def test_none_vs_empty_distinct(self):
        self.interp.seed_log = []
        self.ev.evaluate(self.g, self.task, replicate_id=0, state_id="sX",
                         rollout_id="rX", eval_seed=None)
        s1 = list(self.interp.seed_log)
        self.interp.seed_log = []
        self.ev.evaluate(self.g, self.task, replicate_id=0, state_id="sX",
                         rollout_id="rX", eval_seed="")
        s2 = list(self.interp.seed_log)
        self.assertNotEqual(s1, s2)

    def test_cache_no_collision_for_none_vs_literal_NONE(self):
        self.ev.evaluate(self.g, self.task, replicate_id=0, state_id="sX",
                         rollout_id="rX", eval_seed=None)
        r = self.ev.evaluate(self.g, self.task, replicate_id=0, state_id="sX",
                             rollout_id="rX", eval_seed="NONE")
        self.assertFalse(r.from_cache)

    def test_delimiter_ids_no_collision(self):
        """IDs containing separators must not cause hash ambiguity."""
        task1 = attach_checker(build_task("A|B", "A", 1, "TA1"))
        task2 = attach_checker(build_task("A", "A", 1, "TA1"))
        self.interp.seed_log = []
        self.ev.evaluate(self.g, task1, replicate_id=0, state_id="s|X", rollout_id="rX")
        s1 = list(self.interp.seed_log)
        self.interp.seed_log = []
        self.ev.evaluate(self.g, task2, replicate_id=0, state_id="s|X", rollout_id="rX")
        s2 = list(self.interp.seed_log)
        self.assertNotEqual(s1, s2)

    def test_cache_hit_for_identical_full_key(self):
        self.ev.evaluate(self.g, self.task, replicate_id=0, state_id="sX",
                         rollout_id="rX", eval_seed="B1")
        r = self.ev.evaluate(self.g, self.task, replicate_id=0, state_id="sX",
                             rollout_id="rX", eval_seed="B1")
        self.assertTrue(r.from_cache)


# ===== R35: plan-backed provenance =====
class TestR35PlanProvenance(unittest.TestCase):
    def test_plan_mapping_deterministic(self):
        m1, h1 = generate_plan_mapping()
        m2, h2 = generate_plan_mapping()
        self.assertEqual(h1, h2)
        self.assertEqual(m1, m2)

    def test_unknown_episode_rejected(self):
        recs = []
        for si in range(N_STATES):
            recs.append(_make_rec(si, 0, r=0))
            for a in range(1, N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    recs.append(_make_rec(si, a, r=r))
                recs.append(_make_rec(si, a, r=100, role=ROLE_EXTRA, rewards=[0.05]))
        # also add remaining Q rollouts for action 0
        for r in range(1, Q_ROLLOUTS):
            recs.append(_make_rec(si, 0, r=r))
        recs.append(_make_rec(si, 0, r=100, role=ROLE_EXTRA, rewards=[0.05]))
        # mutate one to unknown episode
        recs[0].episode_id = "unknown_999"
        with self.assertRaises(ValueError) as ctx:
            validate_records(recs, require_registered_shape=True)
        self.assertIn("episode_id", str(ctx.exception))

    def test_wrong_cluster_rejected(self):
        recs = []
        for si in range(N_STATES):
            for a in range(N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    recs.append(_make_rec(si, a, r=r))
                recs.append(_make_rec(si, a, r=100, role=ROLE_EXTRA, rewards=[0.05]))
        recs[0].cluster_id = "wrong_cluster"
        with self.assertRaises(ValueError) as ctx:
            validate_records(recs, require_registered_shape=True)
        self.assertIn("cluster_id", str(ctx.exception))

    def test_wrong_task_rejected(self):
        recs = []
        for si in range(N_STATES):
            for a in range(N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    recs.append(_make_rec(si, a, r=r))
                recs.append(_make_rec(si, a, r=100, role=ROLE_EXTRA, rewards=[0.05]))
        recs[0].task_id = "wrong_task"
        with self.assertRaises(ValueError) as ctx:
            validate_records(recs, require_registered_shape=True)
        self.assertIn("task_id", str(ctx.exception))

    def test_wrong_family_rejected(self):
        recs = []
        for si in range(N_STATES):
            for a in range(N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    recs.append(_make_rec(si, a, r=r))
                recs.append(_make_rec(si, a, r=100, role=ROLE_EXTRA, rewards=[0.05]))
        recs[0].family = "C"
        with self.assertRaises(ValueError) as ctx:
            validate_records(recs, require_registered_shape=True)
        self.assertIn("family", str(ctx.exception))


# ===== R36: protocol doc consistency =====
class TestR36ProtocolConsistency(unittest.TestCase):
    def test_full_consistency_passes(self):
        r = protocol_consistency_check()
        self.assertTrue(r["all_pass"], r["checks"])
        self.assertTrue(r["doc_hash"])

    def test_mutation_n_states_fails(self):
        doc = parse_protocol_document()
        doc["n_states"] = 999
        import hashlib
        # write temp mutated doc
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n\n```json\n" + json.dumps(doc) + "\n```\n")
            path = f.name
        r = protocol_consistency_check(path)
        self.assertFalse(r["all_pass"])
        self.assertFalse(r["checks"]["doc_n_states"]["ok"])
        os.unlink(path)

    def test_mutation_gamma_fails(self):
        doc = parse_protocol_document()
        doc["gamma"] = 0.5
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n\n```json\n" + json.dumps(doc) + "\n```\n")
            path = f.name
        r = protocol_consistency_check(path)
        self.assertFalse(r["all_pass"])
        self.assertFalse(r["checks"]["doc_gamma"]["ok"])
        os.unlink(path)

    def test_mutation_budget_total_fails(self):
        doc = parse_protocol_document()
        doc["budget"]["total"] = 99999
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n\n```json\n" + json.dumps(doc) + "\n```\n")
            path = f.name
        r = protocol_consistency_check(path)
        self.assertFalse(r["all_pass"])
        self.assertFalse(r["checks"]["doc_budget_total"]["ok"])
        os.unlink(path)

    def test_mutation_threshold_fails(self):
        doc = parse_protocol_document()
        doc["thresholds"]["D"] = 0.99
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n\n```json\n" + json.dumps(doc) + "\n```\n")
            path = f.name
        r = protocol_consistency_check(path)
        self.assertFalse(r["all_pass"])
        self.assertFalse(r["checks"]["doc_thresh_D"]["ok"])
        os.unlink(path)

    def test_mutation_estimator_fails(self):
        doc = parse_protocol_document()
        doc["estimator_contract"] = {"horizon": 99, "gamma": 0.95, "r_hat_sources": ["q_rollout_first", "extra_immediate"], "q_hat_role": "q_rollout_only"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n\n```json\n" + json.dumps(doc) + "\n```\n")
            path = f.name
        r = protocol_consistency_check(path)
        self.assertFalse(r["all_pass"])
        self.assertFalse(r["checks"]["doc_est_horizon"]["ok"])
        os.unlink(path)


# ===== R37: protocol/plan hash in registered analysis =====
class TestR37ProtocolPlanHash(unittest.TestCase):
    def _make_full_records(self):
        recs = []
        for si in range(N_STATES):
            for a in range(N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    recs.append(_make_rec(si, a, r=r))
                recs.append(_make_rec(si, a, r=100, role=ROLE_EXTRA, rewards=[0.05]))
        return recs

    def test_missing_protocol_hash_rejected(self):
        recs = self._make_full_records()
        _, plan_hash = get_plan_mapping()
        with self.assertRaises(ValueError) as ctx:
            run_pc1_analysis(recs, 45440, require_registered_shape=True,
                             manifest_hash="mh", runtime_revision="rt",
                             evaluator_version="ev", protocol_hash="", plan_hash=plan_hash)
        self.assertIn("protocol_hash", str(ctx.exception))

    def test_missing_plan_hash_rejected(self):
        recs = self._make_full_records()
        doc = parse_protocol_document()
        ph = compute_protocol_hash(doc)
        with self.assertRaises(ValueError) as ctx:
            run_pc1_analysis(recs, 45440, require_registered_shape=True,
                             manifest_hash="mh", runtime_revision="rt",
                             evaluator_version="ev", protocol_hash=ph, plan_hash="")
        self.assertIn("plan_hash", str(ctx.exception))

    def test_wrong_protocol_hash_rejected(self):
        recs = self._make_full_records()
        _, plan_hash = get_plan_mapping()
        with self.assertRaises(ValueError) as ctx:
            run_pc1_analysis(recs, 45440, require_registered_shape=True,
                             manifest_hash="mh", runtime_revision="rt",
                             evaluator_version="ev", protocol_hash="wrong_hash",
                             plan_hash=plan_hash, plan_artifact_path="dummy.json")
        self.assertIn("protocol_hash", str(ctx.exception))

    def test_wrong_plan_hash_rejected(self):
        recs = self._make_full_records()
        doc = parse_protocol_document()
        ph = compute_protocol_hash(doc)
        with self.assertRaises(ValueError) as ctx:
            run_pc1_analysis(recs, 45440, require_registered_shape=True,
                             manifest_hash="mh", runtime_revision="rt",
                             evaluator_version="ev", protocol_hash=ph,
                             plan_hash="wrong_plan")
        self.assertIn("plan_artifact_path", str(ctx.exception))


# ===== R38: fail-closed gates =====
class TestR38FailClosedGates(unittest.TestCase):
    def test_approval_empty_protocol_hash_denied(self):
        gate = ApprovalGate(approved=True, protocol_status="APPROVED",
                            approver="x", approval_date="2026-01-01",
                            protocol_hash="", expected_protocol_hash="h1")
        with self.assertRaises(PC1ExecutionRefused):
            gate.check()

    def test_approval_empty_expected_hash_denied(self):
        gate = ApprovalGate(approved=True, protocol_status="APPROVED",
                            approver="x", approval_date="2026-01-01",
                            protocol_hash="h1", expected_protocol_hash="")
        with self.assertRaises(PC1ExecutionRefused):
            gate.check()

    def test_approval_empty_approver_denied(self):
        gate = ApprovalGate(approved=True, protocol_status="APPROVED",
                            approver="", approval_date="2026-01-01",
                            protocol_hash="h1", expected_protocol_hash="h1")
        with self.assertRaises(PC1ExecutionRefused):
            gate.check()

    def test_approval_empty_date_denied(self):
        gate = ApprovalGate(approved=True, protocol_status="APPROVED",
                            approver="x", approval_date="",
                            protocol_hash="h1", expected_protocol_hash="h1")
        with self.assertRaises(PC1ExecutionRefused):
            gate.check()

    def test_production_empty_revision_denied(self):
        gate = ProductionRuntimeGate(ready=True, runtime_revision="",
                                     required_revision="r1")
        with self.assertRaises(PC1ExecutionRefused):
            gate.check()

    def test_production_empty_required_denied(self):
        gate = ProductionRuntimeGate(ready=True, runtime_revision="r1",
                                     required_revision="")
        with self.assertRaises(PC1ExecutionRefused):
            gate.check()

    def test_all_booleans_true_proposed_protocol_denied(self):
        runner = SyntheticGateHarness(
            approval_gate=ApprovalGate(approved=True, protocol_status="PROPOSED",
                                       approver="x", approval_date="2026-01-01",
                                       protocol_hash="h", expected_protocol_hash="h"),
            production_gate=ProductionRuntimeGate(ready=True, runtime_revision="r",
                                                   required_revision="r"),
            protocol_gate=ProtocolVersionGate(),
        )
        with self.assertRaises(PC1ExecutionRefused):
            runner.execute_unit("u1", PROTOCOL_VERSION, 10, 8, 0)

    def test_registered_execution_refused(self):
        with self.assertRaises(PC1ExecutionRefused):
            execute_registered_pc1()


# ===== Experiment B: synthetic analysis =====
class TestExperimentBSyntheticAnalysis(unittest.TestCase):
    def test_positive_synthetic_known_result(self):
        """Construct data where action 1 has high Q but low r -> disagreement."""
        recs = []
        for si in range(3):
            mapping, _ = get_plan_mapping()
            sid = f"s{si:03d}"
            ep = mapping[sid]
            for a in range(N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    if a == 0:
                        gen = [0.30, 0.00, 0.00]
                    elif a == 1:
                        gen = [0.00, 0.20, 0.25]
                    else:
                        gen = [0.05, 0.05, 0.05]
                    rec = StateActionRecord(
                        state_id=sid, cluster_id=ep["cluster_id"],
                        action=a, rollout_id=r, replicate_id=0,
                        crn_seed=crn_seed(ep["task_id"], sid, r),
                        sample_role=ROLE_Q, task_id=ep["task_id"],
                        episode_id=ep["episode_id"], family=ep["family"],
                        effective_seed_parts=("SEED", "x"),
                        gen_rewards=gen, planned_slots=24,
                    )
                    recs.append(rec)
                rec = StateActionRecord(
                    state_id=sid, cluster_id=ep["cluster_id"],
                    action=a, rollout_id=100, replicate_id=0,
                    crn_seed=crn_seed(ep["task_id"], sid, 100),
                    sample_role=ROLE_EXTRA, task_id=ep["task_id"],
                    episode_id=ep["episode_id"], family=ep["family"],
                    effective_seed_parts=("SEED", "x"),
                    gen_rewards=[0.05], planned_slots=8,
                )
                recs.append(rec)
        res = run_pc1_analysis(recs, 50000, require_registered_shape=False)
        self.assertGreater(res.D, 0.0)
        self.assertGreater(res.advantage, 0.0)
        self.assertIn(res.decision, ("PASS", "FAIL", "INCONCLUSIVE"))

    def test_negative_missing_provenance(self):
        recs = []
        for si in range(3):
            for a in range(N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    recs.append(_make_rec(si, a, r=r))
                recs.append(_make_rec(si, a, r=100, role=ROLE_EXTRA, rewards=[0.05]))
        with self.assertRaises(ValueError):
            run_pc1_analysis(recs, 50000, require_registered_shape=True,
                             manifest_hash="", runtime_revision="rt",
                             evaluator_version="ev")

    def test_round_trip_consistency(self):
        recs = []
        for si in range(3):
            for a in range(N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    recs.append(_make_rec(si, a, r=r))
                recs.append(_make_rec(si, a, r=100, role=ROLE_EXTRA, rewards=[0.05]))
        res1 = run_pc1_analysis(recs, 50000, require_registered_shape=False,
                                manifest_hash="mh", runtime_revision="rt",
                                evaluator_version="ev")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        save_evidence_artifact(res1, path)
        res2 = replay_from_artifact(path)
        self.assertAlmostEqual(res1.D, res2.D, places=10)
        self.assertAlmostEqual(res1.advantage, res2.advantage, places=10)
        self.assertEqual(res1.decision, res2.decision)
        os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
