"""Update status.json with Stage 1I-R1 completion data."""
import json
from pathlib import Path

status_path = Path(r"D:\GLEPPO_repo\status.json")
with open(status_path, encoding="utf-8") as f:
    status = json.load(f)

# Update phase and state
status["phase"] = "GLEPPO_R26_STAGE1I_R1_COMPLETE"
status["state"] = "R26_STAGE1I_R1_READY_FOR_PLANNER_REVIEW"
status["updated_at"] = "2026-11-04"

# Update current task and next gate
status["current_task"] = "Stage 1I-R1 complete. Awaiting Planner independent review."
status["next_gate"] = "PLANNER_INDEPENDENT_REVIEW_OF_STAGE1I_R1 -> (ONLY_IF_ACCEPTED) R26_ECOS_PROTOCOL_RECONCILIATION"

# Update r26_stage1i_r1 with complete data
status["r26_stage1i_r1"] = {
    "status": "EXECUTOR_COMPLETE_AWAITING_PLANNER_REVIEW",
    "date": "2026-11-04",
    "semantic_map_created": True,
    "semantic_map_json": "research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json",
    "semantic_map_md": "research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md",
    "corrective_report": "research/R26_STAGE1I_R1_CORRECTIVE_REPORT.md",
    "validator_path": "scripts/_r26i_validator.py",
    "validator_parser": "python_ast_module",
    "validator_self_tests": "PASS_15_OF_15",
    "validator_self_test_command": "python scripts/_r26i_validator.py --self-test",
    "validator_self_test_exit_code": 0,
    "map_validation": "PASS",
    "map_validation_command": "python scripts/_r26i_validator.py --validate research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json --base-dir .",
    "map_findings_total": 42,
    "map_mapped_rows": 39,
    "map_none_rows": 3,
    "map_declarations_found": 218,
    "dispositions": {
        "VERIFIED_FIXED": 26,
        "PARTIALLY_FIXED": 14,
        "OPEN": 1,
        "UNVERIFIABLE": 1,
    },
    "disposition_arithmetic": "26+14+1+1=42",
    "disposition_source": "computed_mechanically_from_json_map",
    "r53_corrected": "INDIRECT_evidence_test_mutation_status_not_checked_by_consistency_line_118",
    "r53_disposition": "PARTIALLY_FIXED",
    "r39_cross_referenced": "R16_R20_instrumented_evaluator_tests",
    "r39_evidence_boundaries": "direct_crn_tests_plus_structural_action_exclusion_plus_R16_R20_cross_refs",
    "r39_tautological_test_excluded": "test_action_genotype_excluded_NOT_cited",
    "r18_manual_evidence_complete": True,
    "r18_manual_references_count": 13,
    "r18_includes_cost_baseline_line_44": True,
    "provenance": {
        "stage_1i_parent_pre_work_head": "e2cb353037368a82b5dd9c7b53a1d40f21425750",
        "stage_1i_executor_commit": "a1e6e65e671c876d028492bfed164205c54df08b",
        "stage_1i_planner_review_commit": "dfd7ef909ba4ee97e01c4bb57b0177ae8869d61c",
        "stage_1i_r1_parent": "539f74d5c898abc144992fff4a413a30744c1cc9",
        "main_head": "6bad0b77835a2d00c62287c0c7d9d91d1d186d5e",
    },
    "hard_boundaries": {
        "production_source_changes": False,
        "test_suite_changes": False,
        "registered_pc1_executed": False,
        "family_c_accessed": False,
        "controller_training": "NOT_AUTHORIZED_NOT_STARTED",
        "formal_g3": "FAIL",
        "model_api_calls": 0,
        "model_api_calls_verification": "EXECUTOR_ATTESTED_NOT_INDEPENDENTLY_VERIFIED",
        "production_runtime_calls": 0,
        "production_runtime_verification": "EXECUTOR_ATTESTED_NOT_INDEPENDENTLY_VERIFIED",
        "main_modified": False,
    },
    "full_suite": "450/450_EXECUTOR_REPORTED_NOT_INDEPENDENTLY_REPRODUCED",
}

# Update durable docs references
status["durable_docs_updated"] = {
    "planner_review_commit": "dfd7ef909ba4ee97e01c4bb57b0177ae8869d61c",
    "corrective_prompt_commit": "824523ae00a21c0c91f31a3225cc4c3177d37003",
    "latest_plan_commit": "1514780fb8df2fdfbf3982d540d3a2021ba1b59d",
    "handoff_commit": "1c53356af7bf097def8887a590d75701e15f6ff4",
    "next_session_prompt_commit": "66414caf2f78fcb861379c88f7cd84548ea7b42f",
    "pc1_audit_summary_commit": "0aeb3ecf0a3d7087fe6e6b286b038e6477cd06ae",
    "r1_corrective_report": "research/R26_STAGE1I_R1_CORRECTIVE_REPORT.md",
    "r1_semantic_map_json": "research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json",
    "r1_semantic_map_md": "research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md",
    "r1_validator": "scripts/_r26i_validator.py",
}

# Save
with open(status_path, "w", encoding="utf-8") as f:
    json.dump(status, f, indent=2, ensure_ascii=False)

print("status.json updated with Stage 1I-R1 complete data.")
