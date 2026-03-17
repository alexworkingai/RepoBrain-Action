from __future__ import annotations

from repobrain.review_validator import validate_review_findings


def test_high_severity_claim_without_evidence_is_downgraded() -> None:
    review = {
        "summary_text": "2 files changed, appears low risk.",
        "risk_items": [
            {
                "message": "Possible secret leakage in patch",
                "severity": "high",
                "evidence": [],
            }
        ],
        "suggested_tests": ["Run ruff check .", "Run pytest -q"],
    }

    validated = validate_review_findings(review)

    assert validated["risk_level"] != "high"
    assert not any("secret leakage" in item.lower() for item in validated["possible_signals"])
    assert any(
        "missing concrete secret evidence" in item.lower()
        for item in validated.get("informational_notes", [])
    )
    assert all("secret leakage" not in item.lower() for item in validated["confirmed_findings"])


def test_evidence_backed_high_severity_claim_stays_confirmed() -> None:
    review = {
        "summary_text": "1 file changed, high risk due to conflict markers.",
        "risk_items": [
            {
                "message": "Merge conflict markers present",
                "severity": "high",
                "evidence": [{"kind": "patch", "path": "repobrain/github_flow.py", "source": "patch_scan"}],
            }
        ],
        "suggested_tests": ["Resolve merge conflict markers and re-run /repobrain review"],
    }

    validated = validate_review_findings(review)

    assert validated["risk_level"] == "high"
    assert any("Merge conflict markers present" in item for item in validated["confirmed_findings"])
    assert validated["possible_signals"] == []


def test_summary_and_risk_level_are_consistent_after_validation() -> None:
    review = {
        "summary_text": "Changes appear low risk.",
        "risk_items": [
            {
                "message": "Security-sensitive area changed",
                "severity": "high",
                "evidence": [{"kind": "file_path", "path": "repobrain/security.py", "source": "path_rule"}],
            }
        ],
    }

    validated = validate_review_findings(review)

    assert validated["risk_level"] == "high"
    assert "low risk" not in validated["summary_text"].lower()


def test_docs_only_secret_wording_is_not_promoted_to_possible_signal() -> None:
    review = {
        "summary_text": "Docs update.",
        "risk_items": [
            {
                "message": "Possible secret leakage in patch",
                "severity": "high",
                "evidence": [{"kind": "patch", "path": "docs/security.md", "source": "patch_scan"}],
            }
        ],
    }

    validated = validate_review_findings(review)

    assert not any("secret leakage" in item.lower() for item in validated["possible_signals"])
    assert any("docs-only security wording" in item.lower() for item in validated["informational_notes"])
