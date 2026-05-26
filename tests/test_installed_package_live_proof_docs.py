from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_installed_package_live_proof_doc_exists() -> None:
    assert (ROOT / "docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md").exists()


def test_installed_package_live_proof_doc_states_result_or_blocker() -> None:
    text = _read("docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md").lower()

    assert "installed_package_live_proof_passed" in text or "installed_package_live_proof_failed" in text or "installed_package_live_proof_blocked" in text
    assert "workflow mode" in text
    assert "source checkout avoided" in text
    assert "private_checkout" in text


def test_partner_docs_align_with_installed_package_preference() -> None:
    combined = "\n".join(
        _read(path)
        for path in (
            "docs/partner/PARTNER_TESTING_SETUP.md",
            "docs/partner/PARTNER_RUNTIME_ACCESS_RUNBOOK.md",
            "docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md",
        )
    ).lower()

    assert "installed private package" in combined or "installed_private_package" in combined
    assert "beta-only fallback" in combined or "beta-only" in combined
