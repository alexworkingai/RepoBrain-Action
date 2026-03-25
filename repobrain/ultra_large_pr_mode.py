from __future__ import annotations

from typing import Any


def ultra_large_mode_precheck(github_context: dict[str, Any] | None) -> tuple[bool, list[str]]:
    context = dict(github_context or {})
    changed_raw = context.get("changed_files", [])
    changed_files = [str(item).strip() for item in changed_raw if str(item).strip()] if isinstance(changed_raw, list) else []
    changed_count = len(set(changed_files))
    file_map_raw = context.get("pr_segmentation_file_map", {})
    file_map = file_map_raw if isinstance(file_map_raw, dict) else {}
    segment_classes = {
        str(file_map.get(path, "")).strip().lower()
        for path in changed_files
        if str(file_map.get(path, "")).strip()
    }
    reasons: list[str] = []
    if changed_count >= 80:
        reasons.append("changed_files_threshold")
    if changed_count >= 40 and len(segment_classes) >= 3:
        reasons.append("cross_segment_threshold")
    return bool(reasons), reasons


def _cap_for(command: str, *, level: str) -> int:
    cmd = str(command or "ask").strip().lower()
    if cmd == "review":
        return 14 if level == "extreme" else 18
    if cmd == "fix":
        return 10 if level == "extreme" else 14
    return 8 if level == "extreme" else 10


def _normalized_budget_mode(*, command: str, existing_mode: str, active: bool) -> str:
    mode = str(existing_mode or "not_applied").strip().lower() or "not_applied"
    cmd = str(command or "ask").strip().lower() or "ask"
    if not active:
        return mode
    if mode == "not_applied":
        return f"ultra_large_{cmd}_capped"
    if mode.startswith("ultra_large_"):
        return mode
    return f"ultra_large_{mode}"


def build_ultra_large_pr_mode_contract(
    *,
    command: str,
    pr_changed_files_count: int,
    changed_regions_considered: int,
    pr_segment_count: int,
    pr_cross_segment: bool,
    evidence_budget_overflow: int,
    evidence_budget_mode: str,
    pr_primary_segments: str,
    pr_support_segments: str,
    selected_items_count: int,
    patch_generation_result: str = "n/a",
    patch_target_files_selected: int = 0,
    localized_patch_evidence_count: int = 0,
) -> dict[str, Any]:
    changed_files = max(0, int(pr_changed_files_count or 0))
    changed_regions = max(0, int(changed_regions_considered or 0))
    segment_count = max(0, int(pr_segment_count or 0))
    overflow = max(0, int(evidence_budget_overflow or 0))
    selected = max(0, int(selected_items_count or 0))
    reasons: list[str] = []
    if changed_files >= 80:
        reasons.append("changed_files_threshold")
    if changed_regions >= 260:
        reasons.append("changed_regions_threshold")
    if bool(pr_cross_segment) and segment_count >= 6 and changed_files >= 40:
        reasons.append("cross_segment_spread_threshold")
    if overflow >= 25:
        reasons.append("evidence_budget_pressure")
    active = bool(reasons)

    level = "normal"
    if active:
        level = "extreme" if changed_files >= 150 or changed_regions >= 500 else "large"
    strategy = "standard" if not active else ("primary_first_extreme_cap" if level == "extreme" else "primary_first_capped")
    synthesis_window_cap = _cap_for(command, level=level)
    bounded_files_est = max(0, changed_files - selected)
    normalized_mode = _normalized_budget_mode(
        command=command,
        existing_mode=evidence_budget_mode,
        active=active,
    )

    patch_result = str(patch_generation_result or "n/a").strip().lower()
    localized = max(0, int(localized_patch_evidence_count or 0))
    patch_targets = max(0, int(patch_target_files_selected or 0))
    governance_downgraded = False
    governance_downgrade_reason = "n/a"
    if active and str(command or "").strip().lower() == "fix":
        if patch_result != "valid_patch":
            governance_downgraded = True
            if localized <= 0 or patch_targets <= 0:
                governance_downgrade_reason = "scale_bounded_localization_gap"
            else:
                governance_downgrade_reason = "scale_bounded_confidence_downgrade"

    primary_segments = str(pr_primary_segments or "none").strip() or "none"
    support_segments = str(pr_support_segments or "none").strip() or "none"
    coverage_statement = (
        "Bounded coverage active: deep focus on primary segments; secondary/support treated as bounded context."
        if active
        else "Standard coverage: no ultra-large PR bounds applied."
    )
    return {
        "ultra_large_pr_mode_active": bool(active),
        "ultra_large_pr_mode_level": level,
        "ultra_large_pr_mode_reason": ",".join(reasons) if reasons else "none",
        "ultra_large_pr_depth_strategy": strategy,
        "ultra_large_pr_synthesis_window_cap": int(synthesis_window_cap),
        "ultra_large_pr_evidence_budget_mode": normalized_mode,
        "ultra_large_pr_primary_coverage_summary": f"deep_primary={primary_segments}",
        "ultra_large_pr_bounded_coverage_summary": (
            f"support={support_segments}; bounded_files_est={bounded_files_est}"
        ),
        "ultra_large_pr_coverage_statement": coverage_statement,
        "ultra_large_pr_patch_governance_downgraded": bool(governance_downgraded),
        "ultra_large_pr_patch_governance_reason": governance_downgrade_reason,
    }
