from __future__ import annotations

from repobrain.output_md import render_patch_markdown, render_review_markdown


def _primary(markdown: str) -> str:
    return markdown.split("<details>", 1)[0]


def _details(markdown: str) -> str:
    parts = markdown.split("<details>", 1)
    return parts[1] if len(parts) > 1 else ""


def test_review_default_hides_internal_decision_cards_and_verdicts() -> None:
    md = render_review_markdown(
        review={
            "summary_text": "Compact summary.",
            "risk_level": "low",
            "files_block": ["- `docs/example.md`"],
            "confirmed_findings": [],
            "possible_signals": ["Potential wording drift."],
            "informational_notes": ["Docs-only context."],
            "recommendations": ["Run CI."],
            "risk_drivers": ["Docs may drift from implementation."],
            "evidence_verdicts": [{"claim": "Docs changed", "evidence_anchors": ["docs/example.md"]}],
        },
        verification_report={"summary": "NOT_RUN"},
        audit_summary={"command": "review", "route_final": "REVIEW", "selected": 1},
    )

    assert "Decision cards" not in _primary(md)
    assert "Evidence verdicts" not in _primary(md)
    assert "Decision cards" not in _details(md)
    assert "Evidence verdicts" not in _details(md)


def test_fix_default_hides_patch_governance_and_patch_snippet() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Compact proposal.", "risk_level": "low", "files_changed": [], "suggested_tests": []},
        verification_report={"summary": "NOT_RUN"},
        patch_snippet="diff --git a/x b/x",
        patch_written=False,
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

    assert "Patch governance" not in _primary(md)
    assert "Patch snippet" not in _primary(md)
    assert "Patch governance" not in _details(md)
    assert "Patch snippet" not in _details(md)

