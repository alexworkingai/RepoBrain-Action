from __future__ import annotations

from repobrain.evidence import EvidenceItem
from repobrain.output_md import render_answer_markdown, render_patch_markdown


def test_ask_route_and_scope_are_canonicalized_for_pr_context() -> None:
    md = render_answer_markdown(
        answer_text="Useful answer.",
        evidence=[EvidenceItem(file_path="repobrain/github_flow.py", line_start=1, line_end=2, score=0.8)],
        audit_summary={"command": "ask", "route_final": "REVIEW", "selected": 1, "pr_metadata_used": True},
        next_steps="Review the workflow.",
        command="ask",
    )

    assert "Route: `ASK`" in md
    assert "Scope: `PR ask`" in md
    assert "Route: `REVIEW`" not in md


def test_fix_audit_anchors_report_fix_route() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Safe proposal.", "risk_level": "low", "files_changed": [], "suggested_tests": []},
        verification_report={"summary": "NOT_RUN"},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="proposal-only mode",
        audit_summary={
            "command": "fix",
            "route_final": "REVIEW",
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 0,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_patch",
            "localized_patch_evidence_count": 0,
            "patch_grounding_mode": "pr_metadata",
            "requested_backend": "auto",
            "resolved_backend": "v6",
            "fallback_used": "no",
            "fallback_reason": "none",
        },
    )

    assert "Route: `FIX`" in md
