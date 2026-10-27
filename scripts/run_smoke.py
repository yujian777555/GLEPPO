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

    total_ctx = 0
    total_tool_calls = 0
    total_turns = 0
    total_invalid = 0
    total_valid = 0
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
            "ctx_upper_bound": cfg.lam * cfg.n_eval * cfg.T,
            "generations": gen_stats,
        })
        total_ctx += cfg.lam * cfg.n_eval * cfg.T
        total_valid += sum(g.valid_count for g in ep.logs)
        total_invalid += sum(g.invalid_count for g in ep.logs)

    wall = time.time() - t0
    raw["totals"] = {
        "wall_clock_s": round(wall, 4),
        "ctx_upper_bound": total_ctx,
        "valid_offspring": total_valid,
        "invalid_offspring": total_invalid,
        "invalid_rate": total_invalid / max(1, total_valid + total_invalid),
        "evaluator_cache_hits": ev.cache_hits,
        "evaluator_cache_misses": ev.cache_misses,
        "interpreter_turns": "see per-replica logs in G3/production; stub does not expose token counts",
        "llm_tokens": "UNMEASURED (StubLLM; no production backend)",
        "hardware": "Windows host, Python 3.10.1, stdlib only",
    }

    os.makedirs("research", exist_ok=True)
    with open("research/SMOKE_RAW.json", "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2, ensure_ascii=False)

    print(json.dumps(raw["totals"], indent=2))
    print("SMOKE_OK tasks=", len(tasks), "ctx_upper=", total_ctx, "wall_s=", round(wall, 3))
    return 0


if __name__ == "__main__":
    sys.exit(main())
