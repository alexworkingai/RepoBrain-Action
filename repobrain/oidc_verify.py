from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Callable, Mapping

import jwt
from jwt import (
    DecodeError,
    ExpiredSignatureError,
    ImmatureSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidSignatureError,
    InvalidTokenError,
    MissingRequiredClaimError,
)
from jwt.algorithms import RSAAlgorithm
import requests


GITHUB_OIDC_ISSUER = "https://token.actions.githubusercontent.com"
GITHUB_OIDC_DISCOVERY_URL = f"{GITHUB_OIDC_ISSUER}/.well-known/openid-configuration"


@dataclass(frozen=True)
class GitHubOidcVerifierConfig:
    expected_issuer: str = GITHUB_OIDC_ISSUER
    expected_audience: str = "repobrain-api"
    allowed_algorithms: tuple[str, ...] = ("RS256",)
    clock_skew_seconds: int = 60
    required_claims: tuple[str, ...] = (
        "iss",
        "aud",
        "exp",
        "iat",
        "sub",
        "repository",
        "repository_id",
        "repository_owner",
        "repository_owner_id",
        "run_id",
        "run_number",
        "run_attempt",
        "actor",
        "actor_id",
        "workflow",
        "workflow_ref",
        "workflow_sha",
        "event_name",
        "ref",
        "sha",
    )


@dataclass(frozen=True)
class VerifiedGitHubOidcClaims:
    issuer: str
    audience: str
    subject: str
    repository: str
    repository_id: str
    repository_owner: str
    repository_owner_id: str
    run_id: str
    run_number: str
    run_attempt: str
    actor: str
    actor_id: str
    workflow: str
    workflow_ref: str
    workflow_sha: str
    event_name: str
    ref: str
    sha: str
    repository_visibility: str | None = None
    ref_protected: str | None = None
    head_ref: str | None = None
    base_ref: str | None = None
    job_workflow_ref: str | None = None
    job_workflow_sha: str | None = None
    runner_environment: str | None = None
    environment: str | None = None


