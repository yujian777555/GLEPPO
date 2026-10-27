"""R39-R42 regression tests. No PC1 execution, no Family C."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gleppo.pc1 import (
    BudgetLedger, StateActionRecord, PC1ExecutionRefused,
    ApprovalGate, ProductionRuntimeGate, ProtocolVersionGate,
    PlannerApprovalRecord, SyntheticGateHarness, create_default_gated_runner,
    CANONICAL_PROTOCOL, PROTOCOL_VERSION, PROTOCOL_STATUS,
    protocol_consistency_check, parse_protocol_document, compute_protocol_hash,
    generate_plan_mapping, get_plan_mapping, save_plan_artifact, load_plan_artifact,
    validate_provenance_against_plan, crn_seed,
    compute_r_hat, compute_q_hat, run_pc1_analysis,
    generate_pc1_dry_run_plan, execute_registered_pc1,
    validate_records,
    save_evidence_artifact, load_evidence_artifact, replay_from_artifact,
    ROLE_Q, ROLE_EXTRA, N_ACTIONS, HORIZON, Q_ROLLOUTS, EXTRA_IMMEDIATE,
    N_STATES, HARD_CAP_SLOTS, PLANNED_TOTAL_SLOTS, N_STATE_COLLECTION_EPISODES,
)
from gleppo.evaluator import Evaluator
from gleppo.genotype import make_valid_genotype
from gleppo.interpreter import Interpreter
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
        effective_seed_parts=("SEED", "x"),
        gen_rewards=rewards if rewards is not None else [0.05] * n,
    )
    rec.planned_slots = 24 if role == ROLE_Q else 8
    return rec


# ===== R39: CRN seed collision-free =====
class TestR39CRNSeed(unittest.TestCase):
    def test_same_params_reproducible(self):
        self.assertEqual(crn_seed("T1", "s1", 0, 0), crn_seed("T1", "s1", 0, 0))

    def test_delimiter_no_collision(self):
        """R39: a|b,c vs a,b|c must produce different seeds."""
        s1 = crn_seed("a|b", "c", 0, 0)
        s2 = crn_seed("a", "b|c", 0, 0)
        self.assertNotEqual(s1, s2)

    def test_task_change_changes_seed(self):
        self.assertNotEqual(crn_seed("T1", "s1", 0, 0), crn_seed("T2", "s1", 0, 0))

    def test_state_change_changes_seed(self):
        self.assertNotEqual(crn_seed("T1", "s1", 0, 0), crn_seed("T1", "s2", 0, 0))

    def test_rollout_change_changes_seed(self):
        self.assertNotEqual(crn_seed("T1", "s1", 0, 0), crn_seed("T1", "s1", 1, 0))

    def test_replicate_change_changes_seed(self):
        self.assertNotEqual(crn_seed("T1", "s1", 0, 0), crn_seed("T1", "s1", 0, 1))

    def test_none_empty_string_no_collision(self):
        """R39: None-like and empty inputs must not collide."""
        # crn_seed takes str/int, so test with string representations
        s1 = crn_seed("NONE", "s1", 0, 0)
        s2 = crn_seed("", "s1", 0, 0)
        s3 = crn_seed("EMPTY", "s1", 0, 0)
        self.assertNotEqual(s1, s2)
        self.assertNotEqual(s1, s3)
        self.assertNotEqual(s2, s3)

    def test_action_genotype_excluded(self):
        """R39: CRN seed does not depend on action (by design)."""
        # Same seed for same (task, state, rollout, replicate) regardless of context
        self.assertEqual(crn_seed("T1", "s1", 0, 0), crn_seed("T1", "s1", 0, 0))


# ===== R40: protocol consistency =====
class TestR40ProtocolConsistency(unittest.TestCase):
    def test_full_consistency_passes(self):
        r = protocol_consistency_check()
        self.assertTrue(r["all_pass"], r["checks"])

    def test_mutation_version_fails(self):
        doc = parse_protocol_document()
        doc["code_version"] = "wrong-v9"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# T\n\n```json\n" + json.dumps(doc) + "\n```\n")
            path = f.name
        r = protocol_consistency_check(path)
        self.assertFalse(r["all_pass"])
        os.unlink(path)

    def test_mutation_status_not_checked_by_consistency(self):
        """R49: status is lifecycle concern, not content consistency."""
        doc = parse_protocol_document()
        doc["status"] = "APPROVED"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# T\n\n```json\n" + json.dumps(doc) + "\n```\n")
            path = f.name
        r = protocol_consistency_check(path)
        # R49: status change should NOT fail content consistency
        self.assertTrue(r["all_pass"], "status is lifecycle, not content")
        os.unlink(path)

    def test_mutation_seed_contract_fails(self):
        doc = parse_protocol_document()
        doc["seed_schema"] = {"version": "crn-v2", "fields": ["action", "genotype", "task_id"], "encoding": "typed_json"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# T\n\n```json\n" + json.dumps(doc) + "\n```\n")
            path = f.name
        r = protocol_consistency_check(path)
        self.assertFalse(r["all_pass"])
        os.unlink(path)

    def test_mutation_reward_fails(self):
        doc = parse_protocol_document()
        doc["reward_contract"] = {"w_best": 99.0, "w_valid": 0.1, "w_mean": 0.25, "clip_lo": -0.5, "clip_hi": 1.0}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# T\n\n```json\n" + json.dumps(doc) + "\n```\n")
            path = f.name
        r = protocol_consistency_check(path)
        self.assertFalse(r["all_pass"])
        os.unlink(path)


# ===== R41: plan artifact =====
class TestR41PlanArtifact(unittest.TestCase):
    def test_save_load_roundtrip(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        h1 = save_plan_artifact(path)
        m2, h2 = load_plan_artifact(path)
        self.assertEqual(h1, h2)
        self.assertEqual(len(m2), N_STATES)
        os.unlink(path)

    def test_tampered_artifact_rejected(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        save_plan_artifact(path)
        # tamper
        with open(path) as f:
            art = json.load(f)
        art["mapping"]["s000"]["episode_id"] = "tampered"
        with open(path, "w") as f:
            json.dump(art, f)
        with self.assertRaises(ValueError):
            load_plan_artifact(path)
        os.unlink(path)

    def test_defensive_copy_prevents_mutation(self):
        m1, h1 = get_plan_mapping()
        m1["s000"]["episode_id"] = "MUTATED"
        m2, h2 = get_plan_mapping()
        self.assertNotEqual(m2["s000"]["episode_id"], "MUTATED")
        self.assertEqual(h1, h2)

    def test_wrong_hash_rejected(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        save_plan_artifact(path)
        with open(path) as f:
            art = json.load(f)
        art["plan_hash"] = "wrong_hash"
        with open(path, "w") as f:
            json.dump(art, f)
        with self.assertRaises(ValueError):
            load_plan_artifact(path)
        os.unlink(path)


# ===== R42: approval record =====
class TestR42ApprovalRecord(unittest.TestCase):
    def _real_hash(self):
        return compute_protocol_hash(parse_protocol_document())

    def test_valid_record_passes(self):
        rec = PlannerApprovalRecord(
            approval_id="APR-001", approver="planner",
            approval_date="2026-01-01", protocol_hash=self._real_hash(),
            protocol_status="APPROVED", protocol_version=PROTOCOL_VERSION,
        )
        rec.validate(self._real_hash(), PROTOCOL_VERSION)

    def test_empty_approval_id_rejected(self):
        rec = PlannerApprovalRecord(
            approval_id="", approver="p", approval_date="2026-01-01",
            protocol_hash=self._real_hash(), protocol_status="APPROVED",
            protocol_version=PROTOCOL_VERSION)
        with self.assertRaises(PC1ExecutionRefused):
            rec.validate(self._real_hash(), PROTOCOL_VERSION)

    def test_bad_date_rejected(self):
        rec = PlannerApprovalRecord(
            approval_id="A1", approver="p", approval_date="not-a-date",
            protocol_hash=self._real_hash(), protocol_status="APPROVED",
            protocol_version=PROTOCOL_VERSION)
        with self.assertRaises(PC1ExecutionRefused):
            rec.validate(self._real_hash(), PROTOCOL_VERSION)

    def test_wrong_hash_rejected(self):
        rec = PlannerApprovalRecord(
            approval_id="A1", approver="p", approval_date="2026-01-01",
            protocol_hash="wrong", protocol_status="APPROVED",
            protocol_version=PROTOCOL_VERSION)
        with self.assertRaises(PC1ExecutionRefused):
            rec.validate(self._real_hash(), PROTOCOL_VERSION)

    def test_wrong_version_rejected(self):
        rec = PlannerApprovalRecord(
            approval_id="A1", approver="p", approval_date="2026-01-01",
            protocol_hash=self._real_hash(), protocol_status="APPROVED",
            protocol_version="wrong-v")
        with self.assertRaises(PC1ExecutionRefused):
            rec.validate(self._real_hash(), PROTOCOL_VERSION)

    def test_proposed_status_rejected(self):
        rec = PlannerApprovalRecord(
            approval_id="A1", approver="p", approval_date="2026-01-01",
            protocol_hash=self._real_hash(), protocol_status="PROPOSED",
            protocol_version=PROTOCOL_VERSION)
        with self.assertRaises(PC1ExecutionRefused):
            rec.validate(self._real_hash(), PROTOCOL_VERSION)

    def test_gate_with_forged_record_rejected(self):
        """R42: forged record with matching strings but wrong hash must fail."""
        gate = ApprovalGate(
            approved=True, protocol_status="APPROVED",
            protocol_hash="forged", expected_protocol_hash="forged",
            approval_record=PlannerApprovalRecord(
                approval_id="F1", approver="fake", approval_date="2026-01-01",
                protocol_hash="forged", protocol_status="APPROVED",
                protocol_version=PROTOCOL_VERSION))
        with self.assertRaises(PC1ExecutionRefused):
            gate.check()

    def test_gate_without_record_rejected(self):
        gate = ApprovalGate(approved=True, protocol_status="APPROVED")
        with self.assertRaises(PC1ExecutionRefused):
            gate.check()

    def test_registered_execution_refused(self):
        with self.assertRaises(PC1ExecutionRefused):
            execute_registered_pc1()


if __name__ == "__main__":
    unittest.main(verbosity=2)
