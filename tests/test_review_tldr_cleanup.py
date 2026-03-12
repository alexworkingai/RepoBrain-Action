from __future__ import annotations

from repobrain.output_md import render_review_markdown


def test_review_tldr_does_not_leak_internal_scaffold_headers() -> None:
    md = render_review_markdown(
        review={
            "summary_text": (
                "(1) PR Metadata Summary:\n"
                "Changed core files.\n"
                "(2) Targeted Evidence:\n"
                "Found risky workflow edits.\n"
                "(3) Concise Final Review:\n"
                "Review manually before merge."
            ),
            "risk_level": "medium",
            "confirmed_findings": ["Merge conflict markers present (evidence: 1 file(s))"],
            "possible_signals": [],
            "recommendations": ["Run pytest -q"],
            "risk_drivers": ["CI/CD changed: verify workflows"],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={"route_final": "DEEP", "pass_count": 1},
    )

    assert "(1) PR Metadata Summary:" not in md
    assert "(2) Targeted Evidence:" not in md
    assert "(3) Concise Final Review:" not in md
    assert "TL;DR: Changed core files." in md
