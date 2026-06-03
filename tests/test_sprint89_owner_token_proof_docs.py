from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _public_readiness_next_step, _read_public_readiness_status


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sprint89_architecture_doc_exists() -> None:
    assert (ROOT / "docs/architecture/SPRINT_89_OWNER_TOKEN_INSTALLED_PACKAGE_PROOF.md").exists()


def test_sprint89_docs_keep_owner_token_gate_explicit() -> None:
    architecture = _read("docs/architecture/SPRINT_89_OWNER_TOKEN_INSTALLED_PACKAGE_PROOF.md").lower()
    readiness = _read("docs/release/PUBLIC_READINESS_ASSESSMENT.md").lower()
    owner = _read("docs/release/OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE.md").lower()

    combined = "\n".join((architecture, readiness, owner))
    assert "topocore_v6_artifact_token" in combined
    assert "owner_action_required_token_issuance" in combined
    assert "historical" in combined or "still absent" in architecture or "missing" in architecture


def test_sprint89_public_readiness_parser_moves_to_public_switch_complete() -> None:
    status = _read_public_readiness_status(ROOT)

    assert status == "SPRINT_92D_IMPLEMENTATION_MERGED_LIVE_RETEST_FINDINGS_PENDING_FIX"
    next_step = _public_readiness_next_step(status).lower()
    assert "partner pilot" in next_step or "partner onboarding" in next_step
