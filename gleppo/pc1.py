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
PROTOCOL_STATUS = "PROPOSED_AWAITING_PLANNER_APPROVAL"

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


def protocol_consistency_check() -> dict:
    """R19: verify code constants match CANONICAL_PROTOCOL and registered values."""
    checks: Dict[str, Tuple[bool, str]] = {}
    checks["protocol_version"] = (CANONICAL_PROTOCOL["protocol_version"] == PROTOCOL_VERSION, PROTOCOL_VERSION)
    checks["n_states_100"] = (CANONICAL_PROTOCOL["n_states"] == N_STATES == 100, str(N_STATES))
    checks["n_actions_5"] = (CANONICAL_PROTOCOL["n_actions"] == N_ACTIONS == 5, str(N_ACTIONS))
    checks["q_rollouts_3"] = (CANONICAL_PROTOCOL["q_rollouts"] == Q_ROLLOUTS == 3, str(Q_ROLLOUTS))
    checks["horizon_3"] = (CANONICAL_PROTOCOL["horizon"] == HORIZON == 3, str(HORIZON))
    checks["extra_immediate_1"] = (CANONICAL_PROTOCOL["extra_immediate"] == EXTRA_IMMEDIATE == 1, str(EXTRA_IMMEDIATE))
    checks["gamma"] = (CANONICAL_PROTOCOL["gamma"] == GAMMA, str(GAMMA))
    checks["budget_total_45440"] = (PLANNED_TOTAL_SLOTS == 45440, str(PLANNED_TOTAL_SLOTS))
    checks["hard_cap_50000"] = (HARD_CAP_SLOTS == 50000, str(HARD_CAP_SLOTS))
    checks["threshold_D"] = (THRESHOLD_D == 0.15, str(THRESHOLD_D))
    checks["threshold_adv"] = (THRESHOLD_ADVANTAGE == 0.02, str(THRESHOLD_ADVANTAGE))
    checks["margin_D"] = (MARGIN_D == 0.10, str(MARGIN_D))
    checks["margin_adv"] = (MARGIN_ADV == 0.01, str(MARGIN_ADV))
    all_ok = all(ok for ok, _ in checks.values())
    return {"all_pass": all_ok,
            "checks": {k: {"ok": ok, "detail": d} for k, (ok, d) in checks.items()},
            "canonical": CANONICAL_PROTOCOL}


# ===========================================================================
# R16 seed helpers (single contract)
# ===========================================================================

