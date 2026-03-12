from __future__ import annotations

from repobrain.output_md import render_review_markdown
from repobrain.review_validator import validate_review_findings


def test_confirmed_finding_includes_compact_evidence_reference() -> None:
    review = validate_review_findings(
        {
            "summary_text": "Review summary.",
            "risk_items": [
                {
                    "message": "Merge conflict markers present",
                    "severity": "high",
                    "evidence": [
                        {
                            "kind": "file_path",
                            "path": "repobrain/github_flow.py",
                            "source": "patch_scan",
                        }
                    ],
                }
            ],
        }
    )
    md = render_review_markdown(
        review=review,
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={"route_final": "DEEP", "pass_count": 1},
    )

    assert "### ⚠️ Confirmed findings" in md
    assert "`repobrain/github_flow.py`" in md


def test_heuristic_signal_without_evidence_stays_out_of_confirmed_findings() -> None:
    review = validate_review_findings(
        {
            "summary_text": "Review summary.",
            "risk_items": [
                {
                    "message": "Possible secret leakage in patch",
                    "severity": "high",
                    "evidence": [],
                }
            ],
        }
    )
    md = render_review_markdown(
        review=review,
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={"route_final": "DEEP", "pass_count": 1},
    )

    assert "### ⚠️ Confirmed findings" not in md
    assert "### 🟡 Possible signals" in md
