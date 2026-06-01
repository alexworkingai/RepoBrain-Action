from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_owner_action_required_token_doc_exists() -> None:
    assert (ROOT / "docs/release/OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE.md").exists()


def test_owner_action_required_token_doc_covers_secret_name_and_minimum_scope() -> None:
    text = _read("docs/release/OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE.md").lower()

    assert "topocore_v6_artifact_token" in text
    assert "actions: read" in text
    assert "alexworkingai/topocore" in text
    assert "expiration" in text
    assert "owner action required" in text


def test_owner_action_required_token_doc_has_no_token_value_and_rejects_broad_pat() -> None:
    text = _read("docs/release/OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE.md")
    lowered = text.lower()

    assert "ghp_" not in text
    assert "github_pat_" not in text
    assert "broad classic pat" in lowered or "no broad" in lowered
    assert "no source-repo collaborator access" in lowered
