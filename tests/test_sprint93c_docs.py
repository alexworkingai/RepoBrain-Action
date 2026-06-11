from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8").lower()


def test_quickstart_preserves_no_owner_token_and_no_manual_registration() -> None:
    text = _read("docs/onboarding/PARTNER_SELF_SERVICE_QUICKSTART.md")

    assert "no repobrain owner-generated secret" in text or "no repobrain owner token" in text
    assert "no manual partner registration" in text
    assert "do not install or download topocore" in text
    assert "fully live" in text
    assert "sprint 93d now wires" in text or "sprint 93d now wires the end-to-end" in text
    assert "sprint 93e" in text


def test_architecture_note_documents_93c_boundaries() -> None:
    text = _read("docs/architecture/SPRINT_93C_HOSTED_API_TRUST_AND_PROVISIONING.md")

    assert "post /v1/github/actions/audit" in text
    assert "server-side github oidc verification" in text
    assert "automatic tenant provisioning" in text
    assert "default partner-pilot quota boundary" in text
    assert "private hosted topocore boundary" in text
    assert "not claimed" in text


def test_readme_reflects_93c_without_full_live_claim() -> None:
    text = _read("README.md")

    assert "sprint 93c hosted-boundary truth" in text
    assert "tenant auto-provisioning" in text
    assert "sprint 93d end-to-end self-service truth" in text
    assert "deferred to sprint 93e" in text or "remain deferred to sprint 93e" in text
