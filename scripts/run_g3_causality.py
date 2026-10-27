"""G3 causality gate: each operator must change observable behavior.

Runs on TRAIN family tasks only (A/B). Never Family C.
Writes research/G3_CAUSALITY.md evidence JSON + markdown.
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gleppo.genotype import behavior_hash, make_valid_genotype, canonical_serialize  # noqa: E402
from gleppo.operators import OPERATOR_NAMES, apply_operator  # noqa: E402
from gleppo.interpreter import Interpreter  # noqa: E402
from gleppo.tasks import build_task, attach_checker  # noqa: E402
from gleppo.evaluator import Evaluator  # noqa: E402

N_PARENTS = 4
N_TASKS = 8          # train-family smoke tasks
N_EVAL = 2

FAMILY_TASKS = [
    attach_checker(build_task(f"A-g3-{i:02d}", "A", 100 + i)) for i in range(N_TASKS // 2)
] + [
    attach_checker(build_task(f"B-g3-{i:02d}", "B", 200 + i)) for i in range(N_TASKS // 2)
]


def parent_variants():
    ps = []
    for i in range(N_PARENTS):
        g = make_valid_genotype()
        g.system_prompt = g.system_prompt + f" Variant {i}."
        g.meta = {"parent_id": f"p{i}"}
        ps.append(g)
    return ps


def behavior_signature(g, task, interp: Interpreter, n_rep=2):
    succ = 0
    tools = 0
    turns = 0
    fails = {}
    traces = []
    for r in range(n_rep):
        res = interp.run(g, task, seed_parts=(task["task_id"], r, behavior_hash(g)[:8]))
        succ += int(res.success)
        tools += res.tool_calls
        turns += res.turns
        fails[res.failure_category] = fails.get(res.failure_category, 0) + 1
        traces.append({
            "rep": r,
            "success": res.success,
            "failure_category": res.failure_category,
            "turns": res.turns,
            "tool_calls": res.tool_calls,
            "answer_head": res.answer[:80],
            "trace_types": [t.get("type") for t in res.trace],
        })
    return {
        "success_rate": succ / n_rep,
        "mean_tool_calls": tools / n_rep,
        "mean_turns": turns / n_rep,
        "fails": fails,
        "traces": traces,
    }


def main():
    interp = Interpreter()
    parents = parent_variants()
    report = {
        "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": "STUB_LL M_v1 (docs/RUNTIME_LOCK.md §4) — structural causality, not production-model validation",
        "n_parents": N_PARENTS,
        "n_tasks": N_TASKS,
        "n_eval": N_EVAL,
        "families_used": ["A", "B"],
        "family_c_accessed": False,
        "operators": {},
    }

    for op in OPERATOR_NAMES:
        changed_hash = 0
        changed_behavior = 0
        valid = 0
        invalid = 0
        no_op = 0
        diffs = []
        for p_idx, parent in enumerate(parents):
            ctx = {
                "gen": p_idx,
                "failure_category": ["tool_error", "wrong_answer", "format_error", "timeout"][p_idx % 4],
                "failure_detail": "sample error",
                "mate": parents[(p_idx + 1) % N_PARENTS],
            }
            child, ok, errs = apply_operator(op, parent, ctx)
            if not ok:
                invalid += 1
                diffs.append({"parent": p_idx, "valid": False, "errors": errs})
                continue
            valid += 1
            h_same = behavior_hash(parent) == behavior_hash(child)
            if h_same:
                no_op += 1
            else:
                changed_hash += 1

            # behavioral comparison on 2 train tasks
            beh_change = False
            sample = []
            for task in FAMILY_TASKS[:2]:
                bp = behavior_signature(parent, task, interp, n_rep=N_EVAL)
                bc = behavior_signature(child, task, interp, n_rep=N_EVAL)
                delta = {
                    "task": task["task_id"],
                    "parent": {k: bp[k] for k in ("success_rate", "mean_tool_calls", "mean_turns", "fails")},
                    "child": {k: bc[k] for k in ("success_rate", "mean_tool_calls", "mean_turns", "fails")},
                }
                if (
                    bp["success_rate"] != bc["success_rate"]
                    or bp["mean_tool_calls"] != bc["mean_tool_calls"]
                    or bp["mean_turns"] != bc["mean_turns"]
                    or bp["fails"] != bc["fails"]
                    or bp["traces"][0]["answer_head"] != bc["traces"][0]["answer_head"]
                ):
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
                "parent_prompt_head": parent.system_prompt[:80],
                "child_prompt_head": child.system_prompt[:80],
                "genotype_diff_keys": _diff_keys(parent, child),
                "samples": sample,
            })

        report["operators"][op] = {
            "valid": valid,
            "invalid": invalid,
            "hash_changed": changed_hash,
            "behavior_changed": changed_behavior,
            "no_op": no_op,
            "pass": changed_behavior >= max(1, valid // 2),
            "diffs": diffs,
        }

    os.makedirs("research", exist_ok=True)
    with open("research/G3_CAUSALITY.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    lines = [
        "# G3 Genotype-Causality Report",
        "",
        f"**Date:** {report['date']}",
        f"**Mode:** {report['mode']}",
        f"**Families used:** A/B only. Family C accessed: {report['family_c_accessed']}",
        f"**Parents:** {N_PARENTS} · **Tasks:** {N_TASKS} (signature probe uses 2/operator/parent) · **Replicas:** {N_EVAL}",
        "",
        "| Operator | valid | invalid | hash_changed | behavior_changed | no_op | PASS |",
        "|---|---|---|---|---|---|---|",
    ]
    all_pass = True
    for op, r in report["operators"].items():
        lines.append(
            f"| `{op}` | {r['valid']} | {r['invalid']} | {r['hash_changed']} | {r['behavior_changed']} | {r['no_op']} | {'YES' if r['pass'] else 'NO'} |"
        )
        all_pass = all_pass and r["pass"]
    lines += [
        "",
        f"**Overall G3 (stub mode):** {'PASS' if all_pass else 'FAIL'}",
        "",
        "## Notes",
        "- Evidence JSON: `research/G3_CAUSALITY.json` (hashes, diffs, traces).",
        "- StubLLM preserves causal structure (prompt/tool/workflow edits change traces);",
        "  production-model G3 must be re-run after RUNTIME_LOCK production fields are filled.",
        "- Invalid offspring are counted and dropped, never silently replaced by parents.",
    ]
    with open("research/G3_CAUSALITY.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(json.dumps({op: {k: r[k] for k in ("valid", "invalid", "behavior_changed", "pass")} for op, r in report["operators"].items()}, indent=2))
    print("G3_OVERALL", "PASS" if all_pass else "FAIL")
    return 0 if all_pass else 1


def _diff_keys(p, c):
    d = []
    if p.system_prompt != c.system_prompt:
        d.append("system_prompt")
    if sorted(p.tools) != sorted(c.tools):
        d.append("tools")
    if [s.to_dict() for s in p.workflow] != [s.to_dict() for s in c.workflow]:
        d.append("workflow")
    return d


if __name__ == "__main__":
    sys.exit(main())
