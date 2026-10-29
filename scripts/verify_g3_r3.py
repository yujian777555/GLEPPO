"""Independent integrity verifier for one G3-DIAG-v2-R3 run directory."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gleppo.r3_metrics import check_format_compliant
from gleppo.tasks import attach_checker
from gleppo.tool_path import verify_tool_path_for_task

EXPECTED_TASKS = ["B2-001", "B2-003", "B2-004"]
EXPECTED_SEEDS = ["r3-paired-seed-001", "r3-paired-seed-002", "r3-paired-seed-003"]
EXPECTED_OPERATORS = ["tool_subset_edit", "crossover"]
ARTIFACT_NAMES = ["R3_FROZEN_MANIFEST.json", "R3_RAW.json", "R3_LEDGER.jsonl", "R3_REPORT.md"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def verify(run_dir_arg: str) -> Dict[str, Any]:
    run_dir = Path(run_dir_arg)
    if not run_dir.is_absolute():
        run_dir = (ROOT / run_dir).resolve()
    allowed_root = (ROOT / "research" / "runs").resolve()
    if not within(run_dir, allowed_root):
        raise ValueError("run directory must be inside research/runs")
    if not run_dir.is_dir():
        raise FileNotFoundError(f"run directory not found: {run_dir}")

    result_manifest = read_json(run_dir / "R3_RESULT_MANIFEST.json")
    frozen_path = run_dir / "R3_FROZEN_MANIFEST.json"
    raw_path = run_dir / "R3_RAW.json"
    ledger_path = run_dir / "R3_LEDGER.jsonl"
    report_path = run_dir / "R3_REPORT.md"
    frozen = read_json(frozen_path)
    raw = read_json(raw_path)
    ledger = [
        json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    tasks: Dict[str, dict] = {}
    for rel in ("data/diagnostic_B2.jsonl", "data/diagnostic_B2_R3.jsonl"):
        task_path = ROOT / rel
        for line in task_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                task = attach_checker(json.loads(line))
                tasks[task["task_id"]] = task

    checks: Dict[str, bool] = {}
    manifest_files = result_manifest.get("files", {})
    for name in ARTIFACT_NAMES:
        entry = manifest_files.get(name)
        path = run_dir / name
        checks[f"artifact_hash:{name}"] = bool(
            entry and path.is_file() and sha256_file(path) == entry.get("sha256")
            and path.stat().st_size == entry.get("size_bytes")
        )
    checks["frozen_manifest_hash_link"] = (
        result_manifest.get("frozen_manifest_sha256") == sha256_file(frozen_path)
    )
    checks["result_manifest_run_status_match"] = (
        result_manifest.get("run_id") == raw.get("run_id")
        and result_manifest.get("status") == raw.get("status")
    )

    source_checks = {}
    for rel, entry in frozen.get("files", {}).items():
        rel_path = Path(rel)
        candidate = (ROOT / rel_path).resolve()
        safe = not rel_path.is_absolute() and ".." not in rel_path.parts and within(candidate, ROOT)
        source_checks[rel] = bool(safe and candidate.is_file() and sha256_file(candidate) == entry.get("sha256")
                                   and candidate.stat().st_size == entry.get("size_bytes"))
    checks["frozen_source_hashes"] = bool(source_checks) and all(source_checks.values())

    ids = [row.get("call_id") for row in ledger]
    stats = raw.get("llm_stats", {})
    final_accounting = raw.get("final_accounting", {})
    token_sum = sum(int(row.get("output_tokens", 0)) for row in ledger)
    failures = sum(1 for row in ledger if row.get("status") != "ok")
    checks["ledger_ids_unique"] = len(ids) == len(set(ids))
    checks["ledger_ids_monotonic"] = ids == list(range(1, len(ids) + 1))
    checks["ledger_count_matches_runtime"] = (
        len(ledger) == raw.get("total_actual_generations")
        == stats.get("actual_generations") == final_accounting.get("ledger_rows")
        == final_accounting.get("actual_generations")
    )
    checks["token_delta_matches_runtime"] = (
        token_sum == stats.get("total_tokens") == final_accounting.get("token_delta_sum")
        == final_accounting.get("runtime_total_tokens")
    )
    checks["failure_count_matches_runtime"] = (
        failures == stats.get("failures") == final_accounting.get("ledger_generation_failures")
        == final_accounting.get("runtime_generation_failures")
    )
    checks["runtime_accounting_flag"] = bool(final_accounting.get("accounting_ok"))

    canary = raw.get("canary", {})
    eps = canary.get("episodes", [])
    gate = canary.get("gate", {})
    canary_path_count = sum(bool(ep.get("tool_path_valid")) for ep in eps)
    canary_correct_count = sum(bool(ep.get("answer_correct")) for ep in eps)
    recomputed_canary = bool(
        len(eps) == 3 and canary_path_count == 3 and canary_correct_count >= 2
        and raw.get("revision_match") is True
        and gate.get("accounting_ok") is True
    )
    checks["canary_gate_recomputed_matches_report"] = bool(gate.get("passed")) == recomputed_canary
    checks["canary_metrics_recomputed"] = (
        gate.get("completed_episodes") == len(eps)
        and gate.get("tool_path_pass_count") == canary_path_count
        and gate.get("answer_correct_count") == canary_correct_count
        and gate.get("format_compliant_count") == sum(bool(ep.get("format_compliant")) for ep in eps)
    )

    # Independently recompute answer correctness, format, path, hard validity,
    # and effective success from the saved answers and traces.
    all_episodes: List[Dict[str, Any]] = list(eps)
    pilot_for_metrics = raw.get("pilot", {})
    for task_id, seed_map in pilot_for_metrics.get("pairs", {}).items():
        for seed_id, pair in seed_map.items():
            if pair.get("parent"):
                all_episodes.append(pair["parent"])
            for child_row in pair.get("children", {}).values():
                if child_row.get("episode"):
                    all_episodes.append(child_row["episode"])
    metrics_ok = True
    for ep in all_episodes:
        task = tasks.get(ep.get("task_id"))
        if task is None:
            metrics_ok = False
            continue
        answer = ep.get("answer", "")
        try:
            correct = bool(task["gold_check"](answer, None))
        except Exception:  # noqa: BLE001
            correct = False
        format_ok = check_format_compliant(answer)
        path_details = verify_tool_path_for_task(
            task["task_id"], ep.get("trace", []), task.get("required_tools", [])
        )
        path_ok = bool(path_details.get("passed"))
        hard_ok = format_ok and path_ok
        effective_ok = correct and hard_ok
        if (
            bool(ep.get("answer_correct")) != correct
            or bool(ep.get("format_compliant")) != format_ok
            or bool(ep.get("tool_path_valid")) != path_ok
            or bool(ep.get("hard_validity")) != hard_ok
            or bool(ep.get("effective_success")) != effective_ok
        ):
            metrics_ok = False
    checks["episode_metrics_independently_recomputed"] = metrics_ok

    pilot = raw.get("pilot", {})
    if pilot.get("matrix_complete"):
        pairs = pilot.get("pairs", {})
        coverage_ok = True
        for task_id in EXPECTED_TASKS:
            for seed_id in EXPECTED_SEEDS:
                pair = pairs.get(task_id, {}).get(seed_id)
                if not pair or not pair.get("parent"):
                    coverage_ok = False
                    continue
                for op in EXPECTED_OPERATORS:
                    child = pair.get("children", {}).get(op)
                    if not child or not child.get("attempted"):
                        coverage_ok = False
        checks["complete_pilot_matrix_coverage"] = coverage_ok
        checks["complete_pilot_within_declared_status"] = raw.get("status") == "PILOT_COMPLETE_REQUIRES_INDEPENDENT_REVIEW"
    else:
        checks["complete_pilot_matrix_coverage"] = True
        checks["complete_pilot_within_declared_status"] = raw.get("status") != "PILOT_COMPLETE_REQUIRES_INDEPENDENT_REVIEW"

    aggregate = pilot.get("aggregate", {})
    for op in EXPECTED_OPERATORS:
        attempted_rows = []
        invalid_rows = []
        format_failures = 0
        for task_id, seed_map in pilot.get("pairs", {}).items():
            for seed_id, pair in seed_map.items():
                if not pair.get("parent"):
                    continue
                child_row = pair.get("children", {}).get(op, {})
                if not child_row.get("attempted"):
                    continue
                attempted_rows.append(child_row)
                child = child_row.get("episode")
                if not child_row.get("operator_valid") or not child:
                    invalid_rows.append(child_row)
                elif not child.get("format_compliant"):
                    format_failures += 1
        summary = aggregate.get(op, {})
        checks[f"aggregate_attempt_count:{op}"] = summary.get("paired_comparisons", 0) == len(attempted_rows)
        checks[f"aggregate_invalid_count:{op}"] = summary.get("operator_invalid_count", 0) == len(invalid_rows)
        checks[f"aggregate_format_failure_count:{op}"] = summary.get("child_format_failure_count", 0) == format_failures

    checks["formal_g3_still_fail"] = raw.get("formal_g3") == "FAIL_UNCHANGED"
    checks["pc1_not_approved_or_run"] = raw.get("pc1_approved") is False and raw.get("pc1_executed") is False
    checks["family_c_not_accessed"] = raw.get("family_c_access") is False
    checks["controller_training_not_authorized"] = raw.get("controller_training") == "NOT_AUTHORIZED"

    return {
        "protocol": raw.get("protocol"),
        "run_id": raw.get("run_id"),
        "status": raw.get("status"),
        "verification_pass": all(checks.values()),
        "canary_gate_pass": recomputed_canary,
        "pilot_matrix_complete": bool(pilot.get("matrix_complete")),
        "checks": checks,
        "failed_checks": [key for key, value in checks.items() if not value],
        "source_hash_checks": source_checks,
        "actual_generations": len(ledger),
        "token_delta_sum": token_sum,
        "result_manifest_sha256": sha256_file(run_dir / "R3_RESULT_MANIFEST.json"),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/verify_g3_r3.py research/runs/<RUN_ID>", file=sys.stderr)
        return 2
    try:
        result = verify(sys.argv[1])
    except Exception as exc:
        print(json.dumps({"verification_pass": False, "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["verification_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
