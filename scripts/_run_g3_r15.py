"""GLEPPO R15: C2 cross-task generalization + intervention cost.

H1: C2 maintains C1-level effective_success on new tasks
H2: C2 reduces unnecessary interventions
H3: C2 has real benefit vs C0

Tasks: B2-049 to B2-054 (6 new tasks)
Arms: C0, C1, C2
Budget: 150 model.generate, 300s wall
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from gleppo.genotype import make_task_compatible_reference
from gleppo.interpreter import Interpreter
from gleppo.llm import ProductionLLM, BudgetExceededError
from gleppo.operators import apply_operator
from gleppo.tasks import attach_checker
from gleppo.tool_path import verify_tool_path_for_task

PROTOCOL_ID = "GLEPPO-R15"
EXPECTED_BRANCH = "c7-g3-diag-v2-r1-fastpath"
EXPECTED_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
MAX_GENERATIONS = 150
MAX_WALL_S = 300

ALL_TASKS = ["B2-049", "B2-050", "B2-051", "B2-052", "B2-053", "B2-054"]
FORMAT_SENSITIVE = ["B2-049", "B2-050", "B2-052", "B2-054"]
FORMAT_INSENSITIVE = ["B2-051", "B2-053"]

VALIDATION_SEEDS = ["r15-val-seed-001"]
FINAL_SEEDS = ["r15-final-seed-001", "r15-final-seed-002", "r15-final-seed-003"]
ARMS = ["C0", "C1", "C2"]
FORMAT_CONSTRAINT = "Do NOT include tool outputs before 'Final answer:'."

TASK_FILES = ["data/diagnostic_B2_R15.jsonl"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def load_tasks() -> Dict[str, dict]:
    tasks = {}
    for fname in TASK_FILES:
        fpath = ROOT / fname
        if not fpath.exists():
            continue
        with open(fpath, encoding="utf-8") as f:
            for line in f:
                t = attach_checker(json.loads(line))
                if t["task_id"] in ALL_TASKS:
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
    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "_R15"
    run_dir = ROOT / "research" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    t_start = time.time()

    print(f"GLEPPO R15 run_id={run_id}")
    print(f"New tasks: {ALL_TASKS}")

    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    assert branch == EXPECTED_BRANCH

    frozen = {"protocol_id": PROTOCOL_ID, "run_id": run_id, "files": {}}
    for f in TASK_FILES + ["gleppo/genotype.py", "gleppo/interpreter.py", "gleppo/llm.py",
                           "gleppo/tasks.py", "gleppo/tool_path.py", "gleppo/operators.py", "scripts/_run_g3_r15.py"]:
        p = ROOT / f
        if p.exists():
            frozen["files"][f] = {"sha256": sha256_file(p), "size": p.stat().st_size}
    write_json(run_dir / "R15_FROZEN_MANIFEST.json", frozen)

    llm = ProductionLLM(device="cuda:0", max_new_tokens=256, temperature=0.7, max_generations=MAX_GENERATIONS)
    interp = Interpreter(llm=llm)
    print(f"Revision match: {llm.version == EXPECTED_REVISION}")

    tasks = load_tasks()
    print(f"Loaded {len(tasks)} tasks")

    candidates = []
    for task_id in ALL_TASKS:
        if task_id not in tasks:
            continue
        parent = make_task_compatible_reference(task_id)
        for arm_name in ARMS:
            for seed_id in FINAL_SEEDS:
                mate = make_task_compatible_reference(task_id)
                mate.system_prompt += " Alternative strategy."
                ctx = {"gen": 0, "mate": mate, "failure_category": "wrong_answer"}
                try:
                    child, ok, errs = apply_operator("crossover", parent, ctx)
                except Exception as e:
                    child, ok, errs = None, False, [str(e)]
                group = "FS" if task_id in FORMAT_SENSITIVE else "FI"
                candidates.append({
                    "task_id": task_id, "seed_id": seed_id,
                    "arm": arm_name, "group": group,
                    "parent": parent, "child": child, "child_valid": ok,
                })

    total_units = len(candidates)
    print(f"Units: {total_units}")

    results = {
        "run_id": run_id, "protocol": PROTOCOL_ID,
        "model_revision": llm.version, "revision_match": llm.version == EXPECTED_REVISION,
        "max_generations": MAX_GENERATIONS, "max_wall_s": MAX_WALL_S,
        "tasks": ALL_TASKS, "units": [],
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
        unit_key = f"{cand['group']}/{cand['task_id']}/{cand['seed_id']}/{cand['arm']}"

        try:
            parent_res = run_eval(parent, task, interp, llm, cand["seed_id"], "reference", "baseline")
        except BudgetExceededError:
            budget_exhausted = True
            break

        child_res = None
        c2_decision = None

        if cand["child_valid"] and child is not None:
            if cand["arm"] == "C0":
                try:
                    child_res = run_eval(child, task, interp, llm, cand["seed_id"], "child", "crossover")
                except BudgetExceededError:
                    budget_exhausted = True
                    break
            elif cand["arm"] == "C1":
                child_c1 = child.copy()
                child_c1.system_prompt += " " + FORMAT_CONSTRAINT
                try:
                    child_res = run_eval(child_c1, task, interp, llm, cand["seed_id"], "child", "crossover_format")
                except BudgetExceededError:
                    budget_exhausted = True
                    break
            elif cand["arm"] == "C2":
                try:
                    val_res = run_eval(child, task, interp, llm, VALIDATION_SEEDS[0], "validation", "crossover")
                except BudgetExceededError:
                    budget_exhausted = True
                    break
                if not val_res["format_compliant"]:
                    child_c1 = child.copy()
                    child_c1.system_prompt += " " + FORMAT_CONSTRAINT
                    c2_decision = {"action": "use_C1", "reason": "validation_format_failed", "val_fmt": False}
                    try:
                        child_res = run_eval(child_c1, task, interp, llm, cand["seed_id"], "child", "crossover_format")
                    except BudgetExceededError:
                        budget_exhausted = True
                        break
                else:
                    c2_decision = {"action": "use_C0", "reason": "validation_format_ok", "val_fmt": True}
                    try:
                        child_res = run_eval(child, task, interp, llm, cand["seed_id"], "child", "crossover")
                    except BudgetExceededError:
                        budget_exhausted = True
                        break

        results["units"].append({
            "unit_key": unit_key,
            "task_id": cand["task_id"], "seed_id": cand["seed_id"],
            "arm": cand["arm"], "group": cand["group"],
            "child_valid": cand["child_valid"],
            "parent_result": parent_res, "child_result": child_res,
            "c2_decision": c2_decision,
        })
        units_completed += 1
        if units_completed % 6 == 0:
            print(f"  [{units_completed}/{total_units}] {unit_key}")

    results["budget_exhausted"] = budget_exhausted
    results["units_completed"] = units_completed
    results["total_units"] = total_units

    for group_name in ["FS", "FI"]:
        for arm_name in ARMS:
            arm_units = [u for u in results["units"] if u["group"] == group_name and u["arm"] == arm_name]
            n = len(arm_units)
            if n == 0:
                continue
            child_eff = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["effective_success"])
            fmt_ok = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["format_compliant"])
            results.setdefault("group_aggregates", {})[f"{group_name}/{arm_name}"] = {
                "n": n, "child_eff": child_eff, "child_eff_rate": child_eff / n,
                "child_fmt_rate": fmt_ok / n,
            }

    c2_units = [u for u in results["units"] if u["arm"] == "C2" and u.get("c2_decision")]
    c2_use_c1 = sum(1 for u in c2_units if u["c2_decision"]["action"] == "use_C1")
    results["c2_analysis"] = {"total": len(c2_units), "use_C1": c2_use_c1, "use_C0": len(c2_units) - c2_use_c1}

    val_signals = []
    for u in results["units"]:
        if u["arm"] == "C2" and u.get("c2_decision"):
            val_fmt = u["c2_decision"].get("val_fmt")
            final_fmt = u["child_result"]["format_compliant"] if u["child_result"] else None
            val_signals.append({"task": u["task_id"], "val_fmt": val_fmt, "final_fmt": final_fmt})
    results["trigger_diagnostic"] = val_signals

    ledger = llm.get_generation_ledger()
    stats = llm.get_stats()
    results["llm_stats"] = stats
    results["total_actual_generations"] = len(ledger)
    results["total_wall_s"] = round(time.time() - t_start, 4)
    results["ledger_counter_match"] = len(ledger) == stats.get("actual_generations", -1)
    token_delta = sum(r["output_tokens"] for r in ledger)
    results["token_delta_sum"] = token_delta
    results["token_sum_match"] = token_delta == stats.get("total_tokens", -1)
    results["status"] = "INCONCLUSIVE" if budget_exhausted and units_completed < total_units else "COMPLETE"

    write_json(run_dir / "R15_RAW.json", results)
    with open(run_dir / "R15_LEDGER.jsonl", "w", encoding="utf-8") as f:
        for row in ledger:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    result_manifest = {
        "run_id": run_id, "status": results["status"],
        "frozen_manifest_sha256": sha256_file(run_dir / "R15_FROZEN_MANIFEST.json"),
        "raw_sha256": sha256_file(run_dir / "R15_RAW.json"),
        "ledger_sha256": sha256_file(run_dir / "R15_LEDGER.jsonl"),
    }
    write_json(run_dir / "R15_RESULT_MANIFEST.json", result_manifest)

    print(f"\n=== SUMMARY ===")
    print(f"Status: {results['status']}")
    print(f"Units: {units_completed}/{total_units}")
    print(f"Generations: {len(ledger)}/{MAX_GENERATIONS}")
    print(f"Wall: {results['total_wall_s']}s")
    for key, agg in results.get("group_aggregates", {}).items():
        print(f"  {key}: eff={agg['child_eff']}/{agg['n']} fmt={agg['child_fmt_rate']:.2f}")
    print(f"  C2: use_C1={c2_use_c1} use_C0={len(c2_units)-c2_use_c1}")
    print(f"Artifacts: {run_dir}")
    return results


if __name__ == "__main__":
    main()
