from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_installed_package_live_proof_status_is_explicit() -> None:
    text = _read("docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md").lower()

    assert any(
        token in text
        for token in (
            "installed_package_live_proof_passed",
            "installed_package_live_proof_blocked",
            "installed_package_live_proof_failed",
        )
    )


def test_installed_package_live_proof_doc_tracks_checkout_avoidance_and_backend_truth() -> None:
    text = _read("docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md").lower()

    assert "private topocore source checkout avoided" in text or "private_checkout avoided" in text
    assert "source checkout avoided" in text
    assert "backend" in text


def test_public_readiness_alignment_matches_proof_outcome() -> None:
    readiness = _read("docs/release/PUBLIC_READINESS_ASSESSMENT.md").lower()
    proof = _read("docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md").lower()

    if "installed_package_live_proof_passed" in proof:
        assert "public_switch_ready_after_runtime_proof" in readiness
    else:
        assert (
            "public_blocked_by_runtime_proof" in readiness
            or "public_blocked_by_package_delivery" in readiness
            or "public_blocked_by_token_scope" in readiness
        )