class GitHubOidcVerificationError(ValueError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


class GitHubOidcVerifier:
    def __init__(
        self,
        *,
        config: GitHubOidcVerifierConfig | None = None,
        discovery_fetcher: Callable[[], Mapping[str, Any]] | None = None,
        jwks_fetcher: Callable[[str], Mapping[str, Any]] | None = None,
        request_get: Callable[..., Any] | None = None,
    ) -> None:
        self.config = config or GitHubOidcVerifierConfig()
        self._discovery_fetcher = discovery_fetcher
        self._jwks_fetcher = jwks_fetcher
        self._request_get = request_get or requests.get

    def verify_token(self, token: str, *, expected_audience: str | None = None) -> VerifiedGitHubOidcClaims:
        raw_token = str(token or "").strip()
        if not raw_token:
            raise GitHubOidcVerificationError(
                "OIDC_MISSING_TOKEN",
                "GitHub OIDC token is missing.",
            )

        try:
            header = jwt.get_unverified_header(raw_token)
        except DecodeError as exc:
            raise GitHubOidcVerificationError(
                "OIDC_MALFORMED_TOKEN",
                "GitHub OIDC token could not be parsed.",
            ) from exc

        algorithm = str(header.get("alg", "") or "").strip()
        if algorithm not in self.config.allowed_algorithms:
            raise GitHubOidcVerificationError(
                "OIDC_SIGNATURE_INVALID",
                "GitHub OIDC token algorithm is not allowed.",
            )
        kid = str(header.get("kid", "") or "").strip()
        if not kid:
            raise GitHubOidcVerificationError(
                "OIDC_SIGNATURE_INVALID",
                "GitHub OIDC token key identifier is missing.",
            )

        discovery = self._load_discovery()
        jwks_uri = str(discovery.get("jwks_uri", "") or "").strip()
        if not jwks_uri:
            raise GitHubOidcVerificationError(
                "OIDC_DISCOVERY_FAILED",
                "GitHub OIDC discovery metadata did not provide a JWKS URI.",
                retryable=True,
            )
        jwks = self._load_jwks(jwks_uri)
        public_key = self._resolve_public_key(jwks, kid)

        audience = expected_audience or self.config.expected_audience
        try:
            payload = jwt.decode(
                raw_token,
                key=public_key,
                algorithms=list(self.config.allowed_algorithms),
                audience=audience,
                issuer=self.config.expected_issuer,
                leeway=self.config.clock_skew_seconds,
                options={"require": list(self.config.required_claims)},
            )
        except ExpiredSignatureError as exc:
            raise GitHubOidcVerificationError(
                "OIDC_TOKEN_EXPIRED",
                "GitHub OIDC token expired.",
            ) from exc
        except ImmatureSignatureError as exc:
            raise GitHubOidcVerificationError(
                "OIDC_TOKEN_NOT_YET_VALID",
                "GitHub OIDC token is not yet valid.",
            ) from exc
        except InvalidIssuerError as exc:
            raise GitHubOidcVerificationError(
                "OIDC_INVALID_ISSUER",
                "GitHub OIDC issuer did not match the expected issuer.",
            ) from exc
        except InvalidAudienceError as exc:
            raise GitHubOidcVerificationError(
                "OIDC_INVALID_AUDIENCE",
                "GitHub OIDC audience did not match expected audience.",
            ) from exc
        except MissingRequiredClaimError as exc:
            raise GitHubOidcVerificationError(
                "OIDC_REQUIRED_CLAIM_MISSING",
                "GitHub OIDC token is missing a required claim.",
            ) from exc
        except InvalidSignatureError as exc:
            raise GitHubOidcVerificationError(
                "OIDC_SIGNATURE_INVALID",
                "GitHub OIDC signature validation failed.",
            ) from exc
        except DecodeError as exc:
            raise GitHubOidcVerificationError(
                "OIDC_MALFORMED_TOKEN",
                "GitHub OIDC token is malformed.",
            ) from exc
        except InvalidTokenError as exc:
            raise GitHubOidcVerificationError(
                "OIDC_SIGNATURE_INVALID",
                "GitHub OIDC token verification failed.",
            ) from exc

        return VerifiedGitHubOidcClaims(
            issuer=str(payload["iss"]),
            audience=_claim_text(payload.get("aud")),
            subject=str(payload["sub"]),
            repository=_claim_text(payload.get("repository")),
            repository_id=_claim_text(payload.get("repository_id")),
            repository_owner=_claim_text(payload.get("repository_owner")),
            repository_owner_id=_claim_text(payload.get("repository_owner_id")),
            run_id=_claim_text(payload.get("run_id")),
            run_number=_claim_text(payload.get("run_number")),
            run_attempt=_claim_text(payload.get("run_attempt")),
            actor=_claim_text(payload.get("actor")),
            actor_id=_claim_text(payload.get("actor_id")),
            workflow=_claim_text(payload.get("workflow")),
            workflow_ref=_claim_text(payload.get("workflow_ref")),
            workflow_sha=_claim_text(payload.get("workflow_sha")),
            event_name=_claim_text(payload.get("event_name")),
            ref=_claim_text(payload.get("ref")),
            sha=_claim_text(payload.get("sha")),
            repository_visibility=_optional_claim(payload.get("repository_visibility")),
            ref_protected=_optional_claim(payload.get("ref_protected")),
            head_ref=_optional_claim(payload.get("head_ref")),
            base_ref=_optional_claim(payload.get("base_ref")),
            job_workflow_ref=_optional_claim(payload.get("job_workflow_ref")),
            job_workflow_sha=_optional_claim(payload.get("job_workflow_sha")),
            runner_environment=_optional_claim(payload.get("runner_environment")),
            environment=_optional_claim(payload.get("environment")),
        )

    def _load_discovery(self) -> Mapping[str, Any]:
        if self._discovery_fetcher is not None:
            try:
                return dict(self._discovery_fetcher())
            except Exception as exc:
                raise GitHubOidcVerificationError(
                    "OIDC_DISCOVERY_FAILED",
                    "GitHub OIDC discovery metadata could not be loaded.",
                    retryable=True,
                ) from exc
        try:
            response = self._request_get(GITHUB_OIDC_DISCOVERY_URL, timeout=10)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise GitHubOidcVerificationError(
                "OIDC_DISCOVERY_FAILED",
                "GitHub OIDC discovery metadata could not be loaded.",
                retryable=True,
            ) from exc
        if not isinstance(payload, Mapping):
            raise GitHubOidcVerificationError(
                "OIDC_DISCOVERY_FAILED",
                "GitHub OIDC discovery metadata is invalid.",
                retryable=True,
            )
        return dict(payload)

    def _load_jwks(self, jwks_uri: str) -> Mapping[str, Any]:
        if self._jwks_fetcher is not None:
            try:
                return dict(self._jwks_fetcher(jwks_uri))
            except Exception as exc:
                raise GitHubOidcVerificationError(
                    "OIDC_JWKS_FETCH_FAILED",
                    "GitHub OIDC JWKS could not be loaded.",
                    retryable=True,
                ) from exc
        try:
            response = self._request_get(jwks_uri, timeout=10)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise GitHubOidcVerificationError(
                "OIDC_JWKS_FETCH_FAILED",
                "GitHub OIDC JWKS could not be loaded.",
                retryable=True,
            ) from exc
        if not isinstance(payload, Mapping):
            raise GitHubOidcVerificationError(
                "OIDC_JWKS_FETCH_FAILED",
                "GitHub OIDC JWKS payload is invalid.",
                retryable=True,
            )
        return dict(payload)

    def _resolve_public_key(self, jwks: Mapping[str, Any], kid: str) -> Any:
        keys = jwks.get("keys", [])
        if not isinstance(keys, list):
            raise GitHubOidcVerificationError(
                "OIDC_JWKS_FETCH_FAILED",
                "GitHub OIDC JWKS key set is invalid.",
                retryable=True,
            )
        for item in keys:
            if not isinstance(item, Mapping):
                continue
            if str(item.get("kid", "") or "").strip() != kid:
                continue
            try:
                return RSAAlgorithm.from_jwk(json.dumps(dict(item)))
            except Exception as exc:  # pragma: no cover - crypto library error path
                raise GitHubOidcVerificationError(
                    "OIDC_JWKS_FETCH_FAILED",
                    "GitHub OIDC JWKS key could not be parsed.",
                    retryable=True,
                ) from exc
        raise GitHubOidcVerificationError(
            "OIDC_SIGNATURE_INVALID",
            "GitHub OIDC signing key was not found in the JWKS set.",
        )


def validate_claims_match_identity(
    claims: VerifiedGitHubOidcClaims,
    identity: Mapping[str, Any],
) -> None:
    repository = identity.get("repository", {}) if isinstance(identity.get("repository"), Mapping) else {}
    workflow = identity.get("workflow", {}) if isinstance(identity.get("workflow"), Mapping) else {}

    repository_pairs = {
        "repository.full_name": (claims.repository, repository.get("full_name")),
        "repository.id": (claims.repository_id, repository.get("id")),
        "repository.owner": (claims.repository_owner, repository.get("owner")),
        "repository.owner_id": (claims.repository_owner_id, repository.get("owner_id")),
    }
    for _field_name, (verified_value, identity_value) in repository_pairs.items():
        if _normalize_compare(verified_value) != _normalize_compare(identity_value):
            raise GitHubOidcVerificationError(
                "OIDC_REPOSITORY_MISMATCH",
                "GitHub OIDC repository claims did not match the identity envelope.",
            )

    workflow_pairs = {
        "workflow.run_id": (claims.run_id, workflow.get("run_id")),
        "workflow.run_number": (claims.run_number, workflow.get("run_number")),
        "workflow.run_attempt": (claims.run_attempt, workflow.get("run_attempt")),
        "workflow.actor": (claims.actor, workflow.get("actor")),
        "workflow.actor_id": (claims.actor_id, workflow.get("actor_id")),
        "workflow.workflow": (claims.workflow, workflow.get("workflow")),
        "workflow.workflow_ref": (claims.workflow_ref, workflow.get("workflow_ref")),
        "workflow.workflow_sha": (claims.workflow_sha, workflow.get("workflow_sha")),
        "workflow.event_name": (claims.event_name, workflow.get("event_name")),
        "workflow.ref": (claims.ref, workflow.get("ref")),
        "workflow.sha": (claims.sha, workflow.get("sha")),
    }
    for _field_name, (verified_value, identity_value) in workflow_pairs.items():
        if _normalize_compare(verified_value) != _normalize_compare(identity_value):
            raise GitHubOidcVerificationError(
                "OIDC_WORKFLOW_MISMATCH",
                "GitHub OIDC workflow claims did not match the identity envelope.",
            )


def _claim_text(value: Any) -> str:
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value or "")


def _optional_claim(value: Any) -> str | None:
    text = _claim_text(value).strip()
    return text or None


def _normalize_compare(value: Any) -> str:
    return str(value or "").strip()
