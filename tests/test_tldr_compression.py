from __future__ import annotations

from repobrain.output_md import render_review_markdown


def test_review_tldr_compression_removes_scaffold_and_sets_flag() -> None:
    audit_summary = {
        "route_final": "DEEP",
        "pass_count": 1,
        "verification_pass_count": 0,
        "verification_fail_count": 0,
        "verification_pending_count": 0,
        "verification_not_run_count": 0,
    }
    review = {
        "summary_text": (
            "(1) PR Metadata Summary: workflow and auth files changed\n"
            "(2) Targeted Evidence: workflow and auth files changed\n"
            "(3) Concise Final Review: workflow and auth files changed"
        ),
        "risk_level": "medium",
        "files_block": ["- `repobrain/github_flow.py` (modified, +10/-2)"],
        "confirmed_findings": [],
        "possible_signals": [],
        "risk_drivers": ["workflow and auth files changed"],
        "informational_notes": [],
        "recommendations": ["Run CI checks."],
    }

    md = render_review_markdown(
        review=review,
        verification_report={"summary": "not run", "checks": []},
        audit_summary=audit_summary,
    )

    assert "(1) PR Metadata Summary" not in md
    assert "(2) Targeted Evidence" not in md
    assert "(3) Concise Final Review" not in md
    assert audit_summary["tldr_compressed"] is True
