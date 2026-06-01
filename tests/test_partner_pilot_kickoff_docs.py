from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_partner_pilot_docs_exist() -> None:
    assert (ROOT / "docs/partner/PILOT_KICKOFF_PLAN.md").exists()
    assert (ROOT / "docs/partner/PARTNER_ONBOARDING_EMAIL_TEMPLATE.md").exists()


def test_partner_pilot_docs_keep_installed_package_preferred() -> None:
    kickoff = _read("docs/partner/PILOT_KICKOFF_PLAN.md").lower()
    setup = _read("docs/partner/PARTNER_TESTING_SETUP.md").lower()
    runbook = _read("docs/partner/PARTNER_RUNTIME_ACCESS_RUNBOOK.md").lower()

    combined = "\n".join((kickoff, setup, runbook))
    assert "installed_package" in combined or "installed_private_package" in combined
    assert "private_checkout" in combined
    assert "no shared broad pat" in combined
    assert "per-partner" in combined


def test_partner_onboarding_email_has_no_marketplace_or_partnership_claim() -> None:
    text = _read("docs/partner/PARTNER_ONBOARDING_EMAIL_TEMPLATE.md").lower()
    assert "marketplace" not in text
    assert "partnership" not in text
    assert "microsoft" not in text
