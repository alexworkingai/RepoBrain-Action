from pathlib import Path

import pytest

from repobrain.github_flow import build_issue_comment_url, run_github_flow


def test_run_github_flow_ignores_non_repobrain_comment(capsys) -> None:
    repo_root = Path(__file__).resolve().parents[1]

    status = run_github_flow(
        repo_root=repo_root,
        dry_run=True,
        comment_text="hello world",
        issue_number=None,
    )
    output = capsys.readouterr().out

    assert status == "IGNORED"
    assert "Ignored: comment does not start with /repobrain" in output


def test_run_github_flow_post_mode_requires_issue_number() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    with pytest.raises(ValueError, match="issue_number is required when dry_run=False"):
        run_github_flow(
            repo_root=repo_root,
            dry_run=False,
            comment_text="/repobrain ask provider",
            issue_number=None,
        )


def test_build_issue_comment_url() -> None:
    assert (
        build_issue_comment_url("owner/repo", 123)
        == "https://api.github.com/repos/owner/repo/issues/123/comments"
    )
