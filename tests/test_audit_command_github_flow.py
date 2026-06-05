from __future__ import annotations

import json
from pathlib import Path

from repobrain.commands import parse_command
from repobrain.github_flow import _build_audit_markdown, get_last_audit, run_github_flow


def _pr_event(tmp_path: Path, body: str) -> Path:
    payload = {
        "issue": {
            "number": 32,
            "pull_request": {"url": "https://api.github.com/repos/o/r/pulls/32"},
        },
        "comment": {"body": body, "id": 18, "user": {"login": "alice"}},
        "changed_files": [
            "docs/repobrain_audit_fixture.md",
            ".github/workflows/repobrain.yml",
        ],
        "files": [
            {"filename": "docs/repobrain_audit_fixture.md", "status": "modified"},
            {"filename": ".github/workflows/repobrain.yml", "status": "modified"},
        ],
        "diff_hunks": ["@@ -1 +1 @@\n-safe\n+safer\n"],
    }
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(payload), encoding="utf-8")
    return event_path


def test_parse_audit_commands() -> None:
    assert parse_command("/repobrain audit") == {"cmd": "audit", "query": ""}
    assert parse_command("/repobrain audit Focus on onboarding readiness.") == {
        "cmd": "audit",
        "query": "Focus on onboarding readiness.",
    }


def test_issue_scope_audit_is_supported_and_includes_required_sections() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    audit: dict[str, object] = {}

    markdown = _build_audit_markdown(
        repo_root=repo_root,
        query="",
        tky_mode="local",
        github_context_seed={},
        audit=audit,
    )

    assert "# RepoBrain Repository Audit" in markdown
    assert "Overall score:" in markdown
    assert "## Audit mode" in markdown
    assert "## Category scores" in markdown
    assert "## Critical blockers" in markdown
    assert "## Top improvements" in markdown
    assert "## Recommended next priorities" in markdown
    assert "30/60/90-day roadmap" not in markdown
    assert "## Evidence summary" in markdown
    assert "## Confidence and limitations" in markdown
    assert "## Runtime and safety" in markdown
    assert "- Safety: informational only; no patch/autofix, no file changes, no branch/commit/PR created." in markdown
    assert "Not a merge/security/production approval." in markdown
    assert audit["route_final"] == "AUDIT"
    assert audit["scope_status"] == "repository_audit"


def test_pr_scope_audit_uses_pr_metadata_when_available() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    audit: dict[str, object] = {}

    markdown = _build_audit_markdown(
        repo_root=repo_root,
        query="Summarize repository quality and include this PR context.",
        tky_mode="local",
        github_context_seed={
            "is_pr": True,
            "pr_number": 32,
            "changed_files": [
                "docs/repobrain_audit_fixture.md",
                ".github/workflows/repobrain.yml",
            ],
            "files": [
                {"filename": "docs/repobrain_audit_fixture.md", "status": "modified"},
                {"filename": ".github/workflows/repobrain.yml", "status": "modified"},
            ],
        },
        audit=audit,
    )

    assert "PR context: `yes`" in markdown
    assert "Changed files considered: `2`" in markdown
    assert audit["pr_metadata_used"] is True
    assert audit["scope_status"] == "repository_audit_with_pr_context"


def test_help_output_includes_audit_but_not_unsupported_commands_as_supported(capsys) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain help",
        issue_number=None,
    )
    output = capsys.readouterr().out

    assert status == "DRY_RUN_OK"
    assert "/repobrain audit" in output
    assert "/repobrain doctor" in output
    assert "/repobrain status" in output
    assert "/repobrain score" in output
    assert "compact score summary" in output.lower()

def test_score_and_generic_unsupported_command_surface_remains_honest(capsys) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain score",
        issue_number=None,
    )
    output = capsys.readouterr().out
    assert status == "DRY_RUN_OK"
    assert "# RepoBrain Repository Score" in output
    assert "Use `/repobrain audit` for the full evidence report." in output
    assert "/repobrain audit" in output

    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain " + "fix" + "-lite",
        issue_number=None,
    )
    output = capsys.readouterr().out
    assert status == "DRY_RUN_OK"
    assert "Unsupported RepoBrain command." in output
    assert "/repobrain help" in output
    assert "/repobrain fix-lite" not in output


def test_run_github_flow_audit_dry_run_records_no_mutation_audit_fields() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain audit",
        issue_number=None,
    )
    audit = get_last_audit()

    assert status == "DRY_RUN_OK"
    assert audit["command"] == "audit"
    assert audit["route_final"] == "AUDIT"
    assert audit["patch_authorized"] is False
    assert audit["patch_applied"] is False
    assert audit["files_modified"] is False
    assert audit["branch_created"] is False
    assert audit["commit_created"] is False
    assert audit["pr_created"] is False
    assert audit["resolved_backend"] == "not_applicable"
    assert audit["fallback_reason"] == "audit_v6_capability_unavailable_static_scoring"


def test_run_github_flow_pr_audit_dry_run_records_pr_metadata(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    event_path = _pr_event(tmp_path, "/repobrain audit Include PR context.")
    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="",
        issue_number=None,
        event_path=event_path,
    )
    audit = get_last_audit()

    assert status == "DRY_RUN_OK"
    assert audit["command"] == "audit"
    assert audit["pr_metadata_used"] is True
    assert audit["pr_changed_files_count"] == 2
