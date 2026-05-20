from __future__ import annotations

from typing import Any, Mapping


TRUTHY_ENV_VALUES = frozenset({"1", "true", "yes", "y", "on"})

TOPOCORE_V5_SIMULATION_ENV = "RB_TOPOCORE_V5_SIMULATE_DISABLED"
TOPOCORE_V5_SIMULATED_DISABLED_REASON = "v5_simulated_disabled"
TOPOCORE_V5_OFF_SIMULATION_AVAILABLE = True

TOPOCORE_V5_ALLOW_DEPRECATED_ENV = "RB_TOPOCORE_ALLOW_DEPRECATED_V5"
TOPOCORE_V5_DISABLED_BY_DEFAULT = True
TOPOCORE_V5_DEFAULT_DISABLED_REASON = "v5_disabled_by_default"
TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON = "deprecated_v5_not_allowed"
TOPOCORE_V5_DEPRECATED_ALLOWED_REASON = "v5_deprecated_emergency_allowed"
TOPOCORE_V6_AUTHORITATIVE = True

TOPOCORE_V5_STATUS = "deprecation_candidate"
TOPOCORE_V5_ROLE = "fallback_only"
TOPOCORE_V6_STATUS = "active_lab_default"
TOPOCORE_V5_REMOVAL_APPROVED = False
TOPOCORE_V5_CODE_DEPRECATION_ACTIVE = False
TOPOCORE_V5_FALLBACK_REQUIRED = True


def _is_truthy_env(name: str, env: Mapping[str, str] | None = None) -> bool:
    source = env
    if source is None:
        import os

        source = os.environ
    raw = str(source.get(name, "") or "").strip().lower()
    return raw in TRUTHY_ENV_VALUES


def is_v5_simulated_disabled(env: Mapping[str, str] | None = None) -> bool:
    return _is_truthy_env(TOPOCORE_V5_SIMULATION_ENV, env)


def is_deprecated_v5_allowed(env: Mapping[str, str] | None = None) -> bool:
    return _is_truthy_env(TOPOCORE_V5_ALLOW_DEPRECATED_ENV, env)


def get_topocore_deprecation_policy() -> dict[str, Any]:
    return {
        "topocore_v6_status": TOPOCORE_V6_STATUS,
        "topocore_v6_authoritative": TOPOCORE_V6_AUTHORITATIVE,
        "topocore_v5_status": TOPOCORE_V5_STATUS,
        "topocore_v5_role": TOPOCORE_V5_ROLE,
        "topocore_v5_disabled_by_default": TOPOCORE_V5_DISABLED_BY_DEFAULT,
        "topocore_v5_allow_deprecated_env": TOPOCORE_V5_ALLOW_DEPRECATED_ENV,
        "topocore_v5_deprecated_not_allowed_reason": TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON,
        "topocore_v5_deprecated_allowed_reason": TOPOCORE_V5_DEPRECATED_ALLOWED_REASON,
        "topocore_v5_default_disabled_reason": TOPOCORE_V5_DEFAULT_DISABLED_REASON,
        "topocore_v5_removal_approved": TOPOCORE_V5_REMOVAL_APPROVED,
        "topocore_v5_code_deprecation_active": TOPOCORE_V5_CODE_DEPRECATION_ACTIVE,
        "topocore_v5_fallback_required": TOPOCORE_V5_FALLBACK_REQUIRED,
        "topocore_v5_simulation_env": TOPOCORE_V5_SIMULATION_ENV,
        "topocore_v5_simulated_disabled_reason": TOPOCORE_V5_SIMULATED_DISABLED_REASON,
        "topocore_v5_off_simulation_available": TOPOCORE_V5_OFF_SIMULATION_AVAILABLE,
    }


__all__ = [
    "TOPOCORE_V5_ALLOW_DEPRECATED_ENV",
    "TOPOCORE_V5_CODE_DEPRECATION_ACTIVE",
    "TOPOCORE_V5_DEFAULT_DISABLED_REASON",
    "TOPOCORE_V5_DEPRECATED_ALLOWED_REASON",
    "TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON",
    "TOPOCORE_V5_DISABLED_BY_DEFAULT",
    "TOPOCORE_V5_FALLBACK_REQUIRED",
    "TOPOCORE_V5_OFF_SIMULATION_AVAILABLE",
    "TOPOCORE_V5_REMOVAL_APPROVED",
    "TOPOCORE_V5_ROLE",
    "TOPOCORE_V5_SIMULATED_DISABLED_REASON",
    "TOPOCORE_V5_SIMULATION_ENV",
    "TOPOCORE_V5_STATUS",
    "TOPOCORE_V6_AUTHORITATIVE",
    "TOPOCORE_V6_STATUS",
    "get_topocore_deprecation_policy",
    "is_deprecated_v5_allowed",
    "is_v5_simulated_disabled",
]
