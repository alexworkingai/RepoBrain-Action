from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_artifact_token_preflight_doc_covers_secret_scope_and_rotation() -> None:
    text = _read("docs/release/OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE.md").lower()

    assert "topocore_v6_artifact_token" in text
    assert "actions: read" in text
    assert "expiration" in text
    assert "rotate" in text
    assert "do not print the token value" in text


def test_artifact_token_preflight_steps_are_documented_without_source_checkout() -> None:
    architecture = _read("docs/architecture/SPRINT_89_OWNER_TOKEN_INSTALLED_PACKAGE_PROOF.md").lower()

    for phrase in (
        "list artifacts",
        "download artifact",
        "verify sha-256 sidecar",
        "install `topocore_v6-0.30.0-py3-none-any.whl`".lower(),
        "import `topocore_v6`".lower(),
        "source checkout avoided",
    ):
        assert phrase in architecture
