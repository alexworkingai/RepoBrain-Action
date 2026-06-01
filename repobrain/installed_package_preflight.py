from __future__ import annotations

import re

_WINDOWS_PATH_RE = re.compile(r"[A-Za-z]:\\[^\s`'\"]+")
_POSIX_PATH_RE = re.compile(r"(?<![A-Za-z0-9_])/(?:[^/\s`'\"]+/)*[^/\s`'\"]+")
_GITHUB_PAT_RE = re.compile(r"github_pat_[A-Za-z0-9_]+")
_GHP_RE = re.compile(r"ghp_[A-Za-z0-9]+")
_BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9._\-]+", flags=re.IGNORECASE)


def sanitize_installed_package_preflight_text(text: str) -> str:
    normalized = " ".join(str(text or "").split())
    redacted = _GITHUB_PAT_RE.sub("[redacted-token]", normalized)
    redacted = _GHP_RE.sub("[redacted-token]", redacted)
    redacted = _BEARER_RE.sub("Bearer [redacted-token]", redacted)
    redacted = _WINDOWS_PATH_RE.sub("[redacted-path]", redacted)
    redacted = _POSIX_PATH_RE.sub("[redacted-path]", redacted)
    return redacted


def classify_installed_package_preflight_failure(message: str) -> str:
    sanitized = sanitize_installed_package_preflight_text(message)
    lowered = sanitized.lower()

    if any(
        token in lowered
        for token in (
            "resource not accessible",
            "bad credentials",
            "forbidden",
            "unauthorized",
            "authentication failed",
            "permission denied",
            "requires authentication",
            "insufficient permission",
            "token scope",
        )
    ):
        return "PACKAGE_AUTH_FAILED"

    if any(
        token in lowered
        for token in (
            "digest mismatch",
            "hash mismatch",
            "sha256 mismatch",
            "does not match expected digest",
        )
    ):
        return "PACKAGE_DIGEST_MISMATCH"

    if any(
        token in lowered
        for token in (
            "artifact not found",
            "package not found",
            "no matching distribution found",
            "404 not found",
        )
    ):
        return "PACKAGE_NOT_FOUND"

    if any(
        token in lowered
        for token in (
            "subprocess-exited-with-error",
            "pip install failed",
            "installation failed",
            "failed building wheel",
        )
    ):
        return "PACKAGE_INSTALL_FAILED"

    if any(
        token in lowered
        for token in (
            "no module named",
            "import failed",
            "module not found",
            "importerror",
        )
    ):
        return "PACKAGE_IMPORT_FAILED"

    if any(
        token in lowered
        for token in (
            "capability missing",
            "run_audit_score_v1 is unavailable",
            "audit scoring capability is unavailable",
        )
    ):
        return "CAPABILITY_MISSING"

    if any(
        token in lowered
        for token in (
            "contract rejected",
            "topocore.audit_score.v1 rejected",
            "response rejected by contract guard",
        )
    ):
        return "CONTRACT_REJECTED"

    if any(
        token in lowered
        for token in (
            "workflow policy blocked",
            "secret not configured",
            "missing required secret",
            "policy blocked",
        )
    ):
        return "WORKFLOW_POLICY_BLOCKED"

    return "UNKNOWN_SANITIZED"


__all__ = [
    "classify_installed_package_preflight_failure",
    "sanitize_installed_package_preflight_text",
]
