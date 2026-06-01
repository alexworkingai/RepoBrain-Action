from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_post_switch_ready_status_is_now_claimed_explicitly() -> None:
    combined = "\n".join(
        (
            _read("docs/architecture/SPRINT_91_PUBLIC_SWITCH_PARTNER_PILOT.md"),
            _read("docs/release/PUBLIC_VISIBILITY_APPROVAL_CHECKLIST.md"),
            _read("docs/release/PUBLIC_READINESS_ASSESSMENT.md"),
        )
    )
    assert "PUBLIC_VISIBILITY_SWITCHED_PARTNER_PILOT_READY" in combined
    assert "APPROVED_FOR_PUBLIC_PARTNER_TESTING" in combined


def test_docs_do_not_claim_marketplace_or_topocore_source_distribution() -> None:
    combined = "\n".join(
        (
            _read("docs/architecture/SPRINT_91_PUBLIC_SWITCH_PARTNER_PILOT.md").lower(),
            _read("docs/partner/PILOT_KICKOFF_PLAN.md").lower(),
            _read("docs/partner/PARTNER_ONBOARDING_EMAIL_TEMPLATE.md").lower(),
        )
    )
    assert "marketplace" in combined
    assert "topocore source" in combined
    assert "not distributed" in combined or "private" in combined
