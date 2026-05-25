from __future__ import annotations

import json
from pathlib import Path

from repobrain.commands import parse_command
from repobrain.github_flow import _build_doctor_markdown, get_last_audit, run_github_flow


def _pr_event(tmp_path: Path, body: str, *, fork: bool) -> Path:
    head_repo = "someone/forked-repo" if fork else "owner/repo"
    payload = {
        "issue": {
            "number": 64,
            "pull_request": {"url": "https://api.github.com/repos/o/r/pulls/64"},
        },
        "pull_request": {
            "head": {"sha": "abc", "ref": "feature", "repo": {"full_name": head_repo}},
            "base": {"sha": "def", "ref": "main", "repo": {"full_name": "owner/repo"}},
        },
        "comment": {"body": body, "id": 18, "user": {"login": "alice"}},
    }
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(payload), encoding="utf-8")
    return event_path


def test_parse_doctor_command() -> None:
    assert parse_command("/repobrain doctor") == {"cmd": "doctor", "query": ""}
    assert parse_command("/repobrain doctor Focus on permissions.") == {
        "cmd": "doctor",
        "query": "Focus on permissions.",
    }


def test_issue_doctor_is_supported_and_includes_required_sections(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path
    workflow = repo_root / ".github" / "workflows" / "repobrain.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(
        "name: repobrain\non:\n  issue_comment:\npermissions:\n  contents: read\n  issues: write\n  pull-requests: read\n  checks: read\n  statuses: read\n  actions: read\njobs:\n  qa:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: alexworkingai/RepoBrain-Action@main\n        with:\n          token: ${{ secrets.TOPOCORE_V6_REPO_TOKEN }}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("RB_TOPOCORE_V6_LOCAL_PATH", "hidden")
    audit: dict[str, object] = {}

    markdown = _build_doctor_markdown(
        repo_root=repo_root,
        query="",
        tky_mode="local",
        github_context_seed={"repository": "owner/repo"},
        audit=audit,
    )

    assert "# RepoBrain Doctor" in markdown
    assert "Overall diagnostic status:" in markdown
    assert "## Diagnostic checks" in markdown
    assert "## Recommended fixes" in markdown
    assert "## Runtime and safety" in markdown
    assert "TOPOCORE_V6_REPO_TOKEN" in markdown
    assert "secret value" in markdown.lower()
    assert "no v5 fallback" in markdown.lower()
    assert "private_checkout is beta-only" in markdown.lower()
    assert "pull_request_target" in markdown
    assert audit["route_final"] == "DOCTOR"
    assert audit["resolved_backend"] == "not_applicable"
    assert audit["fallback_reason"] == "doctor_diagnostic_report"


def test_pr_doctor_supports_fork_context_when_available(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    event_path = _pr_event(tmp_path, "/repobrain doctor", fork=True)

    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="",
        issue_number=None,
        event_path=event_path,
    )
    audit = get_last_audit()

    assert status == "DRY_RUN_OK"
    assert audit["command"] == "doctor"
    assert audit["patch_applied"] is False
    assert audit["files_modified"] is False


def test_doctor_does_not_dump_env_or_expose_secret_values(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path
    workflow = repo_root / ".github" / "workflows" / "repobrain.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text("name: repobrain\non:\n  issue_comment:\n", encoding="utf-8")
    monkeypatch.setenv("TOPOCORE_V6_REPO_TOKEN", "super-secret-value")

    markdown = _build_doctor_markdown(
        repo_root=repo_root,
        query="",
        tky_mode="local",
        github_context_seed={},
        audit={},
    )

    assert "super-secret-value" not in markdown
    assert "GITHUB_TOKEN=" not in markdown
    assert "TOPOCORE_V6_REPO_TOKEN" in markdown


def test_run_github_flow_doctor_dry_run_records_report_only_backend() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain doctor",
        issue_number=None,
    )
    audit = get_last_audit()

    assert status == "DRY_RUN_OK"
    assert audit["command"] == "doctor"
    assert audit["resolved_backend"] == "not_applicable"
    assert audit["fallback_reason"] == "doctor_diagnostic_report"
    assert audit["pr_created"] is False
