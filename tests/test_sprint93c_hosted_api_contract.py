from __future__ import annotations

import json

import pytest

from repobrain.hosted_api_contract import (
    BOUNDED_EVIDENCE_VERSION,
    GITHUB_ACTION_AUDIT_REQUEST_VERSION,
    GITHUB_ACTION_AUDIT_RESPONSE_VERSION,
    HostedApiContractError,
    build_error_response,
    build_github_action_audit_request,
    sanitize_request_for_logs,
    validate_github_action_audit_request,
)


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


def test_contract_builder_and_validator_round_trip() -> None:
    payload = build_github_action_audit_request(
        identity=_identity(),
        oidc_jwt="header.payload.signature",
        command={"route": "audit", "profile": "partner-pilot", "raw": "/repobrain audit"},
        evidence={"version": BOUNDED_EVIDENCE_VERSION, "items": [], "limits": {}, "redaction": {}},
    )

    validated = validate_github_action_audit_request(payload)
    preview = sanitize_request_for_logs(payload)

    assert validated["version"] == GITHUB_ACTION_AUDIT_REQUEST_VERSION
    assert validated["command"]["route"] == "audit"
    assert preview["oidc_jwt"] == "[redacted-oidc-jwt]"
    assert "header.payload.signature" not in json.dumps(preview, sort_keys=True)


def test_contract_rejects_large_evidence() -> None:
    payload = build_github_action_audit_request(
        identity=_identity(),
        oidc_jwt="header.payload.signature",
        command={"route": "audit", "profile": "partner-pilot", "raw": "/repobrain audit"},
        evidence={
            "version": BOUNDED_EVIDENCE_VERSION,
            "items": [{"path": f"src/file_{idx}.py"} for idx in range(65)],
            "limits": {},
            "redaction": {},
        },
    )

    with pytest.raises(HostedApiContractError) as exc:
        validate_github_action_audit_request(payload)

    assert exc.value.code == "EVIDENCE_TOO_LARGE"


def test_error_response_is_versioned_and_public_safe() -> None:
    response = build_error_response(
        code="OIDC_INVALID_AUDIENCE",
        message="GitHub OIDC audience did not match expected audience.",
        retryable=False,
    )

    assert response["version"] == GITHUB_ACTION_AUDIT_RESPONSE_VERSION
    assert response["status"] == "error"
    assert response["error"]["code"] == "OIDC_INVALID_AUDIENCE"
    assert response["safety"]["token_redacted"] is True

