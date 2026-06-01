from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _public_readiness_next_step, _read_public_readiness_status


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint90_architecture_doc_exists() -> None:
    assert (ROOT / "docs/architecture/SPRINT_90_DECISIVE_INSTALLED_PACKAGE_PROOF.md").exists()


def test_sprint90_docs_keep_decisive_proof_blocked_when_secret_missing() -> None:
    architecture = _read("docs/architecture/SPRINT_90_DECISIVE_INSTALLED_PACKAGE_PROOF.md").lower()
    readiness = _read("docs/release/PUBLIC_READINESS_ASSESSMENT.md").lower()
    proof = _read("docs/release/INSTALLED_PACKAGE_LIVE_PROOF.md").lower()

    combined = "\n".join((architecture, readiness, proof))
    assert "topocore_v6_artifact_token" in combined
    assert "owner_action_required_token_issuance" in combined
    assert "not rerun" in combined or "not attempted" in combined


def test_sprint90_public_readiness_parser_stays_blocked() -> None:
    status = _read_public_readiness_status(ROOT)

    assert status == "OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE"
    next_step = _public_readiness_next_step(status).lower()
    assert "minimum-scope artifact credential" in next_step
