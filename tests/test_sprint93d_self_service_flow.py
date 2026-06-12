from __future__ import annotations

import json
from pathlib import Path

import pytest

from repobrain.github_flow import get_last_audit, run_github_flow
from repobrain.hosted_api_client import HostedApiClientError, HostedApiSendResult


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
        payload["files"] = [
            {"filename": "docs/repobrain_manual_pr_smoke.md", "status": "modified"},
            {"filename": ".github/workflows/repobrain.yml", "status": "modified"},
        ]
        payload["changed_files"] = [
            "docs/repobrain_manual_pr_smoke.md",
            ".github/workflows/repobrain.yml",
        ]
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(payload), encoding="utf-8")
    return event_path


def _pull_request_event(tmp_path: Path) -> Path:
    payload = {
        "pull_request": {
            "number": 52,
            "base": {
                "sha": "base123",
                "ref": "main",
                "repo": {"full_name": "owner/repo"},
            },
            "head": {
                "sha": "head456",
                "ref": "feature-branch",
                "repo": {"full_name": "owner/repo"},
            },
        },
        "repository": {
            "full_name": "owner/repo",
            "name": "repo",
            "owner": {"login": "owner"},
            "private": False,
        },
        "files": [
            {"filename": "src/app.py", "status": "modified"},
            {"filename": "tests/test_app.py", "status": "modified"},
        ],
        "changed_files": ["src/app.py", "tests/test_app.py"],
    }
    event_path = tmp_path / "pull_request.json"
    event_path.write_text(json.dumps(payload), encoding="utf-8")
    return event_path


def _success_response(markdown: str = "### Hosted report\n- Public-safe hosted result.") -> dict[str, object]:
    return {
        "version": "repobrain.github_action_audit_response.v1",
        "status": "ok",
        "tenant": {
            "tenant_id": "gh_owner_456_repo_123",
            "repository_id": "123",
            "repository": "owner/repo",
            "plan": "partner_pilot_auto",
            "auto_provisioned": True,
            "manual_approval_required": False,
        },
        "quota": {
            "version": "repobrain.partner_quota.v1",
            "status": "ok",
            "profile": "partner_pilot_default",
            "remaining": 19,
            "reset_at": "2026-06-12T00:00:00+00:00",
        },
        "report": {
            "format": "repobrain.audit_report.v1",
            "score": 86,
            "band": "STRONG",
            "markdown": markdown,
        },
        "runtime": {
            "score_authority": "TopoCore",
            "topocore_runtime": "private_server_side",
            "llm_role": "narrative_only",
            "mutation": "disabled",
        },
        "safety": {
            "informational_only": True,
            "patch_autofix": False,
            "branch_commit_pr_created": False,
            "merge_security_production_approval": False,
            "private_runtime_exposed": False,
        },
    }


def _configure_self_service_env(monkeypatch: pytest.MonkeyPatch, *, event_name: str) -> None:
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
    monkeypatch.setenv("RB_SELF_SERVICE_MODE", "true")
    monkeypatch.setenv("RB_SELF_SERVICE_PROFILE", "partner-pilot")
    monkeypatch.setenv("RB_SELF_SERVICE_TERMS_ACCEPTED", "true")
    monkeypatch.setenv("RB_SELF_SERVICE_API_URL", "https://api.example.test")

    class _Provider:
        def get_token(self, *, audience: str | None = None):
            from repobrain.oidc import OidcTokenResult

            return OidcTokenResult(
                available=True,
                audience=audience or "repobrain-api",
                token_present=True,
                token_redacted=True,
                error_code="none",
                message="GitHub OIDC token acquired.",
                token="header.payload.signature",
            )

    monkeypatch.setattr("repobrain.github_flow.GitHubOidcTokenProvider", lambda: _Provider())


