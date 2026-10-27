"""Production smoke test with real model. Family A/B only. No Family C."""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gleppo.evaluator import Evaluator
from gleppo.evolution import EvolutionConfig, evolve
from gleppo.llm import ProductionLLM, StubLLM
from gleppo.manifest import FamilyCGuard, load_split
from gleppo.operators import OPERATOR_NAMES
from gleppo.tasks import attach_checker

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
MAX_GENERATIONS = 512
MAX_WALL_CLOCK_S = 1800  # 30 minutes

def main():
    guard = FamilyCGuard(enabled=True)
    
    # Load 2 train_A + 2 train_B tasks
    tasks = load_split(DATA_DIR, "train_A", with_checker=True)[:2] + \
            load_split(DATA_DIR, "train_B", with_checker=True)[:2]
    for t in tasks:
        guard.check_task(t)
    
    # Initialize ProductionLLM
    print("Loading ProductionLLM (Qwen2.5-7B-Instruct)...")
    llm = ProductionLLM(device="cuda:0", max_new_tokens=256)
    print(f"Model loaded: {llm.name} rev={llm.version}")
    
    # Single request test
    print("=== Single request test ===")
    reply = llm.reply("You are a math solver.", "What is 2+2?", [], ("test", 0, 0))
    print(f"Reply: {reply.text[:100]}")
    assert reply.kind == "answer"
    
    # Single task end-to-end
    print("=== Single task end-to-end ===")
    from gleppo.interpreter import Interpreter
    interp = Interpreter(llm=llm)
    task = attach_checker(dict(tasks[0]))
    g = __import__("gleppo.genotype", fromlist=["make_valid_genotype"]).make_valid_genotype()
    t0 = time.time()
    result = interp.run(g, task, seed_parts=("prod-smoke", 0, 0))
    print(f"Task {task['task_id']}: success={result.success}, fail={result.failure_category}, turns={result.turns}")
    
    # Full 4-task smoke
    print("=== Full 4-task smoke ===")
    cfg = EvolutionConfig(mu=4, lam=2, T=6, n_eval=2)
    ev = Evaluator(interpreter=interp, n_eval=2, runtime_revision="production-v1")
    
    def sched(t, pop, hist):
        return OPERATOR_NAMES[t % len(OPERATOR_NAMES)]
    
    results = []
    total_gen = 0
    t_start = time.time()
    
    for task in tasks:
        if total_gen >= MAX_GENERATIONS or (time.time() - t_start) > MAX_WALL_CLOCK_S:
            print(f"Budget limit reached: {total_gen} generations")
            break
        t0 = time.time()
        ep = evolve(sched, cfg, ev, task, seed=42, episode_id=f"prod-{task['task_id']}")
        dt = time.time() - t0
        total_gen += cfg.T
        results.append({
            "task_id": task["task_id"],
            "family": task["family"],
            "best_success": ep.best_success,
            "wall_clock_s": round(dt, 4),
            "planned_init_slots": ep.planned_init_slots,
            "planned_total_slots": ep.planned_slots,
            "actual_replicas_run": ep.actual_ctx,
            "cache_hit_bundles": ep.cache_hits,
            "valid_offspring": ep.valid_offspring,
            "invalid_offspring": ep.invalid_offspring,
        })
        print(f"  {task['task_id']} ({task['family']}): success={ep.best_success:.3f}, "
              f"ctx={ep.actual_ctx}, cache={ep.cache_hits}, wall={dt:.2f}s")
    
    total_wall = time.time() - t_start
    llm_stats = llm.get_stats()
    
    # Save raw results
    raw = {
        "mode": "PRODUCTION_QWEN25_7B",
        "model_revision": llm.version,
        "n_tasks": len(results),
        "budget": {"max_generations": MAX_GENERATIONS, "max_wall_clock_s": MAX_WALL_CLOCK_S},
        "actual_generations": total_gen,
        "actual_wall_clock_s": round(total_wall, 4),
        "tasks": results,
        "llm_stats": llm_stats,
        "family_c_accessed": False,
    }
    
    os.makedirs("research", exist_ok=True)
    with open("research/PRODUCTION_SMOKE_RAW.json", "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2, ensure_ascii=False)
    
    print(f"\n=== SUMMARY ===")
    print(f"Tasks: {len(results)}, Generations: {total_gen}, Wall: {total_wall:.1f}s")
    print(f"LLM stats: {llm_stats}")
    print(f"Saved to research/PRODUCTION_SMOKE_RAW.json")

if __name__ == "__main__":
    main()
