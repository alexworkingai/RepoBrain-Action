from pathlib import Path

from repobrain.github_flow import GitHubClient, build_pr_files_url, build_reaction_url, run_github_flow


class _DummyResponse:
    def __init__(self, json_data=None) -> None:
        self._json_data = json_data if json_data is not None else []

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._json_data


def test_dry_run_does_not_add_reaction(monkeypatch, tmp_path: Path) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        """
{
  "issue": {"number": 7},
  "comment": {
    "id": 77,
    "body": "/repobrain ask provider",
    "user": {"login": "alice"}
  }
}
""".strip(),
        encoding="utf-8",
    )

    def _fail_reaction(*args, **kwargs):  # pragma: no cover - should never be called
        raise AssertionError("Reaction should not be called in dry-run")

    monkeypatch.setattr(GitHubClient, "add_reaction_to_issue_comment", _fail_reaction)

    status = run_github_flow(
        repo_root=Path(__file__).resolve().parents[1],
        dry_run=True,
        comment_text="",
        issue_number=None,
        event_path=event_path,
    )

    assert status == "DRY_RUN_OK"


def test_reaction_endpoint_url_builders() -> None:
    assert (
        build_reaction_url("owner/repo", 77)
        == "https://api.github.com/repos/owner/repo/issues/comments/77/reactions"
    )
    assert (
        build_pr_files_url("owner/repo", 12)
        == "https://api.github.com/repos/owner/repo/pulls/12/files?per_page=100"
    )


def test_github_client_add_reaction_uses_reactions_endpoint(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url, json, headers, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _DummyResponse()

    monkeypatch.setattr("repobrain.github_flow.requests.post", fake_post)

    client = GitHubClient(repo="owner/repo", token="token")
    client.add_reaction_to_issue_comment(comment_id=321, content="eyes")

    assert captured["url"] == build_reaction_url("owner/repo", 321)
    assert captured["json"] == {"content": "eyes"}
    assert captured["timeout"] == 15


def test_github_client_get_pr_files_uses_endpoint(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_get(url, headers, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["timeout"] = timeout
        return _DummyResponse([{"filename": "repobrain/github_flow.py"}])

    monkeypatch.setattr("repobrain.github_flow.requests.get", fake_get)

    client = GitHubClient(repo="owner/repo", token="token")
    data = client.get_pull_files(pull_number=15)

    assert captured["url"] == build_pr_files_url("owner/repo", 15)
    assert captured["timeout"] == 15
    assert data and data[0]["filename"] == "repobrain/github_flow.py"


def test_internal_reactions_can_be_disabled_by_env(monkeypatch, tmp_path: Path) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(
        """
{
  "issue": {"number": 11},
  "comment": {
    "id": 222,
    "body": "/repobrain help",
    "user": {"login": "alice"}
  }
}
""".strip(),
        encoding="utf-8",
    )

    class FakeClient:
        def __init__(self) -> None:
            self.reaction_called = False
            self.comment_called = False

        def add_reaction_to_issue_comment(self, comment_id: int, content: str = "eyes") -> None:
            self.reaction_called = True

        def create_issue_comment(self, issue_number: int, body_markdown: str) -> None:
            self.comment_called = True

    fake_client = FakeClient()
    monkeypatch.setenv("RB_DISABLE_INTERNAL_REACTIONS", "1")
    monkeypatch.setattr("repobrain.github_flow._build_post_client", lambda: fake_client)

    status = run_github_flow(
        repo_root=Path(__file__).resolve().parents[1],
        dry_run=False,
        comment_text="",
        issue_number=None,
        event_path=event_path,
    )

    assert status == "POSTED_OK"
    assert fake_client.reaction_called is False
    assert fake_client.comment_called is True
