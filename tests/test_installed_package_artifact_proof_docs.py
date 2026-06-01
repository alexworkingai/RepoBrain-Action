from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_installed_package_artifact_proof_doc_exists() -> None:
    assert (ROOT / "docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md").exists()


def test_installed_package_artifact_proof_doc_states_explicit_result() -> None:
    text = _read("docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md").lower()

    assert (
        "installed_package_live_proof_passed" in text
        or "installed_package_live_proof_failed" in text
        or "installed_package_live_proof_blocked" in text
    )


def test_installed_package_artifact_proof_doc_aligns_with_blocked_state() -> None:
    proof = _read("docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md").lower()
    readiness = _read("docs/release/PUBLIC_READINESS_ASSESSMENT.md").lower()

    if "installed_package_live_proof_passed" in proof:
        assert "private_checkout avoided: `yes`" in proof
        assert "source checkout avoided: `yes`" in proof
        assert "auto / v6" in proof
    else:
        assert "owner_action_required_token_issuance" in proof
        assert "token_scope_not_ready" in proof
        assert "owner_action_required_token_issuance" in readiness
        assert "does not claim live external installed-package success" in proof
