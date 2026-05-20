"""Compatibility stubs for the removed v5/lite TKYA runtime.

Sprint 65 removed executable v5/lite runtime behavior. This module remains only
to preserve stable imports while returning sanitized unsupported diagnostics.
"""

from __future__ import annotations

from typing import Any, Literal

from repobrain.topocore_deprecation import (
    TOPOCORE_LEGACY_LITE_REMOVED_REASON,
    TOPOCORE_UNSUPPORTED_LEGACY_BACKEND_REASON,
    TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON,
    TOPOCORE_V5_RUNTIME_REMOVED_REASON,
)
from repobrain.tky_engine import TKYEngine

BACKEND_LITE = "lite"
BACKEND_V5 = "v5"
TKYABackend = Literal["lite", "v5"]


class DeprecatedV5RuntimeRemovedError(RuntimeError):
    """Raised when legacy v5/lite runtime execution is requested."""


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False


def _backend_reason_from_env() -> str:
    import os

    explicit = str(os.getenv("RB_TOPOCORE_BACKEND", "") or "").strip().lower()
    legacy = str(os.getenv("RB_TKYA_BACKEND", "") or "").strip().lower()
    allow_requested = _to_bool(os.getenv("RB_TOPOCORE_ALLOW_DEPRECATED_V5", "0"))

    if explicit == "v5":
        return (
            TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON
            if allow_requested
            else TOPOCORE_V5_RUNTIME_REMOVED_REASON
        )
    if explicit == "lite":
        return TOPOCORE_LEGACY_LITE_REMOVED_REASON
    if legacy == "lite":
        return TOPOCORE_LEGACY_LITE_REMOVED_REASON
    if legacy == "v5":
        return (
            TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON
            if allow_requested
            else TOPOCORE_UNSUPPORTED_LEGACY_BACKEND_REASON
        )
    if allow_requested:
        return TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON
    return TOPOCORE_V5_RUNTIME_REMOVED_REASON


def describe_engine_instance(_engine: Any) -> str:
    return "legacy_runtime_removed"


def get_engine() -> TKYEngine:
    reason = _backend_reason_from_env()
    raise DeprecatedV5RuntimeRemovedError(
        "Deprecated TopoCore v5/lite runtime execution was removed. "
        "Use RB_TOPOCORE_BACKEND=auto or RB_TOPOCORE_BACKEND=v6. "
        f"[{reason}]"
    )


__all__ = [
    "BACKEND_LITE",
    "BACKEND_V5",
    "DeprecatedV5RuntimeRemovedError",
    "TKYABackend",
    "describe_engine_instance",
    "get_engine",
]
