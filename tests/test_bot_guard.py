from pathlib import Path

from repobrain.github_flow import run_github_flow


def test_bot_comment_is_ignored(capsys, tmp_path: Path) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        """
{
  "issue": {"number": 1},
  "comment": {
    "id": 10,
    "body": "/repobrain ask provider",
    "user": {"login": "github-actions[bot]"}
  }
}
""".strip(),
        encoding="utf-8",
    )

    status = run_github_flow(
        repo_root=Path(__file__).resolve().parents[1],
        dry_run=False,
        comment_text="",
        issue_number=None,
        event_path=event_path,
    )
    output = capsys.readouterr().out

    assert status == "IGNORED_BOT"
    assert "Ignored bot comment" in output
