from __future__ import annotations

import json
from pathlib import Path

from repobrain.commands import parse_command
from repobrain.github_flow import _build_status_markdown, get_last_audit, run_github_flow


def _pr_event(tmp_path: Path, body: str) -> Path:
    payload = {
        "issue": {
            "number": 48,
            "pull_request": {"url": "https://api.github.com/repos/o/r/pulls/48"},
        },
        "pull_request": {
            "head": {"sha": "abc", "ref": "feature", "repo": {"full_name": "owner/repo"}},
            "base": {"sha": "def", "ref": "main", "repo": {"full_name": "owner/repo"}},
        },
        "comment": {"body": body, "id": 18, "user": {"login": "alice"}},
    }
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(payload), encoding="utf-8")
    return event_path


def test_parse_status_command() -> None:
    assert parse_command("/repobrain status") == {"cmd": "status", "query": ""}
    assert parse_command("/repobrain status Focus on runtime truth.") == {
        "cmd": "status",
        "query": "Focus on runtime truth.",
    }


def test_issue_status_is_supported_and_includes_version_policy_and_commands() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    audit: dict[str, object] = {}

    markdown = _build_status_markdown(
        repo_root=repo_root,
        query="",
        tky_mode="local",
        github_context_seed={},
        audit=audit,
    )

    assert "# RepoBrain Status" in markdown
    assert "RepoBrain version:" in markdown
    assert "## Command surface" in markdown
    assert "## Backend policy" in markdown
    assert "## Safety policy" in markdown
    assert "/repobrain audit" in markdown
    assert "/repobrain doctor" in markdown
    assert "/repobrain status" in markdown
    assert "/repobrain score" in markdown
    assert "no v5 fallback" in markdown.lower()
    assert "no patch/autofix" in markdown.lower()
    assert audit["route_final"] == "STATUS"
    assert audit["resolved_backend"] == "not_applicable"
    assert audit["fallback_reason"] == "status_report_only"


def test_pr_status_is_supported() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    audit: dict[str, object] = {}
    markdown = _build_status_markdown(
        repo_root=repo_root,
        query="Focus on PR runtime.",
        tky_mode="local",
        github_context_seed={
            "is_pr": True,
            "pr_number": 48,
            "repository": "owner/repo",
            "head_repo_full_name": "owner/repo",
            "pr_same_repo": True,
        },
        audit=audit,
    )

    assert "Event context: `pull_request #48`" in markdown
    assert audit["route_final"] == "STATUS"


def test_run_github_flow_status_dry_run_records_report_only_backend_and_no_mutation() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain status",
        issue_number=None,
    )
    audit = get_last_audit()

    assert status == "DRY_RUN_OK"
    assert audit["command"] == "status"
    assert audit["resolved_backend"] == "not_applicable"
    assert audit["fallback_reason"] == "status_report_only"
    assert audit["patch_applied"] is False
    assert audit["files_modified"] is False


def test_status_does_not_require_topocore_import_or_expose_secrets(monkeypatch: object) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.delenv("RB_TOPOCORE_V6_LOCAL_PATH", raising=False)
    monkeypatch.delenv("TOPOCORE_V6_REPO_TOKEN", raising=False)

    markdown = _build_status_markdown(
        repo_root=repo_root,
        query="",
        tky_mode="local",
        github_context_seed={},
        audit={},
    )

    assert "TOPOCORE_V6_REPO_TOKEN" not in markdown
    assert "github_pat_" not in markdown
    assert "ghp_" not in markdown


def test_pr_status_dry_run_supported_from_event_payload(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    event_path = _pr_event(tmp_path, "/repobrain status")

    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="",
        issue_number=None,
        event_path=event_path,
    )

    assert status == "DRY_RUN_OK"
