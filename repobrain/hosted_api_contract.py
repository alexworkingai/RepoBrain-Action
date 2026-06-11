from __future__ import annotations

import json
import re
from typing import Any, Mapping, Sequence


GITHUB_ACTION_AUDIT_REQUEST_VERSION = "repobrain.github_action_audit_request.v1"
GITHUB_ACTION_AUDIT_RESPONSE_VERSION = "repobrain.github_action_audit_response.v1"
GITHUB_OIDC_IDENTITY_VERSION = "repobrain.github_oidc_identity.v1"
PARTNER_TENANT_VERSION = "repobrain.partner_tenant.v1"
PARTNER_QUOTA_VERSION = "repobrain.partner_quota.v1"
BOUNDED_EVIDENCE_VERSION = "repobrain.bounded_evidence.v1"
HOSTED_API_ENDPOINT_PATH = "/v1/github/actions/audit"

MAX_EVIDENCE_ITEMS = 64
MAX_EVIDENCE_BYTES = 200_000
MAX_MARKDOWN_CHARS = 12_000

ERROR_CODES = {
    "EVIDENCE_TOO_LARGE",
    "INTERNAL_ERROR_REDACTED",
    "INVALID_REQUEST_SHAPE",
    "INVALID_REQUEST_VERSION",
    "OIDC_DISCOVERY_FAILED",
    "OIDC_INVALID_AUDIENCE",
    "OIDC_INVALID_ISSUER",
    "OIDC_JWKS_FETCH_FAILED",
    "OIDC_MALFORMED_TOKEN",
    "OIDC_MISSING_TOKEN",
    "OIDC_REPOSITORY_MISMATCH",
    "OIDC_REQUIRED_CLAIM_MISSING",
    "OIDC_SIGNATURE_INVALID",
    "OIDC_TOKEN_EXPIRED",
    "OIDC_TOKEN_NOT_YET_VALID",
    "OIDC_WORKFLOW_MISMATCH",
    "QUOTA_EXCEEDED",
    "SELF_SERVICE_DISABLED",
    "TERMS_NOT_ACCEPTED",
    "TOPOCORE_UNAVAILABLE",
}

