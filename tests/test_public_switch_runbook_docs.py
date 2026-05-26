from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_public_switch_runbook_doc_exists() -> None:
    assert (ROOT / 'docs/release/PUBLIC_VISIBILITY_SWITCH_RUNBOOK.md').exists()


def test_public_switch_runbook_states_not_executed_in_sprint_85_and_has_required_sections() -> None:
    text = _read('docs/release/PUBLIC_VISIBILITY_SWITCH_RUNBOOK.md').lower()

    assert 'not executed in sprint 85' in text
    assert 'pre-switch checks' in text
    assert 'immediate post-switch checks' in text
    assert 'rollback caveat' in text
    assert 'explicit owner approval' in text


def test_active_public_approval_docs_do_not_claim_public_switch_marketplace_or_unsafe_approval() -> None:
    combined = '\n'.join(
        _read(path) for path in (
            'README.md',
            'docs/release/PUBLIC_VISIBILITY_APPROVAL_CHECKLIST.md',
            'docs/release/RC_TAG_AND_PINNING_PLAN.md',
            'docs/release/FINAL_COMMAND_SURFACE_MATRIX.md',
            'docs/release/PUBLIC_VISIBILITY_SWITCH_RUNBOOK.md',
            'docs/release/PARTNER_TESTING_READINESS.md',
            'docs/release/PUBLIC_READINESS_ASSESSMENT.md',
            'docs/release/RELEASE_CANDIDATE_CHECKLIST.md',
            'docs/release/RELEASE_NOTES_RC1.md',
            'docs/partner/PARTNER_TESTING_SETUP.md',
            'docs/partner/PARTNER_RUNTIME_ACCESS_RUNBOOK.md',
            'docs/partner/PARTNER_FEEDBACK_TEMPLATE.md',
            'docs/partner/PARTNER_SECURITY_NOTES.md',
            'docs/onboarding/INSTALL_REPOBRAIN_EXTERNAL_REPO.md',
            'docs/troubleshooting/REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md',
        )
    ).lower()

    assert 'repo is already public' not in combined
    assert 'marketplace is ready' not in combined
    assert 'microsoft approved' not in combined
    assert 'microsoft partnership' not in combined
    assert 'approved to merge' not in combined
    assert 'security approved' not in combined
    assert 'no active v5 path' not in combined or 'no v5' in combined
    assert 'repobrain-community' in combined
    assert 'no patch/autofix' in combined
    assert 'topocore source rights' in combined
    for forbidden in ('ghp_', 'github_pat_', 'begin private key', 'd:\\ariadna', 'c:\\users', '/mnt/data'):
        assert forbidden not in combined


def test_external_workflow_baseline_remains_read_mostly_and_no_pull_request_target() -> None:
    text = _read('docs/examples/repobrain_external_pilot_workflow.yml').lower()

    assert 'pull_request_target' not in text
    assert 'contents: write' not in text
    assert 'checks: write' not in text
    assert 'pull-requests: write' not in text
    assert 'contents: read' in text
    assert 'checks: read' in text
    assert 'pull-requests: read' in text
