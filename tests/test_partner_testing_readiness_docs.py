from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_partner_testing_readiness_doc_exists() -> None:
    assert (ROOT / 'docs/release/PARTNER_TESTING_READINESS.md').exists()


def test_partner_testing_readiness_doc_states_private_and_owner_approval() -> None:
    text = _read('docs/release/PARTNER_TESTING_READINESS.md').lower()

    assert 'repobrain-action remains private in sprint 86' in text
    assert 'explicit owner approval' in text
    assert 'marketplace work has not started' in text or 'marketplace' in text


def test_partner_testing_readiness_doc_states_runtime_mode_and_security_model() -> None:
    text = _read('docs/release/PARTNER_TESTING_READINESS.md').lower()

    assert 'installed_private_package' in text
    assert 'private_checkout' in text
    assert 'beta-only' in text
    assert 'topocore source license' in text or 'no topocore source license' in text
    assert 'no shared broad pat' in text
    assert 'per-partner token' in text or 'per-partner' in text
    assert 'rotation' in text
    assert 'revocation' in text
