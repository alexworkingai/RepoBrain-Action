from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
from jwt.algorithms import RSAAlgorithm
import pytest

from repobrain.oidc_verify import (
    GITHUB_OIDC_ISSUER,
    GitHubOidcVerificationError,
    GitHubOidcVerifier,
    validate_claims_match_identity,
)


def _build_signing_materials() -> tuple[object, dict[str, object], dict[str, str]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk["kid"] = "test-key"
    discovery = {"issuer": GITHUB_OIDC_ISSUER, "jwks_uri": "https://jwks.example"}
    return private_key, discovery, {"keys": [jwk]}


def _build_claims(now: datetime | None = None) -> dict[str, object]:
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
        "run_number": "5",
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


def _build_token(private_key: object, claims: dict[str, object]) -> str:
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "test-key"})


def _verifier(discovery: dict[str, object], jwks: dict[str, object]) -> GitHubOidcVerifier:
    return GitHubOidcVerifier(
        discovery_fetcher=lambda: discovery,
        jwks_fetcher=lambda _uri: jwks,
    )


def test_valid_mocked_github_oidc_token_verifies() -> None:
    private_key, discovery, jwks = _build_signing_materials()
    claims = _build_claims()
    token = _build_token(private_key, claims)

    verified = _verifier(discovery, jwks).verify_token(token)

    assert verified.repository == "owner/repo"
    assert verified.repository_id == "123"
    assert verified.workflow == "RepoBrain"


def test_wrong_issuer_fails() -> None:
    private_key, discovery, jwks = _build_signing_materials()
    claims = _build_claims()
    claims["iss"] = "https://issuer.example"
    token = _build_token(private_key, claims)

    with pytest.raises(GitHubOidcVerificationError) as exc:
        _verifier(discovery, jwks).verify_token(token)

    assert exc.value.code == "OIDC_INVALID_ISSUER"


def test_wrong_audience_fails() -> None:
    private_key, discovery, jwks = _build_signing_materials()
    claims = _build_claims()
    claims["aud"] = "other-audience"
    token = _build_token(private_key, claims)

    with pytest.raises(GitHubOidcVerificationError) as exc:
        _verifier(discovery, jwks).verify_token(token)

    assert exc.value.code == "OIDC_INVALID_AUDIENCE"


def test_expired_token_fails() -> None:
    private_key, discovery, jwks = _build_signing_materials()
    now = datetime.now(timezone.utc) - timedelta(minutes=10)
    token = _build_token(private_key, _build_claims(now))

    with pytest.raises(GitHubOidcVerificationError) as exc:
        _verifier(discovery, jwks).verify_token(token)

    assert exc.value.code == "OIDC_TOKEN_EXPIRED"


def test_invalid_signature_fails() -> None:
    private_key, discovery, _jwks = _build_signing_materials()
    other_key, _other_discovery, other_jwks = _build_signing_materials()
    token = _build_token(private_key, _build_claims())

    with pytest.raises(GitHubOidcVerificationError) as exc:
        _verifier(discovery, other_jwks).verify_token(token)

    assert exc.value.code == "OIDC_SIGNATURE_INVALID"
    assert token not in str(exc.value)
    assert other_key is not None


def test_missing_required_claim_fails() -> None:
    private_key, discovery, jwks = _build_signing_materials()
    claims = _build_claims()
    claims.pop("workflow_ref")
    token = _build_token(private_key, claims)

    with pytest.raises(GitHubOidcVerificationError) as exc:
        _verifier(discovery, jwks).verify_token(token)

    assert exc.value.code == "OIDC_REQUIRED_CLAIM_MISSING"


def test_discovery_and_jwks_failures_are_mapped() -> None:
    with pytest.raises(GitHubOidcVerificationError) as discovery_exc:
        GitHubOidcVerifier(discovery_fetcher=lambda: (_ for _ in ()).throw(RuntimeError("boom"))).verify_token("abc.def.ghi")
    assert discovery_exc.value.code == "OIDC_MALFORMED_TOKEN"

    private_key, discovery, _jwks = _build_signing_materials()
    token = _build_token(private_key, _build_claims())
    with pytest.raises(GitHubOidcVerificationError) as jwks_exc:
        GitHubOidcVerifier(
            discovery_fetcher=lambda: discovery,
            jwks_fetcher=lambda _uri: (_ for _ in ()).throw(RuntimeError("boom")),
        ).verify_token(token)
    assert jwks_exc.value.code == "OIDC_JWKS_FETCH_FAILED"


def test_claim_consistency_mismatch_fails_closed() -> None:
    private_key, discovery, jwks = _build_signing_materials()
    token = _build_token(private_key, _build_claims())
    verified = _verifier(discovery, jwks).verify_token(token)

    with pytest.raises(GitHubOidcVerificationError) as exc:
        validate_claims_match_identity(
            verified,
            {
                "repository": {"full_name": "owner/other", "id": "123", "owner": "owner", "owner_id": "456"},
                "workflow": {
                    "run_id": "999",
                    "run_number": "5",
                    "run_attempt": "1",
                    "actor": "partner-user",
                    "actor_id": "777",
                    "workflow": "RepoBrain",
                    "workflow_ref": "owner/repo/.github/workflows/repobrain.yml@refs/heads/main",
                    "workflow_sha": "abc123",
                    "event_name": "issue_comment",
                    "ref": "refs/heads/main",
                    "sha": "deadbeef",
                },
            },
        )

    assert exc.value.code == "OIDC_REPOSITORY_MISMATCH"

