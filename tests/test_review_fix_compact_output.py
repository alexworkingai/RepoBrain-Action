from __future__ import annotations

from repobrain.output_md import render_patch_markdown, render_review_markdown


def _primary(markdown: str) -> str:
    return markdown.split("<details>", 1)[0]


def test_review_output_keeps_internal_cards_out_of_default_comment() -> None:
    md = render_review_markdown(
        review={
            "summary_text": "Compact summary.",
            "risk_level": "low",
            "files_block": ["- `repobrain/github_flow.py`"],
            "confirmed_findings": [],
            "possible_signals": ["Potential drift."],
            "informational_notes": ["Keep watching permissions."],
            "recommendations": ["Run CI."],
            "risk_drivers": ["Workflow surface changed."],
        },
        verification_report={"summary": "NOT_RUN"},
        audit_summary={"command": "review", "route_final": "REVIEW", "selected": 1},
    )

    primary = _primary(md)
    assert "Decision cards" not in primary
    assert "Evidence verdicts" not in primary
    assert "Patch governance" not in primary


def test_fix_output_keeps_patch_internals_out_of_default_comment() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Compact proposal.", "risk_level": "low", "files_changed": [], "suggested_tests": []},
        verification_report={"summary": "NOT_RUN"},
        patch_snippet="diff --git a/x b/x",
        patch_written=True,
        patch_apply_message="proposal-only mode",
        audit_summary={
            "command": "fix",
            "route_final": "FIX",
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 0,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_patch",
            "localized_patch_evidence_count": 0,
            "patch_grounding_mode": "pr_metadata",
        },
    )

    primary = _primary(md)
    assert "Patch snippet" not in primary
    assert "Patch artifact" not in primary
    assert "Decision cards" not in primary
