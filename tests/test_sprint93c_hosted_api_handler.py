from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
from jwt.algorithms import RSAAlgorithm

from repobrain.hosted_api_contract import BOUNDED_EVIDENCE_VERSION, build_github_action_audit_request
from repobrain.hosted_api_handler import handle_github_action_audit_request
from repobrain.hosted_topocore_adapter import (
    HostedTopoCoreAuditAdapter,
    HostedTopoCoreAuditRequest,
    HostedTopoCoreAuditResult,
)
from repobrain.oidc_verify import GITHUB_OIDC_ISSUER, GitHubOidcVerifier
from repobrain.quota import InMemoryQuotaStore
from repobrain.tenant_store import InMemoryTenantStore


def _build_signing_materials() -> tuple[object, dict[str, object], dict[str, object]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk["kid"] = "test-key"
    discovery = {"issuer": GITHUB_OIDC_ISSUER, "jwks_uri": "https://jwks.example"}
    return private_key, discovery, {"keys": [jwk]}


def _claims(now: datetime | None = None) -> dict[str, object]:
    issued = now or datetime.now(timezone.utc)
    return {
        "iss": GITHUB_OIDC_ISSUER,
        "aud": "repobrain-api",
        "sub": "repo:owner/repo:ref:refs/heads/main",
        "repository": "owner/repo",
        "repository_id": "123",
        "repository_owner": "owner",
        "repository_owner_id": "456",
        "run_id": "999",
        "run_number": "3",
        "run_attempt": "1",
        "actor": "partner-user",
        "actor_id": "777",
        "workflow": "RepoBrain",
        "workflow_ref": "owner/repo/.github/workflows/repobrain.yml@refs/heads/main",
        "workflow_sha": "abc123",
        "event_name": "issue_comment",
        "ref": "refs/heads/main",
        "sha": "deadbeef",
        "iat": int(issued.timestamp()),
        "nbf": int((issued - timedelta(seconds=5)).timestamp()),
        "exp": int((issued + timedelta(minutes=5)).timestamp()),
    }


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


class _FakeAdapter(HostedTopoCoreAuditAdapter):
    def __init__(self, *, score: int = 86, band: str = "STRONG", markdown: str = "Safe markdown report.") -> None:
        self.score = score
        self.band = band
        self.markdown = markdown
        self.calls = 0

    def run_audit(self, request: HostedTopoCoreAuditRequest) -> HostedTopoCoreAuditResult:
        self.calls += 1
        return HostedTopoCoreAuditResult(
            score=self.score,
            band=self.band,
            markdown=self.markdown,
        )


def _verifier() -> GitHubOidcVerifier:
    _private_key, discovery, jwks = _build_signing_materials()
    return GitHubOidcVerifier(
        discovery_fetcher=lambda: discovery,
        jwks_fetcher=lambda _uri: jwks,
    )


def _request(private_key: object, *, identity: dict[str, object] | None = None) -> dict[str, object]:
    token = jwt.encode(_claims(), private_key, algorithm="RS256", headers={"kid": "test-key"})
    return build_github_action_audit_request(
        identity=identity or _identity(),
        oidc_jwt=token,
        command={"route": "audit", "profile": "partner-pilot", "raw": "/repobrain audit"},
        evidence={"version": BOUNDED_EVIDENCE_VERSION, "items": [], "limits": {}, "redaction": {}},
    )


def test_successful_response_includes_tenant_quota_and_topocore_runtime() -> None:
    private_key, discovery, jwks = _build_signing_materials()
    response = handle_github_action_audit_request(
        _request(private_key),
        verifier=GitHubOidcVerifier(
            discovery_fetcher=lambda: discovery,
            jwks_fetcher=lambda _uri: jwks,
        ),
        tenant_store=InMemoryTenantStore(),
        quota_store=InMemoryQuotaStore(),
        topocore_adapter=_FakeAdapter(),
    )

    assert response["status"] == "ok"
    assert response["tenant"]["tenant_id"] == "gh_owner_456_repo_123"
    assert response["tenant"]["auto_provisioned"] is True
    assert response["quota"]["status"] == "ok"
    assert response["quota"]["remaining"] == 19
    assert response["runtime"]["score_authority"] == "TopoCore"
    assert response["runtime"]["topocore_runtime"] == "private_server_side"
    assert response["safety"]["branch_commit_pr_created"] is False


def test_self_service_disabled_returns_safe_error() -> None:
    private_key, discovery, jwks = _build_signing_materials()
    identity = _identity()
    identity["self_service"] = {"enabled": False, "terms_accepted": True, "mode": "partner-pilot"}

    response = handle_github_action_audit_request(
        _request(private_key, identity=identity),
        verifier=GitHubOidcVerifier(
            discovery_fetcher=lambda: discovery,
            jwks_fetcher=lambda _uri: jwks,
        ),
    )

    assert response["status"] == "error"
    assert response["error"]["code"] == "SELF_SERVICE_DISABLED"


def test_terms_not_accepted_returns_safe_error() -> None:
    private_key, discovery, jwks = _build_signing_materials()
    identity = _identity()
    identity["self_service"] = {"enabled": True, "terms_accepted": False, "mode": "partner-pilot"}

    response = handle_github_action_audit_request(
        _request(private_key, identity=identity),
        verifier=GitHubOidcVerifier(
            discovery_fetcher=lambda: discovery,
            jwks_fetcher=lambda _uri: jwks,
        ),
    )

    assert response["status"] == "error"
    assert response["error"]["code"] == "TERMS_NOT_ACCEPTED"


def test_claim_mismatch_fails_closed() -> None:
    private_key, discovery, jwks = _build_signing_materials()
    identity = _identity()
    identity["repository"]["full_name"] = "owner/other"

    response = handle_github_action_audit_request(
        _request(private_key, identity=identity),
        verifier=GitHubOidcVerifier(
            discovery_fetcher=lambda: discovery,
            jwks_fetcher=lambda _uri: jwks,
        ),
    )

    assert response["status"] == "error"
    assert response["error"]["code"] == "OIDC_REPOSITORY_MISMATCH"


def test_quota_exceeded_blocks_before_topocore() -> None:
    private_key, discovery, jwks = _build_signing_materials()
    adapter = _FakeAdapter()
    quota_store = InMemoryQuotaStore()
    tenant_store = InMemoryTenantStore()
    verifier = GitHubOidcVerifier(
        discovery_fetcher=lambda: discovery,
        jwks_fetcher=lambda _uri: jwks,
    )
    for _ in range(20):
        response = handle_github_action_audit_request(
            _request(private_key),
            verifier=verifier,
            tenant_store=tenant_store,
            quota_store=quota_store,
            topocore_adapter=adapter,
        )
        assert response["status"] == "ok"

    blocked = handle_github_action_audit_request(
        _request(private_key),
        verifier=verifier,
        tenant_store=tenant_store,
        quota_store=quota_store,
        topocore_adapter=adapter,
    )

    assert blocked["status"] == "error"
    assert blocked["error"]["code"] == "QUOTA_EXCEEDED"
    assert adapter.calls == 20


def test_adapter_unavailable_returns_topocore_unavailable_safely() -> None:
    private_key, discovery, jwks = _build_signing_materials()
    response = handle_github_action_audit_request(
        _request(private_key),
        verifier=GitHubOidcVerifier(
            discovery_fetcher=lambda: discovery,
            jwks_fetcher=lambda _uri: jwks,
        ),
    )

    rendered = json.dumps(response, sort_keys=True)
    assert response["status"] == "error"
    assert response["error"]["code"] == "TOPOCORE_UNAVAILABLE"
    assert "header.payload.signature" not in rendered
    assert "private runtime paths" not in rendered.lower()

