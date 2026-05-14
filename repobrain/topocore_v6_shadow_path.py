"""Hard-disabled advisory path skeleton for future TopoCore v6 shadow work.

This module is dependency-free. It does not import TopoCore v6, does not call
external systems, and does not change current RepoBrain runtime behavior.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any

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


class TopoCoreV6ShadowError(ValueError):
    """Raised when shadow-path input is unsafe or invalid."""


class TopoCoreV6ShadowStatus(str, Enum):
    DISABLED = "disabled"
    ENABLED_NOT_IMPLEMENTED = "enabled_not_implemented"
    INVALID_INPUT = "invalid_input"
    FORBIDDEN_OUTPUT_ISSUE = "forbidden_output_issue"
    ARTIFACT_UNAVAILABLE = "artifact_unavailable"
    CONFIGURATION_ERROR = "configuration_error"


@dataclass(frozen=True)
class TopoCoreV6ShadowConfig:
    enabled: bool = False
    artifacts_enabled: bool = False
    fail_closed: bool = False


@dataclass(frozen=True)
class TopoCoreV6ShadowInput:
    command: str = "unknown"
    task_type: str = "unknown"
    safe_query_summary: str = ""
    candidate_ids: tuple[str, ...] = field(default_factory=tuple)
    v5_primary_snapshot: Mapping[str, Any] = field(default_factory=dict)
    summary_bundle: Mapping[str, Any] = field(default_factory=dict)
    validation_run_label: str = ""


@dataclass(frozen=True)
class TopoCoreV6ShadowResult:
    enabled: bool
    status: TopoCoreV6ShadowStatus
    reason: str
    command: str
    task_type: str
    artifacts_enabled: bool
    fail_closed: bool
    failure_category: str
    safety_flags: dict[str, bool]
    artifact_generated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "status": self.status.value,
            "reason": self.reason,
            "command": self.command,
            "task_type": self.task_type,
            "artifacts_enabled": self.artifacts_enabled,
            "fail_closed": self.fail_closed,
            "failure_category": self.failure_category,
            "artifact_generated": self.artifact_generated,
            "safety_flags": dict(self.safety_flags),
        }


def _normalize_text(value: Any, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _env_flag(name: str, default: str = "0", env: Mapping[str, str] | None = None) -> str:
    source = env if env is not None else os.environ
    return _normalize_text(source.get(name, default), default)


def load_shadow_config_from_env(env: Mapping[str, str] | None = None) -> TopoCoreV6ShadowConfig:
    return TopoCoreV6ShadowConfig(
        enabled=_env_flag("RB_TOPOCORE_V6_SHADOW_ENABLED", env=env) == "1",
        artifacts_enabled=_env_flag("RB_TOPOCORE_V6_SHADOW_ARTIFACTS", env=env) == "1",
        fail_closed=_env_flag("RB_TOPOCORE_V6_SHADOW_FAIL_CLOSED", env=env) == "1",
    )


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
            raise TopoCoreV6ShadowError(f"Forbidden shadow-path field detected: {normalized_key}")
        safe[normalized_key] = _sanitize_value(value)
    return safe


def _coerce_input(value: TopoCoreV6ShadowInput | Mapping[str, Any] | None) -> TopoCoreV6ShadowInput:
    if value is None:
        return TopoCoreV6ShadowInput()
    if isinstance(value, TopoCoreV6ShadowInput):
        return value
    if is_dataclass(value):
        value = asdict(value)
    if not isinstance(value, Mapping):
        raise TopoCoreV6ShadowError("Shadow input must be a mapping or TopoCoreV6ShadowInput.")

    safe = _sanitize_mapping(value)
    candidate_ids_raw = safe.get("candidate_ids", ())
    if isinstance(candidate_ids_raw, (str, bytes, bytearray)):
        candidate_ids = (_normalize_text(candidate_ids_raw),)
    else:
        candidate_ids = tuple(
            sorted({_normalize_text(item) for item in candidate_ids_raw if _normalize_text(item)})
        )
    return TopoCoreV6ShadowInput(
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
    )


def _base_safety_flags() -> dict[str, bool]:
    return {
        "contains_raw_query": False,
        "contains_raw_code": False,
        "contains_decide_raw": False,
        "contains_secrets": False,
    }


def _result(
    *,
    config: TopoCoreV6ShadowConfig,
    status: TopoCoreV6ShadowStatus,
    reason: str,
    input_value: TopoCoreV6ShadowInput | None = None,
    failure_category: str = "",
    artifact_generated: bool = False,
) -> TopoCoreV6ShadowResult:
    shadow_input = input_value or TopoCoreV6ShadowInput()
    return TopoCoreV6ShadowResult(
        enabled=config.enabled,
        status=status,
        reason=reason,
        command=shadow_input.command,
        task_type=shadow_input.task_type,
        artifacts_enabled=config.artifacts_enabled,
        fail_closed=config.fail_closed,
        failure_category=failure_category,
        artifact_generated=artifact_generated,
        safety_flags=_base_safety_flags(),
    )


def run_topocore_v6_shadow_path(
    *,
    input_value: TopoCoreV6ShadowInput | Mapping[str, Any] | None = None,
    config: TopoCoreV6ShadowConfig | None = None,
    env: Mapping[str, str] | None = None,
) -> TopoCoreV6ShadowResult:
    """Run the hard-disabled shadow-path skeleton without any runtime wiring.

    Sprint 28 behavior is intentionally no-op and dependency-free. No TopoCore
    v6 calls occur, no artifacts are persisted or published, and no runtime
    side effects are allowed.
    """

    effective_config = config or load_shadow_config_from_env(env)
    try:
        shadow_input = _coerce_input(input_value)
    except TopoCoreV6ShadowError:
        return _result(
            config=effective_config,
            status=TopoCoreV6ShadowStatus.INVALID_INPUT,
            reason="invalid_input",
            failure_category="invalid_input",
            artifact_generated=False,
        )

    if not effective_config.enabled:
        return _result(
            config=effective_config,
            status=TopoCoreV6ShadowStatus.DISABLED,
            reason="shadow_path_disabled_noop",
            input_value=shadow_input,
            failure_category="disabled",
        )

    if effective_config.artifacts_enabled:
        return _result(
            config=effective_config,
            status=TopoCoreV6ShadowStatus.ARTIFACT_UNAVAILABLE,
            reason="artifact_generation_unavailable_in_sprint_28",
            input_value=shadow_input,
            failure_category="artifact_unavailable",
            artifact_generated=False,
        )

    return _result(
        config=effective_config,
        status=TopoCoreV6ShadowStatus.ENABLED_NOT_IMPLEMENTED,
        reason="advisory_shadow_path_enabled_but_not_implemented",
        input_value=shadow_input,
        failure_category="enabled_not_implemented",
        artifact_generated=False,
    )


__all__ = [
    "TopoCoreV6ShadowConfig",
    "TopoCoreV6ShadowError",
    "TopoCoreV6ShadowInput",
    "TopoCoreV6ShadowResult",
    "TopoCoreV6ShadowStatus",
    "load_shadow_config_from_env",
    "run_topocore_v6_shadow_path",
]