def test_issue_comment_self_service_audit_happy_path_uses_hosted_api(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configure_self_service_env(monkeypatch, event_name="issue_comment")

    class _Client:
        def __init__(self, _config) -> None:
            pass

        def send_audit_request(self, request_json):
            assert request_json["command"]["route"] == "audit"
            assert request_json["oidc_jwt"] == "header.payload.signature"
            return HostedApiSendResult(
                response=_success_response(),
                http_status=200,
                sanitized_endpoint="https://api.example.test/v1/github/actions/audit",
            )

    monkeypatch.setattr("repobrain.github_flow.HostedApiClient", _Client)
    event_path = _issue_comment_event(tmp_path, "/repobrain audit Focus on partner self-service readiness.")

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
    assert "Hosted report" in output
    assert "Tenant plan: `partner_pilot_auto`" in output
    assert "header.payload.signature" not in output
    assert audit["route_final"] == "SELF_SERVICE_HOSTED"
    assert audit["self_service_hosted_api_endpoint"] == "https://api.example.test/v1/github/actions/audit"
    assert audit["self_service_hosted_api_response_status"] == "ok"


def test_pull_request_self_service_score_happy_path_uses_hosted_api(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configure_self_service_env(monkeypatch, event_name="pull_request")

    class _Client:
        def __init__(self, _config) -> None:
            pass

        def send_audit_request(self, request_json):
            assert request_json["command"]["route"] == "score"
            return HostedApiSendResult(
                response=_success_response("### Hosted score\n- Compact score summary."),
                http_status=200,
                sanitized_endpoint="https://api.example.test/v1/github/actions/audit",
            )

    monkeypatch.setattr("repobrain.github_flow.HostedApiClient", _Client)
    event_path = _pull_request_event(tmp_path)

    status = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=True,
        comment_text="/repobrain score",
        issue_number=None,
        event_path=event_path,
    )

    output = capsys.readouterr().out
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert "Hosted score" in output
    assert audit["command"] == "score"
    assert audit["route_final"] == "SELF_SERVICE_HOSTED"


def test_workflow_dispatch_self_service_ask_happy_path_uses_simulated_command(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configure_self_service_env(monkeypatch, event_name="workflow_dispatch")
    monkeypatch.setenv("RB_E2E_COMMAND", "/repobrain ask Where is the RepoBrain workflow?")
    monkeypatch.setenv("RB_E2E_PR_NUMBER", "71")

    class _Client:
        def __init__(self, _config) -> None:
            pass

        def send_audit_request(self, request_json):
            assert request_json["command"]["route"] == "ask"
            return HostedApiSendResult(
                response=_success_response("### Hosted ask\n- Workflow located successfully."),
                http_status=200,
                sanitized_endpoint="https://api.example.test/v1/github/actions/audit",
            )

    monkeypatch.setattr("repobrain.github_flow.HostedApiClient", _Client)

    status = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=True,
        comment_text="",
        issue_number=None,
    )

    output = capsys.readouterr().out
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert "Hosted ask" in output
    assert audit["command"] == "ask"
    assert audit["route_final"] == "SELF_SERVICE_HOSTED"


def test_self_service_audit_premium_route_preserves_requested_profile(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configure_self_service_env(monkeypatch, event_name="issue_comment")

    class _Client:
        def __init__(self, _config) -> None:
            pass

        def send_audit_request(self, request_json):
            assert request_json["command"]["route"] == "audit"
            assert request_json["command"]["profile"] == "premium"
            assert request_json["identity"]["command"]["profile"] == "premium"
            return HostedApiSendResult(
                response=_success_response("### Hosted premium audit\n- Premium profile accepted."),
                http_status=200,
                sanitized_endpoint="https://api.example.test/v1/github/actions/audit",
            )

    monkeypatch.setattr("repobrain.github_flow.HostedApiClient", _Client)

    status = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=True,
        comment_text="/repobrain audit --profile premium Focus on partner readiness.",
        issue_number=None,
    )

    output = capsys.readouterr().out
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert "Hosted premium audit" in output
    assert audit["llm_execution_profile_command_override"] == "premium"
    assert audit["self_service_hosted_api_request_preview"]["command"]["profile"] == "premium"


def test_self_service_supported_command_requires_api_url(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configure_self_service_env(monkeypatch, event_name="issue_comment")
    monkeypatch.delenv("RB_SELF_SERVICE_API_URL", raising=False)

    status = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=True,
        comment_text="/repobrain audit",
        issue_number=None,
    )

    output = capsys.readouterr().out
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert "requires `api_url` for hosted api routing in sprint 93d" in output.lower()
    assert audit["route_final"] == "SELF_SERVICE_HOSTED_ERROR"
    assert audit["self_service_hosted_api_error_code"] == "HOSTED_API_URL_MISSING"


def test_self_service_hosted_public_safe_server_error_is_rendered(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configure_self_service_env(monkeypatch, event_name="issue_comment")

    class _Client:
        def __init__(self, _config) -> None:
            pass

        def send_audit_request(self, request_json):
            return HostedApiSendResult(
                response={
                    "version": "repobrain.github_action_audit_response.v1",
                    "status": "error",
                    "error": {
                        "code": "QUOTA_EXCEEDED",
                        "message": "RepoBrain partner-pilot quota was exceeded for this repository.",
                        "retryable": False,
                    },
                    "safety": {
                        "token_redacted": True,
                        "private_runtime_exposed": False,
                    },
                },
                http_status=429,
                sanitized_endpoint="https://api.example.test/v1/github/actions/audit",
            )

    monkeypatch.setattr("repobrain.github_flow.HostedApiClient", _Client)

    status = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=True,
        comment_text="/repobrain audit",
        issue_number=None,
    )

    output = capsys.readouterr().out
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert "RepoBrain partner-pilot quota was exceeded" in output
    assert "Error code: `QUOTA_EXCEEDED`" in output
    assert audit["route_final"] == "SELF_SERVICE_HOSTED_ERROR"


def test_self_service_hosted_client_failure_is_rendered_safely(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _configure_self_service_env(monkeypatch, event_name="issue_comment")

    class _Client:
        def __init__(self, _config) -> None:
            pass

        def send_audit_request(self, request_json):
            raise HostedApiClientError(
                "HOSTED_API_UNAVAILABLE",
                "RepoBrain hosted API is unavailable or unreachable for self-service processing.",
                retryable=True,
                sanitized_endpoint="https://api.example.test/v1/github/actions/audit",
            )

    monkeypatch.setattr("repobrain.github_flow.HostedApiClient", _Client)

    status = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=True,
        comment_text="/repobrain audit",
        issue_number=None,
    )

    output = capsys.readouterr().out
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert "hosted api is unavailable or unreachable" in output.lower()
    assert "traceback" not in output.lower()
    assert audit["route_final"] == "SELF_SERVICE_HOSTED_ERROR"


def test_non_self_service_audit_flow_does_not_construct_hosted_client(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "issue_comment")
    monkeypatch.setenv("GITHUB_RUN_ID", "1001")
    monkeypatch.setenv("RB_SELF_SERVICE_MODE", "false")

    class _Client:
        def __init__(self, _config) -> None:
            raise AssertionError("HostedApiClient must not be used when self-service mode is disabled.")

    monkeypatch.setattr("repobrain.github_flow.HostedApiClient", _Client)

    status = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=True,
        comment_text="/repobrain audit",
        issue_number=None,
    )

    output = capsys.readouterr().out
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert "# RepoBrain Repository Audit" in output
    assert audit["route_final"] == "AUDIT"
