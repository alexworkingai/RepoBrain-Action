from __future__ import annotations

from repobrain.review_validator import validate_review_findings


def test_duplicate_findings_are_collapsed_with_merged_evidence() -> None:
    review = {
        "summary_text": "Multiple workflow files changed.",
        "risk_items": [
            {
                "message": "CI/CD changed: verify workflows",
                "severity": "medium",
                "evidence": [{"kind": "file_path", "path": ".github/workflows/a.yml", "source": "path_rule"}],
            },
            {
                "message": "CI/CD changed: verify workflows",
                "severity": "medium",
                "evidence": [{"kind": "file_path", "path": ".github/workflows/b.yml", "source": "path_rule"}],
            },
        ],
    }

    validated = validate_review_findings(review)

    assert validated["confirmed_findings"] == []
    assert validated["risk_drivers"] == ["CI/CD changed: verify workflows"]
    assert int(validated["validation"]["confirmed_findings_count"]) == 0
    assert int(validated["validation"]["risk_drivers_count"]) == 1


def test_possible_wording_does_not_enter_confirmed_findings() -> None:
    review = {
        "summary_text": "Risk uncertain.",
        "risk_items": [
            {
                "message": "Possible checks disabled in critical path",
                "severity": "medium",
                "evidence": [{"kind": "file_path", "path": "repobrain/github_flow.py", "source": "path_rule"}],
            }
        ],
    }

    validated = validate_review_findings(review)

    assert validated["possible_signals"]
    assert all("Possible checks disabled" not in item for item in validated["confirmed_findings"])
