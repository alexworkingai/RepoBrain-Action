from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_sprint_84_architecture_doc_exists() -> None:
    assert (ROOT / 'docs/architecture/SPRINT_84_TOPOCORE_RUNTIME_DISTRIBUTION_GATE.md').exists()


def test_public_ready_docs_have_explicit_distribution_and_public_readiness_decisions() -> None:
    readiness = _read('docs/release/PUBLIC_READINESS_ASSESSMENT.md').lower()
    strategy = _read('docs/release/PRIVATE_TOPOCORE_DISTRIBUTION_STRATEGY.md').lower()
    checklist = _read('docs/release/RELEASE_CANDIDATE_CHECKLIST.md').lower()

    assert 'public_blocked_by_runtime_proof' in readiness
    assert 'public_ready_pending_owner_approval' in readiness
    assert 'installed_private_package_selected' in strategy
    assert 'readable' in strategy
    assert 'private_checkout' in strategy
    assert 'beta-only' in strategy
    assert 'public-ready distribution gate' in checklist


def test_public_ready_docs_do_not_claim_public_switch_marketplace_or_source_exposure() -> None:
    combined = '\n'.join(
        _read(path) for path in (
            'docs/release/PUBLIC_READINESS_ASSESSMENT.md',
            'docs/release/PRIVATE_TOPOCORE_DISTRIBUTION_STRATEGY.md',
            'docs/release/RELEASE_CANDIDATE_CHECKLIST.md',
            'docs/release/RELEASE_NOTES_RC1.md',
            'docs/security/TOPOCORE_V6_HIGH_SECURITY_POLICY.md',
            'docs/architecture/SPRINT_84_TOPOCORE_RUNTIME_DISTRIBUTION_GATE.md',
        )
    ).lower()

    assert 'repo brain-action is public' not in combined
    assert 'marketplace is ready' not in combined
    assert 'topocore source is distributed safely' not in combined
    assert 'safe-to-merge approval' not in combined
    assert 'security approval' in combined
    assert 'no patch/autofix' in combined
    assert 'no v5' in combined
    assert 'no repobrain-community' in combined
