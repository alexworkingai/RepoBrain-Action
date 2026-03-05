from __future__ import annotations

from typing import Any

from repobrain.config import RepoBrainConfig


def _env_true(name: str, default: bool = False) -> bool:
    cfg = RepoBrainConfig.from_env()
    if name == "RB_REQUIRE_VERIFY_FOR_PATCH":
        return bool(cfg.workflow.require_verify_for_patch)
    if name == "RB_FAIL_ON_NOT_RUN":
        return bool(cfg.workflow.fail_on_not_run)
    return bool(default)


def _verification_flags(verification_report: dict[str, Any]) -> tuple[bool, bool, bool]:
    checks = verification_report.get("checks", [])
    if not isinstance(checks, list):
        checks = []

    statuses = [str(item.get("status", "NOT_RUN")).upper() for item in checks if isinstance(item, dict)]
    has_fail = any(status == "FAIL" for status in statuses)
    has_not_run = any(status == "NOT_RUN" for status in statuses)
    all_pass = bool(statuses) and all(status == "PASS" for status in statuses)
    return has_fail, has_not_run, all_pass


def compute_conclusion(
    route: str,
    verification_report: dict[str, Any],
    intent: str,
) -> tuple[str, str, str]:
    """Compute deterministic GitHub Checks conclusion from route + verification report."""
    normalized_route = str(route or "").strip().upper()
    normalized_intent = str(intent or "").strip().lower()
    has_fail, has_not_run, all_pass = _verification_flags(verification_report)

    require_verify_for_patch = _env_true("RB_REQUIRE_VERIFY_FOR_PATCH", default=False)
    fail_on_not_run = _env_true("RB_FAIL_ON_NOT_RUN", default=False)

    if normalized_route == "BLOCK":
        return "failure", "Blocked by policy", "Engine route=BLOCK."
    if normalized_route == "REFUSE":
        return "neutral", "Refused by policy", "Engine route=REFUSE."
    if normalized_route == "WAIT":
        return "neutral", "Verification pending", "Engine route=WAIT."

    if has_fail:
        return "failure", "Verification failed", "At least one verification check returned FAIL."

    if has_not_run:
        if normalized_intent == "patch" and require_verify_for_patch:
            return "failure", "Verification incomplete", "Patch requires full verification but checks are NOT_RUN."
        if fail_on_not_run:
            return "failure", "Verification incomplete", "Checks are NOT_RUN and policy requires full execution."
        return "neutral", "Verification partial", "One or more checks are NOT_RUN."

    if all_pass:
        return "success", "All checks passed", "Route and verification checks are green."

    if normalized_route in {"FAST", "DEEP", "REVIEW"}:
        return "success", "Route completed", f"Engine route={normalized_route} without failing checks."

    return "neutral", "No definitive signal", "Insufficient data for strict conclusion."
