"""R26-R32 regression tests. Synthetic only. No PC1 execution, no Family C."""
from __future__ import annotations

import json
import os
import re
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
    protocol_consistency_check,
    compute_r_hat, compute_q_hat, run_pc1_analysis,
    generate_pc1_dry_run_plan, execute_registered_pc1,
    validate_records, crn_seed, operator_rng_seed,
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


def _make_rec(si, a, r=0, role=ROLE_Q, rewards=None, cluster=None,
              task_id="T1", episode_id="col000"):
    n = HORIZON if role == ROLE_Q else 1
    rec = StateActionRecord(
        state_id=f"s{si:03d}", cluster_id=cluster or f"c{si:03d}",
        action=a, rollout_id=r, replicate_id=0,
        crn_seed=crn_seed(task_id, f"s{si:03d}", r),
        sample_role=role, task_id=task_id, episode_id=episode_id,
        effective_seed_parts=("SEED", "NONE", task_id, f"s{si:03d}", str(r), "0", "0"),
        gen_rewards=rewards if rewards is not None else [0.05] * n,
    )
    rec.planned_slots = 24 if role == ROLE_Q else 8
    return rec


# ===== R27: negative budget rejection =====
class TestR27NegativeBudget(unittest.TestCase):
    def test_negative_planned_slots_rejected(self):
        bl = BudgetLedger()
        with self.assertRaises(ValueError):
            bl.record_evaluation(-1, 8, 0)
        self.assertEqual(bl.planned_slots, 0, "no mutation on rejection")

    def test_negative_replicas_rejected(self):
        bl = BudgetLedger()
        with self.assertRaises(ValueError):
            bl.record_evaluation(8, -1, 0)
        self.assertEqual(bl.actual_replicas_run, 0)

    def test_negative_cache_rejected(self):
        bl = BudgetLedger()
        with self.assertRaises(ValueError):
            bl.record_evaluation(8, 8, -1)
        self.assertEqual(bl.cache_hit_bundles, 0)

    def test_negative_collection_rejected(self):
        bl = BudgetLedger()
        with self.assertRaises(ValueError):
            bl.record_collection(-1, 0, 0)
        self.assertEqual(bl.planned_collection_slots, 0)

    def test_atomic_failure_on_over_budget(self):
        bl = BudgetLedger()
        bl.record_evaluation(45000, 0, 0)
        with self.assertRaises(ValueError):
            bl.record_evaluation(6000, 0, 0)  # would exceed 50000
        self.assertEqual(bl.planned_slots, 45000, "no partial mutation")

    def test_cannot_lower_ledger_with_negative(self):
        bl = BudgetLedger()
        bl.record_evaluation(100, 50, 0)
        with self.assertRaises(ValueError):
            bl.record_evaluation(-50, 0, 0)  # attempt to lower
        self.assertEqual(bl.planned_slots, 100)

    def test_bool_rejected_as_int(self):
        bl = BudgetLedger()
        with self.assertRaises(ValueError):
            bl.record_evaluation(True, 0, 0)  # bool is not valid int

    def test_reconcile_detects_negative(self):
        bl = BudgetLedger()
        bl.planned_slots = -1
        errors = bl.reconcile(-1)
        self.assertTrue(any("negative" in e for e in errors))


