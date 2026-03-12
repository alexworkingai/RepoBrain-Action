from __future__ import annotations

from repobrain.output_md import render_review_markdown


def test_review_zero_findings_and_zero_risk_drivers_render_cleanly() -> None:
    md = render_review_markdown(
        review={
            "summary_text": "Changes are mostly refactors and naming cleanup.",
            "risk_level": "low",
            "confirmed_findings": [],
            "possible_signals": [],
            "risk_drivers": [],
            "informational_notes": [],
            "recommendations": [],
            "files_block": ["- `repobrain/output_md.py`", "- `repobrain/github_flow.py`"],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={"route_final": "FAST", "pass_count": 1},
    )

    assert "### ⚠️ Confirmed findings" in md
    assert "- none." in md
    assert "No confirmed high-risk findings detected." not in md
    assert "Risk drivers:" in md
    assert "No material risk drivers identified." in md
    assert "- n/a" not in md
    assert "Proceed with standard CI checks before merge." in md
