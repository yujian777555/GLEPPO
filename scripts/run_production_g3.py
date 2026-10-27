"""Production G3 causality with real model. Fixes G3-A/B/C. Family A/B only."""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gleppo.genotype import make_valid_genotype, behavior_hash
from gleppo.interpreter import Interpreter
from gleppo.llm import ProductionLLM, StubLLM
from gleppo.operators import OPERATOR_NAMES, apply_operator
from gleppo.tasks import attach_checker, build_task

MAX_GENERATIONS = 2048
MAX_WALL_CLOCK_S = 1800

class InstrumentedInterpreter(Interpreter):
    """G3-B: records seed_parts to verify paired CRN."""
    def __init__(self, llm=None):
        super().__init__(llm=llm)
        self.seed_log = []

    def run(self, g, task, seed_parts=None):
        self.seed_log.append(tuple(seed_parts))
        return super().run(g, task, seed_parts=seed_parts)


def behavior_signature(g, task, interp, n_rep=2, paired_seed_base=None):
    """G3-B: use paired seeds independent of genotype."""
    succ = 0
    tools = 0
    turns = 0
    fails = {}
    traces = []
    for r in range(n_rep):
        # G3-B: paired seed depends on task+replicate, NOT genotype
        if paired_seed_base is not None:
            seed_parts = (paired_seed_base, task["task_id"], r, 0, 0)
        else:
            seed_parts = (task["task_id"], r, behavior_hash(g)[:8])
        res = interp.run(g, task, seed_parts=seed_parts)
        succ += int(res.success)
        tools += res.tool_calls
        turns += res.turns
        fails[res.failure_category] = fails.get(res.failure_category, 0) + 1
        traces.append({
            "rep": r, "success": res.success,
            "failure_category": res.failure_category,
            "turns": res.turns, "tool_calls": res.tool_calls,
            "answer_head": res.answer[:120],
        })
    return {
        "success_rate": succ / n_rep,
        "mean_tool_calls": tools / n_rep,
        "mean_turns": turns / n_rep,
        "fails": fails,
        "traces": traces,
    }


def _beh_differs(bp, bc):
    if bp["success_rate"] != bc["success_rate"]:
        return True
    if bp["mean_tool_calls"] != bc["mean_tool_calls"] or bp["mean_turns"] != bc["mean_turns"]:
        return True
    if bp["fails"] != bc["fails"]:
        return True
    for t1, t2 in zip(bp["traces"], bc["traces"]):
        if t1["answer_head"] != t2["answer_head"]:
            return True
        if t1.get("trace") != t2.get("trace"):
            return True
    return False