# ===== R28: full budget reconciliation =====
class TestR28FullReconciliation(unittest.TestCase):
    def test_registered_budget_exact(self):
        self.assertEqual(PLANNED_COLLECTION_SLOTS, 5440)
        self.assertEqual(PLANNED_Q_SLOTS, 36000)
        self.assertEqual(PLANNED_EXTRA_SLOTS, 4000)
        self.assertEqual(PLANNED_TOTAL_SLOTS, 45440)

    def test_ledger_components_sum_to_total(self):
        bl = BudgetLedger()
        bl.record_collection(5440, 0, 0)
        for _ in range(100 * 5 * 3):
            bl.record_q_slot(24, 0, 0)  # 3*4*2=24 slots each
        for _ in range(100 * 5):
            bl.record_extra_slot(8, 0, 0)  # 4*2=8 slots each
        self.assertEqual(bl.planned_collection_slots, 5440)
        self.assertEqual(bl.planned_q_slots, 36000)
        self.assertEqual(bl.planned_extra_slots, 4000)
        self.assertEqual(bl.planned_slots, 45440)
        self.assertEqual(bl.reconcile(45440), [])

    def test_missing_collection_slots_rejected(self):
        """R28: registered analysis must reconcile collection slots."""
        recs = []
        for si in range(N_STATES):
            for a in range(N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    rec = _make_rec(si, a, r=r, role=ROLE_Q,
                                    cluster=f"col{si % 40:03d}",
                                    episode_id=f"col{si % 40:03d}",
                                    task_id=f"task-{si % 40:03d}")
                    rec.planned_slots = 24
                    recs.append(rec)
                rec = _make_rec(si, a, r=100, role=ROLE_EXTRA, rewards=[0.05],
                                cluster=f"col{si % 40:03d}",
                                episode_id=f"col{si % 40:03d}",
                                task_id=f"task-{si % 40:03d}")
                rec.planned_slots = 8
                recs.append(rec)
        # This should pass: records sum to 45440-5440=40000, plus collection5440 = 45440
        # But if we pass planned_slots_total=45440 it should reconcile
        with self.assertRaises(ValueError):
            # wrong total (too low) must be rejected
            run_pc1_analysis(recs, 40000, require_registered_shape=True,
                             manifest_hash="mh", runtime_revision="rt",
                             evaluator_version="ev")

    def test_zero_record_slots_rejected_in_registered(self):
        """R28: records with zero planned_slots cannot reconcile to 45,440."""
        recs = []
        for si in range(N_STATES):
            for a in range(N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    recs.append(_make_rec(si, a, r=r, role=ROLE_Q,
                                          cluster=f"col{si % 40:03d}",
                                          episode_id=f"col{si % 40:03d}",
                                          task_id=f"task-{si % 40:03d}"))
                recs.append(_make_rec(si, a, r=100, role=ROLE_EXTRA, rewards=[0.05],
                                      cluster=f"col{si % 40:03d}",
                                      episode_id=f"col{si % 40:03d}",
                                      task_id=f"task-{si % 40:03d}"))
        with self.assertRaises(ValueError):
            run_pc1_analysis(recs, 45440, require_registered_shape=True,
                             manifest_hash="mh", runtime_revision="rt",
                             evaluator_version="ev")


# ===== R29: provenance mapping =====
class TestR29ProvenanceMapping(unittest.TestCase):
    def test_unknown_episode_rejected_specifically(self):
        """R29: full 40-cluster fixture, one episode mutated to unknown."""
        recs = []
        for si in range(N_STATES):
            ep = f"col{si % N_STATE_COLLECTION_EPISODES:03d}"
            for a in range(N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    recs.append(_make_rec(si, a, r=r, role=ROLE_Q,
                                          cluster=ep, episode_id=ep,
                                          task_id=f"task-{ep}"))
                recs.append(_make_rec(si, a, r=100, role=ROLE_EXTRA, rewards=[0.05],
                                      cluster=ep, episode_id=ep,
                                      task_id=f"task-{ep}"))
        # mutate one record to unknown episode
        recs[0].episode_id = "unknown_ep_999"
        recs[0].cluster_id = "unknown_ep_999"
        with self.assertRaises(ValueError) as ctx:
            validate_records(recs, require_registered_shape=True)
        self.assertIn("unknown", str(ctx.exception).lower() + "episode" + str(ctx.exception).lower())

    def test_wrong_cluster_rejected(self):
        recs = []
        for si in range(N_STATES):
            ep = f"col{si % N_STATE_COLLECTION_EPISODES:03d}"
            for a in range(N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    recs.append(_make_rec(si, a, r=r, role=ROLE_Q,
                                          cluster=ep, episode_id=ep,
                                          task_id=f"task-{ep}"))
                recs.append(_make_rec(si, a, r=100, role=ROLE_EXTRA, rewards=[0.05],
                                      cluster=ep, episode_id=ep,
                                      task_id=f"task-{ep}"))
        # wrong cluster for one record
        recs[0].cluster_id = "wrong_cluster"
        with self.assertRaises(ValueError):
            validate_records(recs, require_registered_shape=True)

    def test_dry_run_has_state_to_episode_mapping(self):
        plan = generate_pc1_dry_run_plan()
        ep_units = [s for s in plan.schedule if s["unit"] == "collection_episode"]
        self.assertEqual(len(ep_units), 40)
        for eu in ep_units:
            self.assertIn("assigned_states", eu)
            self.assertGreater(len(eu["assigned_states"]), 0)


# ===== R30: registered provenance =====
class TestR30RegisteredProvenance(unittest.TestCase):
    def _make_full_records(self):
        recs = []
        for si in range(N_STATES):
            ep = f"col{si % N_STATE_COLLECTION_EPISODES:03d}"
            for a in range(N_ACTIONS):
                for r in range(Q_ROLLOUTS):
                    rec = _make_rec(si, a, r=r, role=ROLE_Q,
                                    cluster=ep, episode_id=ep,
                                    task_id=f"task-{ep}")
                    rec.planned_slots = 24
                    recs.append(rec)
                rec = _make_rec(si, a, r=100, role=ROLE_EXTRA, rewards=[0.05],
                                cluster=ep, episode_id=ep,
                                task_id=f"task-{ep}")
                rec.planned_slots = 8
                recs.append(rec)
        return recs

    def test_missing_manifest_hash_rejected(self):
        recs = self._make_full_records()
        with self.assertRaises(ValueError) as ctx:
            run_pc1_analysis(recs, 45440, require_registered_shape=True,
                             manifest_hash="", runtime_revision="rt",
                             evaluator_version="ev")
        self.assertIn("manifest_hash", str(ctx.exception))

    def test_missing_runtime_rejected(self):
        recs = self._make_full_records()
        with self.assertRaises(ValueError) as ctx:
            run_pc1_analysis(recs, 45440, require_registered_shape=True,
                             manifest_hash="mh", runtime_revision="",
                             evaluator_version="ev")
        self.assertIn("runtime_revision", str(ctx.exception))

    def test_missing_evaluator_version_rejected(self):
        recs = self._make_full_records()
        with self.assertRaises(ValueError) as ctx:
            run_pc1_analysis(recs, 45440, require_registered_shape=True,
                             manifest_hash="mh", runtime_revision="rt",
                             evaluator_version="")
        self.assertIn("evaluator_version", str(ctx.exception))

    def test_input_hash_mismatch_rejected_on_replay(self):
        recs = self._make_full_records()
        res = run_pc1_analysis(recs, 45440, require_registered_shape=False,
                               manifest_hash="mh", runtime_revision="rt",
                               evaluator_version="ev")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        save_evidence_artifact(res, path)
        # tamper with the artifact
        ev = load_evidence_artifact(path)
        ev["records"][0]["gen_rewards"] = [999.0] * HORIZON
        with open(path, "w") as f:
            json.dump(ev, f)
        with self.assertRaises(ValueError):
            replay_from_artifact(path)
        os.unlink(path)


# ===== R32: seed/cache key normalization =====
class TestR32SeedCacheNormalization(unittest.TestCase):
    def setUp(self):
        self.interp = InstrumentedInterpreter()
        self.ev = Evaluator(interpreter=self.interp, n_eval=2)
        self.g = make_valid_genotype()
        self.task = attach_checker(build_task("A-r32", "A", 1, "TA1"))

    def test_none_and_empty_seed_distinguished(self):
        """R32: eval_seed=None and eval_seed='' must not share cache."""
        r1 = self.ev.evaluate(self.g, self.task, replicate_id=0,
                              state_id="sX", rollout_id="rX", eval_seed=None)
        self.assertFalse(r1.from_cache)
        r2 = self.ev.evaluate(self.g, self.task, replicate_id=0,
                              state_id="sX", rollout_id="rX", eval_seed="")
        self.assertFalse(r2.from_cache, "empty seed must not hit None-seed cache")

    def test_none_and_empty_give_different_seeds(self):
        self.interp.seed_log = []
        self.ev.evaluate(self.g, self.task, replicate_id=0,
                         state_id="sX", rollout_id="rX", eval_seed=None)
        s1 = list(self.interp.seed_log)
        self.interp.seed_log = []
        self.ev.evaluate(self.g, self.task, replicate_id=0,
                         state_id="sX", rollout_id="rX", eval_seed="")
        s2 = list(self.interp.seed_log)
        self.assertNotEqual(s1, s2)

    def test_cache_hit_for_identical_full_key(self):
        self.ev.evaluate(self.g, self.task, replicate_id=0,
                         state_id="sX", rollout_id="rX", eval_seed="B1")
        r = self.ev.evaluate(self.g, self.task, replicate_id=0,
                             state_id="sX", rollout_id="rX", eval_seed="B1")
        self.assertTrue(r.from_cache)

    def test_cache_no_hit_for_different_eval_seed(self):
        self.ev.evaluate(self.g, self.task, replicate_id=0,
                         state_id="sX", rollout_id="rX", eval_seed="B1")
        r = self.ev.evaluate(self.g, self.task, replicate_id=0,
                             state_id="sX", rollout_id="rX", eval_seed="B2")
        self.assertFalse(r.from_cache)


# ===== R26: protocol document consistency =====
class TestR26ProtocolDocument(unittest.TestCase):
    def test_protocol_document_exists(self):
        path = os.path.join(REPO, "research", "PC1_PROTOCOL_R4_PROPOSED.md")
        self.assertTrue(os.path.exists(path), "PC1_PROTOCOL_R4_PROPOSED.md must exist")

    def test_document_says_proposed(self):
        path = os.path.join(REPO, "research", "PC1_PROTOCOL_R4_PROPOSED.md")
        content = open(path, encoding="utf-8").read()
        self.assertIn("PROPOSED", content)
        self.assertIn("NOT APPROVED", content)

    def test_document_fields_match_code(self):
        """R26: parse the document's canonical field block and compare to code."""
        path = os.path.join(REPO, "research", "PC1_PROTOCOL_R4_PROPOSED.md")
        content = open(path, encoding="utf-8").read()
        # extract JSON block from the canonical field block section
        match = re.search(r'```json\s*\n(\{[^`]+\})\s*\n```', content)
        self.assertIsNotNone(match, "canonical field block JSON not found")
        doc = json.loads(match.group(1))
        self.assertEqual(doc["n_states"], N_STATES)
        self.assertEqual(doc["n_actions"], N_ACTIONS)
        self.assertEqual(doc["q_rollouts"], Q_ROLLOUTS)
        self.assertEqual(doc["horizon"], HORIZON)
        self.assertEqual(doc["extra_immediate"], EXTRA_IMMEDIATE)
        self.assertEqual(doc["n_collection_episodes"], N_STATE_COLLECTION_EPISODES)
        self.assertEqual(doc["budget"]["total"], PLANNED_TOTAL_SLOTS)
        self.assertEqual(doc["budget"]["hard_cap"], HARD_CAP_SLOTS)

    def test_code_version_not_frozen(self):
        self.assertIn("proposed", PROTOCOL_VERSION.lower())

    def test_status_is_proposed(self):
        self.assertIn("PROPOSED", PROTOCOL_STATUS)


# ===== R31: gate semantics =====
class TestR31GateSemantics(unittest.TestCase):
    def test_all_booleans_true_still_denied_for_proposed_protocol(self):
        """R31: even with approved=True, proposed protocol must be denied."""
        runner = SyntheticGateHarness(
            approval_gate=ApprovalGate(approved=True, protocol_status="PROPOSED",
                                       approver="x", approval_date="2026-01-01"),
            production_gate=ProductionRuntimeGate(ready=True, runtime_revision="r1"),
            protocol_gate=ProtocolVersionGate(),
        )
        with self.assertRaises(PC1ExecutionRefused):
            runner.execute_unit("u1", PROTOCOL_VERSION, 10, 8, 0)

    def test_missing_approval_metadata_denied(self):
        runner = SyntheticGateHarness(
            approval_gate=ApprovalGate(approved=True, protocol_status="APPROVED",
                                       approver="", approval_date=""),
            production_gate=ProductionRuntimeGate(ready=True, runtime_revision="r1"),
            protocol_gate=ProtocolVersionGate(),
        )
        with self.assertRaises(PC1ExecutionRefused):
            runner.execute_unit("u1", PROTOCOL_VERSION, 10, 8, 0)

    def test_runtime_revision_mismatch_denied(self):
        runner = SyntheticGateHarness(
            approval_gate=ApprovalGate(approved=True, protocol_status="APPROVED",
                                       approver="x", approval_date="2026-01-01"),
            production_gate=ProductionRuntimeGate(ready=True, runtime_revision="r1",
                                                   required_revision="r2"),
            protocol_gate=ProtocolVersionGate(),
        )
        with self.assertRaises(PC1ExecutionRefused):
            runner.execute_unit("u1", PROTOCOL_VERSION, 10, 8, 0)

    def test_protocol_hash_mismatch_denied(self):
        runner = SyntheticGateHarness(
            approval_gate=ApprovalGate(approved=True, protocol_status="APPROVED",
                                       approver="x", approval_date="2026-01-01",
                                       protocol_hash="abc", expected_protocol_hash="xyz"),
            production_gate=ProductionRuntimeGate(ready=True, runtime_revision="r1"),
            protocol_gate=ProtocolVersionGate(),
        )
        with self.assertRaises(PC1ExecutionRefused):
            runner.execute_unit("u1", PROTOCOL_VERSION, 10, 8, 0)

    def test_registered_execution_still_refused(self):
        with self.assertRaises(PC1ExecutionRefused):
            execute_registered_pc1()

    def test_runner_is_harness_not_collector(self):
        """R31: verify the class is described as a harness, not a full runner."""
        harness = create_default_gated_runner()
        self.assertIsInstance(harness, SyntheticGateHarness)
        self.assertIn("harness", SyntheticGateHarness.__doc__.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
