from __future__ import annotations

from dataclasses import dataclass
import re

_DOC_EXTENSIONS = (".md", ".rst", ".txt", ".adoc")
_SECURITY_TERMS_RE = re.compile(r"(?i)\b(secret|token|password|api[_-]?key|auth|private key|credential)\b")
_STRONG_SECRET_RE = re.compile(
    r"(?i)(begin\s+private\s+key|ghp_[a-z0-9]{20,}|github_pat_[a-z0-9_]{20,}|akia[0-9a-z]{16})"
)
_WORKFLOW_OR_AUTH_PATH_RE = re.compile(
    r"(?i)(^\.github/workflows/|auth|security|crypto|secrets?\.|vault|credentials?)"
)


@dataclass(frozen=True)
class CalibratedSignal:
    severity: str
    bucket: str
    reason_code: str
    reason_short: str


def _is_docs_path(path: str) -> bool:
    lower = str(path or "").strip().lower()
    if not lower:
        return False
    if lower.startswith(("docs/", "documentation/")):
        return True
    return any(lower.endswith(ext) for ext in _DOC_EXTENSIONS)


def calibrate_security_signal(
    *,
    message: str,
    severity: str,
    evidence_paths: list[str] | None = None,
) -> CalibratedSignal:
    msg = str(message or "").strip()
    sev = str(severity or "low").strip().lower()
    if sev not in {"low", "medium", "high"}:
        sev = "low"
    paths = [str(path).strip() for path in (evidence_paths or []) if str(path).strip()]
    docs_only = bool(paths) and all(_is_docs_path(path) for path in paths)

    security_wording = bool(_SECURITY_TERMS_RE.search(msg))
    strong_secret_signal = bool(_STRONG_SECRET_RE.search(msg))
    auth_or_workflow_path = any(_WORKFLOW_OR_AUTH_PATH_RE.search(path or "") for path in paths)

    if docs_only and security_wording and not strong_secret_signal:
        return CalibratedSignal(
            severity="low",
            bucket="informational",
            reason_code="DOCS_SECURITY_WORDING_DOWNGRADED",
            reason_short="Docs-only security wording downgraded to informational.",
        )

    if strong_secret_signal:
        adjusted_severity = "high" if sev in {"medium", "high"} else "medium"
        return CalibratedSignal(
            severity=adjusted_severity,
            bucket="confirmed",
            reason_code="STRONG_SECRET_SIGNAL",
            reason_short="Strong secret-like signal preserved.",
        )

    if security_wording and auth_or_workflow_path and sev == "low":
        return CalibratedSignal(
            severity="medium",
            bucket="confirmed",
            reason_code="AUTH_OR_WORKFLOW_PATH_ELEVATED",
            reason_short="Auth/workflow context elevated security-related signal.",
        )

    return CalibratedSignal(
        severity=sev,
        bucket="confirmed",
        reason_code="NO_CALIBRATION_CHANGE",
        reason_short="Signal kept without calibration changes.",
    )
