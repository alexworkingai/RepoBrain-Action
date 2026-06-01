from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_installed_package_decisive_proof_doc_keeps_result_explicit() -> None:
    text = _read("docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md").lower()

    assert "installed_package_live_proof_blocked" in text
    assert "owner_action_required_token_issuance" in text


def test_installed_package_decisive_proof_doc_does_not_claim_sprint89_rerun() -> None:
    text = _read("docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md").lower()

    assert "proof rerun:" in text
    assert "not attempted" in text
    assert "still absent" in text or "still missing" in text
    assert "does not claim live external installed-package success" in text
