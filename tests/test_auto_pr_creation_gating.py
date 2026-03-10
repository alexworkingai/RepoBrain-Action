from __future__ import annotations

from repobrain.github_flow import _maybe_create_patch_pr


def test_auto_pr_disabled_by_default(monkeypatch) -> None:
    monkeypatch.setenv("RB_CREATE_PR", "0")
    monkeypatch.setenv("RB_APPLY_PATCH", "1")
    monkeypatch.setenv("RB_TRUSTED_CONTEXT", "1")

    called = {"n": 0}

    def fake_create_pull_request(**kwargs):
        called["n"] += 1
        return {"ok": True, "status_code": 201, "data": {"html_url": "https://example/pr/1"}}

    monkeypatch.setattr("repobrain.github_flow.create_pull_request", fake_create_pull_request)
    msg = _maybe_create_patch_pr(
        repo_name="o/r",
        token="t",
        patch_branch="repobrain/patch/1",
        base_branch="main",
        body_markdown="body",
    )
    assert called["n"] == 0
    assert "disabled" in msg


def test_auto_pr_forbidden_message(monkeypatch) -> None:
    monkeypatch.setenv("RB_CREATE_PR", "1")
    monkeypatch.setenv("RB_APPLY_PATCH", "1")
    monkeypatch.setenv("RB_TRUSTED_CONTEXT", "1")

    called = {"n": 0}

    def fake_create_pull_request(**kwargs):
        called["n"] += 1
        return {"ok": False, "status_code": 403, "data": {}}

    monkeypatch.setattr("repobrain.github_flow.create_pull_request", fake_create_pull_request)
    msg = _maybe_create_patch_pr(
        repo_name="o/r",
        token="t",
        patch_branch="repobrain/patch/1",
        base_branch="main",
        body_markdown="body",
    )
    assert called["n"] == 1
    assert "Create PR manually" in msg
