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


def test_decisive_preflight_steps_are_documented_and_not_falsely_passed() -> None:
    architecture = _read("docs/architecture/SPRINT_90_DECISIVE_INSTALLED_PACKAGE_PROOF.md").lower()

    for phrase in (
        "list artifacts",
        "download artifact",
        "verify sha-256 sidecar",
        "install wheel",
        "detect `topocore.audit_score.v1`".lower(),
        "the required secret was still absent at startup",
        "no artifact preflight was rerun",
    ):
        assert phrase in architecture
