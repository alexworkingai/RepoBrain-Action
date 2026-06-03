from __future__ import annotations

import pytest

from repobrain.output_md import render_review_markdown


def test_review_zero_findings_and_zero_risk_drivers_render_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_REPOBRAIN_VERBOSE_DIAGNOSTICS", "1")
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

    assert "Confirmed findings" in md
    assert "Confirmed findings: none." in md
    assert "No confirmed high-risk findings detected." not in md
    assert "Risk drivers:" in md
    assert "No material risk drivers identified." in md
    assert "- n/a" not in md
    assert "Proceed with standard CI checks before merge." in md


def test_review_filters_pseudo_confirmed_findings_line(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_REPOBRAIN_VERBOSE_DIAGNOSTICS", "1")
    md = render_review_markdown(
        review={
            "summary_text": "Small cleanup changes.",
            "risk_level": "low",
            "confirmed_findings": ["No obvious high-risk patterns detected"],
            "possible_signals": [],
            "risk_drivers": [],
            "informational_notes": [],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={"route_final": "FAST", "pass_count": 1},
    )

    assert "No obvious high-risk patterns detected" not in md
    assert "Confirmed findings: none." in md
