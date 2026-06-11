from __future__ import annotations

import json
from pathlib import Path

import pytest

from repobrain.github_flow import get_last_audit, run_github_flow
from repobrain.oidc import GitHubOidcTokenProvider, OIDC_REQUIRED_MESSAGE


class _FakeResponse:
    def __init__(self, payload: dict[str, str], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict[str, str]:
        return dict(self._payload)


def test_oidc_provider_returns_safe_unavailable_status_without_env() -> None:
    result = GitHubOidcTokenProvider(environ={}).get_token()

    assert result.available is False
    assert result.token_present is False
    assert result.audience == "repobrain-api"
    assert result.error_code == "oidc_unavailable"
    assert "id-token: write" in result.message
    assert result.token == ""


def test_oidc_provider_uses_default_audience_and_redacts_token() -> None:
    seen: dict[str, object] = {}

    def _fake_get(url: str, *, headers: dict[str, str], timeout: int) -> _FakeResponse:
        seen["url"] = url
        seen["headers"] = dict(headers)
        seen["timeout"] = timeout
        return _FakeResponse({"value": "header.payload.signature"})

    result = GitHubOidcTokenProvider(
        environ={
            "ACTIONS_ID_TOKEN_REQUEST_URL": "https://token.actions.githubusercontent.com?id=1",
            "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "request-token-secret",
        },
        request_get=_fake_get,
    ).get_token()

    assert result.available is True
    assert result.token_present is True
    assert result.audience == "repobrain-api"
    assert result.token == "header.payload.signature"
    assert "audience=repobrain-api" in str(seen["url"])
    assert "request-token-secret" == seen["headers"]["Authorization"].split(" ", 1)[1]
    assert "header.payload.signature" not in json.dumps(result.redacted_dict())
    assert "request-token-secret" not in json.dumps(result.redacted_dict())


def test_oidc_provider_uses_custom_audience() -> None:
    captured: dict[str, str] = {}

    def _fake_get(url: str, *, headers: dict[str, str], timeout: int) -> _FakeResponse:
        captured["url"] = url
        return _FakeResponse({"value": "jwt"})

    result = GitHubOidcTokenProvider(
        environ={
            "ACTIONS_ID_TOKEN_REQUEST_URL": "https://token.actions.githubusercontent.com",
            "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "request-token-secret",
        },
        request_get=_fake_get,
    ).get_token(audience="partner-audience")

    assert result.audience == "partner-audience"
    assert "audience=partner-audience" in captured["url"]


def test_self_service_mode_requires_terms_before_continuing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("GITHUB_REPOSITORY", "alexworkingai/RepoBrain-Action")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "issue_comment")
    monkeypatch.setenv("GITHUB_RUN_ID", "101")
    monkeypatch.setenv("RB_SELF_SERVICE_MODE", "true")
    monkeypatch.setenv("RB_SELF_SERVICE_PROFILE", "partner-pilot")
    monkeypatch.delenv("RB_SELF_SERVICE_TERMS_ACCEPTED", raising=False)

    status = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=True,
        comment_text="/repobrain help",
        issue_number=None,
    )

    output = capsys.readouterr().out
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert 'terms_accepted: "true"' in output
    assert audit["self_service_status"] == "terms_not_accepted"
    assert audit["route_final"] == "SELF_SERVICE_BLOCKED"


def test_self_service_mode_requires_oidc_when_terms_are_accepted(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("GITHUB_REPOSITORY", "alexworkingai/RepoBrain-Action")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "issue_comment")
    monkeypatch.setenv("GITHUB_RUN_ID", "102")
    monkeypatch.setenv("RB_SELF_SERVICE_MODE", "true")
    monkeypatch.setenv("RB_SELF_SERVICE_PROFILE", "partner-pilot")
    monkeypatch.setenv("RB_SELF_SERVICE_TERMS_ACCEPTED", "true")
    monkeypatch.delenv("ACTIONS_ID_TOKEN_REQUEST_URL", raising=False)
    monkeypatch.delenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN", raising=False)

    status = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=True,
        comment_text="/repobrain help",
        issue_number=None,
    )

    output = capsys.readouterr().out
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert OIDC_REQUIRED_MESSAGE in output
    assert audit["self_service_status"] == "oidc_required"
    assert audit["route_final"] == "SELF_SERVICE_BLOCKED"


def test_self_service_success_preserves_help_behavior_and_redacts_tokens(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
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
    monkeypatch.setenv("GITHUB_REPOSITORY", "alexworkingai/RepoBrain-Action")
    monkeypatch.setenv("GITHUB_REPOSITORY_ID", "123")
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER", "alexworkingai")
    monkeypatch.setenv("GITHUB_REPOSITORY_OWNER_ID", "456")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "issue_comment")
    monkeypatch.setenv("GITHUB_RUN_ID", "103")
    monkeypatch.setenv("GITHUB_RUN_NUMBER", "9")
    monkeypatch.setenv("GITHUB_ACTOR", "partner-user")
    monkeypatch.setenv("RB_SELF_SERVICE_MODE", "true")
    monkeypatch.setenv("RB_SELF_SERVICE_PROFILE", "partner-pilot")
    monkeypatch.setenv("RB_SELF_SERVICE_TERMS_ACCEPTED", "true")
    monkeypatch.setenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "request-token-secret")

    status = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=True,
        comment_text="/repobrain help",
        issue_number=None,
    )

    output = capsys.readouterr().out
    audit = get_last_audit()
    rendered_audit = json.dumps(audit, sort_keys=True)
    assert status == "DRY_RUN_OK"
    assert "## 1. Command list" in output
    assert "header.payload.signature" not in output
    assert "request-token-secret" not in output
    assert "header.payload.signature" not in rendered_audit
    assert "request-token-secret" not in rendered_audit
    assert audit["self_service_status"] == "self_service_ready"
    assert audit["route_final"] == "HELP"
    assert audit["self_service_identity_envelope"]["version"] == "repobrain.github_oidc_identity.v1"


def test_non_self_service_mode_preserves_current_behavior_without_oidc(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("GITHUB_REPOSITORY", "alexworkingai/RepoBrain-Action")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "issue_comment")
    monkeypatch.setenv("GITHUB_RUN_ID", "104")
    monkeypatch.setenv("RB_SELF_SERVICE_MODE", "false")

    status = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=True,
        comment_text="/repobrain help",
        issue_number=None,
    )

    output = capsys.readouterr().out
    audit = get_last_audit()
    assert status == "DRY_RUN_OK"
    assert "## 1. Command list" in output
    assert audit["self_service_status"] == "self_service_disabled"
    assert audit["route_final"] == "HELP"
