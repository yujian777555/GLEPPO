"""Smoke test on TRAIN families only: measure executions, tool calls, latency, failures.

Family C is never executed. Writes research/SMOKE_RAW.json (raw counters).
Cost narrative goes to research/COST_BASELINE.md (written separately).
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gleppo.evaluator import Evaluator  # noqa: E402
from gleppo.evolution import EvolutionConfig, evolve  # noqa: E402
from gleppo.manifest import FamilyCGuard, build_manifests, verify_manifest, load_split  # noqa: E402
from gleppo.operators import OPERATOR_NAMES  # noqa: E402
from gleppo.tasks import attach_checker  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
N_SMOKE_TASKS = 4          # 2 from train_A, 2 from train_B
N_EVAL = 2                 # smoke replicas (main protocol uses 3)
T = 6                      # shortened episode for smoke (main T=15)
MU = 4
LAM = 2


def main():
    guard = FamilyCGuard(enabled=True)
    if not os.path.exists(os.path.join(DATA_DIR, "manifest.json")):
        build_manifests(DATA_DIR)
    errs = verify_manifest(DATA_DIR)
    if errs:
        print("MANIFEST_ERRORS", errs)
        return 2

    tasks = load_split(DATA_DIR, "train_A", with_checker=True)[:2] + load_split(DATA_DIR, "train_B", with_checker=True)[:2]
    for t in tasks:
        guard.check_task(t)

    ev = Evaluator(n_eval=N_EVAL)
    cfg = EvolutionConfig(mu=MU, lam=LAM, T=T, n_eval=N_EVAL)

    def sched(t, pop, hist):
        return OPERATOR_NAMES[t % len(OPERATOR_NAMES)]

    raw = {
        "mode": "SMOKE_STUB",
        "n_tasks": len(tasks),
        "T": T,
        "mu": MU,
        "lam": LAM,
        "n_eval": N_EVAL,
        "family_c_accessed": False,
        "tasks": [],
        "totals": {},
    }

    total_planned_init = 0
    total_planned_offspring = 0
    total_planned = 0
    total_actual_ctx = 0
    total_cache_hits = 0
    total_valid = 0
    total_invalid = 0
    t0 = time.time()

    for task in tasks:
        t1 = time.time()
        ep = evolve(sched, cfg, ev, task, seed=7)
        dt = time.time() - t1
        gen_stats = [
            {
                "t": g.t,
                "operator": g.operator,
                "valid": g.valid_count,
                "invalid": g.invalid_count,
                "best": g.best_success,
                "mean": g.mean_success,
                "reward": g.reward,
            }
            for g in ep.logs
        ]
        raw["tasks"].append({
            "task_id": task["task_id"],
            "family": task["family"],
            "best_success": ep.best_success,
            "wall_clock_s": round(dt, 4),
            "planned_init_slots": ep.planned_init_slots,
            "planned_total_slots": ep.planned_slots,
            "actual_replicas_run": ep.actual_ctx,
            "cache_hit_bundles": ep.cache_hits,
            "generations": gen_stats,
        })
        total_planned_init += ep.planned_init_slots
        total_planned += ep.planned_slots
        total_actual_ctx += ep.actual_ctx
        total_cache_hits += ep.cache_hits
        total_valid += ep.valid_offspring
        total_invalid += ep.invalid_offspring

    total_planned_offspring = total_planned - total_planned_init
    wall = time.time() - t0

    # Task C: explicit slot arithmetic for n_tasks=4, mu=4, lam=2, T=6, n_eval=2
    expected_init = len(tasks) * MU * N_EVAL          # 4*4*2 = 32
    expected_offspring = len(tasks) * T * LAM * N_EVAL  # 4*6*2*2 = 96
    expected_total = expected_init + expected_offspring  # 128

    raw["totals"] = {
        "wall_clock_s": round(wall, 4),
        # R9 units: planned slots vs actual CTX vs cache-hit BUNDLES
        "planned_init_slots": total_planned_init,
        "planned_offspring_slots": total_planned_offspring,
        "planned_total_slots": total_planned,
        "expected_init_slots": expected_init,
        "expected_offspring_slots": expected_offspring,
        "expected_total_slots": expected_total,
        "slot_arithmetic_ok": (
            total_planned_init == expected_init
            and total_planned_offspring == expected_offspring
            and total_planned == expected_total
        ),
        "actual_replicas_run": total_actual_ctx,
        "cache_hit_bundles": total_cache_hits,
        "valid_offspring": total_valid,
        "invalid_offspring": total_invalid,
        "invalid_rate": total_invalid / max(1, total_valid + total_invalid),
        "evaluator_cache_hits_cumulative": ev.cache_hits,
        "evaluator_cache_misses": ev.cache_misses,
        "llm_tokens": "UNMEASURED (StubLLM; no production backend)",
        "hardware": "Windows host, Python 3.10.1, stdlib only",
        "units_note": (
            "planned_*_slots = conservative planned candidate-task replica slots (hard-cap unit); "
            "actual_replicas_run = uncached replica executions that actually ran; "
            "cache_hit_bundles = cached evaluation bundles (1 bundle = n_eval replicas, 0 ran). "
            "Planned slots are NOT actual CTX."
        ),
    }

    os.makedirs("research", exist_ok=True)
    with open("research/SMOKE_RAW.json", "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2, ensure_ascii=False)

    print(json.dumps(raw["totals"], indent=2))
    print("SMOKE_OK tasks=", len(tasks),
          "planned_init=", total_planned_init,
          "planned_offspring=", total_planned_offspring,
          "planned_total=", total_planned,
          "actual_replicas=", total_actual_ctx,
          "cache_bundles=", total_cache_hits,
          "wall_s=", round(wall, 3))
    return 0


if __name__ == "__main__":
    sys.exit(main())
