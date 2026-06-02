from __future__ import annotations

from pathlib import Path

import pytest

from repobrain.doctor_status import build_doctor_report


def test_doctor_returns_pass_with_notes_for_justified_pr_comment_permission(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workflow = tmp_path / ".github" / "workflows" / "repobrain.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(
        "name: RepoBrain\n"
        "permissions:\n"
        "  contents: read\n"
        "  issues: write\n"
        "  pull-requests: write\n"
        "  checks: read\n"
        "  statuses: read\n"
        "  actions: read\n",
        encoding="utf-8",
    )
    docs_dir = tmp_path / "docs" / "partner"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "PARTNER_TESTING_SETUP.md").write_text(
        "pull-requests: write is only for PR command response comments.\nno patch/autofix\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_ACTION_PATH", str(tmp_path / "action"))
    monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
    monkeypatch.setenv("RB_TOPOCORE_V6_RUNTIME_MODE", "private_checkout")
    monkeypatch.setenv("RB_TOPOCORE_V6_LOCAL_PATH", "hidden")

    report = build_doctor_report(repo_root=tmp_path, query="", github_context={})

    assert report["overall_status"] == "PASS_WITH_NOTES"
    permission_check = next(item for item in report["checks"] if item["name"] == "Permissions baseline")
    assert permission_check["status"] == "PASS_WITH_NOTES"
    assert "pull-requests: write" in permission_check["detail"]
