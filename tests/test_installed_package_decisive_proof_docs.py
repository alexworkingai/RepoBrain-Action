from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_installed_package_decisive_proof_doc_keeps_result_explicit() -> None:
    text = _read("docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md").lower()

    assert "installed_package_live_proof_passed" in text
    assert "owner_action_required_token_issuance" in text


def test_installed_package_decisive_proof_doc_preserves_historical_trace_and_current_success() -> None:
    text = _read("docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md").lower()

    assert "sprint 89 correctly stopped because the required secret was absent" in text
    assert "sprint 90 completed the decisive external installed-package runtime proof" in text
    assert "does not claim a public switch" in text
