from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_partner_test_pack_docs_exist() -> None:
    for path in (
        'docs/partner/PARTNER_TESTING_SETUP.md',
        'docs/partner/PARTNER_RUNTIME_ACCESS_RUNBOOK.md',
        'docs/partner/PARTNER_FEEDBACK_TEMPLATE.md',
        'docs/partner/PARTNER_SECURITY_NOTES.md',
    ):
        assert (ROOT / path).exists()


def test_partner_test_pack_docs_state_runtime_model_and_partner_security_truth() -> None:
    setup = _read('docs/partner/PARTNER_TESTING_SETUP.md').lower()
    runbook = _read('docs/partner/PARTNER_RUNTIME_ACCESS_RUNBOOK.md').lower()
    security = _read('docs/partner/PARTNER_SECURITY_NOTES.md').lower()

    assert 'installed_private_package' in setup
    assert 'private_checkout' in setup
    assert 'beta-only fallback' in setup
    assert 'no topocore source rights' in security
    assert 'no patch/autofix' in security
    assert 'no branch/commit/pr creation by repobrain' in security
    assert 'byo-llm' in setup or 'user-paid model' in setup
    assert 'plain python wheel may still contain readable implementation' in runbook


def test_partner_test_pack_docs_require_scoped_credentials_and_no_shared_broad_pat() -> None:
    combined = '\n'.join(
        _read(path) for path in (
            'docs/partner/PARTNER_TESTING_SETUP.md',
            'docs/partner/PARTNER_RUNTIME_ACCESS_RUNBOOK.md',
            'docs/partner/PARTNER_SECURITY_NOTES.md',
        )
    ).lower()

    assert 'per-partner token' in combined or 'per-partner scoped credential' in combined
    assert 'read-only' in combined
    assert 'expiration' in combined
    assert 'rotation' in combined
    assert 'revocation' in combined
    assert 'no shared broad pat' in combined
    assert 'owner token' in combined
    assert 'source license' in combined
