from __future__ import annotations

from repobrain.patch_governance import build_patch_governance_contract


def test_patch_governance_class_patchable_for_valid_patch() -> None:
    contract = build_patch_governance_contract(
        patch_generation_result="valid_patch",
        patch_validation_result="valid_patch",
        patch_targeting_mode="localized",
        patch_targeting_reason="patch_target_narrowed_to_localized_subset",
        localized_patch_evidence_count=2,
        patch_target_files_selected=1,
        patch_guard_triggered=False,
        verification_summary="PASS",
        evidence_verdicts=[{"impact": "medium"}],
    )
    assert contract["patchability_class"] == "patchable"
    assert contract["minimum_proof_threshold_status"] == "met"
    assert contract["verification_preconditions"] == "met"


def test_patch_governance_class_not_localized_for_no_patch_targeting_block() -> None:
    contract = build_patch_governance_contract(
        patch_generation_result="no_patch",
        patch_validation_result="no_patch",
        patch_targeting_mode="none",
        patch_targeting_reason="no_localized_evidence_backed_patch_target",
        localized_patch_evidence_count=0,
        patch_target_files_selected=0,
        patch_guard_triggered=False,
        verification_summary="NOT_RUN",
        evidence_verdicts=[],
    )
    assert contract["patchability_class"] == "patch_blocked_not_localized"
    assert contract["minimum_proof_threshold_status"] == "not_met"
    assert contract["verification_preconditions"] == "missing"


def test_patch_governance_class_verification_missing_when_proof_is_met() -> None:
    contract = build_patch_governance_contract(
        patch_generation_result="no_patch",
        patch_validation_result="no_patch",
        patch_targeting_mode="localized",
        patch_targeting_reason="patch_target_narrowed_to_localized_subset",
        localized_patch_evidence_count=2,
        patch_target_files_selected=1,
        patch_guard_triggered=False,
        verification_summary="NOT_RUN",
        evidence_verdicts=[{"impact": "low"}],
    )
    assert contract["patchability_class"] == "patch_blocked_verification_missing"


def test_patch_governance_class_risk_too_high_for_guard_or_validation_failure() -> None:
    contract = build_patch_governance_contract(
        patch_generation_result="patch_validation_failed",
        patch_validation_result="patch_validation_failed",
        patch_targeting_mode="localized",
        patch_targeting_reason="patch_target_narrowed_to_localized_subset",
        localized_patch_evidence_count=3,
        patch_target_files_selected=1,
        patch_guard_triggered=True,
        verification_summary="PASS",
        evidence_verdicts=[{"impact": "high"}],
    )
    assert contract["patchability_class"] == "patch_blocked_risk_too_high"
    assert contract["patch_risk_class"] == "high"
