"""PC1 myopia-diagnostic protocol: budget ledger, validation, estimators, runner.

R12: BudgetLedger receives explicit actual_replicas_run deltas (no unit mixing).
R13: fail-closed validation of StateActionRecord collections.
R14: sample roles (q_rollout / extra_immediate); r_hat = Q-first-rewards + extra;
     Q_hat uses only complete q_rollout records. Estimator per PC1_INDEPENDENT_REVIEW.
R15: guarded collection/rollout orchestration entry point (dry-run / synthetic only).
R16: one seed contract — see gleppo/evaluator.py:effective_seed_parts.
R17: replayable raw evidence artifact.

PC1 must NOT be executed until independent review approves AND production gate passes.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .reward import generation_reward, discounted_return, GAMMA

PROTOCOL_VERSION = "pc1-proposed-v1-r5"
ESTIMATOR_VERSION = "est-v1-r_hat=q_first+extra,q_hat=q_rollout_only"
PROTOCOL_STATUS = "PROPOSED_NOT_APPROVED"

# ---- Pre-registered thresholds (UNCHANGED) ----
THRESHOLD_D = 0.15
THRESHOLD_ADVANTAGE = 0.02
MARGIN_D = 0.10
MARGIN_ADV = 0.01

# ---- Budget ----
N_STATES = 100
N_ACTIONS = 5
Q_ROLLOUTS = 3
HORIZON = 3
LAMBDA = 4
N_EVAL = 2
MU = 8
EXTRA_IMMEDIATE = 1
N_STATE_COLLECTION_EPISODES = 40
T_COLLECT = 15

PLANNED_Q_SLOTS = N_STATES * N_ACTIONS * Q_ROLLOUTS * HORIZON * LAMBDA * N_EVAL
PLANNED_EXTRA_SLOTS = N_STATES * N_ACTIONS * EXTRA_IMMEDIATE * LAMBDA * N_EVAL
PLANNED_COLLECTION_SLOTS = N_STATE_COLLECTION_EPISODES * (MU * N_EVAL + T_COLLECT * LAMBDA * N_EVAL)
PLANNED_TOTAL_SLOTS = PLANNED_Q_SLOTS + PLANNED_EXTRA_SLOTS + PLANNED_COLLECTION_SLOTS
HARD_CAP_SLOTS = 50000

# R14 sample roles
ROLE_Q = "q_rollout"
ROLE_EXTRA = "extra_immediate"
VALID_ROLES = frozenset({ROLE_Q, ROLE_EXTRA})

# ---- R19: canonical frozen protocol (single source of truth) ----
CANONICAL_PROTOCOL = {
    "protocol_version": PROTOCOL_VERSION,
    "estimator_version": ESTIMATOR_VERSION,
    "status": PROTOCOL_STATUS,
    "n_states": N_STATES, "n_actions": N_ACTIONS,
    "q_rollouts": Q_ROLLOUTS, "horizon": HORIZON,
    "extra_immediate": EXTRA_IMMEDIATE,
    "gamma": GAMMA,
    "thresholds": {"D": THRESHOLD_D, "advantage": THRESHOLD_ADVANTAGE,
                    "margin_D": MARGIN_D, "margin_adv": MARGIN_ADV},
    "budget": {"q_slots": PLANNED_Q_SLOTS, "extra_slots": PLANNED_EXTRA_SLOTS,
                "collection_slots": PLANNED_COLLECTION_SLOTS,
                "total": PLANNED_TOTAL_SLOTS, "hard_cap": HARD_CAP_SLOTS},
    "estimator": {
        "r_hat": "mean of Q-rollout first rewards + extra_immediate rewards",
        "q_hat": "h-step discounted return of q_rollout records only",
        "reward": "gleppo.reward.generation_reward",
        "continuation": "fixed random policy",
    },
    "cluster_unit": "collection_episode",
    "n_clusters": N_STATE_COLLECTION_EPISODES,
}


class _DuplicateKeyChecker(json.JSONDecoder):
    """R45: reject duplicate JSON object keys."""
    def __init__(self, *args, **kwargs):
        super().__init__(object_pairs_hook=self._check_duplicates, *args, **kwargs)

    @staticmethod
    def _check_duplicates(pairs):
        seen = set()
        for key, _ in pairs:
            if key in seen:
                raise ValueError(f"R45: duplicate JSON key '{key}' in protocol document")
            seen.add(key)
        return dict(pairs)


def parse_protocol_document(path: Optional[str] = None) -> dict:
    """R36/R45: parse canonical JSON block; reject duplicate keys."""
    import re as _re
    if path is None:
        import os as _os
        path = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                             "research", "PC1_PROTOCOL_R4_PROPOSED.md")
    with open(path, encoding="utf-8") as f:
        content = f.read()
    match = _re.search(r'```json\s*\n(\{[^`]+\})\s*\n```', content)
    if not match:
        raise ValueError(f"R36: no canonical JSON block found in {path}")
    return json.loads(match.group(1), cls=_DuplicateKeyChecker)


def compute_protocol_hash(doc: dict) -> str:
    """R53: hash of IMMUTABLE protocol content, excluding lifecycle status.

    Lifecycle fields (status, approval metadata) are NOT part of the content
    hash. Changing only lifecycle status leaves the content hash unchanged.
    """
    # R53: filter out lifecycle fields before hashing
    content_fields = {k: v for k, v in doc.items()
                      if k not in ("status", "approval", "approval_id",
                                   "approver", "approval_date", "approval_secret_hash")}
    canonical = json.dumps(content_fields, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


def protocol_consistency_check(path: Optional[str] = None) -> dict:
    """R36: verify code constants match the ACTUAL protocol document (not just code dict)."""
    checks: Dict[str, Tuple[bool, str]] = {}
    try:
        doc = parse_protocol_document(path)
    except Exception as e:
        return {"all_pass": False,
                "checks": {"doc_parse": {"ok": False, "detail": str(e)}}, "doc_hash": ""}

    doc_hash = compute_protocol_hash(doc)

    # R36: compare ALL decision-critical fields against code
    checks["doc_n_states"] = (doc.get("n_states") == N_STATES, f"{doc.get('n_states')} vs {N_STATES}")
    checks["doc_n_actions"] = (doc.get("n_actions") == N_ACTIONS, f"{doc.get('n_actions')} vs {N_ACTIONS}")
    checks["doc_q_rollouts"] = (doc.get("q_rollouts") == Q_ROLLOUTS, f"{doc.get('q_rollouts')} vs {Q_ROLLOUTS}")
    checks["doc_horizon"] = (doc.get("horizon") == HORIZON, f"{doc.get('horizon')} vs {HORIZON}")
    checks["doc_extra_immediate"] = (doc.get("extra_immediate") == EXTRA_IMMEDIATE, f"{doc.get('extra_immediate')} vs {EXTRA_IMMEDIATE}")
    checks["doc_gamma"] = (doc.get("gamma") == GAMMA, f"{doc.get('gamma')} vs {GAMMA}")
    checks["doc_n_episodes"] = (doc.get("n_collection_episodes") == N_STATE_COLLECTION_EPISODES,
                                f"{doc.get('n_collection_episodes')} vs {N_STATE_COLLECTION_EPISODES}")

    thresh = doc.get("thresholds", {})
    checks["doc_thresh_D"] = (thresh.get("D") == THRESHOLD_D, f"{thresh.get('D')} vs {THRESHOLD_D}")
    checks["doc_thresh_adv"] = (thresh.get("advantage") == THRESHOLD_ADVANTAGE, f"{thresh.get('advantage')} vs {THRESHOLD_ADVANTAGE}")
    checks["doc_margin_D"] = (thresh.get("margin_D") == MARGIN_D, f"{thresh.get('margin_D')} vs {MARGIN_D}")
    checks["doc_margin_adv"] = (thresh.get("margin_adv") == MARGIN_ADV, f"{thresh.get('margin_adv')} vs {MARGIN_ADV}")

    budget = doc.get("budget", {})
    checks["doc_budget_q"] = (budget.get("q_slots") == PLANNED_Q_SLOTS, f"{budget.get('q_slots')} vs {PLANNED_Q_SLOTS}")
    checks["doc_budget_extra"] = (budget.get("extra_slots") == PLANNED_EXTRA_SLOTS, f"{budget.get('extra_slots')} vs {PLANNED_EXTRA_SLOTS}")
    checks["doc_budget_collection"] = (budget.get("collection_slots") == PLANNED_COLLECTION_SLOTS, f"{budget.get('collection_slots')} vs {PLANNED_COLLECTION_SLOTS}")
    checks["doc_budget_total"] = (budget.get("total") == PLANNED_TOTAL_SLOTS == 45440, f"{budget.get('total')} vs {PLANNED_TOTAL_SLOTS}")
    checks["doc_budget_cap"] = (budget.get("hard_cap") == HARD_CAP_SLOTS == 50000, f"{budget.get('hard_cap')} vs {HARD_CAP_SLOTS}")

    # R36: estimator and contract strings
    checks["doc_cluster_unit"] = (doc.get("cluster_unit") == "collection_episode", doc.get("cluster_unit", ""))
    # R49: content consistency does NOT check lifecycle status (separate concern)
    # Status is validated by the approval gate, not by content consistency.
    # We only check that a status field exists and is non-empty.
    checks["doc_status_present"] = (bool(doc.get("status", "").strip()), doc.get("status", ""))
    checks["doc_code_version"] = (doc.get("code_version") == PROTOCOL_VERSION,
                                  f"{doc.get('code_version')} vs {PROTOCOL_VERSION}")

    # R52: strict schema validation — reject unknown keys, enforce exact types
    from .reward import W_BEST, W_VALID, W_MEAN, REWARD_CLIP_LO, REWARD_CLIP_HI

    def _check_exact_keys(obj: dict, expected_keys: set, name: str) -> bool:
        actual = set(obj.keys()) if isinstance(obj, dict) else set()
        return actual == expected_keys

    def _is_strict_number(val) -> bool:
        """R56: must be int or float, NOT bool."""
        return isinstance(val, (int, float)) and not isinstance(val, bool)

    # R52: reward contract — exact keys, exact types
    reward_contract = doc.get("reward_contract", {})
    expected_reward_keys = {"w_best", "w_valid", "w_mean", "clip_lo", "clip_hi"}
    checks["doc_reward_schema"] = (_check_exact_keys(reward_contract, expected_reward_keys, "reward"),
                                   str(sorted(reward_contract.keys())))
    checks["doc_reward_w_best"] = (_is_strict_number(reward_contract.get("w_best"))
                                    and reward_contract.get("w_best") == W_BEST, str(reward_contract.get("w_best")))
    checks["doc_reward_w_valid"] = (_is_strict_number(reward_contract.get("w_valid"))
                                     and reward_contract.get("w_valid") == W_VALID, str(reward_contract.get("w_valid")))
    checks["doc_reward_w_mean"] = (_is_strict_number(reward_contract.get("w_mean"))
                                    and reward_contract.get("w_mean") == W_MEAN, str(reward_contract.get("w_mean")))
    checks["doc_reward_clip_lo"] = (_is_strict_number(reward_contract.get("clip_lo"))
                                     and reward_contract.get("clip_lo") == REWARD_CLIP_LO, str(reward_contract.get("clip_lo")))
    checks["doc_reward_clip_hi"] = (_is_strict_number(reward_contract.get("clip_hi"))
                                     and reward_contract.get("clip_hi") == REWARD_CLIP_HI, str(reward_contract.get("clip_hi")))
    # R52: estimator contract — exact keys, exact types
    est_contract = doc.get("estimator_contract", {})
    expected_est_keys = {"horizon", "gamma", "r_hat_sources", "q_hat_role"}
    checks["doc_est_schema"] = (_check_exact_keys(est_contract, expected_est_keys, "estimator"),
                                str(sorted(est_contract.keys())))
    checks["doc_est_horizon"] = (est_contract.get("horizon") == HORIZON, str(est_contract.get("horizon")))
    checks["doc_est_gamma"] = (_is_strict_number(est_contract.get("gamma"))
                                and est_contract.get("gamma") == GAMMA, str(est_contract.get("gamma")))
    checks["doc_est_r_hat_sources"] = (
        est_contract.get("r_hat_sources") == ["q_rollout_first", "extra_immediate"],
        str(est_contract.get("r_hat_sources")))
    checks["doc_est_q_hat_role"] = (est_contract.get("q_hat_role") == "q_rollout_only", str(est_contract.get("q_hat_role")))
    # R52: seed schema — exact keys, verify version and encoding
    seed_contract = doc.get("seed_schema", {})
    expected_seed_keys = {"version", "fields", "encoding"}
    checks["doc_seed_schema"] = (_check_exact_keys(seed_contract, expected_seed_keys, "seed"),
                                 str(sorted(seed_contract.keys())))
    expected_seed_fields = ["base_tag", "task_id", "state_id", "rollout_id", "replicate_id", "replica_index"]
    checks["doc_seed_fields"] = (seed_contract.get("fields") == expected_seed_fields, str(seed_contract.get("fields")))
    checks["doc_seed_version"] = (seed_contract.get("version") == "crn-v2", str(seed_contract.get("version")))
    checks["doc_seed_encoding"] = (seed_contract.get("encoding") == "typed_json", str(seed_contract.get("encoding")))
    checks["doc_seed_excludes_action"] = ("action" not in seed_contract.get("fields", []), "no action in seed")
    checks["doc_seed_excludes_genotype"] = ("genotype" not in seed_contract.get("fields", []), "no genotype in seed")

    all_ok = all(ok for ok, _ in checks.values())
    return {"all_pass": all_ok,
            "checks": {k: {"ok": ok, "detail": d} for k, (ok, d) in checks.items()},
            "doc_hash": doc_hash,
            "doc": doc}


# ===========================================================================
# R16 seed helpers (single contract)
# ===========================================================================

def crn_seed(task_id: str, state_id: str, rollout_id: int, replicate_id: int = 0) -> str:
    """R39: canonical typed JSON CRN key. Excludes action/genotype.

    Uses versioned JSON serialization to prevent delimiter ambiguity.
    Same (task_id, state_id, rollout_id, replicate_id) -> same seed.
    Any field change -> different seed. Action/genotype never enter.
    """
    payload = ["crn-v2", str(task_id), str(state_id), int(rollout_id), int(replicate_id)]
    canonical = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def operator_rng_seed(operator: str, state_id: str, action: int, rollout_id: int, draw: int) -> int:
    """Action/operator-specific generation RNG (separate from evaluation RNG)."""
    h = hashlib.sha256(f"OPRNG|{operator}|{state_id}|{action}|{rollout_id}|{draw}".encode()).hexdigest()
    return int(h[:16], 16) % (2 ** 31 - 1)


# ===========================================================================
# R12 BudgetLedger — explicit units, no mixed arithmetic
# ===========================================================================

@dataclass
class BudgetLedger:
    """R12/R21: explicit units; separate collection component; fail-closed cap."""
    planned_slots: int = 0
    planned_collection_slots: int = 0   # R21: state-collection tracked separately
    planned_q_slots: int = 0
    planned_extra_slots: int = 0
    actual_replicas_run: int = 0
    cache_hit_bundles: int = 0
    invalid_offspring: int = 0
    valid_offspring: int = 0
    operator_llm_calls: int = 0
    agent_llm_turns: int = 0
    notes: List[str] = field(default_factory=list)

    @staticmethod
    def _validate_nonneg(name: str, val) -> int:
        """R27: reject non-integer or negative values before any mutation."""
        if not isinstance(val, int) or isinstance(val, bool):
            raise ValueError(f"R27: {name} must be int, got {type(val).__name__}")
        if val < 0:
            raise ValueError(f"R27: {name} must be non-negative, got {val}")
        return val

    def record_evaluation(self, planned_slots: int, replicas_run_delta: int,
                          cache_bundle_delta: int, valid: int = 1, invalid: int = 0,
                          op_llm_calls: int = 0, agent_turns: int = 0) -> None:
        """R27: validate all inputs; atomic update (all-or-nothing)."""
        ps = self._validate_nonneg("planned_slots", planned_slots)
        rd = self._validate_nonneg("replicas_run_delta", replicas_run_delta)
        cb = self._validate_nonneg("cache_bundle_delta", cache_bundle_delta)
        v = self._validate_nonneg("valid", valid)
        inv = self._validate_nonneg("invalid", invalid)
        llm = self._validate_nonneg("op_llm_calls", op_llm_calls)
        turns = self._validate_nonneg("agent_turns", agent_turns)
        # R27: check cap BEFORE mutation; reject if would exceed
        if self.planned_slots + ps > HARD_CAP_SLOTS:
            raise ValueError(
                f"R27: planned_slots {self.planned_slots}+{ps} would exceed cap {HARD_CAP_SLOTS}")
        self.planned_slots += ps
        self.actual_replicas_run += rd
        self.cache_hit_bundles += cb
        self.valid_offspring += v
        self.invalid_offspring += inv
        self.operator_llm_calls += llm
        self.agent_llm_turns += turns

    def record_collection(self, planned_slots: int, replicas_run_delta: int,
                          cache_bundle_delta: int) -> None:
        """R33: fully atomic collection accounting."""
        ps = self._validate_nonneg("planned_slots", planned_slots)
        rd = self._validate_nonneg("replicas_run_delta", replicas_run_delta)
        cb = self._validate_nonneg("cache_bundle_delta", cache_bundle_delta)
        if self.planned_slots + ps > HARD_CAP_SLOTS:
            raise ValueError(
                f"R33: collection {self.planned_slots}+{ps} would exceed cap {HARD_CAP_SLOTS}")
        self.planned_collection_slots += ps
        self.planned_slots += ps
        self.actual_replicas_run += rd
        self.cache_hit_bundles += cb

    def record_q_slot(self, planned_slots: int, replicas_run_delta: int,
                      cache_bundle_delta: int) -> None:
        """R33: fully atomic — validate all args before ANY mutation."""
        ps = self._validate_nonneg("planned_slots", planned_slots)
        rd = self._validate_nonneg("replicas_run_delta", replicas_run_delta)
        cb = self._validate_nonneg("cache_bundle_delta", cache_bundle_delta)
        if self.planned_slots + ps > HARD_CAP_SLOTS:
            raise ValueError(
                f"R33: planned_slots {self.planned_slots}+{ps} would exceed cap {HARD_CAP_SLOTS}")
        # All checks passed — commit all mutations atomically
        self.planned_q_slots += ps
        self.planned_slots += ps
        self.actual_replicas_run += rd
        self.cache_hit_bundles += cb
        self.valid_offspring += 1

    def record_extra_slot(self, planned_slots: int, replicas_run_delta: int,
                          cache_bundle_delta: int) -> None:
        """R33: fully atomic — validate all args before ANY mutation."""
        ps = self._validate_nonneg("planned_slots", planned_slots)
        rd = self._validate_nonneg("replicas_run_delta", replicas_run_delta)
        cb = self._validate_nonneg("cache_bundle_delta", cache_bundle_delta)
        if self.planned_slots + ps > HARD_CAP_SLOTS:
            raise ValueError(
                f"R33: planned_slots {self.planned_slots}+{ps} would exceed cap {HARD_CAP_SLOTS}")
        # All checks passed — commit all mutations atomically
        self.planned_extra_slots += ps
        self.planned_slots += ps
        self.actual_replicas_run += rd
        self.cache_hit_bundles += cb

    def check_cap(self) -> bool:
        """R27: cap check includes non-negative invariant."""
        return (self.planned_slots <= HARD_CAP_SLOTS
                and self.planned_slots >= 0
                and self.actual_replicas_run >= 0)

    def reconcile(self, expected_total: int) -> List[str]:
        """R27: full invariant check (non-negative, component sum, cap)."""
        errors = []
        for name, val in [("planned_slots", self.planned_slots),
                          ("actual_replicas_run", self.actual_replicas_run),
                          ("cache_hit_bundles", self.cache_hit_bundles),
                          ("planned_collection_slots", self.planned_collection_slots),
                          ("planned_q_slots", self.planned_q_slots),
                          ("planned_extra_slots", self.planned_extra_slots)]:
            if val < 0:
                errors.append(f"{name} is negative: {val}")
        if self.planned_slots != expected_total:
            errors.append(f"planned_slots {self.planned_slots} != expected {expected_total}")
        component_sum = self.planned_collection_slots + self.planned_q_slots + self.planned_extra_slots
        if component_sum != self.planned_slots:
            errors.append(f"component sum {component_sum} != total {self.planned_slots}")
        if self.planned_slots > HARD_CAP_SLOTS:
            errors.append(f"planned_slots {self.planned_slots} exceeds cap {HARD_CAP_SLOTS}")
        return errors

    def summary(self) -> dict:
        return {
            "planned_slots": self.planned_slots,
            "actual_replicas_run": self.actual_replicas_run,
            "cache_hit_bundles": self.cache_hit_bundles,
            "invalid_offspring": self.invalid_offspring,
            "valid_offspring": self.valid_offspring,
            "operator_llm_calls": self.operator_llm_calls,
            "agent_llm_turns": self.agent_llm_turns,
            "hard_cap_slots": HARD_CAP_SLOTS,
            "within_cap": self.check_cap(),
        }


# ===========================================================================
# R13/R14 StateActionRecord + fail-closed validation
# ===========================================================================

@dataclass
class StateActionRecord:
    """R22/R23: full provenance for replay."""
    state_id: str
    cluster_id: str
    action: int
    rollout_id: int
    replicate_id: int
    crn_seed: str
    sample_role: str
    gen_rewards: List[float]
    family: str = "A"
    task_id: str = ""                   # R22: task provenance
    episode_id: str = ""                # R22: source collection-episode ID
    planned_slots: int = 0
    invalid_count: int = 0
    cache_hit_bundles: int = 0
    actual_replicas_run: int = 0
    effective_seed_parts: Tuple[str, ...] = ()


def validate_records(records: List[StateActionRecord],
                     require_registered_shape: bool = True,
                     plan_mapping: Optional[Dict[str, dict]] = None) -> None:
    """R13: fail closed. Raises ValueError with a specific message on any violation."""
    if not records:
        raise ValueError("R13: empty record collection")

    seen_keys: set = set()
    state_clusters: Dict[str, set] = {}
    q_counts: Dict[Tuple[str, int], int] = {}
    extra_counts: Dict[Tuple[str, int], int] = {}
    states: set = set()
    clusters: set = set()

    for i, rec in enumerate(records):
        tag = f"record[{i}] state={rec.state_id} action={rec.action}"
        if rec.sample_role not in VALID_ROLES:
            raise ValueError(f"R13/R14: {tag}: invalid sample_role {rec.sample_role!r}")
        if not rec.state_id:
            raise ValueError(f"R13: {tag}: empty state_id")
        if not rec.cluster_id:
            raise ValueError(f"R13: {tag}: empty cluster_id")
        if rec.action < 0 or rec.action >= N_ACTIONS:
            raise ValueError(f"R13: {tag}: invalid action {rec.action}")
        if rec.family not in ("A", "B"):
            raise ValueError(f"R13/R15: {tag}: family {rec.family!r} not in A/B")
        if rec.planned_slots < 0 or rec.invalid_count < 0 or rec.actual_replicas_run < 0:
            raise ValueError(f"R13: {tag}: negative counter")
        if not rec.crn_seed:
            raise ValueError(f"R13: {tag}: missing crn_seed")
        if not rec.effective_seed_parts:
            raise ValueError(f"R13: {tag}: missing effective_seed_parts")

        # R13: reward trace validation
        for r in rec.gen_rewards:
            if not math.isfinite(r):
                raise ValueError(f"R13: {tag}: non-finite reward {r}")
        if rec.sample_role == ROLE_Q:
            if len(rec.gen_rewards) != HORIZON:
                raise ValueError(
                    f"R13/R14: {tag}: q_rollout must have exactly {HORIZON} rewards, got {len(rec.gen_rewards)}")
            # R33: per-record Q slot validation (unconditional)
            expected_slots = HORIZON * LAMBDA * N_EVAL
            if rec.planned_slots != expected_slots:
                raise ValueError(
                    f"R33: {tag}: q_rollout planned_slots {rec.planned_slots} != {expected_slots}")
            q_counts[(rec.state_id, rec.action)] = q_counts.get((rec.state_id, rec.action), 0) + 1
        else:  # ROLE_EXTRA
            if len(rec.gen_rewards) != 1:
                raise ValueError(
                    f"R13/R14: {tag}: extra_immediate must have exactly 1 reward, got {len(rec.gen_rewards)}")
            # R33: per-record extra slot validation (unconditional)
            expected_slots = LAMBDA * N_EVAL
            if rec.planned_slots != expected_slots:
                raise ValueError(
                    f"R33: {tag}: extra_immediate planned_slots {rec.planned_slots} != {expected_slots}")
            extra_counts[(rec.state_id, rec.action)] = extra_counts.get((rec.state_id, rec.action), 0) + 1

        # R13: duplicate key check (state, action, rollout, replicate, role)
        key = (rec.state_id, rec.action, rec.rollout_id, rec.replicate_id, rec.sample_role)
        if key in seen_keys:
            raise ValueError(f"R13: duplicate sample key {key}")
        seen_keys.add(key)

        state_clusters.setdefault(rec.state_id, set()).add(rec.cluster_id)
        states.add(rec.state_id)
        clusters.add(rec.cluster_id)

    # R35: validate against plan mapping FIRST (registered mode only)
    if require_registered_shape:
        if plan_mapping is None:
            plan_mapping, _ = get_plan_mapping()
        validate_provenance_against_plan(records, plan_mapping)

    # R13: state-cluster conflict
    for sid, cids in state_clusters.items():
        if len(cids) > 1:
            raise ValueError(f"R13: state {sid} maps to conflicting clusters {cids}")

    # R13: every state must have all N_ACTIONS represented (any mode)
    state_actions: Dict[str, set] = {}
    for rec in records:
        state_actions.setdefault(rec.state_id, set()).add(rec.action)
    for sid, acts in state_actions.items():
        missing = set(range(N_ACTIONS)) - acts
        if missing:
            raise ValueError(f"R13: state {sid} missing actions {sorted(missing)}")

    if require_registered_shape:
        # R28: EXACT registered state count
        if len(states) != N_STATES:
            raise ValueError(f"R28: need exactly {N_STATES} states, got {len(states)}")
        # R28: exact per-state-action sample counts
        for sid in states:
            for a in range(N_ACTIONS):
                qc = q_counts.get((sid, a), 0)
                if qc != Q_ROLLOUTS:
                    raise ValueError(
                        f"R28: state {sid} action {a}: {qc} q_rollout, need exactly {Q_ROLLOUTS}")
                ec = extra_counts.get((sid, a), 0)
                if ec != EXTRA_IMMEDIATE:
                    raise ValueError(
                        f"R28: state {sid} action {a}: {ec} extra_immediate, need exactly {EXTRA_IMMEDIATE}")
        # R28/R29: exactly 40 registered clusters
        if len(clusters) != N_STATE_COLLECTION_EPISODES:
            raise ValueError(
                f"R28/R29: need exactly {N_STATE_COLLECTION_EPISODES} clusters, got {len(clusters)}")



# ===========================================================================
# R14 estimators
# ===========================================================================

def compute_r_hat(records: List[StateActionRecord]) -> Dict[Tuple[str, int], float]:
    """R14: r_hat(s,a) = mean of (Q-rollout first rewards + extra_immediate rewards).

    Estimator per PC1_INDEPENDENT_REVIEW proposed amendment:
    'r_hat uses the three first-step rewards already collected in Q rollouts
     plus this extra sample, all under the same reward function.'
    """
    sums: Dict[Tuple[str, int], List[float]] = {}
    for rec in records:
        if rec.sample_role == ROLE_Q:
            if rec.gen_rewards:
                sums.setdefault((rec.state_id, rec.action), []).append(rec.gen_rewards[0])
        elif rec.sample_role == ROLE_EXTRA:
            if rec.gen_rewards:
                sums.setdefault((rec.state_id, rec.action), []).append(rec.gen_rewards[0])
    return {k: sum(v) / len(v) for k, v in sums.items() if v}


def compute_q_hat(records: List[StateActionRecord], gamma: float = GAMMA) -> Dict[Tuple[str, int], float]:
    """R14: Q_hat uses ONLY complete q_rollout records (never extra_immediate)."""
    sums: Dict[Tuple[str, int], List[float]] = {}
    for rec in records:
        if rec.sample_role != ROLE_Q:
            continue
        ret = discounted_return(rec.gen_rewards[:HORIZON], gamma=gamma)
        sums.setdefault((rec.state_id, rec.action), []).append(ret)
    return {k: sum(v) / len(v) for k, v in sums.items() if v}


def _per_state_stats(r_hat: Dict, q_hat: Dict) -> List[dict]:
    """R13: do NOT default missing actions to 0.0 — caller must have validated."""
    states = sorted({k[0] for k in q_hat})
    rows = []
    for s in states:
        r_vals = {}
        q_vals = {}
        for a in range(N_ACTIONS):
            if (s, a) not in r_hat:
                raise ValueError(f"R13: missing r_hat for state {s} action {a}")
            if (s, a) not in q_hat:
                raise ValueError(f"R13: missing q_hat for state {s} action {a}")
            r_vals[a] = r_hat[(s, a)]
            q_vals[a] = q_hat[(s, a)]
        a_r = _argmax_by(r_vals)
        a_q = _argmax_by(q_vals)
        rows.append({
            "state_id": s, "a_r": a_r, "a_q": a_q,
            "disagree": int(a_r != a_q),
            "advantage": q_vals[a_q] - q_vals[a_r],
        })
    return rows


def _argmax_by(d: Dict[int, float]) -> int:
    return min(d.items(), key=lambda kv: (-kv[1], kv[0]))[0]


def _cluster_bootstrap(rows: List[dict], clusters: Dict[str, List[dict]],
                       n_boot: int = 10000, seed: int = 20261027) -> dict:
    if not clusters:
        raise ValueError("R13: no clusters for bootstrap")
    rng = random.Random(seed)
    cluster_ids = sorted(clusters.keys())
    Ds: List[float] = []
    advs: List[float] = []
    for _ in range(n_boot):
        sampled = [cluster_ids[rng.randrange(len(cluster_ids))] for _ in cluster_ids]
        boot_rows: List[dict] = []
        for cid in sampled:
            boot_rows.extend(clusters[cid])
        if not boot_rows:
            continue
        Ds.append(sum(r["disagree"] for r in boot_rows) / len(boot_rows))
        advs.append(sum(r["advantage"] for r in boot_rows) / len(boot_rows))
    if not Ds:
        raise ValueError("R13: bootstrap produced no samples")
    Ds.sort()
    advs.sort()
    lo_i = int(0.025 * len(Ds))
    hi_i = max(lo_i, int(0.975 * len(Ds)) - 1)
    return {"D_ci": (Ds[lo_i], Ds[hi_i]), "adv_ci": (advs[lo_i], advs[hi_i])}


# ===========================================================================
# R17 raw evidence
# ===========================================================================

def _sanitize_record(rec: StateActionRecord) -> dict:
    """R22/R23: sanitized per-record fields (no gold labels)."""
    return {
        "state_id": rec.state_id,
        "cluster_id": rec.cluster_id,
        "action": rec.action,
        "sample_role": rec.sample_role,
        "rollout_id": rec.rollout_id,
        "replicate_id": rec.replicate_id,
        "crn_seed": rec.crn_seed,
        "effective_seed_parts": list(rec.effective_seed_parts),
        "family": rec.family,
        "task_id": rec.task_id,
        "episode_id": rec.episode_id,
        "gen_rewards": list(rec.gen_rewards),
        "planned_slots": rec.planned_slots,
        "invalid_count": rec.invalid_count,
        "cache_hit_bundles": rec.cache_hit_bundles,
        "actual_replicas_run": rec.actual_replicas_run,
    }


# ===========================================================================
# R13/R14/R17 main analysis
# ===========================================================================

def run_pc1_analysis(records: List[StateActionRecord],
                     planned_slots_total: int,
                     strata_fn: Optional[Callable[[str], str]] = None,
                     require_registered_shape: bool = True,
                     manifest_hash: str = "",
                     runtime_revision: str = "",
                     evaluator_version: str = "",
                     protocol_hash: str = "",
                     plan_hash: str = "",
                     plan_artifact_path: str = "") -> "PC1Result":
    """R13: validate first, fail closed. R28: full reconciliation. R30: provenance."""
    # R40: protocol consistency must pass before registered analysis
    if require_registered_shape:
        consistency = protocol_consistency_check()
        if not consistency.get("all_pass", False):
            raise ValueError("R40: protocol_consistency_check failed — document/code mismatch")
        if not manifest_hash or not manifest_hash.strip():
            raise ValueError("R30: registered analysis requires non-empty manifest_hash")
        if not runtime_revision or not runtime_revision.strip():
            raise ValueError("R30: registered analysis requires non-empty runtime_revision")
        if not evaluator_version or not evaluator_version.strip():
            raise ValueError("R30: registered analysis requires non-empty evaluator_version")
        if not protocol_hash or not protocol_hash.strip():
            raise ValueError("R37: registered analysis requires non-empty protocol_hash")
        if not plan_hash or not plan_hash.strip():
            raise ValueError("R37: registered analysis requires non-empty plan_hash")
        if not plan_artifact_path or not plan_artifact_path.strip():
            raise ValueError("R44: registered analysis requires plan_artifact_path")
        # R37: verify protocol hash matches actual document
        actual_doc_hash = compute_protocol_hash(parse_protocol_document())
        if protocol_hash != actual_doc_hash:
            raise ValueError(
                f"R37: protocol_hash mismatch: got '{protocol_hash}', expected '{actual_doc_hash}'")
        # R44: load and verify plan artifact
        try:
            artifact_mapping, artifact_hash = load_plan_artifact(plan_artifact_path)
        except Exception as e:
            raise ValueError(f"R44: cannot load plan artifact: {e}")
        if plan_hash != artifact_hash:
            raise ValueError(
                f"R44: plan_hash mismatch: got '{plan_hash}', artifact hash '{artifact_hash}'")
        # R44: validate records against the ARTIFACT mapping, not get_plan_mapping()
        validate_provenance_against_plan(records, artifact_mapping)
    # R21: reject invalid totals
    if planned_slots_total <= 0:
        raise ValueError(f"R21: planned_slots_total must be positive, got {planned_slots_total}")
    if planned_slots_total > HARD_CAP_SLOTS:
        raise ValueError(f"R21: planned slots {planned_slots_total} exceed hard cap {HARD_CAP_SLOTS}")

    validate_records(records, require_registered_shape=require_registered_shape,
                     plan_mapping=artifact_mapping if require_registered_shape and plan_artifact_path else None)

    # R40: protocol consistency must pass before registered statistics
    if require_registered_shape:
        consistency = protocol_consistency_check()
        if not consistency.get("all_pass", False):
            raise ValueError("R40: protocol_consistency_check failed — document/code mismatch")

    # R28: full budget reconciliation with explicit collection component
    ledger = BudgetLedger()
    for rec in records:
        if rec.sample_role == ROLE_Q:
            ledger.record_q_slot(rec.planned_slots, rec.actual_replicas_run, rec.cache_hit_bundles)
        else:
            ledger.record_extra_slot(rec.planned_slots, rec.actual_replicas_run, rec.cache_hit_bundles)
    # R28: collection slots are NOT in diagnostic records; add them explicitly
    # In registered mode, planned_slots_total must equal Q+extra+collection = 45,440
    record_planned = ledger.planned_slots  # Q + extra only
    if record_planned > planned_slots_total:
        raise ValueError(
            f"R28: record planned slots {record_planned} exceed caller total {planned_slots_total}")
    if require_registered_shape:
        # R28: reconcile to exact registered total
        collection_slots = PLANNED_COLLECTION_SLOTS
        expected_total = PLANNED_TOTAL_SLOTS  # 45,440
        if planned_slots_total != expected_total:
            raise ValueError(
                f"R28: planned_slots_total {planned_slots_total} != registered {expected_total}")
        ledger.record_collection(collection_slots, 0, 0)
        if ledger.planned_slots != expected_total:
            raise ValueError(
                f"R28: ledger total {ledger.planned_slots} != registered {expected_total}")
        if record_planned != PLANNED_Q_SLOTS + PLANNED_EXTRA_SLOTS:
            raise ValueError(
                f"R28: record planned {record_planned} != Q+extra {PLANNED_Q_SLOTS + PLANNED_EXTRA_SLOTS}")

    r_hat = compute_r_hat(records)
    q_hat = compute_q_hat(records)
    rows = _per_state_stats(r_hat, q_hat)
    if not rows:
        raise ValueError("no state records")

    D = sum(r["disagree"] for r in rows) / len(rows)
    adv = sum(r["advantage"] for r in rows) / len(rows)

    clusters: Dict[str, List[dict]] = {}
    by_state: Dict[str, str] = {}
    for rec in records:
        if rec.state_id in by_state and by_state[rec.state_id] != rec.cluster_id:
            raise ValueError(f"R13: state {rec.state_id} cluster conflict")
        by_state[rec.state_id] = rec.cluster_id
    for r in rows:
        cid = by_state[r["state_id"]]
        clusters.setdefault(cid, []).append(r)

    ci = _cluster_bootstrap(rows, clusters)
    D_ci, adv_ci = ci["D_ci"], ci["adv_ci"]

    point_ok = (D >= THRESHOLD_D) and (adv >= THRESHOLD_ADVANTAGE)
    ci_ok = (D_ci[0] > MARGIN_D) and (adv_ci[0] > MARGIN_ADV)
    if point_ok and ci_ok:
        decision = "PASS"
    elif (D_ci[1] < THRESHOLD_D) and (adv_ci[1] < THRESHOLD_ADVANTAGE):
        decision = "FAIL"
    else:
        decision = "INCONCLUSIVE"

    strata: Dict[str, dict] = {}
    if strata_fn:
        for r in rows:
            b = strata_fn(r["state_id"])
            strata.setdefault(b, {"n": 0, "disagree": 0, "adv": 0.0})
            strata[b]["n"] += 1
            strata[b]["disagree"] += r["disagree"]
            strata[b]["adv"] += r["advantage"]
        for v in strata.values():
            v["D"] = v["disagree"] / max(1, v["n"])
            v["advantage"] = v["adv"] / max(1, v["n"])

    # R23: replayable evidence with full statistics
    raw_evidence = {
        "protocol_version": PROTOCOL_VERSION,
        "estimator_version": ESTIMATOR_VERSION,
        "protocol_status": PROTOCOL_STATUS,
        "protocol_hash": protocol_hash,
        "plan_hash": plan_hash,
        "plan_artifact_path": plan_artifact_path,
        "manifest_hash": manifest_hash,
        "runtime_revision": runtime_revision,
        "evaluator_version": evaluator_version,
        "is_synthetic": not require_registered_shape,
        "seed_contract": "effective_seed_parts(base, task_id, state_id, rollout_id, replicate_id, replica_index)",
        "thresholds": {"D": THRESHOLD_D, "advantage": THRESHOLD_ADVANTAGE,
                       "margin_D": MARGIN_D, "margin_adv": MARGIN_ADV},
        "bootstrap": {"seed": 20261027, "n_resamples": 10000, "method": "cluster_bootstrap_by_episode"},
        "D": D, "advantage": adv,
        "D_ci": list(D_ci), "adv_ci": list(adv_ci),
        "decision": decision,
        "n_states": len(rows), "n_clusters": len(clusters), "n_records": len(records),
        "r_hat": {f"{k[0]}|{k[1]}": v for k, v in r_hat.items()},
        "q_hat": {f"{k[0]}|{k[1]}": v for k, v in q_hat.items()},
        "rows": rows,
        "strata": strata,
        "records": [_sanitize_record(r) for r in records],
        "budget": ledger.summary(),
        "budget_components": {
            "collection_slots": ledger.planned_collection_slots,
            "q_slots": ledger.planned_q_slots,
            "extra_slots": ledger.planned_extra_slots,
            "total_planned": ledger.planned_slots,
        },
        "planned_slots_total": planned_slots_total,
        "decision_rule": "PASS if D>=0.15 and adv>=0.02 and CI margins excluded; else FAIL if CI below thresholds; else INCONCLUSIVE->SR1",
    }
    # R23: input record hash
    rec_json = json.dumps([_sanitize_record(r) for r in records], sort_keys=True)
    raw_evidence["input_record_hash"] = hashlib.sha256(rec_json.encode()).hexdigest()[:32]

    return PC1Result(
        D=D, advantage=adv, D_ci=D_ci, adv_ci=adv_ci,
        n_states=len(rows), n_clusters=len(clusters),
        decision=decision, planned_slots_total=planned_slots_total,
        raw_evidence=raw_evidence,
    )


@dataclass
class PC1Result:
    D: float
    advantage: float
    D_ci: Tuple[float, float]
    adv_ci: Tuple[float, float]
    n_states: int
    n_clusters: int
    decision: str
    planned_slots_total: int
    raw_evidence: dict


# ===========================================================================
# R15 PC1 collection/rollout orchestration (dry-run only)
# ===========================================================================

@dataclass
class PC1Plan:
    """Deterministic dry-run plan for the registered PC1 experiment."""
    protocol_version: str
    n_states: int
    n_actions: int
    q_rollouts: int
    horizon: int
    extra_immediate: int
    n_collection_episodes: int
    planned_q_slots: int
    planned_extra_slots: int
    planned_collection_slots: int
    planned_total_slots: int
    hard_cap: int
    within_cap: bool
    schedule: List[dict]
    budget_ledger_plan: dict


def generate_pc1_dry_run_plan() -> PC1Plan:
    """R15: emit the full planned schedule WITHOUT executing anything.

    Produces a deterministic plan of every (state, action, rollout, replicate,
    sample_role) unit and its planned-slot cost. This is the auditable contract
    for what WOULD be executed under registered PC1.
    """
    schedule: List[dict] = []
    planned_so_far = 0
    # R22: explicit state-to-episode mapping
    state_episode_map: Dict[str, str] = {}

    # State collection episodes (R22: each state assigned to an episode)
    for ep in range(N_STATE_COLLECTION_EPISODES):
        policy = "random" if ep < N_STATE_COLLECTION_EPISODES // 2 else "heuristic"
        init_slots = MU * N_EVAL
        gen_slots = T_COLLECT * LAMBDA * N_EVAL
        planned_so_far += init_slots + gen_slots
        if planned_so_far > HARD_CAP_SLOTS:
            raise ValueError(f"R15: dry-run plan exceeds hard cap at collection episode {ep}")
        # R22: assign states to episodes (round-robin)
        ep_states = [f"s{si:03d}" for si in range(ep, N_STATES, N_STATE_COLLECTION_EPISODES)]
        for sid in ep_states:
            state_episode_map[sid] = f"col{ep:03d}"
        schedule.append({
            "unit": "collection_episode", "episode_id": f"col{ep:03d}",
            "policy": policy, "family": "A" if ep % 2 == 0 else "B",
            "assigned_states": ep_states,
            "planned_init_slots": init_slots, "planned_gen_slots": gen_slots,
        })

    # Q rollouts + extra immediate for each (state, action)
    for si in range(N_STATES):
        sid = f"s{si:03d}"
        ep_id = state_episode_map.get(sid, f"col{si % N_STATE_COLLECTION_EPISODES:03d}")
        for a in range(N_ACTIONS):
            for r in range(Q_ROLLOUTS):
                slots = HORIZON * LAMBDA * N_EVAL
                planned_so_far += slots
                if planned_so_far > HARD_CAP_SLOTS:
                    raise ValueError(f"R15: dry-run plan exceeds hard cap at s{si} a{a} r{r}")
                schedule.append({
                    "unit": "q_rollout", "state_id": sid, "action": a,
                    "rollout_id": r, "sample_role": ROLE_Q,
                    "episode_id": ep_id, "task_id": f"task-{ep_id}",
                    "crn_seed": crn_seed(f"task-{ep_id}", sid, r),
                    "planned_slots": slots,
                })
            for e in range(EXTRA_IMMEDIATE):
                slots = LAMBDA * N_EVAL
                planned_so_far += slots
                if planned_so_far > HARD_CAP_SLOTS:
                    raise ValueError(f"R15: dry-run plan exceeds hard cap at extra s{si} a{a}")
                schedule.append({
                    "unit": "extra_immediate", "state_id": sid, "action": a,
                    "rollout_id": 1000 + e, "sample_role": ROLE_EXTRA,
                    "episode_id": ep_id, "task_id": f"task-{ep_id}",
                    "crn_seed": crn_seed(f"task-{ep_id}", sid, 1000 + e),
                    "planned_slots": slots,
                })

    ledger_plan = {
        "planned_q_slots": PLANNED_Q_SLOTS,
        "planned_extra_slots": PLANNED_EXTRA_SLOTS,
        "planned_collection_slots": PLANNED_COLLECTION_SLOTS,
        "planned_total_slots": PLANNED_TOTAL_SLOTS,
        "hard_cap": HARD_CAP_SLOTS,
        "within_cap": PLANNED_TOTAL_SLOTS <= HARD_CAP_SLOTS,
    }

    return PC1Plan(
        protocol_version=PROTOCOL_VERSION,
        n_states=N_STATES, n_actions=N_ACTIONS,
        q_rollouts=Q_ROLLOUTS, horizon=HORIZON,
        extra_immediate=EXTRA_IMMEDIATE,
        n_collection_episodes=N_STATE_COLLECTION_EPISODES,
        planned_q_slots=PLANNED_Q_SLOTS,
        planned_extra_slots=PLANNED_EXTRA_SLOTS,
        planned_collection_slots=PLANNED_COLLECTION_SLOTS,
        planned_total_slots=PLANNED_TOTAL_SLOTS,
        hard_cap=HARD_CAP_SLOTS,
        within_cap=PLANNED_TOTAL_SLOTS <= HARD_CAP_SLOTS,
        schedule=schedule,
        budget_ledger_plan=ledger_plan,
    )


# ===========================================================================
# R35: deterministic state-to-episode plan mapping with hash
# ===========================================================================

def generate_plan_mapping() -> Tuple[Dict[str, dict], str]:
    """R35: deterministic state-to-episode/task/cluster/family mapping.

    Returns (mapping, plan_hash) where mapping[state_id] = {episode_id, task_id, cluster_id, family}.
    plan_hash is SHA256 of the canonical JSON serialization.
    """
    import json as _json
    mapping: Dict[str, dict] = {}
    for si in range(N_STATES):
        ep_idx = si % N_STATE_COLLECTION_EPISODES
        ep_id = f"col{ep_idx:03d}"
        task_id = f"task-{ep_id}"
        cluster_id = ep_id  # cluster == episode in this design
        family = "A" if ep_idx % 2 == 0 else "B"
        sid = f"s{si:03d}"
        mapping[sid] = {
            "episode_id": ep_id,
            "task_id": task_id,
            "cluster_id": cluster_id,
            "family": family,
        }
    # canonical hash
    canonical = _json.dumps(mapping, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    plan_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]
    return mapping, plan_hash


# R51: registered canonical plan identity — INDEPENDENTLY PINNED
REGISTERED_PLAN_ID = "pc1-plan-v1"
REGISTERED_PLAN_VERSION = "1.0"
# R51: this hash is pinned at design time and reviewed — NOT recomputed from the
# same generator at runtime. If the mapping logic changes, this constant must be
# updated through a reviewed protocol amendment.
REGISTERED_PLAN_HASH = "af11096d3329e25e6e23f53be237e696"  # independently pinned

def _compute_canonical_plan_hash() -> str:
    """Compute the hash from the canonical mapping (used once to verify the pin)."""
    mapping, h = generate_plan_mapping()
    return h

def get_registered_plan_hash() -> str:
    """R51: return the INDEPENDENTLY PINNED registered plan hash."""
    return REGISTERED_PLAN_HASH


# R41: immutable plan mapping — defensive copies, no stale hash
_PLAN_MAPPING_CACHE: Optional[Tuple[Dict[str, dict], str]] = None

def get_plan_mapping() -> Tuple[Dict[str, dict], str]:
    """R41: returns (deep_copy_of_mapping, hash). Caller mutations cannot affect cache."""
    global _PLAN_MAPPING_CACHE
    if _PLAN_MAPPING_CACHE is None:
        _PLAN_MAPPING_CACHE = generate_plan_mapping()
    mapping, plan_hash = _PLAN_MAPPING_CACHE
    # R41: return defensive copy so caller mutations don't corrupt cache
    return {k: dict(v) for k, v in mapping.items()}, plan_hash


def save_plan_artifact(path: str) -> str:
    """R41: serialize plan mapping to deterministic artifact, return hash."""
    mapping, plan_hash = get_plan_mapping()
    # R55: bind protocol content hash into the plan artifact
    from .pc1 import compute_protocol_hash as _cph, parse_protocol_document as _ppd
    try:
        _doc = _ppd()
        _proto_hash = _cph(_doc)
    except Exception:
        _proto_hash = ""
    artifact = {
        "plan_id": REGISTERED_PLAN_ID,
        "plan_version": REGISTERED_PLAN_VERSION,
        "plan_hash": plan_hash,
        "protocol_content_hash": _proto_hash,
        "mapping": mapping,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return plan_hash


def load_plan_artifact(path: str, require_registered: bool = True) -> Tuple[Dict[str, dict], str]:
    """R47: load and verify plan artifact against REGISTERED canonical plan.

    If require_registered=True, the artifact must match the independently
    pinned registered plan hash — self-consistent but noncanonical plans
    are rejected.
    """
    with open(path, encoding="utf-8") as f:
        artifact = json.load(f)
    mapping = artifact.get("mapping", {})
    stored_hash = artifact.get("plan_hash", "")
    # R41: recompute hash from actual content
    canonical = json.dumps(mapping, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    actual_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]
    if stored_hash != actual_hash:
        raise ValueError(
            f"R41: plan artifact hash mismatch: stored={stored_hash}, actual={actual_hash}")
    # R47: must match registered canonical plan
    if require_registered:
        registered_hash = get_registered_plan_hash()
        if actual_hash != registered_hash:
            raise ValueError(
                f"R51: plan artifact is not the registered plan: "
                f"artifact_hash={actual_hash}, registered_hash={registered_hash}")
        # R51: verify plan identity and version
        if artifact.get("plan_id") != REGISTERED_PLAN_ID:
            raise ValueError(
                f"R51: plan_id mismatch: got '{artifact.get('plan_id')}', "
                f"expected '{REGISTERED_PLAN_ID}'")
        if artifact.get("plan_version") != REGISTERED_PLAN_VERSION:
            raise ValueError(
                f"R51: plan_version mismatch: got '{artifact.get('plan_version')}', "
                f"expected '{REGISTERED_PLAN_VERSION}'")
        # R55: verify protocol content hash binding
        from .pc1 import compute_protocol_hash as _cph, parse_protocol_document as _ppd
        try:
            _doc = _ppd()
            _current_proto_hash = _cph(_doc)
        except Exception:
            _current_proto_hash = ""
        stored_proto_hash = artifact.get("protocol_content_hash", "")
        if not stored_proto_hash:
            raise ValueError("R55: plan artifact missing protocol_content_hash")
        if stored_proto_hash != _current_proto_hash:
            raise ValueError(
                f"R55: protocol_content_hash mismatch: artifact='{stored_proto_hash}', "
                f"current='{_current_proto_hash}'")
    return mapping, actual_hash


def validate_provenance_against_plan(records: List[StateActionRecord],
                                     plan_mapping: Dict[str, dict]) -> None:
    """R35: validate each record matches the plan mapping exactly."""
    for i, rec in enumerate(records):
        tag = f"record[{i}] state={rec.state_id}"
        if rec.state_id not in plan_mapping:
            raise ValueError(f"R35: {tag}: state not in plan mapping")
        expected = plan_mapping[rec.state_id]
        if rec.episode_id != expected["episode_id"]:
            raise ValueError(
                f"R35: {tag}: episode_id '{rec.episode_id}' != plan '{expected['episode_id']}'")
        if rec.task_id != expected["task_id"]:
            raise ValueError(
                f"R35: {tag}: task_id '{rec.task_id}' != plan '{expected['task_id']}'")
        if rec.cluster_id != expected["cluster_id"]:
            raise ValueError(
                f"R35: {tag}: cluster_id '{rec.cluster_id}' != plan '{expected['cluster_id']}'")
        if rec.family != expected["family"]:
            raise ValueError(
                f"R35: {tag}: family '{rec.family}' != plan '{expected['family']}'")


class PC1ExecutionRefused(Exception):
    """Raised when registered PC1 execution is attempted without approval."""


def execute_registered_pc1(*args, **kwargs):
    """R15: default entry point REFUSES to execute registered PC1."""
    raise PC1ExecutionRefused(
        "Registered PC1 execution is NOT APPROVED. Requires independent review "
        "approval AND production runtime gate. Use generate_pc1_dry_run_plan() "
        "for the dry-run plan and run_pc1_analysis() for synthetic tests only."
    )


# ===========================================================================
# R23 serialization / replay
# ===========================================================================

def save_evidence_artifact(result: "PC1Result", path: str) -> None:
    """R23: serialize the full evidence artifact to JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result.raw_evidence, f, indent=2, sort_keys=True)

