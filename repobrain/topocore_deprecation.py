from __future__ import annotations

from typing import Any


TOPOCORE_V5_STATUS = "deprecation_candidate"
TOPOCORE_V5_ROLE = "fallback_only"
TOPOCORE_V6_STATUS = "active_lab_default"
TOPOCORE_V5_REMOVAL_APPROVED = False
TOPOCORE_V5_CODE_DEPRECATION_ACTIVE = False
TOPOCORE_V5_FALLBACK_REQUIRED = True


def get_topocore_deprecation_policy() -> dict[str, Any]:
    return {
        "topocore_v6_status": TOPOCORE_V6_STATUS,
        "topocore_v5_status": TOPOCORE_V5_STATUS,
        "topocore_v5_role": TOPOCORE_V5_ROLE,
        "topocore_v5_removal_approved": TOPOCORE_V5_REMOVAL_APPROVED,
        "topocore_v5_code_deprecation_active": TOPOCORE_V5_CODE_DEPRECATION_ACTIVE,
        "topocore_v5_fallback_required": TOPOCORE_V5_FALLBACK_REQUIRED,
    }


__all__ = [
    "TOPOCORE_V5_CODE_DEPRECATION_ACTIVE",
    "TOPOCORE_V5_FALLBACK_REQUIRED",
    "TOPOCORE_V5_REMOVAL_APPROVED",
    "TOPOCORE_V5_ROLE",
    "TOPOCORE_V5_STATUS",
    "TOPOCORE_V6_STATUS",
    "get_topocore_deprecation_policy",
]
