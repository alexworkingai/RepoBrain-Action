from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_artifact_access_authorization_model_doc_exists() -> None:
    assert (ROOT / "docs/release/ARTIFACT_ACCESS_AUTHORIZATION_MODEL.md").exists()


def test_artifact_access_authorization_model_doc_covers_required_sections() -> None:
    text = _read("docs/release/ARTIFACT_ACCESS_AUTHORIZATION_MODEL.md").lower()

    for phrase in (
        "token_scope_not_ready",
        "github app installation token",
        "fine-grained personal access token",
        "classic pat",
        "github packages",
        "private release asset",
        "managed runtime",
        "selected sprint 88 path",
        "token permissions",
        "expiration and rotation",
        "source checkout avoidance",
        "rejected options",
    ):
        assert phrase in text


def test_artifact_access_authorization_model_doc_rejects_broad_pat_as_partner_default() -> None:
    text = _read("docs/release/ARTIFACT_ACCESS_AUTHORIZATION_MODEL.md").lower()

    assert "no broad pat as partner-ready default" in text or "not accepted as the partner-ready path" in text
    assert "actions: read" in text
    assert "artifa" in text
