"""Still-disabled advisory boundary around the TopoCore v6 shadow skeleton.

This module is dependency-free. It does not import TopoCore v6, does not call
external systems, and does not change current RepoBrain runtime behavior.
"""

from __future__ import annotations
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any

from repobrain.topocore_v6_shadow_path import (
    TopoCoreV6ShadowConfig,
    TopoCoreV6ShadowInput,
    TopoCoreV6ShadowResult,
    assert_shadow_result_safe,
    load_shadow_config_from_env,
    run_topocore_v6_shadow_path,
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

_ALLOWED_FAILURE_CATEGORIES = frozenset(
    {
        "disabled",
        "advisory_boundary_noop",
        "enabled_not_implemented",
        "invalid_input",
        "forbidden_output_issue",
        "shadow_path_unavailable",
        "configuration_error",
    }
)


class TopoCoreV6AdvisoryBoundaryError(ValueError):
    """Raised when advisory-boundary input or output is unsafe."""


class TopoCoreV6AdvisoryBoundaryStatus(str, Enum):
    DISABLED = "disabled"
    ADVISORY_BOUNDARY_NOOP = "advisory_boundary_noop"
    ENABLED_NOT_IMPLEMENTED = "enabled_not_implemented"
    INVALID_INPUT = "invalid_input"
    FORBIDDEN_OUTPUT_ISSUE = "forbidden_output_issue"
    SHADOW_PATH_UNAVAILABLE = "shadow_path_unavailable"
    CONFIGURATION_ERROR = "configuration_error"


@dataclass(frozen=True)
class TopoCoreV6AdvisoryBoundaryConfig:
    enabled: bool = False
    artifacts_enabled: bool = False
    fail_closed: bool = False


@dataclass(frozen=True)
class TopoCoreV6AdvisoryBoundaryInput:
    command: str = "unknown"
    task_type: str = "unknown"
    safe_query_summary: str = ""
    candidate_ids: tuple[str, ...] = field(default_factory=tuple)
    v5_primary_snapshot: Mapping[str, Any] = field(default_factory=dict)
    summary_bundle: Mapping[str, Any] = field(default_factory=dict)
    validation_run_label: str = ""
    request_id_safe: str = ""


@dataclass(frozen=True)
class TopoCoreV6AdvisoryBoundaryResult:
    enabled: bool
    status: TopoCoreV6AdvisoryBoundaryStatus
    reason: str
    command: str
    task_type: str
    boundary_mode: str
    shadow_status: str
    artifacts_enabled: bool
    fail_closed: bool
    failure_category: str
    safety_flags: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "status": self.status.value,
            "reason": self.reason,
            "command": self.command,
            "task_type": self.task_type,
            "boundary_mode": self.boundary_mode,
            "shadow_status": self.shadow_status,
            "artifacts_enabled": self.artifacts_enabled,
            "fail_closed": self.fail_closed,
            "failure_category": self.failure_category,
            "safety_flags": dict(self.safety_flags),
        }


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _contains_forbidden_keys(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalize_text(key).lower()
            if normalized_key in _FORBIDDEN_FIELDS:
                return True
            if _contains_forbidden_keys(item):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_keys(item) for item in value)
    return False


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _sanitize_mapping(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
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
            raise TopoCoreV6AdvisoryBoundaryError(
                f"Forbidden advisory-boundary field detected: {normalized_key}"
            )
        safe[normalized_key] = _sanitize_value(value)
    return safe


def _base_safety_flags() -> dict[str, bool]:
    return {
        "contains_raw_query": False,
        "contains_raw_code": False,
        "contains_decide_raw": False,
        "contains_secrets": False,
    }


def _shadow_config_from_boundary(
    config: TopoCoreV6AdvisoryBoundaryConfig,
) -> TopoCoreV6ShadowConfig:
    return TopoCoreV6ShadowConfig(
        enabled=config.enabled,
        artifacts_enabled=config.artifacts_enabled,
        fail_closed=config.fail_closed,
    )


def load_advisory_boundary_config_from_env(
    env: Mapping[str, str] | None = None,
) -> TopoCoreV6AdvisoryBoundaryConfig:
    shadow_config = load_shadow_config_from_env(env)
    return TopoCoreV6AdvisoryBoundaryConfig(
        enabled=shadow_config.enabled,
        artifacts_enabled=shadow_config.artifacts_enabled,
        fail_closed=shadow_config.fail_closed,
    )


def normalize_advisory_boundary_failure_category(value: Any) -> str:
    normalized = _normalize_text(value).lower()
    if normalized in _ALLOWED_FAILURE_CATEGORIES:
        return normalized
    return "configuration_error"


def _coerce_input(
    value: TopoCoreV6AdvisoryBoundaryInput | Mapping[str, Any] | None,
) -> TopoCoreV6AdvisoryBoundaryInput:
    if value is None:
        return TopoCoreV6AdvisoryBoundaryInput()
    if isinstance(value, TopoCoreV6AdvisoryBoundaryInput):
        return value
    if is_dataclass(value):
        value = asdict(value)
    if not isinstance(value, Mapping):
        raise TopoCoreV6AdvisoryBoundaryError(
            "Advisory-boundary input must be a mapping or TopoCoreV6AdvisoryBoundaryInput."
        )

    safe = _sanitize_mapping(value)
    candidate_ids_raw = safe.get("candidate_ids", ())
    if isinstance(candidate_ids_raw, (str, bytes, bytearray)):
        candidate_ids = (_normalize_text(candidate_ids_raw),)
    else:
        candidate_ids = tuple(
            sorted({_normalize_text(item) for item in candidate_ids_raw if _normalize_text(item)})
        )
    return TopoCoreV6AdvisoryBoundaryInput(
        command=_normalize_text(safe.get("command"), "unknown"),
        task_type=_normalize_text(safe.get("task_type"), "unknown"),
        safe_query_summary=_normalize_text(safe.get("safe_query_summary")),
        candidate_ids=candidate_ids,
        v5_primary_snapshot=_sanitize_mapping(safe.get("v5_primary_snapshot", {}))
        if isinstance(safe.get("v5_primary_snapshot", {}), Mapping)
        else {},
        summary_bundle=_sanitize_mapping(safe.get("summary_bundle", {}))
        if isinstance(safe.get("summary_bundle", {}), Mapping)
        else {},
        validation_run_label=_normalize_text(safe.get("validation_run_label")),
        request_id_safe=_normalize_text(safe.get("request_id_safe")),
    )


def _to_shadow_input(
    input_value: TopoCoreV6AdvisoryBoundaryInput,
) -> TopoCoreV6ShadowInput:
    return TopoCoreV6ShadowInput(
        command=input_value.command,
        task_type=input_value.task_type,
        safe_query_summary=input_value.safe_query_summary,
        candidate_ids=input_value.candidate_ids,
        v5_primary_snapshot=input_value.v5_primary_snapshot,
        summary_bundle=input_value.summary_bundle,
        validation_run_label=input_value.validation_run_label,
    )


def _result(
    *,
    config: TopoCoreV6AdvisoryBoundaryConfig,
    status: TopoCoreV6AdvisoryBoundaryStatus,
    reason: str,
    input_value: TopoCoreV6AdvisoryBoundaryInput | None = None,
    shadow_status: str = "",
    failure_category: str = "",
) -> TopoCoreV6AdvisoryBoundaryResult:
    boundary_input = input_value or TopoCoreV6AdvisoryBoundaryInput()
    normalized_category = normalize_advisory_boundary_failure_category(
        failure_category or status.value
    )
    return TopoCoreV6AdvisoryBoundaryResult(
        enabled=config.enabled,
        status=status,
        reason=reason,
        command=boundary_input.command,
        task_type=boundary_input.task_type,
        boundary_mode="still_disabled",
        shadow_status=shadow_status,
        artifacts_enabled=config.artifacts_enabled,
        fail_closed=config.fail_closed,
        failure_category=normalized_category,
        safety_flags=_base_safety_flags(),
    )


def assert_advisory_boundary_result_safe(
    result: TopoCoreV6AdvisoryBoundaryResult | Mapping[str, Any],
) -> dict[str, Any]:
    payload = result.to_dict() if isinstance(result, TopoCoreV6AdvisoryBoundaryResult) else dict(result)
    if _contains_forbidden_keys(payload):
        raise TopoCoreV6AdvisoryBoundaryError(
            "Forbidden output field detected in advisory-boundary result."
        )

    safety_flags = payload.get("safety_flags")
    if not isinstance(safety_flags, Mapping):
        raise TopoCoreV6AdvisoryBoundaryError("Advisory-boundary result requires safety_flags.")
    for key in ("contains_raw_query", "contains_raw_code", "contains_decide_raw", "contains_secrets"):
        if safety_flags.get(key) is not False:
            raise TopoCoreV6AdvisoryBoundaryError(
                f"Advisory-boundary safety flag must remain false: {key}"
            )

    payload["failure_category"] = normalize_advisory_boundary_failure_category(
        payload.get("failure_category")
    )
    return payload


def _from_shadow_result(
    *,
    config: TopoCoreV6AdvisoryBoundaryConfig,
    input_value: TopoCoreV6AdvisoryBoundaryInput,
    shadow_result: TopoCoreV6ShadowResult,
) -> TopoCoreV6AdvisoryBoundaryResult:
    shadow_payload = assert_shadow_result_safe(shadow_result)
    shadow_status = _normalize_text(shadow_payload.get("status"))

    if shadow_status == "disabled":
        status = TopoCoreV6AdvisoryBoundaryStatus.DISABLED
        reason = "advisory_boundary_disabled_noop"
        failure_category = "disabled"
    elif shadow_status == "artifact_unavailable":
        status = TopoCoreV6AdvisoryBoundaryStatus.ADVISORY_BOUNDARY_NOOP
        reason = "advisory_boundary_artifacts_unavailable_noop"
        failure_category = "advisory_boundary_noop"
    elif shadow_status == "enabled_not_implemented":
        status = TopoCoreV6AdvisoryBoundaryStatus.ENABLED_NOT_IMPLEMENTED
        reason = "advisory_boundary_enabled_but_not_implemented"
        failure_category = "enabled_not_implemented"
    elif shadow_status == "invalid_input":
        status = TopoCoreV6AdvisoryBoundaryStatus.INVALID_INPUT
        reason = "invalid_input"
        failure_category = "invalid_input"
    else:
        status = TopoCoreV6AdvisoryBoundaryStatus.SHADOW_PATH_UNAVAILABLE
        reason = "shadow_path_unavailable"
        failure_category = "shadow_path_unavailable"

    return _result(
        config=config,
        status=status,
        reason=reason,
        input_value=input_value,
        shadow_status=shadow_status,
        failure_category=failure_category,
    )


def run_disabled_advisory_boundary(
    *,
    input_value: TopoCoreV6AdvisoryBoundaryInput | Mapping[str, Any] | None = None,
    config: TopoCoreV6AdvisoryBoundaryConfig | None = None,
    env: Mapping[str, str] | None = None,
) -> TopoCoreV6AdvisoryBoundaryResult:
    """Run the still-disabled advisory boundary without any runtime wiring."""

    effective_config = config or load_advisory_boundary_config_from_env(env)
    try:
        boundary_input = _coerce_input(input_value)
    except TopoCoreV6AdvisoryBoundaryError:
        return _result(
            config=effective_config,
            status=TopoCoreV6AdvisoryBoundaryStatus.INVALID_INPUT,
            reason="invalid_input",
            failure_category="invalid_input",
        )

    shadow_result = run_topocore_v6_shadow_path(
        input_value=_to_shadow_input(boundary_input),
        config=_shadow_config_from_boundary(effective_config),
    )
    boundary_result = _from_shadow_result(
        config=effective_config,
        input_value=boundary_input,
        shadow_result=shadow_result,
    )
    assert_advisory_boundary_result_safe(boundary_result)
    return boundary_result


__all__ = [
    "TopoCoreV6AdvisoryBoundaryConfig",
    "TopoCoreV6AdvisoryBoundaryError",
    "TopoCoreV6AdvisoryBoundaryInput",
    "TopoCoreV6AdvisoryBoundaryResult",
    "TopoCoreV6AdvisoryBoundaryStatus",
    "assert_advisory_boundary_result_safe",
    "load_advisory_boundary_config_from_env",
    "normalize_advisory_boundary_failure_category",
    "run_disabled_advisory_boundary",
]
