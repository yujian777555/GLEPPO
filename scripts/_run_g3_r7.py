"""R7: C1 format constraint paired validation.

Arms: C0 (original crossover), C1 (crossover + format constraint only)
Tasks: B2-012 to B2-017 (6 NEW tasks)
Seeds: 3 per task
Budget: 150 model.generate calls, 300s wall
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from gleppo.genotype import make_task_compatible_reference
from gleppo.interpreter import Interpreter
from gleppo.llm import ProductionLLM, BudgetExceededError
from gleppo.operators import apply_operator
from gleppo.tasks import attach_checker
from gleppo.tool_path import verify_tool_path_for_task

PROTOCOL_ID = "G3-DIAG-v2-R7"
EXPECTED_BRANCH = "c7-g3-diag-v2-r1-fastpath"
EXPECTED_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
MAX_GENERATIONS = 150
MAX_WALL_S = 300

TASK_IDS = ["B2-012", "B2-013", "B2-014", "B2-015", "B2-016", "B2-017"]
SEED_IDS = ["r7-paired-seed-001", "r7-paired-seed-002", "r7-paired-seed-003"]
ARMS = [("C0", "crossover"), ("C1", "crossover_format_only")]
TASK_FILE = "data/diagnostic_B2_R7.jsonl"


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
    with open(ROOT / TASK_FILE, encoding="utf-8") as f:
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
    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "_R7"
    run_dir = ROOT / "research" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    t_start = time.time()

    print(f"R7 run_id={run_id}")
    print(f"Arms: C0=crossover, C1=crossover_format_only")

    # Preflight
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert branch == EXPECTED_BRANCH

    # Frozen manifest
    frozen = {
        "protocol_id": PROTOCOL_ID, "run_id": run_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_head": head, "files": {},
    }
    for f in ["research/R7_PROTOCOL.md", TASK_FILE, "gleppo/operators.py",
              "gleppo/genotype.py", "gleppo/interpreter.py", "gleppo/llm.py",
              "gleppo/tasks.py", "gleppo/tool_path.py", "scripts/_run_g3_r7.py"]:
        p = ROOT / f
        if p.exists():
            frozen["files"][f] = {"sha256": sha256_file(p), "size": p.stat().st_size}
    write_json(run_dir / "R7_FROZEN_MANIFEST.json", frozen)

    # Load model
    llm = ProductionLLM(device="cuda:0", max_new_tokens=256, temperature=0.7, max_generations=MAX_GENERATIONS)
    interp = Interpreter(llm=llm)
    print(f"Revision match: {llm.version == EXPECTED_REVISION}")

    tasks = load_tasks()
    print(f"Loaded {len(tasks)} tasks: {sorted(tasks.keys())}")

    # Build candidates: 6 tasks x 3 seeds x 2 arms = 36 units
    candidates = []
    for task_id in TASK_IDS:
        if task_id not in tasks:
            continue
        parent = make_task_compatible_reference(task_id)
        for arm_name, op_name in ARMS:
            for seed_id in SEED_IDS:
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
                    "child_valid": ok,
                })

    total_units = len(candidates)
    print(f"Units: {total_units}, estimated generations: {total_units * 2 * 2}")

    # Execute
    results = {
        "run_id": run_id, "protocol": PROTOCOL_ID,
        "model_revision": llm.version, "revision_match": llm.version == EXPECTED_REVISION,
        "max_generations": MAX_GENERATIONS, "max_wall_s": MAX_WALL_S,
        "tasks": sorted(tasks.keys()), "seeds": SEED_IDS,
        "arms": [f"{a[0]}={a[1]}" for a in ARMS],
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
        unit_key = f"{cand['task_id']}/{cand['seed_id']}/{cand['arm']}"

        try:
            parent_res = run_eval(parent, task, interp, llm, cand["seed_id"], "reference", "baseline")
        except BudgetExceededError:
            budget_exhausted = True
            break

        child_res = None
        if cand["child_valid"] and child is not None:
            try:
                child_res = run_eval(child, task, interp, llm, cand["seed_id"], "child", cand["operator"])
            except BudgetExceededError:
                budget_exhausted = True
                break

        results["units"].append({
            "unit_key": unit_key,
            "task_id": cand["task_id"], "seed_id": cand["seed_id"],
            "arm": cand["arm"], "operator": cand["operator"],
            "child_valid": cand["child_valid"],
            "parent_result": parent_res, "child_result": child_res,
        })
        units_completed += 1
        if units_completed % 6 == 0:
            print(f"  [{units_completed}/{total_units}] {unit_key}")

    # Aggregate per arm
    results["budget_exhausted"] = budget_exhausted
    results["units_completed"] = units_completed
    results["total_units"] = total_units

    arm_aggs = {}
    for arm_name, _ in ARMS:
        arm_units = [u for u in results["units"] if u["arm"] == arm_name]
        n = len(arm_units)
        if n == 0:
            continue
        parent_eff = sum(1 for u in arm_units if u["parent_result"] and u["parent_result"]["effective_success"])
        child_eff = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["effective_success"])
        improved = sum(1 for u in arm_units if u["child_result"] and u["parent_result"]
                       and u["child_result"]["effective_success"] and not u["parent_result"]["effective_success"])
        degraded = sum(1 for u in arm_units if u["child_result"] and u["parent_result"]
                       and not u["child_result"]["effective_success"] and u["parent_result"]["effective_success"])
        fmt_ok = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["format_compliant"])
        path_ok = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["tool_path_valid"])
        answer_ok = sum(1 for u in arm_units if u["child_result"] and u["child_result"]["answer_correct"])
        arm_aggs[arm_name] = {
            "n": n, "parent_eff": parent_eff, "parent_eff_rate": parent_eff / n,
            "child_eff": child_eff, "child_eff_rate": child_eff / n,
            "improved": improved, "degraded": degraded, "same": n - improved - degraded,
            "child_fmt_rate": fmt_ok / n, "child_path_rate": path_ok / n,
            "child_answer_rate": answer_ok / n,
        }
    results["arm_aggregates"] = arm_aggs

    # Paired C1 vs C0
    c0_by_key = {f"{u['task_id']}/{u['seed_id']}": u for u in results["units"] if u["arm"] == "C0"}
    c1_by_key = {f"{u['task_id']}/{u['seed_id']}": u for u in results["units"] if u["arm"] == "C1"}
    common = set(c0_by_key.keys()) & set(c1_by_key.keys())
    c1_wins = sum(1 for k in common if c1_by_key[k]["child_result"] and c1_by_key[k]["child_result"]["effective_success"]
                  and not (c0_by_key[k]["child_result"] and c0_by_key[k]["child_result"]["effective_success"]))
    c0_wins = sum(1 for k in common if c0_by_key[k]["child_result"] and c0_by_key[k]["child_result"]["effective_success"]
                  and not (c1_by_key[k]["child_result"] and c1_by_key[k]["child_result"]["effective_success"]))
    results["paired_c1_vs_c0"] = {"c1_wins": c1_wins, "c0_wins": c0_wins, "ties": len(common) - c1_wins - c0_wins}

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

    results["status"] = "INCONCLUSIVE" if budget_exhausted and units_completed < total_units else "COMPLETE"

    # Save
    write_json(run_dir / "R7_RAW.json", results)
    with open(run_dir / "R7_LEDGER.jsonl", "w", encoding="utf-8") as f:
        for row in ledger:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    result_manifest = {
        "run_id": run_id, "status": results["status"],
        "frozen_manifest_sha256": sha256_file(run_dir / "R7_FROZEN_MANIFEST.json"),
        "raw_sha256": sha256_file(run_dir / "R7_RAW.json"),
        "ledger_sha256": sha256_file(run_dir / "R7_LEDGER.jsonl"),
    }
    write_json(run_dir / "R7_RESULT_MANIFEST.json", result_manifest)

    print(f"\n=== SUMMARY ===")
    print(f"Status: {results['status']}")
    print(f"Units: {units_completed}/{total_units}")
    print(f"Generations: {len(ledger)}/{MAX_GENERATIONS}")
    print(f"Wall: {results['total_wall_s']}s")
    for arm, agg in arm_aggs.items():
        print(f"  {arm}: parent={agg['parent_eff']}/{agg['n']} child={agg['child_eff']}/{agg['n']} "
              f"fmt={agg['child_fmt_rate']:.2f} path={agg['child_path_rate']:.2f}")
    print(f"  Paired C1 vs C0: c1_wins={c1_wins} c0_wins={c0_wins}")
    print(f"Artifacts: {run_dir}")
    return results


if __name__ == "__main__":
    main()
