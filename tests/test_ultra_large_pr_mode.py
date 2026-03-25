from __future__ import annotations

from repobrain.ultra_large_pr_mode import (
    build_ultra_large_pr_mode_contract,
    ultra_large_mode_precheck,
)


def test_ultra_large_mode_precheck_activates_for_changed_files_threshold() -> None:
    active, reasons = ultra_large_mode_precheck(
        {
            "changed_files": [f"src/file_{idx}.py" for idx in range(85)],
            "pr_segmentation_file_map": {},
        }
    )

    assert active is True
    assert "changed_files_threshold" in reasons


def test_ultra_large_mode_contract_inactive_for_small_pr() -> None:
    contract = build_ultra_large_pr_mode_contract(
        command="review",
        pr_changed_files_count=9,
        changed_regions_considered=18,
        pr_segment_count=2,
        pr_cross_segment=False,
        evidence_budget_overflow=0,
        evidence_budget_mode="review_risk_weighted_incremental",
        pr_primary_segments="core_code:repobrain/github_flow",
        pr_support_segments="tests:tests",
        selected_items_count=9,
    )

    assert contract["ultra_large_pr_mode_active"] is False
    assert contract["ultra_large_pr_mode_level"] == "normal"
    assert contract["ultra_large_pr_mode_reason"] == "none"


def test_ultra_large_mode_contract_downgrades_fix_governance_when_bounded() -> None:
    contract = build_ultra_large_pr_mode_contract(
        command="fix",
        pr_changed_files_count=130,
        changed_regions_considered=420,
        pr_segment_count=7,
        pr_cross_segment=True,
        evidence_budget_overflow=36,
        evidence_budget_mode="fix_localized_strict_incremental",
        pr_primary_segments="core_code:repobrain/github_flow",
        pr_support_segments="tests:tests, docs:docs",
        selected_items_count=14,
        patch_generation_result="no_patch",
        patch_target_files_selected=0,
        localized_patch_evidence_count=0,
    )

    assert contract["ultra_large_pr_mode_active"] is True
    assert contract["ultra_large_pr_mode_level"] in {"large", "extreme"}
    assert contract["ultra_large_pr_patch_governance_downgraded"] is True
    assert contract["ultra_large_pr_patch_governance_reason"] == "scale_bounded_localization_gap"
