from __future__ import annotations

import json
from pathlib import Path

from repobrain.github_flow import run_github_flow


def test_review_requires_pr_context(capsys) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="/repobrain review",
        issue_number=None,
        tky_mode="baseline",
    )
    output = capsys.readouterr().out
    assert status == "DRY_RUN_OK"
    assert "Review/fix is available in Pull Requests." in output


def test_review_in_pr_context_renders_review(capsys, tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    event_payload = {
        "issue": {
            "number": 12,
            "pull_request": {"url": "https://api.github.com/repos/o/r/pulls/12"},
        },
        "comment": {"body": "/repobrain review", "id": 10, "user": {"login": "alice"}},
    }
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(event_payload), encoding="utf-8")

    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="",
        issue_number=None,
        tky_mode="baseline",
        event_path=event_path,
    )
    output = capsys.readouterr().out
    assert status == "DRY_RUN_OK"
    assert "PR Review" in output
