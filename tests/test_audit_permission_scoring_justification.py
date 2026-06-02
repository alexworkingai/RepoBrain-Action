from __future__ import annotations

from pathlib import Path

from repobrain.audit_scoring import score_repository_audit


def test_justified_pr_comment_permission_is_not_top_critical_blocker(tmp_path: Path) -> None:
    workflow = tmp_path / ".github" / "workflows" / "repobrain.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(
        "name: repobrain\n"
        "on:\n"
        "  issue_comment:\n"
        "permissions:\n"
        "  contents: read\n"
        "  issues: write\n"
        "  pull-requests: write\n"
        "  checks: read\n"
        "jobs:\n"
        "  qa:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: alexworkingai/RepoBrain-Action@main\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Repo\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "troubleshooting").mkdir()
    (tmp_path / "docs" / "troubleshooting" / "REPOBRAIN_EXTERNAL_TROUBLESHOOTING.md").write_text(
        "pull-requests: write is only for PR command response comments.\n"
        "no patch/autofix.\n"
        "no branch/commit/pr created by RepoBrain.\n",
        encoding="utf-8",
    )

    report = score_repository_audit(repo_root=tmp_path)
    blocker_titles = [str(item.get("title", "")) for item in report["critical_blockers"]]
    improvement_titles = [str(item.get("title", "")) for item in report["top_improvements"]]

    assert "Workflow permissions include `pull-requests: write`" not in blocker_titles
    assert "Document and monitor PR comment response permission." in improvement_titles


def test_broad_write_permissions_still_penalize_and_block(tmp_path: Path) -> None:
    workflow = tmp_path / ".github" / "workflows" / "repobrain.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(
        "name: repobrain\n"
        "on:\n"
        "  pull_request_target:\n"
        "permissions:\n"
        "  contents: write\n"
        "  issues: write\n"
        "  pull-requests: write\n"
        "  checks: write\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Repo\n", encoding="utf-8")

    report = score_repository_audit(repo_root=tmp_path)
    blocker_titles = [str(item.get("title", "")) for item in report["critical_blockers"]]

    assert "Workflow uses `pull_request_target`" in blocker_titles
    assert "Workflow permissions include `contents: write`" in blocker_titles
