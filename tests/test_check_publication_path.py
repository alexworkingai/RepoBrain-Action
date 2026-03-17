from __future__ import annotations

from pathlib import Path

import repobrain.github_flow as gf


class _FakeClient:
    def __init__(self) -> None:
        self.repo = "owner/repo"
        self.token = "token"


def test_publish_pr_check_run_uses_command_specific_names(monkeypatch, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    def _fake_publish_check_run(**kwargs):  # type: ignore[no-untyped-def]
        calls.append(dict(kwargs))
        return {"ok": True, "status_code": 201}

    monkeypatch.setattr(gf, "publish_check_run", _fake_publish_check_run)

    for cmd in ("ask", "review", "fix"):
        audit = {
            "route_final": "FAST",
            "check_intent": "analysis" if cmd == "ask" else ("review" if cmd == "review" else "patch"),
            "verification_report": {"overall": "NOT_RUN", "checks": []},
            "pr_head_sha": "abc123",
        }
        gf._publish_pr_check_run(
            repo_root=tmp_path,
            client=_FakeClient(),
            cmd=cmd,
            issue_number=7,
            body_markdown="body",
            audit=audit,
            github_context_seed={"head_sha": "abc123"},
        )
        assert audit["check_run_published"] is True
        assert audit["check_run_name"].startswith("RepoBrain")
        assert audit["check_run_attempted"] is True
        assert audit["check_run_failure_class"] == "none"

    assert len(calls) == 3
    assert {str(item["name"]) for item in calls} == {"RepoBrain Ask", "RepoBrain Review", "RepoBrain Fix"}


def test_publish_pr_check_run_sets_skip_reason_when_head_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(gf, "_resolve_pr_head_sha", lambda **_: "")
    audit = {"route_final": "FAST", "check_intent": "analysis", "verification_report": {"overall": "NOT_RUN"}}

    gf._publish_pr_check_run(
        repo_root=tmp_path,
        client=_FakeClient(),
        cmd="ask",
        issue_number=3,
        body_markdown="body",
        audit=audit,
        github_context_seed={},
    )

    assert audit["check_run_published"] is False
    assert audit["check_run_skip_reason"] == "head_sha_missing"


def test_publish_pr_check_run_defers_for_issue_comment(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GITHUB_EVENT_NAME", "issue_comment")
    called = {"count": 0}

    def _fake_publish_check_run(**kwargs):  # type: ignore[no-untyped-def]
        called["count"] += 1
        return {"ok": True, "status_code": 201}

    monkeypatch.setattr(gf, "publish_check_run", _fake_publish_check_run)
    audit = {
        "route_final": "FAST",
        "check_intent": "analysis",
        "verification_report": {"overall": "NOT_RUN"},
        "pr_head_sha": "abc123",
    }

    gf._publish_pr_check_run(
        repo_root=tmp_path,
        client=_FakeClient(),
        cmd="ask",
        issue_number=3,
        body_markdown="body",
        audit=audit,
        github_context_seed={"head_sha": "abc123"},
    )

    assert called["count"] == 0
    assert audit["check_run_attempted"] is False
    assert audit["check_run_skip_reason"] == "deferred_workflow_publisher"
    assert audit["check_run_failure_class"] == "deferred"
    assert audit["check_run_token_source"] == "workflow_run_github_token"


def test_publish_pr_check_run_records_permissions_header_on_failure(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")

    def _fake_publish_check_run(**kwargs):  # type: ignore[no-untyped-def]
        return {
            "ok": False,
            "status_code": 403,
            "required_permissions_header": "checks=write",
        }

    monkeypatch.setattr(gf, "publish_check_run", _fake_publish_check_run)
    audit = {
        "route_final": "FAST",
        "check_intent": "analysis",
        "verification_report": {"overall": "NOT_RUN"},
        "pr_head_sha": "abc123",
    }

    gf._publish_pr_check_run(
        repo_root=tmp_path,
        client=_FakeClient(),
        cmd="ask",
        issue_number=3,
        body_markdown="body",
        audit=audit,
        github_context_seed={"head_sha": "abc123"},
    )

    assert audit["check_run_attempted"] is True
    assert audit["check_run_published"] is False
    assert audit["check_run_status_code"] == 403
    assert audit["check_run_required_permissions_header"] == "checks=write"
    assert audit["check_run_failure_class"] == "permissions"


def test_repobrain_workflow_allows_check_run_publication() -> None:
    workflow = Path(".github/workflows/repobrain.yml").read_text(encoding="utf-8")
    assert "checks: write" in workflow
    assert "RB_CHECK_RUN_PUBLISH_MODE: \"deferred\"" in workflow


def test_privileged_checks_publisher_workflow_is_sanitized() -> None:
    workflow = Path(".github/workflows/repobrain_checks_publisher.yml").read_text(encoding="utf-8")
    assert "workflow_run:" in workflow
    assert "checks: write" in workflow
    assert "actions: read" in workflow
    assert "actions/checkout" not in workflow
