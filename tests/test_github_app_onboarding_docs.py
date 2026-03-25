from __future__ import annotations

from pathlib import Path


def test_github_app_setup_doc_covers_selected_repo_and_readiness_statuses() -> None:
    text = Path("docs/onboarding/github_app_setup.md").read_text(encoding="utf-8")

    assert "GitHub App-first" in text
    assert "selected repositories" in text.lower()
    assert "RB_GH_APP_ID" in text
    assert "RB_GH_APP_INSTALLATION_ID" in text
    assert "RB_GH_APP_PRIVATE_KEY" in text
    assert "RB_GH_APP_REPOSITORY_SELECTION" in text
    assert "RB_GH_APP_SELECTED_REPOS" in text
    assert "READY" in text
    assert "MISSING_PERMISSION" in text
    assert "MISSING_CONFIG" in text
    assert "UNSUPPORTED_SETUP" in text


def test_permissions_doc_covers_required_workflow_permissions() -> None:
    text = Path("docs/onboarding/permissions.md").read_text(encoding="utf-8")

    assert "checks: write" in text
    assert "issues: write" in text
    assert "pull-requests: write" in text
    assert "statuses: read" in text
    assert "actions: read" in text