def crn_seed(task_id: str, state_id: str, rollout_id: int, replicate_id: int = 0) -> str:
    """R20: paired CRN key includes task and outer replicate. Excludes action/genotype."""
    return hashlib.sha256(f"CRN|{task_id}|{state_id}|{rollout_id}|{replicate_id}".encode()).hexdigest()[:16]


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
        """R27: collection accounting with same validation."""
        ps = self._validate_nonneg("planned_slots", planned_slots)
        rd = self._validate_nonneg("replicas_run_delta", replicas_run_delta)
        cb = self._validate_nonneg("cache_bundle_delta", cache_bundle_delta)
        if self.planned_slots + ps > HARD_CAP_SLOTS:
            raise ValueError(
                f"R27: collection {self.planned_slots}+{ps} would exceed cap {HARD_CAP_SLOTS}")
        self.planned_collection_slots += ps
        self.planned_slots += ps
        self.actual_replicas_run += rd
        self.cache_hit_bundles += cb

    def record_q_slot(self, planned_slots: int, replicas_run_delta: int,
                      cache_bundle_delta: int) -> None:
        ps = self._validate_nonneg("planned_slots", planned_slots)
        self.planned_q_slots += ps
        self.record_evaluation(ps, replicas_run_delta, cache_bundle_delta, valid=1)

    def record_extra_slot(self, planned_slots: int, replicas_run_delta: int,
                          cache_bundle_delta: int) -> None:
        ps = self._validate_nonneg("planned_slots", planned_slots)
        self.planned_extra_slots += ps
        self.record_evaluation(ps, replicas_run_delta, cache_bundle_delta, valid=0)

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
                     require_registered_shape: bool = True) -> None:
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
            q_counts[(rec.state_id, rec.action)] = q_counts.get((rec.state_id, rec.action), 0) + 1
        else:  # ROLE_EXTRA
            if len(rec.gen_rewards) != 1:
                raise ValueError(
                    f"R13/R14: {tag}: extra_immediate must have exactly 1 reward, got {len(rec.gen_rewards)}")
            extra_counts[(rec.state_id, rec.action)] = extra_counts.get((rec.state_id, rec.action), 0) + 1

        # R13: duplicate key check (state, action, rollout, replicate, role)
        key = (rec.state_id, rec.action, rec.rollout_id, rec.replicate_id, rec.sample_role)
        if key in seen_keys:
            raise ValueError(f"R13: duplicate sample key {key}")
        seen_keys.add(key)

        state_clusters.setdefault(rec.state_id, set()).add(rec.cluster_id)
        states.add(rec.state_id)
        clusters.add(rec.cluster_id)

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
        # R29: provenance must be present
        for rec in records:
            if not rec.task_id:
                raise ValueError(f"R29: record state={rec.state_id} missing task_id")
            if not rec.episode_id:
                raise ValueError(f"R29: record state={rec.state_id} missing episode_id")


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
                     evaluator_version: str = "") -> "PC1Result":
    """R13: validate first, fail closed. R28: full reconciliation. R30: provenance."""
    # R30: registered provenance must be non-empty BEFORE any statistics
    if require_registered_shape:
        if not manifest_hash or not manifest_hash.strip():
            raise ValueError("R30: registered analysis requires non-empty manifest_hash")
        if not runtime_revision or not runtime_revision.strip():
            raise ValueError("R30: registered analysis requires non-empty runtime_revision")
        if not evaluator_version or not evaluator_version.strip():
            raise ValueError("R30: registered analysis requires non-empty evaluator_version")
    # R21: reject invalid totals
    if planned_slots_total <= 0:
        raise ValueError(f"R21: planned_slots_total must be positive, got {planned_slots_total}")
    if planned_slots_total > HARD_CAP_SLOTS:
        raise ValueError(f"R21: planned slots {planned_slots_total} exceed hard cap {HARD_CAP_SLOTS}")

    validate_records(records, require_registered_shape=require_registered_shape)

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

    def check(self) -> None:
        if not self.approved:
            raise PC1ExecutionRefused(
                "R31: approval gate NOT satisfied (approved=False).")
        if self.protocol_status != "APPROVED":
            raise PC1ExecutionRefused(
                f"R31: protocol status is '{self.protocol_status}', need 'APPROVED'. "
                "A proposed protocol cannot be executed even if boolean flags are set.")
        if not self.approver or not self.approval_date:
            raise PC1ExecutionRefused(
                "R31: approval metadata incomplete (need approver + approval_date).")
        if self.expected_protocol_hash and self.protocol_hash != self.expected_protocol_hash:
            raise PC1ExecutionRefused(
                f"R31: protocol hash mismatch: expected {self.expected_protocol_hash}, "
                f"got {self.protocol_hash}")


@dataclass
class ProductionRuntimeGate:
    """R31: production runtime gate. Binds to a concrete runtime-lock revision."""
    ready: bool = False
    runtime_revision: str = ""
    required_revision: str = ""

    def check(self) -> None:
        if not self.ready:
            raise PC1ExecutionRefused(
                "R31: production runtime gate NOT ready.")
        if self.required_revision and self.runtime_revision != self.required_revision:
            raise PC1ExecutionRefused(
                f"R31: runtime revision mismatch: need '{self.required_revision}', "
                f"got '{self.runtime_revision}'")


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
