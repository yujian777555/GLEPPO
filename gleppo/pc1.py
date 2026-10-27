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

PROTOCOL_VERSION = "pc1-amendment-v3-r3"
ESTIMATOR_VERSION = "est-v1-r_hat=q_first+extra,q_hat=q_rollout_only"

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


# ===========================================================================
# R16 seed helpers (single contract)
# ===========================================================================

def crn_seed(state_id: str, rollout_id: int) -> str:
    """Paired evaluation CRN seed: shared across actions for (state, rollout)."""
    return hashlib.sha256(f"CRN|{state_id}|{rollout_id}".encode()).hexdigest()[:16]


def operator_rng_seed(operator: str, state_id: str, action: int, rollout_id: int, draw: int) -> int:
    """Action/operator-specific generation RNG (separate from evaluation RNG)."""
    h = hashlib.sha256(f"OPRNG|{operator}|{state_id}|{action}|{rollout_id}|{draw}".encode()).hexdigest()
    return int(h[:16], 16) % (2 ** 31 - 1)


# ===========================================================================
# R12 BudgetLedger — explicit units, no mixed arithmetic
# ===========================================================================

@dataclass
class BudgetLedger:
    """R12: every counter is incremented from explicit deltas in its own unit."""
    planned_slots: int = 0
    actual_replicas_run: int = 0      # uncached replica executions
    cache_hit_bundles: int = 0        # 1 bundle = n_eval replicas returned, 0 ran
    invalid_offspring: int = 0
    valid_offspring: int = 0
    operator_llm_calls: int = 0
    agent_llm_turns: int = 0
    notes: List[str] = field(default_factory=list)

    def record_evaluation(self, planned_slots: int, replicas_run_delta: int,
                          cache_bundle_delta: int, valid: int = 1, invalid: int = 0,
                          op_llm_calls: int = 0, agent_turns: int = 0) -> None:
        """Record one evaluation unit. replicas_run_delta comes from the evaluator
        counter delta (actual uncached replica executions), NOT from valid*n_eval."""
        self.planned_slots += planned_slots
        self.actual_replicas_run += replicas_run_delta
        self.cache_hit_bundles += cache_bundle_delta
        self.valid_offspring += valid
        self.invalid_offspring += invalid
        self.operator_llm_calls += op_llm_calls
        self.agent_llm_turns += agent_turns

    def record_init(self, mu: int, n_eval: int, replicas_run_delta: int,
                    cache_bundle_delta: int) -> None:
        self.record_evaluation(
            planned_slots=mu * n_eval,
            replicas_run_delta=replicas_run_delta,
            cache_bundle_delta=cache_bundle_delta,
            valid=mu, invalid=0,
        )

    def check_cap(self) -> bool:
        return self.planned_slots <= HARD_CAP_SLOTS

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
    """One sample. Immutable metadata for replay (R17)."""
    state_id: str
    cluster_id: str
    action: int
    rollout_id: int
    replicate_id: int
    crn_seed: str
    sample_role: str                    # R14: ROLE_Q or ROLE_EXTRA
    gen_rewards: List[float]            # q_rollout: len==HORIZON; extra_immediate: len==1
    family: str = "A"                   # R15: must be A or B
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
        if len(states) < N_STATES:
            raise ValueError(f"R13: need >= {N_STATES} states for registered PC1, got {len(states)}")
        # every state must have all 5 actions with Q_ROLLOUTS Q records
        for sid in states:
            for a in range(N_ACTIONS):
                qc = q_counts.get((sid, a), 0)
                if qc < Q_ROLLOUTS:
                    raise ValueError(
                        f"R13: state {sid} action {a}: {qc} q_rollout records, need >= {Q_ROLLOUTS}")
                ec = extra_counts.get((sid, a), 0)
                if ec < EXTRA_IMMEDIATE:
                    raise ValueError(
                        f"R13: state {sid} action {a}: {ec} extra_immediate records, need >= {EXTRA_IMMEDIATE}")
        if len(clusters) < 2:
            raise ValueError(f"R13: need >= 2 independent clusters for bootstrap, got {len(clusters)}")


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
    """R17: sanitized per-record fields (no gold labels)."""
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
    """R13: validate first, fail closed. R17: emit replayable evidence."""
    if planned_slots_total > HARD_CAP_SLOTS:
        raise ValueError(f"planned slots {planned_slots_total} exceed hard cap {HARD_CAP_SLOTS}")

    validate_records(records, require_registered_shape=require_registered_shape)

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

    # R17: replayable evidence
    ledger = BudgetLedger()
    for rec in records:
        ledger.record_evaluation(
            planned_slots=rec.planned_slots,
            replicas_run_delta=rec.actual_replicas_run,
            cache_bundle_delta=rec.cache_hit_bundles,
            valid=1 if rec.sample_role == ROLE_Q else 0,
            invalid=rec.invalid_count,
        )

    raw_evidence = {
        "protocol_version": PROTOCOL_VERSION,
        "estimator_version": ESTIMATOR_VERSION,
        "manifest_hash": manifest_hash,
        "runtime_revision": runtime_revision,
        "evaluator_version": evaluator_version,
        "seed_contract": "effective_seed_parts(state_id, task_id, rollout_id, replicate_id, replica_index); override via eval_seed",
        "thresholds": {"D": THRESHOLD_D, "advantage": THRESHOLD_ADVANTAGE,
                       "margin_D": MARGIN_D, "margin_adv": MARGIN_ADV},
        "bootstrap": {"seed": 20261027, "n_resamples": 10000, "method": "cluster_bootstrap_by_episode"},
        "r_hat": {f"{k[0]}|{k[1]}": v for k, v in r_hat.items()},
        "q_hat": {f"{k[0]}|{k[1]}": v for k, v in q_hat.items()},
        "rows": rows,
        "strata": strata,
        "records": [_sanitize_record(r) for r in records],
        "budget": ledger.summary(),
        "planned_slots_total": planned_slots_total,
        "n_records": len(records),
        "decision_rule": "PASS if D>=0.15 and adv>=0.02 and CI margins excluded; else FAIL if CI below thresholds; else INCONCLUSIVE->SR1",
        "decision": decision,
        "replay_command": f"gleppo.pc1.run_pc1_analysis(records_from_raw, planned_slots_total={planned_slots_total}, require_registered_shape=True)",
    }

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

    # State collection episodes
    for ep in range(N_STATE_COLLECTION_EPISODES):
        policy = "random" if ep < N_STATE_COLLECTION_EPISODES // 2 else "heuristic"
        init_slots = MU * N_EVAL
        gen_slots = T_COLLECT * LAMBDA * N_EVAL
        planned_so_far += init_slots + gen_slots
        if planned_so_far > HARD_CAP_SLOTS:
            raise ValueError(f"R15: dry-run plan exceeds hard cap at collection episode {ep}")
        schedule.append({
            "unit": "collection_episode", "episode_id": f"col{ep:03d}",
            "policy": policy, "family": "A" if ep % 2 == 0 else "B",
            "planned_init_slots": init_slots, "planned_gen_slots": gen_slots,
        })

    # Q rollouts + extra immediate for each (state, action)
    for si in range(N_STATES):
        for a in range(N_ACTIONS):
            for r in range(Q_ROLLOUTS):
                slots = HORIZON * LAMBDA * N_EVAL
                planned_so_far += slots
                if planned_so_far > HARD_CAP_SLOTS:
                    raise ValueError(f"R15: dry-run plan exceeds hard cap at s{si} a{a} r{r}")
                schedule.append({
                    "unit": "q_rollout", "state_id": f"s{si:03d}", "action": a,
                    "rollout_id": r, "sample_role": ROLE_Q,
                    "crn_seed": crn_seed(f"s{si:03d}", r),
                    "planned_slots": slots,
                })
            for e in range(EXTRA_IMMEDIATE):
                slots = LAMBDA * N_EVAL
                planned_so_far += slots
                if planned_so_far > HARD_CAP_SLOTS:
                    raise ValueError(f"R15: dry-run plan exceeds hard cap at extra s{si} a{a}")
                schedule.append({
                    "unit": "extra_immediate", "state_id": f"s{si:03d}", "action": a,
                    "rollout_id": 1000 + e, "sample_role": ROLE_EXTRA,
                    "crn_seed": crn_seed(f"s{si:03d}", 1000 + e),
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
# Zero-cost protocol check (updated for R12-R16)
# ===========================================================================

def zero_cost_protocol_check() -> dict:
    checks: Dict[str, Tuple[bool, str]] = {}

    checks["planned_within_hard_cap"] = (PLANNED_TOTAL_SLOTS <= HARD_CAP_SLOTS, f"{PLANNED_TOTAL_SLOTS}<={HARD_CAP_SLOTS}")
    checks["states_at_least_100"] = (N_STATES >= 100, f"{N_STATES}")
    checks["init_slots_included"] = (PLANNED_COLLECTION_SLOTS >= N_STATE_COLLECTION_EPISODES * MU * N_EVAL, f"{PLANNED_COLLECTION_SLOTS}")

    s1 = crn_seed("s0", 0)
    s2 = crn_seed("s0", 1)
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
