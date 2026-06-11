from __future__ import annotations

import json

import pytest

from repobrain.hosted_api_client import (
    HostedApiClient,
    HostedApiClientConfig,
    HostedApiClientError,
    validate_hosted_api_url,
)
from repobrain.hosted_api_contract import BOUNDED_EVIDENCE_VERSION, build_github_action_audit_request


def _identity() -> dict[str, object]:
    return {
        "version": "repobrain.github_oidc_identity.v1",
        "provider": "github_actions_oidc",
        "oidc": {
            "available": True,
            "audience": "repobrain-api",
            "token_present": True,
            "token_redacted": True,
        },
        "repository": {
            "full_name": "owner/repo",
            "owner": "owner",
            "name": "repo",
            "id": "123",
            "owner_id": "456",
            "visibility": "public",
        },
        "workflow": {
            "workflow": "RepoBrain",
            "workflow_ref": "owner/repo/.github/workflows/repobrain.yml@refs/heads/main",
            "workflow_sha": "abc123",
            "job": "repobrain",
            "run_id": "999",
            "run_number": "3",
            "run_attempt": "1",
            "event_name": "issue_comment",
            "ref": "refs/heads/main",
            "sha": "deadbeef",
            "actor": "partner-user",
            "actor_id": "777",
        },
        "action": {
            "repository": "alexworkingai/RepoBrain-Action",
            "ref": "main",
            "version": "0.5.0-rc.1",
        },
        "command": {
            "name": "audit",
            "profile": "partner-pilot",
            "raw": "/repobrain audit",
        },
        "self_service": {
            "enabled": True,
            "terms_accepted": True,
            "mode": "partner-pilot",
        },
    }


def _request() -> dict[str, object]:
    return build_github_action_audit_request(
        identity=_identity(),
        oidc_jwt="header.payload.signature",
        command={"route": "audit", "profile": "partner-pilot", "raw": "/repobrain audit"},
        evidence={"version": BOUNDED_EVIDENCE_VERSION, "items": [], "limits": {}, "redaction": {}},
    )


class _FakeResponse:
    def __init__(self, payload: dict[str, object], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict[str, object]:
        return dict(self._payload)


def test_validate_hosted_api_url_requires_https_outside_localhost() -> None:
    assert validate_hosted_api_url("https://api.example.test") == "https://api.example.test/v1/github/actions/audit"
    assert validate_hosted_api_url("http://localhost:8000") == "http://localhost:8000/v1/github/actions/audit"

    with pytest.raises(HostedApiClientError) as exc:
        validate_hosted_api_url("http://example.test")

    assert exc.value.code == "HOSTED_API_URL_INVALID"


def test_hosted_api_client_sends_request_and_validates_success_response() -> None:
    seen: dict[str, object] = {}

    def _fake_post(url: str, *, json: dict[str, object], headers: dict[str, str], timeout: float) -> _FakeResponse:
        seen["url"] = url
        seen["json"] = json
        seen["headers"] = dict(headers)
        seen["timeout"] = timeout
        return _FakeResponse(
            {
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
                    "markdown": "Hosted audit result.",
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
        )

    result = HostedApiClient(
        HostedApiClientConfig(api_url="https://api.example.test"),
        request_post=_fake_post,
    ).send_audit_request(_request())

    assert result.status == "ok"
    assert result.http_status == 200
    assert result.sanitized_endpoint == "https://api.example.test/v1/github/actions/audit"
    assert seen["url"] == "https://api.example.test/v1/github/actions/audit"
    assert seen["headers"] == {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    assert "header.payload.signature" == seen["json"]["oidc_jwt"]


def test_hosted_api_client_preserves_public_safe_error_response() -> None:
    def _fake_post(url: str, *, json: dict[str, object], headers: dict[str, str], timeout: float) -> _FakeResponse:
        return _FakeResponse(
            {
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
            status_code=429,
        )

    result = HostedApiClient(
        HostedApiClientConfig(api_url="https://api.example.test"),
        request_post=_fake_post,
    ).send_audit_request(_request())

    assert result.status == "error"
    assert result.response["error"]["code"] == "QUOTA_EXCEEDED"


def test_hosted_api_client_rejects_invalid_non_json_response() -> None:
    class _InvalidResponse:
        status_code = 200

        def json(self) -> object:
            return ["not", "a", "dict"]

    def _fake_post(url: str, *, json: dict[str, object], headers: dict[str, str], timeout: float) -> _InvalidResponse:
        return _InvalidResponse()

    with pytest.raises(HostedApiClientError) as exc:
        HostedApiClient(
            HostedApiClientConfig(api_url="https://api.example.test"),
            request_post=_fake_post,
        ).send_audit_request(_request())

    assert exc.value.code == "HOSTED_API_INVALID_RESPONSE"
    assert "header.payload.signature" not in str(exc.value)
    assert "header.payload.signature" not in json.dumps({"message": exc.value.message})
