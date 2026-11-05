"""Generate Markdown rendering of the semantic evidence map."""
import json
from pathlib import Path

REPO = Path(r"D:\GLEPPO_repo")
map_path = REPO / "research" / "R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json"

with open(map_path, encoding="utf-8") as f:
    data = json.load(f)

lines = []
lines.append("# R26 Stage 1I-R1 Semantic Evidence Map")
lines.append("")
lines.append(f"**Schema version:** {data.get('schema_version', '1.0')}")
lines.append(f"**Generated:** {data.get('generated_at', 'N/A')}")
lines.append(f"**Branch:** {data.get('branch', 'N/A')}")
lines.append(f"**Source snapshot:** {data.get('source_snapshot', 'N/A')}")
lines.append("")
lines.append("This document renders the canonical machine-readable map in")
lines.append("`research/R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.json` as 42 formal Finding rows (R12-R53).")
lines.append("")

# Summary table
from collections import Counter
dispositions = Counter(f["disposition"] for f in data["findings"])
evidence_types = Counter(f["evidence_type"] for f in data["findings"])

lines.append("## Disposition Summary")
lines.append("")
lines.append("| Disposition | Count |")
lines.append("|---|---|")
for d in ["VERIFIED_FIXED", "PARTIALLY_FIXED", "OPEN", "UNVERIFIABLE", "REGRESSION"]:
    if d in dispositions:
        lines.append(f"| {d} | {dispositions[d]} |")
lines.append(f"| **Total** | **{sum(dispositions.values())}** |")
lines.append("")
lines.append(f"Arithmetic: {' + '.join(f'{v} {k}' for k,v in sorted(dispositions.items()))} = {sum(dispositions.values())}")
lines.append("")
lines.append("| Evidence Type | Count |")
lines.append("|---|---|")
for et in ["DIRECT", "INDIRECT", "MANUAL", "NONE"]:
    if et in evidence_types:
        lines.append(f"| {et} | {evidence_types[et]} |")
lines.append("")

# Rows without direct test evidence
none_rows = [f["id"] for f in data["findings"] if not f.get("test_evidence")]
lines.append(f"**Rows with no test mapping (NONE):** {', '.join(none_rows)}")
lines.append(f"**Rows with test mapping:** {42 - len(none_rows)}")
lines.append("")

# Individual finding sections
lines.append("---")
lines.append("")
lines.append("## Finding Rows")
lines.append("")

for f in data["findings"]:
    fid = f["id"]
    lines.append(f"### {f['original_finding_heading']}")
    lines.append("")
    lines.append(f"- **ID:** {fid}")
    lines.append(f"- **Original review:** {f['original_review_document']}")
    lines.append(f"- **Failure mode:** {f['original_failure_mode']}")
    lines.append(f"- **Evidence type:** {f['evidence_type']}")
    lines.append(f"- **Disposition:** {f['disposition']}")
    lines.append("")

    # Acceptance criteria
    lines.append("**Complete original acceptance criteria:**")
    for ac in f.get("complete_original_acceptance_criteria", []):
        lines.append(f"- {ac}")
    lines.append("")

    # Test evidence
    if f.get("test_evidence"):
        lines.append("**Test evidence:**")
        for i, te in enumerate(f["test_evidence"]):
            lines.append(f"")
            lines.append(f"#### Test {i+1}: `{te['test_file']}::{te['test_class']}::{te['test_function']}`")
            lines.append(f"- **Declaration:** lines {te.get('declaration_start_line', '?')}-{te.get('declaration_end_line', '?')}")
            lines.append(f"- **Call path:** {te.get('call_path', 'N/A')}")

            # Assertions
            assertions = te.get("assertion_expressions", [])
            if assertions:
                lines.append(f"- **Assertions:**")
                for a in assertions:
                    lines.append(f"  - Line {a.get('line', '?')}: `{a.get('expression', 'N/A')}`")

            # Source symbols
            source_syms = te.get("source_symbols", [])
            if source_syms:
                lines.append(f"- **Source symbols:**")
                for s in source_syms:
                    rng = f"lines {s.get('start_line', '?')}-{s.get('end_line', '?')}" if s.get('start_line') else "line range unresolved"
                    lines.append(f"  - `{s.get('symbol', '?')}` in `{s.get('file', '?')}` ({rng})")

            # Branch reachability
            br = te.get("branch_reached", {})
            if isinstance(br, dict):
                reached = "YES" if br.get("reached") else "NO"
                lines.append(f"- **Branch reached:** {reached} — {br.get('explanation', 'N/A')}")
            else:
                lines.append(f"- **Branch reached:** {'YES' if br else 'NO'}")

            # Acceptance conditions
            if te.get("acceptance_conditions_proven"):
                lines.append(f"- **Directly proven:** {'; '.join(te['acceptance_conditions_proven'])}")
            if te.get("acceptance_conditions_indirect"):
                lines.append(f"- **Indirectly supported:** {'; '.join(te['acceptance_conditions_indirect'])}")
            if te.get("acceptance_conditions_uncovered"):
                lines.append(f"- **Uncovered:** {'; '.join(te['acceptance_conditions_uncovered'])}")

            lines.append(f"- **Harness type:** {te.get('harness_type', 'N/A')}")
        lines.append("")
    else:
        lines.append("**Test evidence:** NONE (no direct test evidence)")
        lines.append("")

    # Manual evidence
    if f.get("manual_evidence"):
        lines.append("**Manual evidence:**")
        for me in f["manual_evidence"]:
            line_ref = me.get("line", "?")
            lines.append(f"- `{me.get('source', '?')}` line {line_ref}: {me.get('value', '?')} — {me.get('note', '')}")
        if f.get("manual_evidence_note"):
            lines.append(f"- **Note:** {f['manual_evidence_note']}")
        lines.append("")

    # Evidence boundaries (for R39, R53)
    if f.get("evidence_boundaries"):
        eb = f["evidence_boundaries"]
        lines.append("**Evidence boundaries:**")
        for k, v in eb.items():
            if isinstance(v, list):
                lines.append(f"- **{k.replace('_', ' ').title()}:**")
                for item in v:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"- **{k.replace('_', ' ').title()}:** {v}")
        lines.append("")

    # Proven / indirect / uncovered
    if f.get("proven_acceptance_conditions"):
        lines.append(f"**Proven acceptance conditions:** {'; '.join(f['proven_acceptance_conditions'])}")
    if f.get("indirectly_supported_conditions"):
        lines.append(f"**Indirectly supported:** {'; '.join(f['indirectly_supported_conditions'])}")
    if f.get("uncovered_acceptance_conditions"):
        lines.append(f"**Uncovered acceptance conditions:** {'; '.join(f['uncovered_acceptance_conditions'])}")
    lines.append("")
    lines.append(f"**Disposition rationale:** {f.get('disposition_rationale', 'N/A')}")
    lines.append("")
    lines.append("---")
    lines.append("")

# Write output
out_path = REPO / "research" / "R26_STAGE1I_SEMANTIC_EVIDENCE_MAP.md"
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"Markdown rendering saved to {out_path}")
print(f"Total lines: {len(lines)}")
