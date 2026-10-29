"""R4: Selection mechanism generalization experiment.

Hard cap: 150 actual model.generate calls, 300s wall clock.
5 tasks x 5 seeds x 3 strategies = 75 units.
Each unit: 1 parent + 1 child = 2 evaluations.
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
from gleppo.r4_selection import run_selection_mechanisms, static_check_s1
from gleppo.tasks import attach_checker
from gleppo.tool_path import verify_tool_path_for_task

PROTOCOL_ID = "G3-DIAG-v2-R4"
EXPECTED_BRANCH = "c7-g3-diag-v2-r1-fastpath"
EXPECTED_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
SEED_IDS = [f"r4-paired-seed-{i:03d}" for i in range(1, 6)]
MAX_GENERATIONS = 150
MAX_WALL_S = 300
TASK_IDS = ["B2-001", "B2-003", "B2-004", "B2-005", "B2-006"]
OPERATORS = ["tool_subset_edit", "crossover"]
FROZEN_FILES = [
    "research/R4_PROTOCOL.md",
    "data/diagnostic_B2.jsonl",
    "data/diagnostic_B2_R4.jsonl",
    "gleppo/r4_selection.py",
    "gleppo/tool_path.py",
    "gleppo/genotype.py",
    "gleppo/interpreter.py",
    "gleppo/llm.py",
    "gleppo/operators.py",
    "gleppo/tasks.py",
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
    tasks = {}
    for fname in ["data/diagnostic_B2.jsonl", "data/diagnostic_B2_R4.jsonl"]:
        with open(ROOT / fname, encoding="utf-8") as f:
            for line in f:
                t = attach_checker(json.loads(line))
                if t["task_id"] in TASK_IDS:
                    tasks[t["task_id"]] = t
    return tasks


def make_reference_for_task(task_id: str):
    return make_task_compatible_reference(task_id)


def run_eval(g, task, interp, llm, seed_id, role, operator):
    """Run one evaluation, return metrics dict."""
    seed = (PROTOCOL_ID, task["task_id"], seed_id, 0, 0)
    prov = {
        "task_id": task["task_id"],
        "operator": operator,
        "genotype_role": role,
        "replicate": 0,
        "turn": 0,
    }
    res = interp.run(g, task, seed_parts=seed, provenance=prov)
    tp = verify_tool_path_for_task(task["task_id"], res.trace, task.get("required_tools", []))

    # Extract final answer for gold check
    answer = res.answer
    answer_correct = bool(task.get("gold_check") and task["gold_check"](answer, g))

    # Format compliance
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
        "success": res.success,
        "failure": res.failure_category,
        "turns": res.turns,
        "tool_calls": res.tool_calls,
        "answer_preview": answer[:150],
        "tool_path_details": tp,
        "trace_summary": [
            {"type": e.get("type"), "ok": e.get("ok"), "detail": e.get("detail", ""), "output": str(e.get("output", ""))[:80]}
            for e in res.trace
        ],
    }


def main():
    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "_R4"
    run_dir = ROOT / "research" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    t_start = time.time()
    print(f"R4 run_id={run_id}")
    print(f"Hard cap: {MAX_GENERATIONS} generations, {MAX_WALL_S}s wall")

    # Preflight
    branch = git(["branch", "--show-current"])
    head = git(["rev-parse", "HEAD"])
    assert branch == EXPECTED_BRANCH, f"wrong branch: {branch}"

    # Frozen manifest BEFORE model load
    frozen = {
        "protocol_id": PROTOCOL_ID,
        "run_id": run_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_head": head,
        "files": {},
    }
    for f in FROZEN_FILES:
        p = ROOT / f
        if p.exists():
            frozen["files"][f] = {"sha256": sha256_file(p), "size": p.stat().st_size}
        else:
            frozen["files"][f] = {"sha256": None, "size": 0, "missing": True}
    write_json(run_dir / "R4_FROZEN_MANIFEST.json", frozen)
    print(f"Frozen manifest written: {len(frozen['files'])} files")

    # Load model
    llm = ProductionLLM(
        device="cuda:0", max_new_tokens=256, temperature=0.7,
        max_generations=MAX_GENERATIONS,
    )
    interp = Interpreter(llm=llm)
    rev_match = llm.version == EXPECTED_REVISION
    print(f"Revision match: {rev_match} ({llm.version[:16]}...)")

    tasks = load_tasks()
    print(f"Loaded {len(tasks)} tasks: {sorted(tasks.keys())}")

    # Build candidate pairs
    candidates = []
    for task_id in TASK_IDS:
        if task_id not in tasks:
            print(f"WARNING: task {task_id} not found!")
            continue
        parent = make_reference_for_task(task_id)
        for seed_id in SEED_IDS:
            for op_name in OPERATORS:
                mate = make_reference_for_task(task_id)
                mate.system_prompt += " Alternative strategy: compute intermediates first."
                ctx = {"gen": 0, "mate": mate, "failure_category": "wrong_answer"}
                try:
                    child, ok, errs = apply_operator(op_name, parent, ctx)
                except Exception as e:
                    child, ok, errs = None, False, [str(e)]
                candidates.append({
                    "task_id": task_id,
                    "seed_id": seed_id,
                    "operator": op_name,
                    "parent": parent,
                    "child": child,
                    "child_valid": ok,
                    "child_errors": errs if not ok else [],
                })

    total_units = len(candidates)
    estimated_generations = total_units * 2 * 2  # 2 evals per unit, ~2 gens per eval
    print(f"Candidate units: {total_units}")
    print(f"Estimated generations: {estimated_generations}")

    if estimated_generations > MAX_GENERATIONS:
        print(f"WARNING: estimated {estimated_generations} > cap {MAX_GENERATIONS}")
        print("Will mark INCONCLUSIVE if budget exhausted before matrix completes")

    # Execute
    results = {
        "run_id": run_id,
        "protocol": PROTOCOL_ID,
        "model_revision": llm.version,
        "revision_match": rev_match,
        "max_generations": MAX_GENERATIONS,
        "max_wall_s": MAX_WALL_S,
        "tasks": sorted(tasks.keys()),
        "seeds": SEED_IDS,
        "operators": OPERATORS,
        "units": [],
        "selection_results": {},
    }

    budget_exhausted = False
    units_completed = 0

    for cand in candidates:
        if budget_exhausted:
            break
        if llm._call_id >= MAX_GENERATIONS or (time.time() - t_start) > MAX_WALL_S:
            budget_exhausted = True
            break

        task = tasks[cand["task_id"]]
        parent = cand["parent"]
        child = cand["child"]
        unit_key = f"{cand['task_id']}/{cand['seed_id']}/{cand['operator']}"

        # Static check first (zero cost)
        s1_result = static_check_s1(child, cand["task_id"]) if child else {"pass": False, "violations": ["no_child"]}

        # Run parent
        try:
            parent_res = run_eval(parent, task, interp, llm, cand["seed_id"], "reference", "baseline")
        except BudgetExceededError:
            budget_exhausted = True
            break

        # Run child (if valid)
        child_res = None
        if cand["child_valid"] and child is not None:
            try:
                child_res = run_eval(child, task, interp, llm, cand["seed_id"], "child", cand["operator"])
            except BudgetExceededError:
                budget_exhausted = True
                break

        # Selection mechanisms
        selection = run_selection_mechanisms(parent, child, cand["task_id"], parent_res, child_res)

        unit_record = {
            "unit_key": unit_key,
            "task_id": cand["task_id"],
            "seed_id": cand["seed_id"],
            "operator": cand["operator"],
            "child_valid": cand["child_valid"],
            "child_errors": cand["child_errors"],
            "parent_result": parent_res,
            "child_result": child_res,
            "selection": selection,
            "s1_static_pass": s1_result.get("pass", False),
        }
        results["units"].append(unit_record)
        units_completed += 1

        if units_completed % 5 == 0:
            print(f"  [{units_completed}/{total_units}] {unit_key}")

    # Aggregate
    results["budget_exhausted"] = budget_exhausted
    results["units_completed"] = units_completed
    results["total_units"] = total_units

    # Compute aggregates per mechanism
    for mech in ["S0_unfiltered", "S1_static_filter", "S2_static_select", "S3_post_exec_diag"]:
        accepted = 0
        total = 0
        harmful = 0
        effective_success = 0
        for u in results["units"]:
            total += 1
            sel = u["selection"].get(mech, {})
            is_accepted = False
            if mech == "S0_unfiltered":
                is_accepted = sel.get("accepted", False)
            elif mech == "S1_static_filter":
                is_accepted = sel.get("pass", False)
            elif mech == "S2_static_select":
                is_accepted = sel.get("accepted", False)
            elif mech == "S3_post_exec_diag":
                is_accepted = sel.get("pass", False)

            if is_accepted:
                accepted += 1
                cr = u.get("child_result") or {}
                if not cr.get("effective_success", False):
                    harmful += 1
                else:
                    effective_success += 1

        results["selection_results"][mech] = {
            "total_candidates": total,
            "accepted": accepted,
            "rejected": total - accepted,
            "acceptance_rate": accepted / total if total > 0 else 0,
            "harmful_accepted": harmful,
            "harmful_rate": harmful / accepted if accepted > 0 else 0,
            "effective_success_among_accepted": effective_success,
        }

    # Parent/child effective success rates
    parent_eff = sum(1 for u in results["units"] if u["parent_result"] and u["parent_result"]["effective_success"])
    child_eff = sum(1 for u in results["units"] if u["child_result"] and u["child_result"]["effective_success"])
    results["parent_effective_success_rate"] = parent_eff / len(results["units"]) if results["units"] else 0
    results["child_effective_success_rate"] = child_eff / len(results["units"]) if results["units"] else 0

    # Paired outcomes
    improved = sum(1 for u in results["units"]
                   if u["child_result"] and u["parent_result"]
                   and u["child_result"]["effective_success"] and not u["parent_result"]["effective_success"])
    degraded = sum(1 for u in results["units"]
                   if u["child_result"] and u["parent_result"]
                   and not u["child_result"]["effective_success"] and u["parent_result"]["effective_success"])
    same = sum(1 for u in results["units"]
               if u["child_result"] and u["parent_result"]
               and u["child_result"]["effective_success"] == u["parent_result"]["effective_success"])
    results["paired_outcomes"] = {"improved": improved, "degraded": degraded, "same": same}

    # Finalize accounting
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
    elif results["paired_outcomes"]["degraded"] > results["paired_outcomes"]["improved"]:
        results["status"] = "PILOT_COMPLETE_NEGATIVE_TREND"
    else:
        results["status"] = "PILOT_COMPLETE_REQUIRES_INDEPENDENT_REVIEW"

    # Save artifacts
    write_json(run_dir / "R4_RAW.json", results)

    with open(run_dir / "R4_LEDGER.jsonl", "w", encoding="utf-8") as f:
        for row in ledger:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # Result manifest
    result_manifest = {
        "run_id": run_id,
        "status": results["status"],
        "frozen_manifest_sha256": sha256_file(run_dir / "R4_FROZEN_MANIFEST.json"),
        "raw_sha256": sha256_file(run_dir / "R4_RAW.json"),
        "ledger_sha256": sha256_file(run_dir / "R4_LEDGER.jsonl"),
    }
    write_json(run_dir / "R4_RESULT_MANIFEST.json", result_manifest)

    # Print summary
    print(f"\n=== SUMMARY ===")
    print(f"Status: {results['status']}")
    print(f"Units: {units_completed}/{total_units}")
    print(f"Generations: {len(ledger)}/{MAX_GENERATIONS}")
    print(f"Wall: {results['total_wall_s']}s/{MAX_WALL_S}s")
    print(f"Budget exhausted: {budget_exhausted}")
    print(f"Parent effective_success: {results['parent_effective_success_rate']:.3f}")
    print(f"Child effective_success: {results['child_effective_success_rate']:.3f}")
    print(f"Paired: improved={improved} degraded={degraded} same={same}")
    print(f"\nSelection mechanisms:")
    for mech, r in results["selection_results"].items():
        print(f"  {mech}: accepted={r['accepted']}/{r['total_candidates']} harmful={r['harmful_accepted']}")
    print(f"\nArtifacts: {run_dir}")
    print(f"Result manifest SHA-256: {result_manifest['raw_sha256'][:16]}")

    return results


if __name__ == "__main__":
    main()
