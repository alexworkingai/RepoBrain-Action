from __future__ import annotations

import json
from pathlib import Path

import pytest

from repobrain.github_flow import get_last_audit, run_github_flow


def _issue_comment_event(tmp_path: Path, body: str, *, is_pr: bool = False) -> Path:
    payload: dict[str, object] = {
        "issue": {
            "number": 41,
        },
        "comment": {
            "body": body,
            "id": 18,
            "user": {"login": "partner-user"},
        },
        "repository": {
            "full_name": "owner/repo",
            "name": "repo",
            "owner": {"login": "owner"},
            "private": False,
        },
    }
    if is_pr:
        payload["issue"]["pull_request"] = {"url": "https://api.github.com/repos/owner/repo/pulls/41"}
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(payload), encoding="utf-8")
    return event_path


def _configure_queue_env(monkeypatch: pytest.MonkeyPatch, *, event_name: str = "issue_comment") -> None:
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_REPOSITORY_ID", "123")
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER", "owner")
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER_ID", "456")
    monkeypatch.setenv("GITHUB_WORKFLOW", "RepoBrain")
    monkeypatch.setenv("GITHUB_WORKFLOW_REF", "owner/repo/.github/workflows/repobrain.yml@refs/heads/main")
    monkeypatch.setenv("GITHUB_WORKFLOW_SHA", "workflowsha")
    monkeypatch.setenv("GITHUB_JOB", "repobrain")
    monkeypatch.setenv("GITHUB_RUN_ID", "999")
    monkeypatch.setenv("GITHUB_RUN_NUMBER", "3")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("GITHUB_EVENT_NAME", event_name)
    monkeypatch.setenv("GITHUB_REF", "refs/heads/main")
    monkeypatch.setenv("GITHUB_SHA", "deadbeef")
    monkeypatch.setenv("GITHUB_ACTOR", "partner-user")
    monkeypatch.setenv("GITHUB_ACTOR_ID", "777")
    monkeypatch.setenv("GITHUB_ACTION_REPOSITORY", "alexworkingai/RepoBrain-Action")
    monkeypatch.setenv("GITHUB_ACTION_REF", "main")
    monkeypatch.setenv("RB_TRANSPORT_MODE", "github_app_queue")
    monkeypatch.setenv("RB_SELF_SERVICE_PROFILE", "partner-pilot")
    monkeypatch.setenv("RB_SELF_SERVICE_TERMS_ACCEPTED", "true")
    monkeypatch.setenv("RB_SELF_SERVICE_MODE", "false")
    monkeypatch.delenv("RB_SELF_SERVICE_API_URL", raising=False)


def _block_hosted_and_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    class _HostedClient:
        def __init__(self, _config) -> None:
            raise AssertionError("HostedApiClient must not be used in github_app_queue mode.")

    monkeypatch.setattr("repobrain.github_flow.HostedApiClient", _HostedClient)
    monkeypatch.setattr(
        "repobrain.github_flow.GitHubOidcTokenProvider",
        lambda: (_ for _ in ()).throw(AssertionError("OIDC must not be acquired in github_app_queue mode.")),
    )
    monkeypatch.setattr(
        "repobrain.github_flow.score_repository_audit",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("Queue mode must not run score_repository_audit.")),
    )
    monkeypatch.setattr(
        "repobrain.github_flow.enrich_audit_report_with_optional_v6",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("Queue mode must not run TopoCore enrichment.")),
    )


def test_github_app_queue_score_posts_queued_acknowledgement(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configure_queue_env(monkeypatch)
    _block_hosted_and_runtime(monkeypatch)
    event_path = _issue_comment_event(tmp_path, "/repobrain score")

    status = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=True,
        comment_text="",
        issue_number=None,
        event_path=event_path,
    )

    output = capsys.readouterr().out
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert "RepoBrain request queued" in output
    assert "<!-- repobrain:queue:v1" in output
    assert "Transport: `github_app_queue`" in output
    assert "pending_private_control_worker" in output
    assert audit["route_final"] == "SELF_SERVICE_GITHUB_QUEUE"
    assert audit["github_native_queue_request_id"].startswith("rbq_")
    assert audit["github_native_queue_payload"]["command"] == "score"
    assert audit["github_native_queue_payload"]["profile"] == "partner-pilot"


def test_github_app_queue_audit_premium_pr_context_posts_queue_marker(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configure_queue_env(monkeypatch)
    _block_hosted_and_runtime(monkeypatch)
    event_path = _issue_comment_event(tmp_path, "/repobrain audit --profile premium Focus on queue mode.", is_pr=True)

    status = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=True,
        comment_text="",
        issue_number=None,
        event_path=event_path,
    )

    output = capsys.readouterr().out
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert "Command: `/repobrain audit --profile premium Focus on queue mode.`" in output
    assert '"pull_request_number": 41' in output
    assert audit["github_native_queue_payload"]["event_kind"] == "pull_request"
    assert audit["github_native_queue_payload"]["profile"] == "premium"


def test_github_app_queue_requires_terms_accepted(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configure_queue_env(monkeypatch)
    _block_hosted_and_runtime(monkeypatch)
    monkeypatch.setenv("RB_SELF_SERVICE_TERMS_ACCEPTED", "false")

    status = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=True,
        comment_text="/repobrain audit",
        issue_number=None,
    )

    output = capsys.readouterr().out
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert "TERMS_NOT_ACCEPTED_FOR_GITHUB_QUEUE" in output
    assert audit["route_final"] == "SELF_SERVICE_QUEUE_ERROR"
    assert audit["self_service_status"] == "terms_not_accepted_for_github_queue"


def test_invalid_transport_mode_returns_public_safe_error(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configure_queue_env(monkeypatch)
    monkeypatch.setenv("RB_TRANSPORT_MODE", "bogus")

    status = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=True,
        comment_text="/repobrain score",
        issue_number=None,
    )

    output = capsys.readouterr().out
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert "INVALID_TRANSPORT_MODE" in output
    assert audit["self_service_status"] == "invalid_transport_mode"


def test_github_app_queue_rejects_unsupported_event(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configure_queue_env(monkeypatch, event_name="pull_request")
    _block_hosted_and_runtime(monkeypatch)

    status = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=True,
        comment_text="/repobrain score",
        issue_number=None,
    )

    output = capsys.readouterr().out
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert "GITHUB_QUEUE_UNSUPPORTED_EVENT" in output
    assert audit["route_final"] == "SELF_SERVICE_QUEUE_ERROR"
    assert audit["self_service_status"] == "github_queue_unsupported_event"
