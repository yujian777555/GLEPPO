"""R57-R59 regression tests. No PC1 execution, no Family C."""
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
    PlannerApprovalRecord, TrustedApprovalArtifact,
    SyntheticGateHarness, create_default_gated_runner,
    CANONICAL_PROTOCOL, PROTOCOL_VERSION, PROTOCOL_STATUS,
    REGISTERED_PROTOCOL_CONTENT_HASH, REGISTERED_PLAN_HASH,
    protocol_consistency_check, parse_protocol_document, compute_protocol_hash,
    generate_plan_mapping, get_plan_mapping, get_registered_plan_hash,
    save_plan_artifact, load_plan_artifact,
    crn_seed, run_pc1_analysis, execute_registered_pc1,
    generate_pc1_dry_run_plan,
    ROLE_Q, ROLE_EXTRA, N_ACTIONS, HORIZON, Q_ROLLOUTS, EXTRA_IMMEDIATE,
    N_STATES, HARD_CAP_SLOTS, PLANNED_TOTAL_SLOTS,
)
from gleppo.evaluator import Evaluator
from gleppo.genotype import make_valid_genotype
from gleppo.interpreter import Interpreter
from gleppo.tasks import build_task, attach_checker

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEST_KEY = b"test-approval-key-not-for-production"


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


# ===== R57+R54: approval gate tests =====
class TestR54ApprovalGate(unittest.TestCase):
    def _real_hash(self):
        return compute_protocol_hash(parse_protocol_document())

    def test_proposed_rejects_all_flags_true(self):
        """R54: PROPOSED canonical status rejects even with all flags set."""
        doc = parse_protocol_document()
        if doc.get("status") != "PROPOSED_NOT_APPROVED":
            self.skipTest("protocol not in PROPOSED state")
        art = TrustedApprovalArtifact(
            artifact_id="A1", approver="test", approval_date="2026-01-01",
            protocol_hash=self._real_hash(), protocol_version=PROTOCOL_VERSION,
            approval_action="APPROVE_PC1_PROTOCOL", authorization_status="APPROVED",
            protocol_document_id="PC1_PROTOCOL_R4_PROPOSED",
        )
        art.signature = TrustedApprovalArtifact.sign(art, TEST_KEY)
        gate = ApprovalGate(
            approved=True, protocol_status="APPROVED",
            protocol_hash=self._real_hash(), expected_protocol_hash=self._real_hash(),
            trusted_artifact=art, approval_key=TEST_KEY,
        )
        with self.assertRaises(PC1ExecutionRefused):
            gate.check()

    def test_no_signature_rejected(self):
        art = TrustedApprovalArtifact(
            artifact_id="A1", approver="test", approval_date="2026-01-01",
            protocol_hash=self._real_hash(), protocol_version=PROTOCOL_VERSION,
            approval_action="APPROVE_PC1_PROTOCOL", authorization_status="APPROVED",
            protocol_document_id="PC1_PROTOCOL_R4_PROPOSED",
        )
        # signature left empty
        with self.assertRaises(PC1ExecutionRefused):
            art.verify(self._real_hash(), PROTOCOL_VERSION, TEST_KEY)

    def test_wrong_signature_rejected(self):
        art = TrustedApprovalArtifact(
            artifact_id="A1", approver="test", approval_date="2026-01-01",
            protocol_hash=self._real_hash(), protocol_version=PROTOCOL_VERSION,
            approval_action="APPROVE_PC1_PROTOCOL", authorization_status="APPROVED",
            protocol_document_id="PC1_PROTOCOL_R4_PROPOSED",
        )
        art.signature = "forged_signature"
        with self.assertRaises(PC1ExecutionRefused):
            art.verify(self._real_hash(), PROTOCOL_VERSION, TEST_KEY)

    def test_wrong_action_rejected(self):
        art = TrustedApprovalArtifact(
            artifact_id="A1", approver="test", approval_date="2026-01-01",
            protocol_hash=self._real_hash(), protocol_version=PROTOCOL_VERSION,
            approval_action="APPROVE",  # wrong
            authorization_status="APPROVED",
            protocol_document_id="PC1_PROTOCOL_R4_PROPOSED",
        )
        art.signature = TrustedApprovalArtifact.sign(art, TEST_KEY)
        with self.assertRaises(PC1ExecutionRefused):
            art.verify(self._real_hash(), PROTOCOL_VERSION, TEST_KEY)

    def test_wrong_status_rejected(self):
        art = TrustedApprovalArtifact(
            artifact_id="A1", approver="test", approval_date="2026-01-01",
            protocol_hash=self._real_hash(), protocol_version=PROTOCOL_VERSION,
            approval_action="APPROVE_PC1_PROTOCOL",
            authorization_status="NOT_APPROVED",
            protocol_document_id="PC1_PROTOCOL_R4_PROPOSED",
        )
        art.signature = TrustedApprovalArtifact.sign(art, TEST_KEY)
        with self.assertRaises(PC1ExecutionRefused):
            art.verify(self._real_hash(), PROTOCOL_VERSION, TEST_KEY)

    def test_wrong_document_id_rejected(self):
        art = TrustedApprovalArtifact(
            artifact_id="A1", approver="test", approval_date="2026-01-01",
            protocol_hash=self._real_hash(), protocol_version=PROTOCOL_VERSION,
            approval_action="APPROVE_PC1_PROTOCOL", authorization_status="APPROVED",
            protocol_document_id="WRONG_DOC",
        )
        art.signature = TrustedApprovalArtifact.sign(art, TEST_KEY)
        with self.assertRaises(PC1ExecutionRefused):
            art.verify(self._real_hash(), PROTOCOL_VERSION, TEST_KEY)

    def test_wrong_protocol_hash_rejected(self):
        art = TrustedApprovalArtifact(
            artifact_id="A1", approver="test", approval_date="2026-01-01",
            protocol_hash="wrong_hash", protocol_version=PROTOCOL_VERSION,
            approval_action="APPROVE_PC1_PROTOCOL", authorization_status="APPROVED",
            protocol_document_id="PC1_PROTOCOL_R4_PROPOSED",
        )
        art.signature = TrustedApprovalArtifact.sign(art, TEST_KEY)
        with self.assertRaises(PC1ExecutionRefused):
            art.verify(self._real_hash(), PROTOCOL_VERSION, TEST_KEY)

    def test_bad_date_rejected(self):
        art = TrustedApprovalArtifact(
            artifact_id="A1", approver="test", approval_date="2026-99-99",
            protocol_hash=self._real_hash(), protocol_version=PROTOCOL_VERSION,
            approval_action="APPROVE_PC1_PROTOCOL", authorization_status="APPROVED",
            protocol_document_id="PC1_PROTOCOL_R4_PROPOSED",
        )
        art.signature = TrustedApprovalArtifact.sign(art, TEST_KEY)
        with self.assertRaises(PC1ExecutionRefused):
            art.verify(self._real_hash(), PROTOCOL_VERSION, TEST_KEY)

    def test_registered_execution_refused(self):
        with self.assertRaises(PC1ExecutionRefused):
            execute_registered_pc1()


