from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from repobrain.llm.batch_planner import Batch

_SUPPORT_SEGMENT_CLASSES = {
    "tests",
    "docs",
    "workflow_ci",
    "config_build",
    "tooling_scripts",
    "generated_or_vendor",
}


@dataclass(frozen=True)
class BatchPlan:
    ordered_batches: list[Batch]
    batch_planner_used: bool
    batch_plan_mode: str
    batch_count_planned: int
    batch_primary_segments: str
    batch_support_segments: str
    batch_fallback_reason: str

    def as_audit_fields(self) -> dict[str, Any]:
        return {
            "batch_planner_used": bool(self.batch_planner_used),
            "batch_plan_mode": str(self.batch_plan_mode or "fallback_original_order"),
            "batch_count_planned": int(self.batch_count_planned),
            "batch_primary_segments": str(self.batch_primary_segments or "none"),
            "batch_support_segments": str(self.batch_support_segments or "none"),
            "batch_fallback_reason": str(self.batch_fallback_reason or "none"),
        }


def _join_labels(values: list[str]) -> str:
    normalized = [str(item).strip() for item in values if str(item).strip()]
    return ",".join(normalized) if normalized else "none"


def _segment_for_batch(batch: Batch, file_segment_map: dict[str, str]) -> tuple[str, bool]:
    counts: dict[str, int] = {}
    for path in batch.paths:
        segment_class = str(file_segment_map.get(str(path).strip(), "mixed_or_other") or "mixed_or_other")
        counts[segment_class] = counts.get(segment_class, 0) + 1
    if not counts:
        return "mixed_or_other", False
    dominant_segment = sorted(counts.items(), key=lambda item: (-int(item[1]), str(item[0])))[0][0]
    return dominant_segment, dominant_segment in _SUPPORT_SEGMENT_CLASSES


def plan_review_fix_batches(
    batches: list[Batch],
    *,
    command: str,
    pr_segmentation: dict[str, Any] | None,
    evidence_budget_state: dict[str, Any] | None,
    runtime_limits: dict[str, Any] | None,
) -> BatchPlan:
    _ = evidence_budget_state
    _ = runtime_limits
    normalized_cmd = str(command or "").strip().lower()
    if normalized_cmd not in {"review", "fix"}:
        return BatchPlan(
            ordered_batches=list(batches),
            batch_planner_used=False,
            batch_plan_mode="fallback_original_order",
            batch_count_planned=len(batches),
            batch_primary_segments="none",
            batch_support_segments="none",
            batch_fallback_reason="unsupported_command",
        )

    file_segment_map_raw = (pr_segmentation or {}).get("file_segment_class_map", {})
    file_segment_map = (
        {
            str(path).strip(): str(segment).strip()
            for path, segment in file_segment_map_raw.items()
            if str(path).strip() and str(segment).strip()
        }
        if isinstance(file_segment_map_raw, dict)
        else {}
    )
    if not batches:
        return BatchPlan(
            ordered_batches=[],
            batch_planner_used=False,
            batch_plan_mode="fallback_original_order",
            batch_count_planned=0,
            batch_primary_segments="none",
            batch_support_segments="none",
            batch_fallback_reason="no_batches",
        )
    if not file_segment_map:
        return BatchPlan(
            ordered_batches=list(batches),
            batch_planner_used=False,
            batch_plan_mode="fallback_original_order",
            batch_count_planned=len(batches),
            batch_primary_segments="none",
            batch_support_segments="none",
            batch_fallback_reason="missing_segmentation_map",
        )

    annotated: list[tuple[int, str, str, Batch]] = []
    primary_segments: list[str] = []
    support_segments: list[str] = []
    for batch in batches:
        dominant_segment, is_support = _segment_for_batch(batch, file_segment_map)
        priority = 1 if is_support else 0
        sort_hint = ",".join(sorted(str(path) for path in batch.paths))
        annotated.append((priority, dominant_segment, sort_hint, batch))
        if is_support:
            support_segments.append(dominant_segment)
        else:
            primary_segments.append(dominant_segment)

    annotated.sort(key=lambda item: (item[0], item[1], item[2], item[3].batch_id))
    ordered_batches = [item[3] for item in annotated]
    return BatchPlan(
        ordered_batches=ordered_batches,
        batch_planner_used=True,
        batch_plan_mode="segment_primary_first",
        batch_count_planned=len(ordered_batches),
        batch_primary_segments=_join_labels(list(dict.fromkeys(primary_segments))),
        batch_support_segments=_join_labels(list(dict.fromkeys(support_segments))),
        batch_fallback_reason="none",
    )
