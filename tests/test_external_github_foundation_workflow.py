from __future__ import annotations

from pathlib import Path


def test_external_github_foundation_workflow_is_bounded_and_artifact_complete() -> None:
    workflow = Path(".github/workflows/repobrain_external_foundation.yml").read_text(encoding="utf-8")

    assert "name: RepoBrain External GitHub Foundation" in workflow
    assert "workflow_call:" in workflow
    assert "caller_event_name:" in workflow
    assert "Resolve external GitHub foundation command boundary" in workflow
    assert 'if [[ "$cmd" == "help" || "$cmd" == "ask" ]]; then' in workflow
    assert "Post unsupported command boundary comment" in workflow
    assert "supports only `/repobrain help` and `/repobrain ask`" in workflow
    assert "uses: alexworkingai/RepoBrain-Action@main" in workflow
    assert "GITHUB_EVENT_NAME: ${{ inputs.caller_event_name }}" in workflow
    assert "Generate external install readiness artifacts" in workflow
    assert "Upload RepoBrain audit artifact" in workflow
    assert "Upload RepoBrain diagnostic summary artifact" in workflow
    assert "Upload RepoBrain TKYA evidence pack artifact" in workflow
    assert "Upload RepoBrain install readiness artifacts" in workflow


def test_external_github_foundation_template_uses_reusable_workflow_call() -> None:
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


def test_external_mode_doc_describes_github_foundation_boundary() -> None:
    text = Path("docs/EXTERNAL_MODE.md").read_text(encoding="utf-8")

    assert "External GitHub Mode Foundation (Third-Party)" in text
    assert "supported: `/repobrain help`, `/repobrain doctor`, `/repobrain ask ...`, `/repobrain review` (bounded read-only Review v1), `/repobrain fix` (bounded Fix-Lite suggestion-only)" in text
    assert "unsupported (explicit block): out-of-contract commands" in text
    assert "docs/packaging/repobrain_external_github_foundation_template.yml" in text
