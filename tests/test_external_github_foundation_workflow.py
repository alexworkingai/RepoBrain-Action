from __future__ import annotations

from pathlib import Path


def test_external_github_foundation_template_uses_public_reusable_workflow() -> None:
    template = Path("docs/packaging/repobrain_external_github_foundation_template.yml").read_text(encoding="utf-8")

    assert "name: RepoBrain External GitHub Mode" in template
    assert "issue_comment:" in template
    assert "workflow_dispatch:" in template
    assert "uses: alexworkingai/repobrain-community/.github/workflows/repobrain_external_foundation.yml@main" in template
    assert "comment_text: ${{ github.event_name == 'workflow_dispatch' && inputs.comment_text || github.event.comment.body }}" in template
    assert "issue_number: ${{ github.event_name == 'workflow_dispatch' && inputs.issue_number || github.event.issue.number }}" in template
    assert "workflow_path: .github/workflows/repobrain_external.yml" in template
    assert "caller_event_name: ${{ github.event_name }}" in template
    assert "secrets: inherit" in template


def test_external_mode_doc_describes_current_github_foundation_boundary() -> None:
    text = Path("docs/EXTERNAL_MODE.md").read_text(encoding="utf-8")

    assert "External GitHub Mode Foundation (Third-Party)" in text
    assert "supported: `/repobrain help`, `/repobrain doctor`, `/repobrain ask ...`, `/repobrain review` (bounded read-only Review Candidate), `/repobrain fix` (bounded Fix-Lite Candidate manual patch suggestion)" in text
    assert "unsupported (explicit block): out-of-contract commands" in text
    assert "docs/packaging/repobrain_external_github_foundation_template.yml" in text


def test_packaging_doc_describes_review_candidate_and_fix_lite_candidate() -> None:
    text = Path("docs/packaging/EXTERNAL_GITHUB_FOUNDATION.md").read_text(encoding="utf-8")

    assert "/repobrain review" in text
    assert "bounded read-only Review Candidate" in text
    assert "/repobrain fix" in text
    assert "bounded Fix-Lite Candidate manual patch suggestion" in text
    assert "Fix-Lite Candidate remains manual-only" in text
