from __future__ import annotations

from repobrain.output_md import render_review_markdown
from repobrain.review_validator import validate_review_findings


def test_risk_driver_items_are_not_rendered_as_confirmed_findings() -> None:
    review = validate_review_findings(
        {
            "summary_text": "Workflow and CI changes detected.",
            "risk_items": [
                {
                    "message": "CI/CD changed: verify workflows",
                    "severity": "medium",
                    "evidence": [{"kind": "file_path", "path": ".github/workflows/repobrain.yml"}],
                }
            ],
        }
    )

    md = render_review_markdown(
        review=review,
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "route_final": "FAST",
            "pass_count": 1,
            "review_confirmed_findings_count": int(review["validation"]["confirmed_findings_count"]),
            "review_risk_drivers_count": int(review["validation"]["risk_drivers_count"]),
            "review_possible_signals_count": int(review["validation"]["possible_signals_count"]),
            "review_informational_notes_count": int(review["validation"]["informational_notes_count"]),
        },
    )

    assert "Risk drivers:" in md
    assert "- CI/CD changed: verify workflows" in md
    assert "### ⚠️ Confirmed findings" in md
    assert "- CI/CD changed: verify workflows" not in md.split("### ⚠️ Confirmed findings", 1)[1]