# ===== R57+R55: plan binding tests =====
class TestR55PlanBinding(unittest.TestCase):
    def test_missing_protocol_hash_rejected(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        save_plan_artifact(path)
        with open(path) as f:
            art = json.load(f)
        del art["protocol_content_hash"]
        with open(path, "w") as f:
            json.dump(art, f)
        with self.assertRaises(ValueError):
            load_plan_artifact(path)
        os.unlink(path)

    def test_wrong_protocol_hash_rejected(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        save_plan_artifact(path)
        with open(path) as f:
            art = json.load(f)
        art["protocol_content_hash"] = "wrong_hash"
        with open(path, "w") as f:
            json.dump(art, f)
        with self.assertRaises(ValueError):
            load_plan_artifact(path)
        os.unlink(path)

    def test_alternative_mapping_rejected(self):
        """R55: even with recomputed self-hash, noncanonical plan is rejected."""
        mapping, _ = get_plan_mapping()
        mapping["s000"]["episode_id"] = "tampered"
        import hashlib
        canonical = json.dumps(mapping, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        new_hash = hashlib.sha256(canonical.encode()).hexdigest()[:32]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        # save with correct plan_id/version but wrong mapping
        art = {
            "plan_id": "pc1-plan-v1", "plan_version": "1.0",
            "plan_hash": new_hash,
            "protocol_content_hash": REGISTERED_PROTOCOL_CONTENT_HASH,
            "mapping": mapping,
        }
        with open(path, "w") as f:
            json.dump(art, f)
        with self.assertRaises(ValueError):
            load_plan_artifact(path)
        os.unlink(path)

    def test_canonical_roundtrip(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        h1 = save_plan_artifact(path)
        m2, h2 = load_plan_artifact(path)
        self.assertEqual(h1, h2)
        self.assertEqual(len(m2), N_STATES)
        os.unlink(path)


# ===== R57+R56: strict type tests =====
class TestR56StrictTypes(unittest.TestCase):
    def _make_doc_with_reward(self, w_best_val):
        doc = parse_protocol_document()
        doc["reward_contract"] = {
            "w_best": w_best_val, "w_valid": 0.1, "w_mean": 0.25,
            "clip_lo": -0.5, "clip_hi": 1.0,
        }
        return doc

    def _check_doc(self, doc):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# T\n\n```json\n" + json.dumps(doc) + "\n```\n")
            path = f.name
        r = protocol_consistency_check(path)
        os.unlink(path)
        return r

    def test_bool_true_rejected(self):
        r = self._check_doc(self._make_doc_with_reward(True))
        self.assertFalse(r["all_pass"])

    def test_bool_false_rejected(self):
        r = self._check_doc(self._make_doc_with_reward(False))
        self.assertFalse(r["all_pass"])

    def test_string_rejected(self):
        r = self._check_doc(self._make_doc_with_reward("1.0"))
        self.assertFalse(r["all_pass"])

    def test_missing_field_rejected(self):
        doc = parse_protocol_document()
        doc["reward_contract"] = {"w_valid": 0.1, "w_mean": 0.25, "clip_lo": -0.5, "clip_hi": 1.0}
        r = self._check_doc(doc)
        self.assertFalse(r["all_pass"])

    def test_extra_field_rejected(self):
        doc = parse_protocol_document()
        rc = dict(doc["reward_contract"])
        rc["extra_term"] = 99.0
        doc["reward_contract"] = rc
        r = self._check_doc(doc)
        self.assertFalse(r["all_pass"])

    def test_valid_numbers_pass(self):
        r = self._check_doc(self._make_doc_with_reward(1.0))
        self.assertTrue(r["all_pass"])


# ===== R58: registered protocol hash =====
class TestR58RegisteredProtocolHash(unittest.TestCase):
    def test_registered_hash_matches_computed(self):
        doc = parse_protocol_document()
        computed = compute_protocol_hash(doc)
        self.assertEqual(computed, REGISTERED_PROTOCOL_CONTENT_HASH)

    def test_save_fails_on_hash_mismatch(self):
        """R61: save_plan_artifact raises when current protocol hash != registered."""
        # Use a temp protocol doc with modified content so computed hash != registered
        doc = parse_protocol_document()
        doc["n_states"] = 999  # change a decision-critical field
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# T\n\n```json\n" + json.dumps(doc) + "\n```\n")
            bad_path = f.name
        # Temporarily monkey-patch parse_protocol_document to return the bad doc
        import gleppo.pc1 as pc1_mod
        orig_parse = pc1_mod.parse_protocol_document
        try:
            pc1_mod.parse_protocol_document = lambda path=None: doc
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                path = f.name
            with self.assertRaises(ValueError):
                save_plan_artifact(path)
            # Verify no valid artifact was written
            if os.path.exists(path):
                with open(path) as f:
                    content = f.read()
                self.assertNotIn("plan_hash", content, "no valid artifact should be written")
            os.unlink(path)
        finally:
            pc1_mod.parse_protocol_document = orig_parse
            os.unlink(bad_path)

    def test_save_load_roundtrip_normal(self):
        """R61: valid protocol allows normal save/load/roundtrip."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        h1 = save_plan_artifact(path)
        m2, h2 = load_plan_artifact(path)
        self.assertEqual(h1, h2)
        self.assertEqual(len(m2), N_STATES)
        os.unlink(path)


# ===== R59: protocol document ID =====
class TestR59DocumentID(unittest.TestCase):
    def test_wrong_doc_id_rejected(self):
        art = TrustedApprovalArtifact(
            artifact_id="A1", approver="test", approval_date="2026-01-01",
            protocol_hash=REGISTERED_PROTOCOL_CONTENT_HASH, protocol_version=PROTOCOL_VERSION,
            approval_action="APPROVE_PC1_PROTOCOL", authorization_status="APPROVED",
            protocol_document_id="WRONG",
        )
        import hmac
        payload = art._canonical_payload().encode("utf-8")
        art.signature = hmac.new(b"test-key", payload, "sha256").hexdigest()
        with self.assertRaises(PC1ExecutionRefused):
            art.verify(REGISTERED_PROTOCOL_CONTENT_HASH, PROTOCOL_VERSION, b"test-key")


if __name__ == "__main__":
    unittest.main(verbosity=2)
