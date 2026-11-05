"""R26 Algorithm Pilot: Deterministic orchestration of all arms.

StubLLM only. Family A/B only. NOT PC1, NOT Formal G3, NOT confirmatory.
"""
import json
import hashlib
import random
import time
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from gleppo.evolution import EvolutionConfig, evolve, stable_seed, Individual
from gleppo.evaluator import Evaluator
from gleppo.interpreter import Interpreter
from gleppo.llm import StubLLM
from gleppo.tasks import attach_checker, TRAIN_TEMPLATES_A, TRAIN_TEMPLATES_B, VAL_TEMPLATES_A, VAL_TEMPLATES_B
from gleppo.operators import OPERATOR_NAMES
from gleppo.reward import GAMMA

from experiments.r26_operator_pilot.controllers import (
    RuleController, LinUCBController, QLearnController, pilot_context_v1,
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
OUT_DIR = Path(__file__).resolve().parent

MU, LAM, T, N_EVAL = 8, 4, 15, 2
TRAIN_SEEDS = [11, 22]
VAL_SEEDS = [1011, 1022]


def load_tasks(path: Path, n: int) -> list:
    tasks = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= n: break
            t = json.loads(line)
            tasks.append(attach_checker(t))
    return tasks


def make_evaluator():
    llm = StubLLM()
    interp = Interpreter(llm=llm)
    return Evaluator(interpreter=interp, n_eval=N_EVAL)


def run_arm_episode(arm: str, task: dict, seed: int, train: bool) -> dict:
    cfg = EvolutionConfig(mu=MU, lam=LAM, T=T, n_eval=N_EVAL)
    evaluator = make_evaluator()

    # Build controller
    rule_ctl = RuleController()
    linucb_ctl = LinUCBController()
    qlearn_ctl = QLearnController()
    if not train:
        # Will be frozen externally
        pass

    # Operator schedule
    op_usage = {op: 0 for op in OPERATOR_NAMES}
    rewards_last3 = []
    stagnation = 0
    last_best = 0.0

    def schedule(t, pop, history):
        nonlocal stagnation, last_best, op_usage

        best = max((x.success for x in pop), default=0.0)
        mean = sum(x.success for x in pop) / max(1, len(pop))

        if history:
            last = history[-1]
            if best <= last_best + 1e-9:
                stagnation += 1
            else:
                stagnation = 0
        last_best = best

        # Build pilot context
        fail_rates = {}
        for ind in pop:
            if ind.failure:
                fail_rates[ind.failure] = fail_rates.get(ind.failure, 0) + 1
        for k in fail_rates:
            fail_rates[k] /= max(1, len(pop))

        tool_sets = [list(ind.geno.tools) for ind in pop]
        workflows = [[getattr(s, "type", "") for s in ind.geno.workflow] for ind in pop]
        op_delta_mean = history[-1].get("op_delta_mean", 0.0) if history else 0.0
        valid_rate = history[-1].get("valid_rate", 0.0) if history else 0.0

        ctx = pilot_context_v1(
            best, mean, t, T, stagnation, fail_rates,
            valid_rate, op_delta_mean, rewards_last3,
            tool_sets, workflows, op_usage,
        )

        # Select operator
        if arm.startswith("F"):
            op = OPERATOR_NAMES[int(arm[1]) - 1]
        elif arm == "RND":
            op = random.choice(OPERATOR_NAMES)
        elif arm == "RULE":
            op = rule_ctl.select(t, best, mean, history) if history else rule_ctl.initial_fallback()
        elif arm == "LINUCB":
            op = linucb_ctl.select(ctx)
        elif arm == "QLEARN":
            op = qlearn_ctl.select(ctx, training=train)
        else:
            raise ValueError(arm)

        op_usage[op] = op_usage.get(op, 0) + 1
        return op

    # Run episode
    eid = f"{task['task_id']}-{seed}"
    t0 = time.time()
    result = evolve(schedule, cfg, evaluator, task, seed=seed, episode_id=eid)
    wall = time.time() - t0

    # Post-episode controller updates
    if result.logs:
        for i, log in enumerate(result.logs):
            rewards_last3.append(log.reward)
            if arm == "LINUCB":
                # Build context for this generation (approximate)
                ctx = [0.0] * 15  # simplified; use actual if available
                linucb_ctl.update(op_usage and list(op_usage.keys())[0] or OPERATOR_NAMES[0], ctx, log.reward)
            elif arm == "QLEARN":
                qlearn_ctl.update(log.reward, terminal=(i == len(result.logs) - 1))
        if arm == "QLEARN":
            qlearn_ctl.finalize_episode(result.logs[-1].reward)

    return {
        "arm": arm, "task_id": task["task_id"], "seed": seed, "train": train,
        "best_success": result.best_success,
        "final_mean": result.logs[-1].mean_success if result.logs else 0.0,
        "discounted_return": sum(log.reward * (GAMMA ** log.t) for log in result.logs),
        "valid_offspring": result.valid_offspring,
        "invalid_offspring": result.invalid_offspring,
        "planned_slots": result.planned_slots,
        "actual_ctx": result.actual_ctx,
        "cache_hits": result.cache_hits,
        "wall_time": wall,
        "generations": len(result.logs),
        "per_gen": [{"t": log.t, "op": log.operator, "best": log.best_success,
                      "mean": log.mean_success, "reward": log.reward,
                      "valid": log.valid_count, "invalid": log.invalid_count}
                     for log in result.logs],
    }


def main():
    print("Loading tasks...")
    train_a = load_tasks(DATA_DIR / "train_A.jsonl", 7)
    train_b = load_tasks(DATA_DIR / "train_B.jsonl", 5)
    val_a = load_tasks(DATA_DIR / "val_A.jsonl", 3)
    val_b = load_tasks(DATA_DIR / "val_B.jsonl", 3)
    train_tasks = train_a + train_b  # 12 tasks
    val_tasks = val_a + val_b  # 6 tasks

    print(f"Train: {len(train_tasks)} tasks, Val: {len(val_tasks)} tasks")

    arms = [f"F{i}" for i in range(1, 6)] + ["RND", "RULE", "LINUCB", "QLEARN"]
    episodes = []

    # TRAIN phase
    for arm in arms:
        print(f"\n=== TRAIN: {arm} ===")
        for task in train_tasks:
            for seed in TRAIN_SEEDS:
                ep = run_arm_episode(arm, task, seed, train=True)
                episodes.append(ep)
                print(f"  {task['task_id']} seed={seed} best={ep['best_success']:.3f} ret={ep['discounted_return']:.3f}")

    # VALIDATION phase (controllers should be frozen here)
    for arm in arms:
        print(f"\n=== VAL: {arm} ===")
        for task in val_tasks:
            for seed in VAL_SEEDS:
                ep = run_arm_episode(arm, task, seed, train=False)
                episodes.append(ep)
                print(f"  {task['task_id']} seed={seed} best={ep['best_success']:.3f}")

    # Save raw episodes
    with open(OUT_DIR / "RAW_EPISODES.jsonl", "w", encoding="utf-8") as f:
        for ep in episodes:
            f.write(json.dumps(ep) + "\n")

    # Compute summary
    from collections import defaultdict
    by_arm_train = defaultdict(list)
    by_arm_val = defaultdict(list)
    for ep in episodes:
        if ep["train"]:
            by_arm_train[ep["arm"]].append(ep)
        else:
            by_arm_val[ep["arm"]].append(ep)

    summary = {}
    for arm in arms:
        tr = by_arm_train[arm]; va = by_arm_val[arm]
        summary[arm] = {
            "train_best_mean": sum(e["best_success"] for e in tr) / max(1, len(tr)),
            "val_best_mean": sum(e["best_success"] for e in va) / max(1, len(va)),
            "val_final_mean": sum(e.get("final_mean", 0) for e in va) / max(1, len(va)),
            "val_return_mean": sum(e["discounted_return"] for e in va) / max(1, len(va)),
            "val_valid_rate": sum(e["valid_offspring"] for e in va) / max(1, sum(e["valid_offspring"] + e["invalid_offspring"] for e in va)),
            "val_episodes": len(va),
            "train_episodes": len(tr),
        }

    with open(OUT_DIR / "SUMMARY.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for arm in arms:
        s = summary[arm]
        print(f"{arm:10s} train_best={s['train_best_mean']:.3f} val_best={s['val_best_mean']:.3f} val_ret={s['val_return_mean']:.3f}")

    # Paired bootstrap comparison
    print("\n=== Paired comparisons (VAL) ===")
    rng = random.Random(42)
    for comp_arm in ["LINUCB", "QLEARN"]:
        for base_arm in ["RND", "RULE", "F1"]:
            pairs = []
            for e1 in by_arm_val[comp_arm]:
                for e2 in by_arm_val[base_arm]:
                    if e1["task_id"] == e2["task_id"] and e1["seed"] == e2["seed"]:
                        pairs.append(e1["best_success"] - e2["best_success"])
            if not pairs: continue
            n = len(pairs)
            boot_means = []
            for _ in range(10000):
                sample = [pairs[rng.randrange(n)] for _ in range(n)]
                boot_means.append(sum(sample) / n)
            boot_means.sort()
            mean_diff = sum(pairs) / n
            ci_lo = boot_means[int(0.025 * 10000)]
            ci_hi = boot_means[int(0.975 * 10000)]
            print(f"{comp_arm} vs {base_arm}: diff={mean_diff:+.4f} 95%CI=[{ci_lo:+.4f},{ci_hi:+.4f}] n={n}")

    print(f"\nTotal episodes: {len(episodes)}")
    print(f"Planned slots: {sum(e['planned_slots'] for e in episodes)}")
    print("DONE")


if __name__ == "__main__":
    main()
