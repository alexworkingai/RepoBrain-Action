from __future__ import annotations

from repobrain.pr_impact import build_pr_impact_facts


def test_docs_smoke_pr_is_classified_as_docs_only_low_risk() -> None:
    facts = build_pr_impact_facts(
        github_context={
            "is_pr": True,
            "pr_number": 41,
            "changed_files": ["docs/repobrain_manual_pr_smoke.md"],
        }
    )

    assert facts["changed_files"] == ["docs/repobrain_manual_pr_smoke.md"]
    assert facts["change_type"] == "docs-only"
    assert facts["docs_only"] is True
    assert facts["behavior_affecting"] is False
    assert facts["architecture_runtime_impact"] == "no direct impact"
    assert facts["security_posture_impact"] == "no direct impact"
    assert facts["risk_level"] == "LOW"

