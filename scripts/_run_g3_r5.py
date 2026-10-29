"""R5: Operator degradation repair + selection mechanism validation.

Three arms:
- A0: Original operators (tool_subset_edit, crossover)
- A1: Fixed operators + static hard constraint filter
- A2: Fixed operators + static filter + post-execution selection

Tasks: B2-001, B2-003, B2-004, B2-005, B2-006 (5 tasks)
Seeds: 3 per task
Hard cap: 150 model.generate calls, 300s wall
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from gleppo.genotype import make_task_compatible_reference, behavior_hash, validate_genotype
from gleppo.interpreter import Interpreter
from gleppo.llm import ProductionLLM, BudgetExceededError
from gleppo.operators import apply_operator
from gleppo.r4_selection import static_check_s1, run_selection_mechanisms
from gleppo.tasks import attach_checker
from gleppo.tool_path import verify_tool_path_for_task

PROTOCOL_ID = "G3-DIAG-v2-R5"
EXPECTED_BRANCH = "c7-g3-diag-v2-r1-fastpath"
EXPECTED_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
SEED_IDS = ["r5-paired-seed-001", "r5-paired-seed-002", "r5-paired-seed-003"]
MAX_GENERATIONS = 150
MAX_WALL_S = 300

# R5 arms: (arm_name, operator_name)
ARMS = [
    ("A0_original", "tool_subset_edit"),
    ("A0_original", "crossover"),
    ("A1_fixed_filtered", "tool_subset_edit_fixed"),
    ("A1_fixed_filtered", "crossover_fixed"),
]

TASK_IDS = ["B2-001", "B2-003", "B2-004", "B2-005", "B2-006"]
TASK_FILES = [
    "data/diagnostic_B2.jsonl",
    "data/diagnostic_B2_R3.jsonl",  # B2-004
    "data/diagnostic_B2_R4.jsonl",  # B2-005, B2-006
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def git(args: List[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()


def load_tasks() -> Dict[str, dict]:
    """R5 fix: load from ALL task files including R3 (B2-004)."""
    tasks = {}
    for fname in TASK_FILES:
        fpath = ROOT / fname
        if not fpath.exists():
            print(f"  WARNING: {fname} not found")
            continue
        with open(fpath, encoding="utf-8") as f:
            for line in f:
                t = attach_checker(json.loads(line))
                if t["task_id"] in TASK_IDS:
                    tasks[t["task_id"]] = t
    return tasks


def run_eval(g, task, interp, llm, seed_id, role, operator):
    seed = (PROTOCOL_ID, task["task_id"], seed_id, 0, 0)
    prov = {"task_id": task["task_id"], "operator": operator, "genotype_role": role, "replicate": 0, "turn": 0}
    res = interp.run(g, task, seed_parts=seed, provenance=prov)
    tp = verify_tool_path_for_task(task["task_id"], res.trace, task.get("required_tools", []))

    answer = res.answer
    answer_correct = bool(task.get("gold_check") and task["gold_check"](answer, g))

    format_ok = False
    if "Final answer:" in answer:
        idx = answer.index("Final answer:")
        after = answer[idx + len("Final answer:"):].strip()
        first_line = after.split("\n")[0].strip() if after else ""
        format_ok = bool(after) and len(first_line) <= 100

    tool_path_valid = tp.get("passed", False)
    hard_validity = format_ok and tool_path_valid
    effective_success = answer_correct and hard_validity

    return {
        "answer_correct": answer_correct,
        "format_compliant": format_ok,
        "tool_path_valid": tool_path_valid,
        "hard_validity": hard_validity,
        "effective_success": effective_success,
        "answer_preview": answer[:150],
    }


def main():
    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "_R5"
    run_dir = ROOT / "research" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    t_start = time.time()

    print(f"R5 run_id={run_id}")
    print(f"Arms: {[a[0] for a in ARMS]}")
    print(f"Operators: {[a[1] for a in ARMS]}")

    # Preflight
    branch = git(["branch", "--show-current"])
    head = git(["rev-parse", "HEAD"])
    assert branch == EXPECTED_BRANCH, f"wrong branch: {branch}"

    # Frozen manifest
    frozen = {
        "protocol_id": PROTOCOL_ID, "run_id": run_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_head": head, "files": {},
    }
    for f in ["research/R4_PROTOCOL.md", "gleppo/operators.py", "gleppo/r4_selection.py",
              "gleppo/genotype.py", "gleppo/interpreter.py", "gleppo/llm.py",
              "gleppo/tasks.py", "gleppo/tool_path.py", "scripts/_run_g3_r5.py"]:
        p = ROOT / f
        if p.exists():
            frozen["files"][f] = {"sha256": sha256_file(p), "size": p.stat().st_size}
    write_json(run_dir / "R5_FROZEN_MANIFEST.json", frozen)

    # Load model
    llm = ProductionLLM(device="cuda:0", max_new_tokens=256, temperature=0.7, max_generations=MAX_GENERATIONS)
    interp = Interpreter(llm=llm)
    print(f"Revision match: {llm.version == EXPECTED_REVISION}")

    tasks = load_tasks()
    print(f"Loaded {len(tasks)} tasks: {sorted(tasks.keys())}")

    # Build candidates: 5 tasks x 3 seeds x 4 arms = 60 units
    candidates = []
    for task_id in TASK_IDS:
        if task_id not in tasks:
            print(f"  WARNING: {task_id} not loaded")
            continue
        parent = make_task_compatible_reference(task_id)
        for seed_id in SEED_IDS:
            for arm_name, op_name in ARMS:
                mate = make_task_compatible_reference(task_id)
                mate.system_prompt += " Alternative strategy: compute intermediates first."
                ctx = {"gen": 0, "mate": mate, "failure_category": "wrong_answer"}
                try:
                    child, ok, errs = apply_operator(op_name, parent, ctx)
                except Exception as e:
                    child, ok, errs = None, False, [str(e)]
                candidates.append({
                    "task_id": task_id, "seed_id": seed_id,
                    "arm": arm_name, "operator": op_name,
                    "parent": parent, "child": child,
                    "child_valid": ok, "child_errors": errs if not ok else [],
                })

    total_units = len(candidates)
    estimated = total_units * 2 * 2
    print(f"Units: {total_units}, estimated generations: {estimated}")

    # Execute
    results = {
        "run_id": run_id, "protocol": PROTOCOL_ID,
        "model_revision": llm.version, "revision_match": llm.version == EXPECTED_REVISION,
        "max_generations": MAX_GENERATIONS, "max_wall_s": MAX_WALL_S,
        "tasks": sorted(tasks.keys()), "seeds": SEED_IDS,
        "arms": [f"{a[0]}/{a[1]}" for a in ARMS],
        "units": [],
    }

    budget_exhausted = False
    units_completed = 0

    for cand in candidates:
        if llm._call_id >= MAX_GENERATIONS or (time.time() - t_start) > MAX_WALL_S:
            budget_exhausted = True
            break

        task = tasks[cand["task_id"]]
        parent = cand["parent"]
        child = cand["child"]
        unit_key = f"{cand['task_id']}/{cand['seed_id']}/{cand['arm']}/{cand['operator']}"

        # Static check
        s1_result = static_check_s1(child, cand["task_id"]) if child else {"pass": False, "violations": ["no_child"]}

        # Run parent
        try:
            parent_res = run_eval(parent, task, interp, llm, cand["seed_id"], "reference", "baseline")
        except BudgetExceededError:
            budget_exhausted = True
            break

        # Run child
        child_res = None
        if cand["child_valid"] and child is not None:
            try:
                child_res = run_eval(child, task, interp, llm, cand["seed_id"], "child", cand["operator"])
            except BudgetExceededError:
                budget_exhausted = True
                break

        # Selection mechanisms
        selection = run_selection_mechanisms(parent, child, cand["task_id"], parent_res, child_res)

        results["units"].append({
            "unit_key": unit_key,
            "task_id": cand["task_id"], "seed_id": cand["seed_id"],
            "arm": cand["arm"], "operator": cand["operator"],
            "child_valid": cand["child_valid"], "child_errors": cand["child_errors"],
            "parent_result": parent_res, "child_result": child_res,
            "selection": selection,
            "s1_static_pass": s1_result.get("pass", False),
        })
        units_completed += 1

        if units_completed % 10 == 0:
            print(f"  [{units_completed}/{total_units}] {unit_key}")

    # Aggregate per arm
    results["budget_exhausted"] = budget_exhausted
    results["units_completed"] = units_completed
    results["total_units"] = total_units

    arm_aggregates = {}
    for arm_name, op_name in ARMS:
        arm_key = f"{arm_name}/{op_name}"
        arm_units = [u for u in results["units"] if u["arm"] == arm_name and u["operator"] == op_name]
        n = len(arm_units)
        if n == 0:
            continue
        parent_eff = sum(1 for u in arm_units if u["parent_result"] and u["parent_result"]["effective_success"])
        child_eff = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["effective_success"])
        improved = sum(1 for u in arm_units if u["child_result"] and u["parent_result"]
                       and u["child_result"]["effective_success"] and not u["parent_result"]["effective_success"])
        degraded = sum(1 for u in arm_units if u["child_result"] and u["parent_result"]
                       and not u["child_result"]["effective_success"] and u["parent_result"]["effective_success"])
        same = sum(1 for u in arm_units if u["child_result"] and u["parent_result"]
                   and u["child_result"]["effective_success"] == u["parent_result"]["effective_success"])
        path_ok = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["tool_path_valid"])
        fmt_ok = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["format_compliant"])

        arm_aggregates[arm_key] = {
            "n": n,
            "parent_effective_success": parent_eff, "parent_eff_rate": parent_eff/n,
            "child_effective_success": child_eff, "child_eff_rate": child_eff/n,
            "improved": improved, "degraded": degraded, "same": same,
            "child_tool_path_rate": path_ok/n, "child_format_rate": fmt_ok/n,
        }
    results["arm_aggregates"] = arm_aggregates

    # Selection mechanism comparison (across all units)
    for mech in ["S0_unfiltered", "S1_static_filter", "S2_static_select", "S3_post_exec_diag"]:
        accepted = sum(1 for u in results["units"]
                       if u["selection"].get(mech, {}).get("accepted", False)
                       or u["selection"].get(mech, {}).get("pass", False))
        results.setdefault("selection_summary", {})[mech] = {
            "accepted": accepted, "total": len(results["units"]),
        }

    # Accounting
    ledger = llm.get_generation_ledger()
    stats = llm.get_stats()
    results["llm_stats"] = stats
    results["total_actual_generations"] = len(ledger)
    results["total_wall_s"] = round(time.time() - t_start, 4)
    results["ledger_counter_match"] = len(ledger) == stats.get("actual_generations", -1)
    token_delta = sum(r["output_tokens"] for r in ledger)
    results["token_delta_sum"] = token_delta
    results["token_sum_match"] = token_delta == stats.get("total_tokens", -1)

    # Status
    if budget_exhausted and units_completed < total_units:
        results["status"] = "INCONCLUSIVE"
    else:
        results["status"] = "COMPLETE_REQUIRES_INDEPENDENT_REVIEW"

    # Save
    write_json(run_dir / "R5_RAW.json", results)
    with open(run_dir / "R5_LEDGER.jsonl", "w", encoding="utf-8") as f:
        for row in ledger:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    result_manifest = {
        "run_id": run_id, "status": results["status"],
        "frozen_manifest_sha256": sha256_file(run_dir / "R5_FROZEN_MANIFEST.json"),
        "raw_sha256": sha256_file(run_dir / "R5_RAW.json"),
        "ledger_sha256": sha256_file(run_dir / "R5_LEDGER.jsonl"),
    }
    write_json(run_dir / "R5_RESULT_MANIFEST.json", result_manifest)

    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Status: {results['status']}")
    print(f"Units: {units_completed}/{total_units}")
    print(f"Generations: {len(ledger)}/{MAX_GENERATIONS}")
    print(f"Wall: {results['total_wall_s']}s")
    print(f"\nArm aggregates:")
    for arm_key, agg in arm_aggregates.items():
        print(f"  {arm_key}:")
        print(f"    parent={agg['parent_effective_success']}/{agg['n']} ({agg['parent_eff_rate']:.3f})")
        print(f"    child={agg['child_effective_success']}/{agg['n']} ({agg['child_eff_rate']:.3f})")
        print(f"    improved={agg['improved']} degraded={agg['degraded']} same={agg['same']}")
        print(f"    path={agg['child_tool_path_rate']:.3f} fmt={agg['child_format_rate']:.3f}")
    print(f"\nArtifacts: {run_dir}")
    return results


if __name__ == "__main__":
    main()
