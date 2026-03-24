from __future__ import annotations

from typing import Any


_NOT_LOCALIZED_REASONS = {
    "no_localized_evidence_backed_patch_target",
    "no_confirmed_localized_evidence",
    "no_localized_evidence",
    "all_targets_non_patchable_or_low_localization",
}


def _verification_preconditions(summary: str) -> str:
    normalized = str(summary or "").strip().upper()
    if normalized == "PASS":
        return "met"
    if normalized in {"NOT_RUN", "PENDING", "N/A", "NA", "NONE", ""}:
        return "missing"
    if normalized == "FAIL":
        return "failed"
    return "partial"


def _patch_risk_class(*, evidence_verdicts: list[dict[str, Any]], patch_guard_triggered: bool) -> str:
    if patch_guard_triggered:
        return "high"
    impacts = {
        str(item.get("impact", "") or "").strip().lower()
        for item in evidence_verdicts
        if isinstance(item, dict)
    }
    if "high" in impacts:
        return "high"
    if "medium" in impacts:
        return "medium"
    return "low"


def build_patch_governance_contract(
    *,
    patch_generation_result: str,
    patch_validation_result: str,
    patch_targeting_mode: str,
    patch_targeting_reason: str,
    localized_patch_evidence_count: int,
    patch_target_files_selected: int,
    patch_guard_triggered: bool,
    verification_summary: str,
    evidence_verdicts: list[dict[str, Any]] | None = None,
) -> dict[str, str]:
    result = str(patch_generation_result or "n/a").strip().lower()
    validation = str(patch_validation_result or "n/a").strip().lower()
    targeting_mode = str(patch_targeting_mode or "n/a").strip().lower()
    targeting_reason = str(patch_targeting_reason or "n/a").strip() or "n/a"
    localized_signals = max(0, int(localized_patch_evidence_count or 0))
    selected_targets = max(0, int(patch_target_files_selected or 0))
    proof_threshold_status = (
        "met"
        if localized_signals > 0 and selected_targets > 0 and targeting_mode not in {"none", "n/a", "not_applicable"}
        else "not_met"
    )
    verification_preconditions = _verification_preconditions(verification_summary)
    verdicts = [item for item in (evidence_verdicts or []) if isinstance(item, dict)]
    patch_risk_class = _patch_risk_class(
        evidence_verdicts=verdicts,
        patch_guard_triggered=bool(patch_guard_triggered),
    )

    if result == "valid_patch":
        patchability_class = "patchable"
        governance_reason = "validated_patch_grounded"
        why_now = "Patch passed grounding checks with localized target context."
        why_not = "n/a"
        uncertainty = "bounded_review_required"
        next_safe_step = "Review `artifacts/patch.diff`, run CI, then apply/merge."
    elif bool(patch_guard_triggered) or validation in {"patch_validation_failed", "provider_failed"}:
        patchability_class = "patch_blocked_risk_too_high"
        governance_reason = "unsafe_or_invalid_patch_candidate"
        why_now = "Candidate patch failed safety/format/grounding gate."
        why_not = targeting_reason if targeting_reason != "n/a" else validation
        uncertainty = "high_until_manual_review"
        next_safe_step = "Narrow scope manually, then rerun /repobrain review and /repobrain fix."
    elif proof_threshold_status == "met" and verification_preconditions in {"missing", "failed"}:
        patchability_class = "patch_blocked_verification_missing"
        governance_reason = "verification_precondition_not_met"
        why_now = "Localization was sufficient, but verification gate is incomplete."
        why_not = verification_preconditions
        uncertainty = "medium_precondition_gap"
        next_safe_step = "Run verification checks, then rerun /repobrain fix."
    elif targeting_reason.lower() in _NOT_LOCALIZED_REASONS or targeting_mode == "none":
        patchability_class = "patch_blocked_not_localized"
        governance_reason = "patch_target_not_localized"
        why_now = "No reliable localized patch target was found."
        why_not = targeting_reason
        uncertainty = "bounded_by_localization_gap"
        next_safe_step = "Narrow request to concrete files/hunks and rerun /repobrain fix."
    elif localized_signals <= 0:
        patchability_class = "patch_blocked_insufficient_evidence"
        governance_reason = "insufficient_evidence_for_patch"
        why_now = "Evidence did not clear minimum proof threshold for safe patching."
        why_not = targeting_reason
        uncertainty = "high_evidence_gap"
        next_safe_step = "Run /repobrain review to gather evidence-backed findings, then rerun fix."
    else:
        patchability_class = "no_patch_safe_default"
        governance_reason = "safe_no_patch_default"
        why_now = "No safe grounded patch candidate was available for this run."
        why_not = targeting_reason
        uncertainty = "bounded_safe_default"
        next_safe_step = "Keep no_patch and escalate manual remediation if risk remains."

    return {
        "patchability_class": patchability_class,
        "patch_risk_class": patch_risk_class,
        "minimum_proof_threshold_status": proof_threshold_status,
        "verification_preconditions": verification_preconditions,
        "governance_reason": governance_reason,
        "why_now": why_now,
        "why_not": why_not,
        "uncertainty": uncertainty,
        "next_safe_step": next_safe_step,
    }