def main():
    # G3-A: explicitly inject ProductionLLM
    print("Loading ProductionLLM...")
    llm = ProductionLLM(device="cuda:0", max_new_tokens=256)
    interp = InstrumentedInterpreter(llm=llm)
    print(f"Backend: {llm.name} rev={llm.version}")

    # G3-C: explicit Family A + Family B tasks
    family_a_task = attach_checker(build_task("A-g3-prod-00", "A", 100, "TA1"))
    family_b_task = attach_checker(build_task("B-g3-prod-00", "B", 200, "TB1"))
    tasks = [family_a_task, family_b_task]
    
    print(f"G3 tasks: A={family_a_task['task_id']}({family_a_task['family']}), "
          f"B={family_b_task['task_id']}({family_b_task['family']})")

    parents = []
    for i in range(4):
        g = make_valid_genotype()
        g.system_prompt += f" Variant {i}."
        g.meta = {"parent_id": f"p{i}"}
        parents.append(g)

    report = {
        "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": "PRODUCTION_QWEN25_7B",
        "model_revision": llm.version,
        "backend": llm.name,
        "n_parents": 4,
        "tasks": [{"task_id": t["task_id"], "family": t["family"]} for t in tasks],
        "n_replicas": 2,
        "family_c_accessed": False,
        "operators": {},
    }

    total_gen = 0
    t_start = time.time()

    for op in OPERATOR_NAMES:
        if total_gen >= MAX_GENERATIONS or (time.time() - t_start) > MAX_WALL_CLOCK_S:
            print(f"Budget limit reached at {op}")
            break

        changed_hash = 0
        changed_behavior = 0
        valid = 0
        invalid = 0
        diffs = []

        for p_idx, parent in enumerate(parents):
            ctx = {
                "gen": p_idx,
                "failure_category": ["tool_error", "wrong_answer", "format_error", "timeout"][p_idx % 4],
                "failure_detail": "sample error",
                "mate": parents[(p_idx + 1) % 4],
            }
            child, ok, errs = apply_operator(op, parent, ctx)
            if not ok:
                invalid += 1
                continue
            valid += 1
            h_same = behavior_hash(parent) == behavior_hash(child)
            if not h_same:
                changed_hash += 1

            # G3-C: use BOTH family A and family B tasks
            beh_change = False
            sample = []
            for task in tasks:
                # G3-B: paired seed independent of genotype
                paired_base = f"paired-{task['task_id']}-p{p_idx}"
                bp = behavior_signature(parent, task, interp, n_rep=2, paired_seed_base=paired_base)
                bc = behavior_signature(child, task, interp, n_rep=2, paired_seed_base=paired_base)
                delta = {
                    "task_id": task["task_id"],
                    "family": task["family"],
                    "parent": {k: bp[k] for k in ("success_rate", "mean_tool_calls", "mean_turns", "fails")},
                    "child": {k: bc[k] for k in ("success_rate", "mean_tool_calls", "mean_turns", "fails")},
                }
                if _beh_differs(bp, bc):
                    beh_change = True
                    delta["parent_trace"] = bp["traces"][0]
                    delta["child_trace"] = bc["traces"][0]
                sample.append(delta)

            if beh_change:
                changed_behavior += 1
            diffs.append({
                "parent": p_idx,
                "valid": True,
                "hash_changed": not h_same,
                "behavior_changed": beh_change,
                "parent_hash": behavior_hash(parent),
                "child_hash": behavior_hash(child),
                "samples": sample,
            })

        total_gen += valid * 2 * 2  # 2 tasks × 2 replicas
        report["operators"][op] = {
            "valid": valid, "invalid": invalid,
            "hash_changed": changed_hash,
            "behavior_changed": changed_behavior,
            "pass": changed_behavior >= max(1, valid // 2),
            "diffs": diffs,
        }
        print(f"  {op}: valid={valid}, invalid={invalid}, "
              f"hash_changed={changed_hash}, behavior_changed={changed_behavior}, "
              f"pass={report['operators'][op]['pass']}")

    report["llm_stats"] = llm.get_stats()
    report["total_generations"] = total_gen
    report["total_wall_clock_s"] = round(time.time() - t_start, 4)

    all_pass = all(r["pass"] for r in report["operators"].values())
    report["g3_overall"] = "PASS" if all_pass else "FAIL"

    os.makedirs("research", exist_ok=True)
    with open("research/PRODUCTION_G3_RAW.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Write report
    lines = [
        "# Production G3 Causality Report",
        "",
        f"**Date:** {report['date']}",
        f"**Backend:** {report['backend']} rev={report['model_revision']}",
        f"**Tasks:** A={family_a_task['task_id']}, B={family_b_task['task_id']}",
        f"**Overall:** {report['g3_overall']}",
        "",
        "| Operator | valid | invalid | hash_changed | behavior_changed | PASS |",
        "|---|---|---|---|---|---|",
    ]
    for op, r in report["operators"].items():
        lines.append(f"| `{op}` | {r['valid']} | {r['invalid']} | "
                     f"{r['hash_changed']} | {r['behavior_changed']} | "
                     f"{'YES' if r['pass'] else 'NO'} |")
    lines.append(f"\n**LLM stats:** {report['llm_stats']}")
    lines.append(f"\n**Total generations:** {report['total_generations']}")
    lines.append(f"\n**Paired CRN:** seeds depend on (task, replicate), NOT genotype")

    with open("research/PRODUCTION_G3_REPORT.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nG3_OVERALL: {report['g3_overall']}")
    print(f"Saved to research/PRODUCTION_G3_RAW.json and PRODUCTION_G3_REPORT.md")


if __name__ == "__main__":
    main()