def load_evidence_artifact(path: str) -> dict:
    """R23: load a saved evidence artifact."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def deserialize_records(sanitized: List[dict]) -> List[StateActionRecord]:
    """R23: reconstruct StateActionRecord objects from sanitized dicts."""
    return [StateActionRecord(
        state_id=d["state_id"], cluster_id=d["cluster_id"],
        action=d["action"], rollout_id=d["rollout_id"],
        replicate_id=d["replicate_id"], crn_seed=d["crn_seed"],
        sample_role=d["sample_role"], gen_rewards=list(d["gen_rewards"]),
        family=d.get("family", "A"), task_id=d.get("task_id", ""),
        episode_id=d.get("episode_id", ""),
        planned_slots=d.get("planned_slots", 0),
        invalid_count=d.get("invalid_count", 0),
        cache_hit_bundles=d.get("cache_hit_bundles", 0),
        actual_replicas_run=d.get("actual_replicas_run", 0),
        effective_seed_parts=tuple(d.get("effective_seed_parts", ())),
    ) for d in sanitized]

def replay_from_artifact(path: str) -> "PC1Result":
    """R23/R30: reload records, verify input hash, RECOMPUTE statistics."""
    ev = load_evidence_artifact(path)
    records = deserialize_records(ev["records"])
    # R30: verify input record hash before recomputing
    rec_json = json.dumps([_sanitize_record(r) for r in records], sort_keys=True)
    actual_hash = hashlib.sha256(rec_json.encode()).hexdigest()[:32]
    expected_hash = ev.get("input_record_hash", "")
    if expected_hash and actual_hash != expected_hash:
        raise ValueError(
            f"R30: input record hash mismatch: expected {expected_hash}, got {actual_hash}")
    return run_pc1_analysis(
        records,
        planned_slots_total=ev["planned_slots_total"],
        require_registered_shape=not ev.get("is_synthetic", True),
        manifest_hash=ev.get("manifest_hash", ""),
        runtime_revision=ev.get("runtime_revision", ""),
        evaluator_version=ev.get("evaluator_version", ""),
    )


# ===========================================================================
# R25 gated collection/rollout runner (default-deny)
# ===========================================================================

@dataclass
class TrustedApprovalArtifact:
    """R50: HMAC-signed approval artifact.

    The HMAC key (approval_key) must be provided by an external trusted source
    (e.g., Planner's signing infrastructure), NOT derived from the protocol
    document. The signature authenticates the approval fields.
    """
    artifact_id: str = ""
    approver: str = ""
    approval_date: str = ""
    protocol_hash: str = ""
    protocol_version: str = ""
    approval_action: str = ""      # R54: must be "APPROVE"
    authorization_status: str = "" # R54: must be "APPROVED"
    signature: str = ""   # HMAC-SHA256 over canonical approval fields

    def _canonical_payload(self) -> str:
        return json.dumps([
            self.artifact_id, self.approver, self.approval_date,
            self.protocol_hash, self.protocol_version,
            self.approval_action, self.authorization_status,
        ], separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def sign(artifact: "TrustedApprovalArtifact", approval_key: bytes) -> str:
        """R50: create HMAC signature over approval fields. Key from external source."""
        import hmac
        payload = artifact._canonical_payload().encode("utf-8")
        return hmac.new(approval_key, payload, "sha256").hexdigest()

    def verify(self, expected_protocol_hash: str, expected_version: str,
               approval_key: bytes) -> None:
        """R50: verify HMAC signature and all fields. Fail-closed."""
        import re as _re
        import hmac
        from datetime import date as _date
        if not approval_key:
            raise PC1ExecutionRefused("R50: no approval key provided")
        if not self.signature or not self.signature.strip():
            raise PC1ExecutionRefused("R50: artifact has no signature")
        # Verify HMAC signature
        expected_sig = self.sign(self, approval_key)
        if not hmac.compare_digest(self.signature, expected_sig):
            raise PC1ExecutionRefused("R50: approval signature is invalid")
        # Standard field checks
        if not self.artifact_id or not self.artifact_id.strip():
            raise PC1ExecutionRefused("R50: artifact_id is empty")
        if not self.approver or not self.approver.strip():
            raise PC1ExecutionRefused("R50: approver is empty")
        if not self.approval_date or not self.approval_date.strip():
            raise PC1ExecutionRefused("R50: approval_date is empty")
        if not _re.match(r"^\d{4}-\d{2}-\d{2}$", self.approval_date):
            raise PC1ExecutionRefused(
                f"R50: approval_date '{self.approval_date}' is not ISO format")
        try:
            y, m, d = map(int, self.approval_date.split("-"))
            _date(y, m, d)
        except (ValueError, TypeError):
            raise PC1ExecutionRefused(
                f"R50: approval_date '{self.approval_date}' is not a valid calendar date")
        if self.protocol_hash != expected_protocol_hash:
            raise PC1ExecutionRefused(
                f"R50: protocol_hash mismatch: got '{self.protocol_hash}', "
                f"expected '{expected_protocol_hash}'")
        if self.protocol_version != expected_version:
            raise PC1ExecutionRefused(
                f"R50: protocol_version mismatch: got '{self.protocol_version}', "
                f"expected '{expected_version}'")
        # R54: approval action and authorization status must match
        if self.approval_action != "APPROVE":
            raise PC1ExecutionRefused(
                f"R54: approval_action '{self.approval_action}' != 'APPROVE'")
        if self.authorization_status != "APPROVED":
            raise PC1ExecutionRefused(
                f"R54: authorization_status '{self.authorization_status}' != 'APPROVED'")


@dataclass
class PlannerApprovalRecord:
    """R42: structured approval record. Must be generated only after real authorization."""
    approval_id: str = ""
    approver: str = ""
    approval_date: str = ""        # ISO format: YYYY-MM-DD
    protocol_hash: str = ""
    protocol_status: str = ""      # must be "APPROVED"
    protocol_version: str = ""

    def validate(self, expected_protocol_hash: str, expected_version: str,
                 canonical_status: str = "") -> None:
        """R43: validate record against canonical protocol. Fail-closed.

        canonical_status must be the ACTUAL status from the protocol document.
        The gate rejects if the canonical protocol is still PROPOSED.
        """
        import re as _re
        from datetime import date as _date
        if not self.approval_id or not self.approval_id.strip():
            raise PC1ExecutionRefused("R43: approval_id is empty")
        if not self.approver or not self.approver.strip():
            raise PC1ExecutionRefused("R43: approver is empty")
        if not self.approval_date or not self.approval_date.strip():
            raise PC1ExecutionRefused("R43: approval_date is empty")
        # R43: validate REAL calendar date (not just regex shape)
        if not _re.match(r"^\d{4}-\d{2}-\d{2}$", self.approval_date):
            raise PC1ExecutionRefused(
                f"R43: approval_date '{self.approval_date}' is not ISO format YYYY-MM-DD")
        try:
            y, m, d = map(int, self.approval_date.split("-"))
            _date(y, m, d)
        except (ValueError, TypeError):
            raise PC1ExecutionRefused(
                f"R43: approval_date '{self.approval_date}' is not a valid calendar date")
        if self.protocol_status != "APPROVED":
            raise PC1ExecutionRefused(
                f"R43: protocol_status='{self.protocol_status}', need 'APPROVED'")
        if not self.protocol_hash or not self.protocol_hash.strip():
            raise PC1ExecutionRefused("R43: protocol_hash is empty")
        if self.protocol_hash != expected_protocol_hash:
            raise PC1ExecutionRefused(
                f"R43: protocol_hash mismatch: got '{self.protocol_hash}', "
                f"expected '{expected_protocol_hash}'")
        if not self.protocol_version or not self.protocol_version.strip():
            raise PC1ExecutionRefused("R43: protocol_version is empty")
        if self.protocol_version != expected_version:
            raise PC1ExecutionRefused(
                f"R43: protocol_version mismatch: got '{self.protocol_version}', "
                f"expected '{expected_version}'")
        # R43: canonical protocol must itself be APPROVED
        if canonical_status and canonical_status != "APPROVED":
            raise PC1ExecutionRefused(
                f"R43: canonical protocol status is '{canonical_status}', "
                f"cannot authorize while PROPOSED")


@dataclass
class ApprovalGate:
    """R31: approval gate requiring protocol status + hash + Planner metadata.

    Boolean `approved` alone is NOT sufficient. The gate requires:
    - protocol_status == "APPROVED"
    - canonical protocol hash matches expected
    - non-empty approver and approval_date
    Default: all fields unset → deny.
    """
    approved: bool = False
    approver: str = ""
    approval_date: str = ""
    protocol_status: str = ""
    protocol_hash: str = ""
    expected_protocol_hash: str = ""

    approval_record: Optional[PlannerApprovalRecord] = None
    trusted_artifact: Optional[TrustedApprovalArtifact] = None
    approval_key: Optional[bytes] = None   # external trust anchor

    def check(self) -> None:
        """R54: require trusted artifact with valid HMAC + canonical APPROVED status. Fail-closed."""
        if not self.approved:
            raise PC1ExecutionRefused("R54: approved=False")
        # R54: must have a trusted artifact with signature
        if self.trusted_artifact is None:
            raise PC1ExecutionRefused("R54: no TrustedApprovalArtifact provided")
        if self.approval_key is None:
            raise PC1ExecutionRefused("R54: no approval_key provided")
        # R54: read canonical protocol and check its status
        doc = parse_protocol_document()
        canonical_status = doc.get("status", "")
        if canonical_status not in ("APPROVED",):
            raise PC1ExecutionRefused(
                f"R54: canonical protocol status is '{canonical_status}', "
                f"need 'APPROVED' — PROPOSED/NOT_APPROVED cannot authorize")
        expected_hash = compute_protocol_hash(doc)
        expected_version = doc.get("code_version", PROTOCOL_VERSION)
        # R54: verify the trusted artifact (HMAC + action + status + fields)
        self.trusted_artifact.verify(expected_hash, expected_version, self.approval_key)
        # R50: also verify gate-level hash consistency
        if not self.protocol_hash or not self.protocol_hash.strip():
            raise PC1ExecutionRefused("R50: gate protocol_hash is empty")
        if self.protocol_hash != self.trusted_artifact.protocol_hash:
            raise PC1ExecutionRefused(
                f"R50: gate hash '{self.protocol_hash}' != artifact hash '{self.trusted_artifact.protocol_hash}'")


@dataclass
class ProductionRuntimeGate:
    """R31: production runtime gate. Binds to a concrete runtime-lock revision."""
    ready: bool = False
    runtime_revision: str = ""
    required_revision: str = ""

    def check(self) -> None:
        """R38: fail-closed — both revisions must be non-empty and match."""
        if not self.ready:
            raise PC1ExecutionRefused("R38: production runtime gate NOT ready")
        if not self.runtime_revision or not self.runtime_revision.strip():
            raise PC1ExecutionRefused("R38: runtime_revision is empty")
        if not self.required_revision or not self.required_revision.strip():
            raise PC1ExecutionRefused("R38: required_revision is empty")
        if self.runtime_revision != self.required_revision:
            raise PC1ExecutionRefused(
                f"R38: runtime revision mismatch: got '{self.runtime_revision}', "
                f"expected '{self.required_revision}'")


@dataclass
class ProtocolVersionGate:
    """R25: protocol version gate. Requires matching version."""
    required_version: str = PROTOCOL_VERSION

    def check(self, actual_version: str) -> None:
        if actual_version != self.required_version:
            raise PC1ExecutionRefused(
                f"R25: protocol version mismatch: expected {self.required_version}, got {actual_version}")


class SyntheticGateHarness:
    """R31: synthetic gate/accounting harness (NOT a full collection/rollout runner).

    This class provides gate checks and budget accounting for synthetic testing
    of the execution path. It does NOT load tasks, invoke evaluators, execute
    rollouts, or write raw artifacts. The full collection/rollout runner is
    NOT YET IMPLEMENTED and requires Planner protocol approval + production
    runtime before implementation.

    All gates default-deny. Boolean flags alone cannot authorize a proposed
    protocol — the approval gate checks protocol status, hash, and approval metadata.
    """

    def __init__(self, approval_gate: ApprovalGate,
                 production_gate: ProductionRuntimeGate,
                 protocol_gate: ProtocolVersionGate):
        self.approval_gate = approval_gate
        self.production_gate = production_gate
        self.protocol_gate = protocol_gate
        self.ledger = BudgetLedger()
        self.executed_units: List[str] = []

    def _check_all_gates(self, protocol_version: str) -> None:
        self.approval_gate.check()
        self.production_gate.check()
        self.protocol_gate.check(protocol_version)

    def execute_unit(self, unit_id: str, protocol_version: str,
                     planned_slots: int, replicas_run_delta: int,
                     cache_bundle_delta: int) -> None:
        """R25: execute one unit with gate + budget checks."""
        self._check_all_gates(protocol_version)
        if self.ledger.planned_slots + planned_slots > HARD_CAP_SLOTS:
            raise PC1ExecutionRefused(
                f"R25: unit {unit_id} would exceed hard cap "
                f"({self.ledger.planned_slots}+{planned_slots}>{HARD_CAP_SLOTS})")
        self.ledger.record_evaluation(planned_slots, replicas_run_delta, cache_bundle_delta)
        self.executed_units.append(unit_id)

    def execute_collection_episode(self, episode_id: str, protocol_version: str,
                                   planned_slots: int, replicas_run_delta: int,
                                   cache_bundle_delta: int) -> None:
        self._check_all_gates(protocol_version)
        if self.ledger.planned_slots + planned_slots > HARD_CAP_SLOTS:
            raise PC1ExecutionRefused(
                f"R25: collection {episode_id} would exceed hard cap")
        self.ledger.record_collection(planned_slots, replicas_run_delta, cache_bundle_delta)
        self.executed_units.append(f"col:{episode_id}")

    def summary(self) -> dict:
        return {"ledger": self.ledger.summary(),
                "executed_units": len(self.executed_units),
                "gates": {
                    "approval": self.approval_gate.approved,
                    "production": self.production_gate.ready,
                    "protocol": self.protocol_gate.required_version,
                }}


def create_default_gated_runner() -> SyntheticGateHarness:
    """R25: default runner with ALL gates closed (default-deny)."""
    return SyntheticGateHarness(
        approval_gate=ApprovalGate(approved=False),
        production_gate=ProductionRuntimeGate(ready=False),
        protocol_gate=ProtocolVersionGate(),
    )


# ===========================================================================
# Zero-cost protocol check (updated for R12-R16)
# ===========================================================================

def zero_cost_protocol_check() -> dict:
    checks: Dict[str, Tuple[bool, str]] = {}

    checks["planned_within_hard_cap"] = (PLANNED_TOTAL_SLOTS <= HARD_CAP_SLOTS, f"{PLANNED_TOTAL_SLOTS}<={HARD_CAP_SLOTS}")
    checks["states_at_least_100"] = (N_STATES >= 100, f"{N_STATES}")
    checks["init_slots_included"] = (PLANNED_COLLECTION_SLOTS >= N_STATE_COLLECTION_EPISODES * MU * N_EVAL, f"{PLANNED_COLLECTION_SLOTS}")

    s1 = crn_seed("T1", "s0", 0)
    s2 = crn_seed("T1", "s0", 1)
    checks["crn_distinct_across_rollouts"] = (s1 != s2, f"{s1}!={s2}")

    # R12: BudgetLedger unit separation
    bl = BudgetLedger()
    bl.record_evaluation(planned_slots=8, replicas_run_delta=4, cache_bundle_delta=1, valid=2, invalid=0)
    checks["ledger_no_unit_mixing"] = (bl.actual_replicas_run == 4 and bl.cache_hit_bundles == 1, f"replicas={bl.actual_replicas_run} bundles={bl.cache_hit_bundles}")
    checks["ledger_planned_independent"] = (bl.planned_slots == 8, f"planned={bl.planned_slots}")

    # R14: reward identity
    rew = [0.1, -0.2, 0.3]
    q = discounted_return(rew, GAMMA)
    manual = rew[0] + GAMMA * rew[1] + GAMMA**2 * rew[2]
    checks["q_uses_same_first_term"] = (abs(q - manual) < 1e-9, f"{q}")

    big = generation_reward(10.0, 0.0, 10.0, 0.0, 1.0)
    neg = generation_reward(0.0, 10.0, 0.0, 10.0, 0.0)
    checks["reward_clip_hi"] = (big == 1.0, f"{big}")
    checks["reward_clip_lo"] = (neg == -0.5, f"{neg}")

    all_ok = all(ok for ok, _ in checks.values())
    return {
        "protocol_version": PROTOCOL_VERSION,
        "estimator_version": ESTIMATOR_VERSION,
        "all_pass": all_ok,
        "checks": {k: {"ok": ok, "detail": d} for k, (ok, d) in checks.items()},
        "budget": {
            "q_slots": PLANNED_Q_SLOTS, "extra_slots": PLANNED_EXTRA_SLOTS,
            "collection_slots": PLANNED_COLLECTION_SLOTS,
            "total_planned": PLANNED_TOTAL_SLOTS,
            "hard_cap": HARD_CAP_SLOTS, "headroom": HARD_CAP_SLOTS - PLANNED_TOTAL_SLOTS,
        },
        "thresholds": {"D": THRESHOLD_D, "advantage": THRESHOLD_ADVANTAGE,
                       "margin_D": MARGIN_D, "margin_advantage": MARGIN_ADV,
                       "inconclusive_rule": "SR1 STOP"},
    }
