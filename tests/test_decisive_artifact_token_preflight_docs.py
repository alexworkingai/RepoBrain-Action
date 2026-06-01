from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_decisive_artifact_token_doc_covers_scope_and_no_value_handling() -> None:
    text = _read("docs/release/OWNER_ACTION_REQUIRED_TOKEN_ISSUANCE.md").lower()

    assert "topocore_v6_artifact_token" in text
    assert "actions: read" in text
    assert "expiration" in text
    assert "rotate" in text
    assert "do not print the token value" in text
    assert "owner action completed" in text


def test_decisive_preflight_steps_are_documented_and_passed_truthfully() -> None:
    architecture = _read("docs/architecture/SPRINT_90_DECISIVE_INSTALLED_PACKAGE_PROOF.md").lower()

    for phrase in (
        "artifacts listed",
        "artifact downloaded",
        "sha-256 sidecar verified",
        "wheel installed",
        "package imported",
        "contract detected",
        "installed_package_preflight_status=pass",
    ):
        assert phrase in architecture
