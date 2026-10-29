"""G3-DIAG-v2-R3 gated canary and paired performance-validity pilot."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from gleppo.genotype import make_task_compatible_reference, behavior_hash, validate_genotype
from gleppo.interpreter import Interpreter
from gleppo.llm import ProductionLLM, BudgetExceededError
from gleppo.operators import apply_operator
from gleppo.r3_metrics import evaluate_r3_metrics
from gleppo.tasks import attach_checker
from gleppo.tool_path import B2_TOOL_PATH_CONTRACTS

PROTOCOL_ID = "G3-DIAG-v2-R3"
EXPECTED_BRANCH = "c7-g3-diag-v2-r1-fastpath"
EXPECTED_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
SEED_IDS = ["r3-paired-seed-001", "r3-paired-seed-002", "r3-paired-seed-003"]
MAX_GENERATIONS = 100
MAX_WALL_S = 300
PILOT_TASK_IDS = ["B2-001", "B2-003", "B2-004"]
OPERATORS = ["tool_subset_edit", "crossover"]
FROZEN_FILES = [
    "research/G3_DIAG_R3_PROTOCOL.md",
    "data/diagnostic_B2.jsonl",
    "data/diagnostic_B2_R3.jsonl",
    "scripts/_run_g3_r3.py",
    "scripts/verify_g3_r3.py",
    "gleppo/r3_metrics.py",
    "gleppo/tool_path.py",
    "gleppo/genotype.py",
    "gleppo/interpreter.py",
    "gleppo/llm.py",
    "gleppo/operators.py",
    "gleppo/tasks.py",
    "tests/test_r3_protocol.py",
    ".github/workflows/r3-offline-validation.yml",
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


def preflight_git() -> Dict[str, str]:
    branch = git(["branch", "--show-current"])
    head = git(["rev-parse", "HEAD"])
    dirty = git(["status", "--porcelain", "--untracked-files=no"])
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"wrong branch: expected {EXPECTED_BRANCH}, got {branch!r}")
    if dirty:
        raise RuntimeError("tracked working tree is dirty; commit/revert source changes first: " + dirty)
    return {"branch": branch, "head": head, "tracked_worktree_clean": "true"}


def load_tasks() -> Dict[str, dict]:
    tasks: Dict[str, dict] = {}
    with (ROOT / "data" / "diagnostic_B2.jsonl").open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                task = attach_checker(json.loads(line))
                if task["task_id"] in {"B2-001", "B2-003"}:
                    tasks[task["task_id"]] = task

    with (ROOT / "data" / "diagnostic_B2_R3.jsonl").open(encoding="utf-8") as f:
        r3_rows = [json.loads(line) for line in f if line.strip()]
    if len(r3_rows) != 1:
        raise RuntimeError(f"R3 task file must contain exactly one task, got {len(r3_rows)}")
    task = attach_checker(r3_rows[0])
    if task["task_id"] != "B2-004" or task["gold"] != "41":
        raise RuntimeError("B2-004 identity/gold mismatch")
    if "Final answer: 41" in task["input"]:
        raise RuntimeError("gold answer leaked directly into model-facing task input")
    if task["required_tools"] != ["py_sandbox", "calc"]:
        raise RuntimeError("B2-004 required tool list mismatch")
    if B2_TOOL_PATH_CONTRACTS.get("B2-004") != [("py_sandbox", "32"), ("calc", "41")]:
        raise RuntimeError("B2-004 frozen tool-path contract mismatch")
    tasks["B2-004"] = task
    if set(tasks) != set(PILOT_TASK_IDS):
        raise RuntimeError(f"unexpected R3 task set: {sorted(tasks)}")

    for task_id in PILOT_TASK_IDS:
        genotype = make_task_compatible_reference(task_id)
        errors = validate_genotype(genotype)
        if errors:
            raise RuntimeError(f"invalid reference genotype {task_id}: {errors}")
        tool_steps = [s.tool for s in genotype.workflow if s.type == "tool"]
        if tool_steps != tasks[task_id]["required_tools"]:
            raise RuntimeError(f"reference workflow mismatch for {task_id}: {tool_steps}")
    return tasks


def freeze_manifest(run_dir: Path, git_info: Dict[str, str]) -> Dict[str, Any]:
    entries: Dict[str, Dict[str, Any]] = {}
    for rel in FROZEN_FILES:
        path = ROOT / rel
        if not path.is_file():
            raise RuntimeError(f"required frozen file missing: {rel}")
        entries[rel] = {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
    manifest = {
        "protocol": PROTOCOL_ID,
        "run_id": run_dir.name,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git": git_info,
        "model": {"name": "qwen2.5-7b-instruct", "expected_revision": EXPECTED_REVISION},
        "seed_ids": list(SEED_IDS),
        "budget": {"max_actual_generations": MAX_GENERATIONS, "max_wall_clock_seconds_including_model_load": MAX_WALL_S},
        "metrics": {
            "answer_correct": "gold checker independent of format/path",
            "format_compliant": "exact prefix, nonempty value <=100 characters, one line",
            "tool_path_valid": "ordered required tools with exact outputs",
            "hard_validity": "format_compliant AND tool_path_valid",
            "effective_success": "answer_correct AND hard_validity",
            "behavior_changed": "diagnostic only",
        },
        "files": entries,
    }
    write_json(run_dir / "R3_FROZEN_MANIFEST.json", manifest)
    return manifest


def seed_parts(task_id: str, seed_id: str) -> tuple:
    # No genotype/operator identity enters the paired seed.
    return (f"{PROTOCOL_ID}|{task_id}|{seed_id}", task_id, seed_id, 0, 0)


def ensure_budget(llm: ProductionLLM, started: float) -> None:
    if llm._call_id >= MAX_GENERATIONS:
        raise BudgetExceededError(f"R3 generation cap reached: {llm._call_id}/{MAX_GENERATIONS}")
    if time.monotonic() - started >= MAX_WALL_S:
        raise BudgetExceededError(f"R3 wall-clock deadline reached: {MAX_WALL_S}s")


def run_episode(genotype, task: dict, seed_id: str, seed_index: int,
                interp: Interpreter, llm: ProductionLLM, started: float,
                role: str, operator: str) -> Dict[str, Any]:
    ensure_budget(llm, started)
    provenance = {
        "task_id": task["task_id"], "operator": operator,
        "genotype_role": role, "replicate": seed_index,
        "seed_id": seed_id, "turn": 0,
    }
    result = interp.run(genotype, task, seed_parts=seed_parts(task["task_id"], seed_id), provenance=provenance)
    metrics = evaluate_r3_metrics(result.answer, task, genotype, result.trace)
    return {
        "task_id": task["task_id"], "seed_id": seed_id, "seed_index": seed_index,
        "role": role, "operator": operator, "genotype_hash": behavior_hash(genotype),
        "answer": result.answer, "failure_category": result.failure_category,
        "interpreter_success": bool(result.success), "turns": result.turns,
        "tool_calls": result.tool_calls, **metrics, "trace": result.trace,
    }


def behavior_changed(parent: Dict[str, Any], child: Dict[str, Any]) -> bool:
    keys = ("answer_correct", "format_compliant", "tool_path_valid", "hard_validity",
            "effective_success", "failure_category", "turns", "tool_calls", "answer")
    if any(parent.get(k) != child.get(k) for k in keys):
        return True
    def events(ep):
        return [(e.get("type"), e.get("ok"), e.get("detail"), e.get("output"))
                for e in ep.get("trace", []) if e.get("type") != "meta"]
    return events(parent) != events(child)


def accounting(llm: ProductionLLM) -> Dict[str, Any]:
    ledger = llm.get_generation_ledger()
    stats = llm.get_stats()
    ids = [row.get("call_id") for row in ledger]
    token_delta_sum = sum(int(row.get("output_tokens", 0)) for row in ledger)
    failures_ledger = sum(1 for row in ledger if row.get("status") != "ok")
    unique_ids = len(ids) == len(set(ids))
    monotonic_ids = ids == list(range(1, len(ids) + 1))
    count_match = len(ledger) == stats.get("actual_generations", -1) == llm._call_id
    token_match = token_delta_sum == stats.get("total_tokens", -1)
    failure_match = failures_ledger == stats.get("failures", -1)
    return {
        "ledger_rows": len(ledger), "actual_generations": stats.get("actual_generations", -1),
        "reserved_call_count": llm._call_id, "unique_call_ids": unique_ids,
        "monotonic_call_ids": monotonic_ids, "generation_count_match": count_match,
        "token_delta_sum": token_delta_sum, "runtime_total_tokens": stats.get("total_tokens", -1),
        "token_sum_match": token_match, "ledger_generation_failures": failures_ledger,
        "runtime_generation_failures": stats.get("failures", -1), "failure_ledger_match": failure_match,
        "model_revision": stats.get("revision"),
        "accounting_ok": bool(unique_ids and monotonic_ids and count_match and token_match and failure_match),
        "stats": stats,
    }


def episode_summary(ep: Dict[str, Any]) -> Dict[str, Any]:
    keys = ("task_id", "seed_id", "role", "operator", "genotype_hash", "answer",
            "failure_category", "interpreter_success", "answer_correct", "format_compliant",
            "tool_path_valid", "hard_validity", "effective_success", "turns", "tool_calls",
            "tool_path_details")
    return {key: ep.get(key) for key in keys}


def aggregate_pilot(pilot: Dict[str, Any]) -> Dict[str, Any]:
    aggregate: Dict[str, Any] = {}
    for op in OPERATORS:
        rows = []
        for task_id in PILOT_TASK_IDS:
            for seed_id in SEED_IDS:
                pair = pilot.get("pairs", {}).get(task_id, {}).get(seed_id)
                if not pair or not pair.get("parent"):
                    continue
                child_row = pair.get("children", {}).get(op, {})
                if not child_row or not child_row.get("attempted"):
                    continue
                parent = pair["parent"]
                child = child_row.get("episode")
                child_valid = bool(child_row.get("operator_valid")) and bool(child)
                child_correct = bool(child.get("answer_correct")) if child_valid else False
                child_hard = bool(child.get("hard_validity")) if child_valid else False
                child_path = bool(child.get("tool_path_valid")) if child_valid else False
                child_format = bool(child.get("format_compliant")) if child_valid else False
                child_effective = bool(child.get("effective_success")) if child_valid else False
                rows.append({
                    "task_id": task_id, "seed_id": seed_id,
                    "operator_valid": child_valid,
                    "parent_answer_correct": bool(parent["answer_correct"]),
                    "child_answer_correct": child_correct,
                    "paired_correctness_delta": int(child_correct) - int(bool(parent["answer_correct"])),
                    "parent_hard_validity": bool(parent["hard_validity"]),
                    "child_hard_validity": child_hard,
                    "parent_tool_path_valid": bool(parent["tool_path_valid"]),
                    "child_tool_path_valid": child_path,
                    "parent_format_compliant": bool(parent["format_compliant"]),
                    "child_format_compliant": child_format,
                    "parent_effective_success": bool(parent["effective_success"]),
                    "child_effective_success": child_effective,
                    "behavior_changed": bool(child_row.get("behavior_changed")) if child_valid else False,
                })
        n = len(rows)
        if not n:
            aggregate[op] = {"paired_comparisons": 0, "paired_rows": []}
            continue
        aggregate[op] = {
            "paired_comparisons": n,
            "operator_invalid_count": sum(not r["operator_valid"] for r in rows),
            "parent_answer_correct_rate": sum(r["parent_answer_correct"] for r in rows) / n,
            "child_answer_correct_rate": sum(r["child_answer_correct"] for r in rows) / n,
            "parent_hard_validity_rate": sum(r["parent_hard_validity"] for r in rows) / n,
            "child_hard_validity_rate": sum(r["child_hard_validity"] for r in rows) / n,
            "parent_tool_path_rate": sum(r["parent_tool_path_valid"] for r in rows) / n,
            "child_tool_path_rate": sum(r["child_tool_path_valid"] for r in rows) / n,
            "parent_format_failure_count": sum(not r["parent_format_compliant"] for r in rows),
            "child_format_failure_count": sum(r["operator_valid"] and not r["child_format_compliant"] for r in rows),
            "parent_effective_success_rate": sum(r["parent_effective_success"] for r in rows) / n,
            "child_effective_success_rate": sum(r["child_effective_success"] for r in rows) / n,
            "mean_paired_correctness_delta": sum(r["paired_correctness_delta"] for r in rows) / n,
            "behavior_changed_count_diagnostic_only": sum(r["behavior_changed"] for r in rows),
            "paired_rows": rows,
        }
    return aggregate


def make_report(results: Dict[str, Any]) -> str:
    canary = results.get("canary", {})
    gate = canary.get("gate", {})
    lines = [
        "# G3-DIAG-v2-R3 Run Report", "",
        f"- Run ID: {results.get('run_id')}",
        f"- Status: {results.get('status')}",
        f"- Model revision: {results.get('model_revision')}",
        f"- Revision match: {results.get('revision_match')}",
        f"- Actual generations: {results.get('total_actual_generations', 0)} / {MAX_GENERATIONS}",
        f"- Wall clock: {results.get('total_wall_s', 0):.3f}s / {MAX_WALL_S}s", "",
        "## Canary gate", "",
        f"- Completed: {gate.get('completed_episodes', 0)}/3",
        f"- Tool path: {gate.get('tool_path_pass_count', 0)}/3",
        f"- Answer correct: {gate.get('answer_correct_count', 0)}/3",
        f"- Format compliant: {gate.get('format_compliant_count', 0)}/3",
        f"- Accounting valid: {gate.get('accounting_ok')}",
        f"- Canary passed: {gate.get('passed')}", "",
    ]
    pilot = results.get("pilot", {})
    if pilot.get("matrix_complete"):
        lines.extend(["## Paired pilot aggregate", ""])
        for op, data in pilot.get("aggregate", {}).items():
            lines.extend([
                f"### {op}", "",
                f"- Paired comparisons: {data.get('paired_comparisons', 0)}",
                f"- Invalid operator outcomes (counted as failures): {data.get('operator_invalid_count', 0)}",
                f"- Parent/child answer-correct rate: {data.get('parent_answer_correct_rate')} / {data.get('child_answer_correct_rate')}",
                f"- Parent/child tool-path rate: {data.get('parent_tool_path_rate')} / {data.get('child_tool_path_rate')}",
                f"- Parent/child hard-validity rate: {data.get('parent_hard_validity_rate')} / {data.get('child_hard_validity_rate')}",
                f"- Parent/child format failures: {data.get('parent_format_failure_count')} / {data.get('child_format_failure_count')}",
                f"- Mean paired correctness delta: {data.get('mean_paired_correctness_delta')}",
                f"- Behavior changes (diagnostic only): {data.get('behavior_changed_count_diagnostic_only')}", "",
            ])
    else:
        lines.extend(["## Paired pilot", "",
                      f"- Matrix complete: {pilot.get('matrix_complete', False)}",
                      f"- Stop reason: {pilot.get('stop_reason', 'not entered')}", ""])
    lines.extend([
        "## Interpretation boundary", "",
        "- Behavior change is diagnostic only and is not evidence of performance improvement.",
        "- A child violating the required tool path is not an effective success even if its answer matches gold.",
        "- Formal G3 remains FAIL. PC1, controller training, and Family C access remain not authorized/not run.", "",
    ])
    if results.get("fatal_error"):
        lines.extend(["## Error", "", str(results["fatal_error"]), ""])
    return "\n".join(lines)


def main() -> int:
    started = time.monotonic()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_R3"
    run_dir = ROOT / "research" / "runs" / run_id
    llm: Optional[ProductionLLM] = None
    results: Dict[str, Any] = {
        "protocol": PROTOCOL_ID, "run_id": run_id, "status": "PREFLIGHT",
        "formal_g3": "FAIL_UNCHANGED", "pc1_approved": False, "pc1_executed": False,
        "family_c_access": False, "controller_training": "NOT_AUTHORIZED",
        "canary": {"episodes": [], "gate": {"passed": False}},
        "pilot": {"matrix_complete": False, "pairs": {}, "stop_reason": "not entered"},
    }
    run_dir.mkdir(parents=True, exist_ok=False)
    try:
        git_info = preflight_git()
        tasks = load_tasks()
        freeze_manifest(run_dir, git_info)
        results["git"] = git_info
        results["frozen_manifest_sha256"] = sha256_file(run_dir / "R3_FROZEN_MANIFEST.json")
        print(f"R3 run_id={run_id}; branch={git_info['branch']}; head={git_info['head']}")
        print("Frozen source/task manifest written before model loading and model.generate.")

        if time.monotonic() - started >= MAX_WALL_S:
            raise BudgetExceededError("wall-clock cap reached before model load")
        llm = ProductionLLM(device="cuda:0", max_new_tokens=256, temperature=0.7,
                            max_generations=MAX_GENERATIONS)
        original_reply = llm.reply

        def guarded_reply(*args, **kwargs):
            if time.monotonic() - started >= MAX_WALL_S:
                raise BudgetExceededError(f"wall-clock deadline reached before model.generate ({MAX_WALL_S}s)")
            return original_reply(*args, **kwargs)

        llm.reply = guarded_reply
        interp = Interpreter(llm=llm)
        model_path = str(getattr(llm, "model_path", ""))
        config = getattr(getattr(llm, "model", None), "config", None)
        config_revision = getattr(config, "_commit_hash", None)
        revision_match = (
            llm.version == EXPECTED_REVISION
            and EXPECTED_REVISION in model_path
            and (config_revision is None or config_revision == EXPECTED_REVISION)
        )
        results["model_revision"] = llm.version
        results["model_path"] = model_path
        results["model_config_revision"] = config_revision
        results["revision_match"] = revision_match

        if not revision_match:
            results["status"] = "CANARY_FAIL_STOP"
            results["canary"]["gate"] = {
                "completed_episodes": 0, "tool_path_pass_count": 0,
                "answer_correct_count": 0, "format_compliant_count": 0,
                "accounting_ok": False, "passed": False, "reason": "model revision mismatch",
            }
            results["pilot"]["stop_reason"] = "revision mismatch; no model calls made"
        else:
            canary_refs: Dict[str, Dict[str, Any]] = {}
            for seed_index, seed_id in enumerate(SEED_IDS):
                try:
                    ep = run_episode(
                        make_task_compatible_reference("B2-004"), tasks["B2-004"], seed_id,
                        seed_index, interp, llm, started, "reference", "canary_reference",
                    )
                    results["canary"]["episodes"].append(ep)
                    canary_refs[seed_id] = ep
                    print(f"canary {seed_id}: path={ep['tool_path_valid']} answer={ep['answer_correct']} format={ep['format_compliant']}")
                except BudgetExceededError as exc:
                    results["canary"]["stop_reason"] = str(exc)
                    break

            canary_eps = results["canary"]["episodes"]
            canary_accounting = accounting(llm)
            path_count = sum(bool(ep["tool_path_valid"]) for ep in canary_eps)
            correct_count = sum(bool(ep["answer_correct"]) for ep in canary_eps)
            canary_complete = len(canary_eps) == len(SEED_IDS)
            canary_pass = bool(
                canary_complete and path_count == 3 and correct_count >= 2
                and canary_accounting["accounting_ok"] and revision_match
                and llm._call_id <= MAX_GENERATIONS and time.monotonic() - started <= MAX_WALL_S
            )
            results["canary"]["gate"] = {
                "completed_episodes": len(canary_eps), "tool_path_pass_count": path_count,
                "answer_correct_count": correct_count,
                "format_compliant_count": sum(bool(ep["format_compliant"]) for ep in canary_eps),
                "accounting_ok": canary_accounting["accounting_ok"],
                "accounting_snapshot": canary_accounting, "passed": canary_pass,
                "reason": "all frozen canary gates passed" if canary_pass else "one or more frozen canary gates failed",
            }
            results["canary"]["reference_by_seed"] = {seed: episode_summary(ep) for seed, ep in canary_refs.items()}

            if not canary_pass:
                results["status"] = "CANARY_FAIL_STOP"
                results["pilot"]["stop_reason"] = "canary gate failed; paired pilot not run"
                print("STOP: canary failed; operator comparison not run.")
            else:
                results["status"] = "PILOT_RUNNING"
                pairs: Dict[str, Dict[str, Any]] = {task_id: {} for task_id in PILOT_TASK_IDS}
                stop_reason = ""
                matrix_complete = True
                for task_id in PILOT_TASK_IDS:
                    for seed_index, seed_id in enumerate(SEED_IDS):
                        try:
                            parent_g = make_task_compatible_reference(task_id)
                            if task_id == "B2-004":
                                parent_ep = canary_refs[seed_id]
                            else:
                                parent_ep = run_episode(parent_g, tasks[task_id], seed_id, seed_index,
                                                        interp, llm, started, "reference", "paired_reference")
                            row: Dict[str, Any] = {"parent": parent_ep, "children": {}}
                            pairs[task_id][seed_id] = row

                            for op_name in OPERATORS:
                                ensure_budget(llm, started)
                                mate = make_task_compatible_reference(task_id)
                                mate.system_prompt += " Alternative strategy: compute intermediate values explicitly."
                                try:
                                    child_g, op_ok, op_errors = apply_operator(
                                        op_name, parent_g,
                                        {"gen": 0, "mate": mate, "failure_category": "wrong_answer"},
                                    )
                                except Exception as exc:
                                    row["children"][op_name] = {
                                        "attempted": True, "operator_valid": False,
                                        "errors": [f"{type(exc).__name__}: {exc}"],
                                        "episode": None, "behavior_changed": False,
                                    }
                                    continue
                                genotype_errors = validate_genotype(child_g) if op_ok else list(op_errors or [])
                                if not op_ok or genotype_errors:
                                    row["children"][op_name] = {
                                        "attempted": True, "operator_valid": False,
                                        "errors": list(op_errors or []) + list(genotype_errors or []),
                                        "episode": None, "behavior_changed": False,
                                    }
                                    continue
                                child_ep = run_episode(child_g, tasks[task_id], seed_id, seed_index,
                                                       interp, llm, started, "child", op_name)
                                changed = behavior_changed(parent_ep, child_ep)
                                child_ep["behavior_changed"] = changed
                                row["children"][op_name] = {
                                    "attempted": True, "operator_valid": True, "errors": [],
                                    "episode": child_ep, "behavior_changed": changed,
                                }
                                print(f"pilot {task_id}/{seed_id}/{op_name}: parent_correct={parent_ep['answer_correct']} child_correct={child_ep['answer_correct']} child_path={child_ep['tool_path_valid']} changed={changed}")
                        except BudgetExceededError as exc:
                            stop_reason = str(exc)
                            matrix_complete = False
                            break
                    if stop_reason:
                        break

                results["pilot"]["pairs"] = pairs
                results["pilot"]["matrix_complete"] = bool(matrix_complete and not stop_reason)
                results["pilot"]["stop_reason"] = stop_reason or "complete predeclared matrix"
                results["pilot"]["aggregate"] = aggregate_pilot(results["pilot"])
                final_accounting = accounting(llm)
                within_budget = (
                    llm._call_id <= MAX_GENERATIONS and time.monotonic() - started <= MAX_WALL_S
                    and final_accounting["accounting_ok"] and revision_match
                )
                if results["pilot"]["matrix_complete"] and within_budget:
                    results["status"] = "PILOT_COMPLETE_REQUIRES_INDEPENDENT_REVIEW"
                else:
                    results["status"] = "INCONCLUSIVE"
                    if not within_budget and not stop_reason:
                        results["pilot"]["stop_reason"] = "budget/deadline/accounting/revision gate failed"

    except BudgetExceededError as exc:
        results["status"] = "INCONCLUSIVE"
        results["fatal_error"] = str(exc)
        results["pilot"]["stop_reason"] = str(exc)
    except Exception as exc:
        results["status"] = "ERROR_STOP"
        results["fatal_error"] = f"{type(exc).__name__}: {exc}"
        print(results["fatal_error"], file=sys.stderr)
    finally:
        if llm is not None:
            ledger = llm.get_generation_ledger()
            stats = llm.get_stats()
            final_accounting = accounting(llm)
        else:
            ledger = []
            stats = {"model": "qwen2.5-7b-instruct", "revision": None, "requests": 0,
                     "actual_generations": 0, "total_tokens": 0, "failures": 0}
            final_accounting = {
                "ledger_rows": 0, "actual_generations": 0, "reserved_call_count": 0,
                "unique_call_ids": True, "monotonic_call_ids": True, "generation_count_match": True,
                "token_delta_sum": 0, "runtime_total_tokens": 0, "token_sum_match": True,
                "ledger_generation_failures": 0, "runtime_generation_failures": 0,
                "failure_ledger_match": True, "accounting_ok": True, "stats": stats,
            }
        elapsed = time.monotonic() - started
        results["llm_stats"] = stats
        results["final_accounting"] = final_accounting
        results["total_actual_generations"] = len(ledger)
        results["total_wall_s"] = round(elapsed, 4)
        results["budget_exhausted"] = bool(len(ledger) >= MAX_GENERATIONS or elapsed > MAX_WALL_S)
        results["formal_g3"] = "FAIL_UNCHANGED"
        results["pc1_approved"] = False
        results["pc1_executed"] = False
        results["family_c_access"] = False
        results["controller_training"] = "NOT_AUTHORIZED"

        ledger_path = run_dir / "R3_LEDGER.jsonl"
        with ledger_path.open("w", encoding="utf-8", newline="\n") as f:
            for row in ledger:
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        raw_path = run_dir / "R3_RAW.json"
        write_json(raw_path, results)
        report_path = run_dir / "R3_REPORT.md"
        report_path.write_text(make_report(results), encoding="utf-8")
        names = ["R3_FROZEN_MANIFEST.json", "R3_RAW.json", "R3_LEDGER.jsonl", "R3_REPORT.md"]
        result_manifest = {
            "protocol": PROTOCOL_ID, "run_id": run_id, "status": results.get("status"),
            "frozen_manifest_sha256": sha256_file(run_dir / "R3_FROZEN_MANIFEST.json") if (run_dir / "R3_FROZEN_MANIFEST.json").is_file() else None,
            "files": {
                name: {"sha256": sha256_file(run_dir / name), "size_bytes": (run_dir / name).stat().st_size}
                for name in names if (run_dir / name).is_file()
            },
        }
        write_json(run_dir / "R3_RESULT_MANIFEST.json", result_manifest)
        print(f"R3 status={results.get('status')}")
        print(f"actual_generations={results.get('total_actual_generations')} / {MAX_GENERATIONS}")
        print(f"wall_clock={results.get('total_wall_s')} / {MAX_WALL_S}s")
        print(f"accounting_ok={final_accounting.get('accounting_ok')}")
        print(f"artifacts={run_dir}")
        print(f"result_manifest_sha256={sha256_file(run_dir / 'R3_RESULT_MANIFEST.json')}")

    return 1 if results.get("status") == "ERROR_STOP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
