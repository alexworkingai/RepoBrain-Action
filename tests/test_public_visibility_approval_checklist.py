from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_public_visibility_approval_checklist_exists() -> None:
    assert (ROOT / 'docs/release/PUBLIC_VISIBILITY_APPROVAL_CHECKLIST.md').exists()


def test_public_visibility_approval_checklist_states_private_owner_approval_and_marketplace_truth() -> None:
    text = _read('docs/release/PUBLIC_VISIBILITY_APPROVAL_CHECKLIST.md').lower()

    assert 'repobrain-action is still private' in text
    assert 'not switched in sprint 86' in text
    assert 'marketplace work is not started' in text
    assert 'explicit owner approval' in text
    assert 'public_blocked_by_runtime_proof' in text or 'public_visibility_approval_pack_ready' in text or 'public_ready_pending_owner_approval' in text


def test_public_visibility_approval_checklist_covers_decisions_and_gates() -> None:
    text = _read('docs/release/PUBLIC_VISIBILITY_APPROVAL_CHECKLIST.md').lower()

    for phrase in (
        'owner approves public visibility',
        'owner approves selected partner testing',
        'owner approves rc tag creation',
        'owner approves partner runtime/token issuance',
        'technical readiness',
        'security readiness',
        'legal and licensing readiness',
        'partner readiness',
        'approved_for_public_partner_testing',
        'approval_pending',
        'blocked_by_security',
        'blocked_by_docs',
        'blocked_by_runtime',
        'blocked_by_legal',
        'blocked_by_validation',
    ):
        assert phrase in text
