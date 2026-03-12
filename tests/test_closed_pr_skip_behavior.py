from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _build_review_markdown


class _FakeClient:
    def __init__(self, pull_payload: dict[str, object]) -> None:
        self._pull_payload = pull_payload
        self.repo = "owner/repo"

    def get_pull(self, pull_number: int) -> dict[str, object]:
        assert pull_number == 42
        return dict(self._pull_payload)

    def get_pull_files(self, pull_number: int) -> list[dict[str, object]]:  # pragma: no cover
        raise AssertionError("PR files must not be requested for closed/merged PR skip path")


def test_review_on_merged_pr_returns_usersafe_skip_comment() -> None:
    audit: dict[str, object] = {}
    body = _build_review_markdown(
        repo_root=Path(__file__).resolve().parents[1],
        cmd="review",
        query="",
        is_pull_request=True,
        issue_number=42,
        dry_run=False,
        client=_FakeClient({"state": "closed", "merged": True}),
        tky_mode="baseline",
        remote_url="",
        api_key="",
        hmac_secret="",
        enable_hmac=False,
        audit=audit,
    )

    assert "Skipped: `/repobrain review` runs only on open PRs." in body
    assert "closed/merged" in body
    assert audit["skip_reason_code"] == "pr_closed_or_merged_review"
    assert audit["skip_visible_to_user"] is True


def test_fix_on_closed_pr_returns_usersafe_skip_comment() -> None:
    audit: dict[str, object] = {}
    body = _build_review_markdown(
        repo_root=Path(__file__).resolve().parents[1],
        cmd="fix",
        query="",
        is_pull_request=True,
        issue_number=42,
        dry_run=False,
        client=_FakeClient({"state": "closed", "merged": False}),
        tky_mode="baseline",
        remote_url="",
        api_key="",
        hmac_secret="",
        enable_hmac=False,
        audit=audit,
    )

    assert "Skipped: `/repobrain fix` runs only on open PRs with an active diff context." in body
    assert "already closed" in body
    assert audit["skip_reason_code"] == "pr_closed_or_merged_fix"
    assert audit["skip_visible_to_user"] is True