_TOKEN_PATTERNS = (
    re.compile(r"\bghp_[A-Za-z0-9_]+\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]+\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)
_PRIVATE_PATH_PATTERNS = (
    re.compile(r"(?i)\.topocore-v6"),
    re.compile(r"(?i)ariadna_minsk"),
    re.compile(r"(?i)c:\\users"),
    re.compile(r"(?i)/mnt/data"),
)
_AUTHORIZATION_RE = re.compile(r"(?i)\bauthorization\s*:")
_OIDC_HEADER_TOKEN_RE = re.compile(r"\b[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")


class HostedApiContractError(ValueError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


def build_github_action_audit_request(
    *,
    identity: Mapping[str, Any],
    oidc_jwt: str,
    command: Mapping[str, Any],
    evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "version": GITHUB_ACTION_AUDIT_REQUEST_VERSION,
        "identity": dict(identity),
        "oidc_jwt": str(oidc_jwt or "").strip(),
        "command": dict(command),
        "evidence": dict(evidence or {"version": BOUNDED_EVIDENCE_VERSION, "items": [], "limits": {}, "redaction": {}}),
    }


def sanitize_request_for_logs(request_json: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(request_json)
    if "oidc_jwt" in payload:
        token_present = bool(str(payload.get("oidc_jwt", "") or "").strip())
        payload["oidc_jwt"] = "[redacted-oidc-jwt]" if token_present else ""
    _assert_public_safe(payload)
    return payload


def validate_github_action_audit_request(request_json: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(request_json, Mapping):
        raise HostedApiContractError(
            "INVALID_REQUEST_SHAPE",
            "Hosted audit request must be a JSON object.",
        )
    version = str(request_json.get("version", "") or "").strip()
    if version != GITHUB_ACTION_AUDIT_REQUEST_VERSION:
        raise HostedApiContractError(
            "INVALID_REQUEST_VERSION",
            "Hosted audit request version is invalid.",
        )

    identity = request_json.get("identity", {})
    if not isinstance(identity, Mapping):
        raise HostedApiContractError(
            "INVALID_REQUEST_SHAPE",
            "Hosted audit request identity block is invalid.",
        )
    identity_version = str(identity.get("version", "") or "").strip()
    if identity_version != GITHUB_OIDC_IDENTITY_VERSION:
        raise HostedApiContractError(
            "INVALID_REQUEST_SHAPE",
            "Hosted audit request identity version is invalid.",
        )

    oidc_jwt = str(request_json.get("oidc_jwt", "") or "").strip()
    command = request_json.get("command", {})
    if not isinstance(command, Mapping):
        raise HostedApiContractError(
            "INVALID_REQUEST_SHAPE",
            "Hosted audit request command block is invalid.",
        )
    evidence = request_json.get("evidence", {})
    if not isinstance(evidence, Mapping):
        raise HostedApiContractError(
            "INVALID_REQUEST_SHAPE",
            "Hosted audit request evidence block is invalid.",
        )
    _validate_bounded_evidence(evidence)

    normalized = {
        "version": GITHUB_ACTION_AUDIT_REQUEST_VERSION,
        "identity": dict(identity),
        "oidc_jwt": oidc_jwt,
        "command": {
            "route": str(command.get("route", "") or "").strip().lower(),
            "profile": str(command.get("profile", "") or "").strip() or "default",
            "raw": str(command.get("raw", "") or "").strip(),
        },
        "evidence": dict(evidence),
    }
    _assert_public_safe(sanitize_request_for_logs(normalized))
    return normalized


def build_success_response(
    *,
    tenant: Mapping[str, Any],
    quota: Mapping[str, Any],
    report: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "version": GITHUB_ACTION_AUDIT_RESPONSE_VERSION,
        "status": "ok",
        "tenant": dict(tenant),
        "quota": dict(quota),
        "report": dict(report),
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
    _assert_public_safe(payload)
    return payload


def build_error_response(
    *,
    code: str,
    message: str,
    retryable: bool,
) -> dict[str, Any]:
    if code not in ERROR_CODES:
        code = "INTERNAL_ERROR_REDACTED"
    payload = {
        "version": GITHUB_ACTION_AUDIT_RESPONSE_VERSION,
        "status": "error",
        "error": {
            "code": code,
            "message": _safe_text(message, max_length=240),
            "retryable": bool(retryable),
        },
        "safety": {
            "token_redacted": True,
            "private_runtime_exposed": False,
        },
    }
    _assert_public_safe(payload)
    return payload


def _validate_bounded_evidence(evidence: Mapping[str, Any]) -> None:
    version = str(evidence.get("version", "") or "").strip()
    if version and version != BOUNDED_EVIDENCE_VERSION:
        raise HostedApiContractError(
            "INVALID_REQUEST_SHAPE",
            "Evidence version is invalid.",
        )
    items = evidence.get("items", [])
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes)):
        raise HostedApiContractError(
            "INVALID_REQUEST_SHAPE",
            "Evidence items must be a list.",
        )
    if len(items) > MAX_EVIDENCE_ITEMS:
        raise HostedApiContractError(
            "EVIDENCE_TOO_LARGE",
            "Evidence payload exceeded the allowed bounded item count.",
        )
    try:
        raw_size = len(json.dumps(evidence))
    except (TypeError, ValueError):
        raise HostedApiContractError(
            "INVALID_REQUEST_SHAPE",
            "Evidence payload could not be serialized safely.",
        ) from None
    if raw_size > MAX_EVIDENCE_BYTES:
        raise HostedApiContractError(
            "EVIDENCE_TOO_LARGE",
            "Evidence payload exceeded the allowed bounded size.",
        )
    _assert_public_safe(evidence)


def _assert_public_safe(value: Any) -> None:
    text = json.dumps(value, sort_keys=True, default=str)
    if _AUTHORIZATION_RE.search(text):
        raise HostedApiContractError(
            "INTERNAL_ERROR_REDACTED",
            "Hosted API payload contained an authorization header reference.",
        )
    for pattern in _TOKEN_PATTERNS:
        if pattern.search(text):
            raise HostedApiContractError(
                "INTERNAL_ERROR_REDACTED",
                "Hosted API payload contained a secret-like token.",
            )
    for pattern in _PRIVATE_PATH_PATTERNS:
        if pattern.search(text):
            raise HostedApiContractError(
                "INTERNAL_ERROR_REDACTED",
                "Hosted API payload contained a private runtime path.",
            )


def _safe_text(value: Any, *, max_length: int) -> str:
    text = " ".join(str(value or "").split())
    text = _AUTHORIZATION_RE.sub("[redacted-authorization]", text)
    for pattern in _TOKEN_PATTERNS:
        text = pattern.sub("[redacted-secret]", text)
    if text.count(".") >= 2 and _OIDC_HEADER_TOKEN_RE.search(text):
        text = _OIDC_HEADER_TOKEN_RE.sub("[redacted-oidc-jwt]", text)
    for pattern in _PRIVATE_PATH_PATTERNS:
        text = pattern.sub("[redacted-path]", text)
    return text[:max_length].strip()
