"""Sanitized advisory artifact helper for future TopoCore v6 analysis.

This module is dependency-free. It does not import TopoCore v6, does not call
external systems, does not write artifacts to disk, and does not change current
RepoBrain runtime behavior.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any

from repobrain.topocore_v6_decision_diff import (
    DecisionDiffReport,
    DecisionDiffSeverity,
)

_FORBIDDEN_FIELDS = frozenset(
    {
        ".env",
        "api_key",
        "artifact_internals",
        "compression_stats",
        "decide_raw",
        "dotenv",
        "env",
        "event_internals",
        "governance_internals",
        "hidden_prompt",
        "password",
        "private_key",
        "prompt",
        "raw_code",
        "raw_diff",
        "raw_query",
        "raw_trace",
        "secret",
        "system_prompt",
        "token",
        "trace",
    }
)

_ALLOWED_COMMANDS = frozenset({"ask", "review", "fix", "verify", "unknown"})
_ALLOWED_MODES = frozenset({"manual_local", "future_shadow_advisory"})
_SCHEMA_VERSION = "topocore-v6-advisory-artifact/v1"
_ARTIFACT_KIND = "topocore_v6_advisory"


class AdvisoryArtifactError(ValueError):
    """Raised when an advisory artifact input or payload is unsafe."""


@dataclass(frozen=True)
class AdvisoryArtifactMetadata:
    mode: str = "manual_local"
    command: str = "unknown"
    validation_run_label: str = ""
    fixture_name: str = ""
    future_shadow_persist_allowed: bool = False


@dataclass(frozen=True)
class AdvisoryArtifactInput:
    v5_primary_snapshot: dict[str, Any]
    v6_advisory_snapshot: dict[str, Any]
    decision_diff: dict[str, Any]
    metadata: AdvisoryArtifactMetadata = field(default_factory=AdvisoryArtifactMetadata)


@dataclass(frozen=True)
class AdvisoryArtifact:
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _sanitize_mapping(value)
    if isinstance(value, (list, tuple)):
        return [_sanitize_value(item) for item in value]
    return value


def _sanitize_mapping(mapping: Mapping[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in mapping.items():
        normalized_key = _normalize_text(key)
        if not normalized_key:
            continue
        lowered = normalized_key.lower()
        if lowered in _FORBIDDEN_FIELDS:
            raise AdvisoryArtifactError(f"Forbidden advisory artifact field detected: {normalized_key}")
        safe[normalized_key] = _sanitize_value(value)
    return safe


def _coerce_metadata(metadata: AdvisoryArtifactMetadata | Mapping[str, Any] | None) -> AdvisoryArtifactMetadata:
    if metadata is None:
        return AdvisoryArtifactMetadata()
    if isinstance(metadata, AdvisoryArtifactMetadata):
        return metadata
    if is_dataclass(metadata):
        metadata = asdict(metadata)
    if not isinstance(metadata, Mapping):
        raise AdvisoryArtifactError("Artifact metadata must be a mapping or AdvisoryArtifactMetadata.")

    safe = _sanitize_mapping(metadata)
    mode = _normalize_text(safe.get("mode"), "manual_local")
    command = _normalize_text(safe.get("command"), "unknown")
    if mode not in _ALLOWED_MODES:
        raise AdvisoryArtifactError(f"Unsupported advisory artifact mode: {mode}")
    if command not in _ALLOWED_COMMANDS:
        command = "unknown"
    return AdvisoryArtifactMetadata(
        mode=mode,
        command=command,
        validation_run_label=_normalize_text(safe.get("validation_run_label")),
        fixture_name=_normalize_text(safe.get("fixture_name")),
        future_shadow_persist_allowed=bool(safe.get("future_shadow_persist_allowed", False)),
    )


def _coerce_safe_mapping(value: Mapping[str, Any] | Any, *, label: str) -> dict[str, Any]:
    if is_dataclass(value):
        value = asdict(value)
    if not isinstance(value, Mapping):
        raise AdvisoryArtifactError(f"{label} must be a mapping or dataclass.")
    return _sanitize_mapping(value)


def _coerce_decision_diff(decision_diff: DecisionDiffReport | Mapping[str, Any] | Any) -> dict[str, Any]:
    if isinstance(decision_diff, DecisionDiffReport):
        return _sanitize_mapping(decision_diff.to_dict())
    return _coerce_safe_mapping(decision_diff, label="decision_diff")


def _extract_severity(decision_diff: Mapping[str, Any]) -> str:
    severity = _normalize_text(decision_diff.get("overall_severity"), "info").lower()
    if severity not in {item.value for item in DecisionDiffSeverity}:
        severity = DecisionDiffSeverity.INFO.value
    return severity


def _extract_failure_category(decision_diff: Mapping[str, Any]) -> str:
    findings = decision_diff.get("findings")
    if not isinstance(findings, list):
        return ""
    for finding in findings:
        if not isinstance(finding, Mapping):
            continue
        category = _normalize_text(finding.get("category")).lower()
        if category and category != "aligned":
            return category
    return ""


def _build_go_no_go_hint(*, severity: str) -> str:
    return {
        DecisionDiffSeverity.INFO.value: "go_candidate",
        DecisionDiffSeverity.LOW.value: "go_candidate",
        DecisionDiffSeverity.MEDIUM.value: "needs_review",
        DecisionDiffSeverity.HIGH.value: "blocked",
    }[severity]


def build_advisory_artifact(
    *,
    v5_primary_snapshot: Mapping[str, Any] | Any,
    v6_advisory_snapshot: Mapping[str, Any] | Any,
    decision_diff: DecisionDiffReport | Mapping[str, Any] | Any,
    metadata: AdvisoryArtifactMetadata | Mapping[str, Any] | None = None,
) -> AdvisoryArtifact:
    """Build a sanitized in-memory advisory artifact.

    The artifact is JSON-serializable, dependency-free, and safe for future
    manual/local or advisory-only analysis. It never writes to disk and never
    authorizes patching or runtime behavior changes.
    """

    safe_metadata = _coerce_metadata(metadata)
    safe_v5_snapshot = _coerce_safe_mapping(v5_primary_snapshot, label="v5_primary_snapshot")
    safe_v6_snapshot = _coerce_safe_mapping(v6_advisory_snapshot, label="v6_advisory_snapshot")
    safe_decision_diff = _coerce_decision_diff(decision_diff)

    severity = _extract_severity(safe_decision_diff)
    failure_category = _extract_failure_category(safe_decision_diff)
    go_no_go_hint = _build_go_no_go_hint(severity=severity)

    if safe_metadata.command == "fix" and severity in {
        DecisionDiffSeverity.MEDIUM.value,
        DecisionDiffSeverity.HIGH.value,
    }:
        go_no_go_hint = "blocked" if severity == DecisionDiffSeverity.HIGH.value else "needs_review"

    payload = {
        "schema_version": _SCHEMA_VERSION,
        "artifact_kind": _ARTIFACT_KIND,
        "mode": safe_metadata.mode,
        "command": safe_metadata.command,
        "source": {
            "runtime_primary": "v5_tkya",
            "advisory": "topocore_v6",
            "llm_provider_family": "github_models",
        },
        "v5_primary_snapshot": safe_v5_snapshot,
        "v6_advisory_snapshot": safe_v6_snapshot,
        "decision_diff": safe_decision_diff,
        "classification": {
            "overall_severity": severity,
            "go_no_go_hint": go_no_go_hint,
            "failure_category": failure_category,
        },
        "retention": {
            "default_scope": "manual_local_only",
            "default_persist": False,
            "future_shadow_persist_allowed": bool(safe_metadata.future_shadow_persist_allowed),
        },
        "safety": {
            "contains_raw_query": False,
            "contains_raw_code": False,
            "contains_decide_raw": False,
            "contains_secrets": False,
        },
    }

    if safe_metadata.validation_run_label:
        payload["validation_run_label"] = safe_metadata.validation_run_label
    if safe_metadata.fixture_name:
        payload["fixture_name"] = safe_metadata.fixture_name

    artifact = AdvisoryArtifact(payload=_sanitize_mapping(payload))
    assert_advisory_artifact_safe(artifact)
    return artifact


def assert_advisory_artifact_safe(artifact: AdvisoryArtifact | Mapping[str, Any]) -> None:
    """Validate that an advisory artifact contains only safe, sanitized fields."""

    payload = artifact.to_dict() if isinstance(artifact, AdvisoryArtifact) else _coerce_safe_mapping(artifact, label="artifact")
    if _normalize_text(payload.get("schema_version")) != _SCHEMA_VERSION:
        raise AdvisoryArtifactError("Unexpected advisory artifact schema version.")
    if _normalize_text(payload.get("artifact_kind")) != _ARTIFACT_KIND:
        raise AdvisoryArtifactError("Unexpected advisory artifact kind.")

    safety = payload.get("safety")
    if not isinstance(safety, Mapping):
        raise AdvisoryArtifactError("Advisory artifact safety section is required.")
    for key in ("contains_raw_query", "contains_raw_code", "contains_decide_raw", "contains_secrets"):
        if safety.get(key) is not False:
            raise AdvisoryArtifactError(f"Advisory artifact safety flag must remain false: {key}")

    _sanitize_mapping(payload)


__all__ = [
    "AdvisoryArtifact",
    "AdvisoryArtifactError",
    "AdvisoryArtifactInput",
    "AdvisoryArtifactMetadata",
    "assert_advisory_artifact_safe",
    "build_advisory_artifact",
]
