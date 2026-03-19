from __future__ import annotations

from repobrain.llm.batch_planner import Batch
from repobrain.review_batch_planner import plan_review_fix_batches


def _batch(batch_id: str, *paths: str) -> Batch:
    return Batch(
        batch_id=batch_id,
        paths=list(paths),
        diff_hunks=[],
        snippet_ids=[],
        estimated_input_tokens=400,
    )


def test_segment_aware_batch_planner_prioritizes_primary_segments() -> None:
    batches = [
        _batch("b_docs", "docs/guide.md"),
        _batch("b_core", "repobrain/github_flow.py"),
        _batch("b_tests", "tests/test_flow.py"),
    ]
    plan = plan_review_fix_batches(
        batches,
        command="review",
        pr_segmentation={
            "file_segment_class_map": {
                "docs/guide.md": "docs",
                "repobrain/github_flow.py": "core_code",
                "tests/test_flow.py": "tests",
            }
        },
        evidence_budget_state={},
        runtime_limits={},
    )

    assert [item.batch_id for item in plan.ordered_batches] == ["b_core", "b_docs", "b_tests"]
    assert plan.batch_planner_used is True
    assert plan.batch_plan_mode == "segment_primary_first"
    assert plan.batch_count_planned == 3
    assert plan.batch_primary_segments == "core_code"
    assert plan.batch_support_segments == "docs,tests"
    assert plan.batch_fallback_reason == "none"


def test_segment_aware_batch_planner_falls_back_without_segmentation() -> None:
    batches = [_batch("b1", "a.py"), _batch("b2", "b.py")]
    plan = plan_review_fix_batches(
        batches,
        command="fix",
        pr_segmentation={},
        evidence_budget_state={},
        runtime_limits={},
    )

    assert [item.batch_id for item in plan.ordered_batches] == ["b1", "b2"]
    assert plan.batch_planner_used is False
    assert plan.batch_plan_mode == "fallback_original_order"
    assert plan.batch_fallback_reason == "missing_segmentation_map"


def test_segment_aware_batch_planner_is_deterministic_for_same_input() -> None:
    batches = [
        _batch("b_cfg", "pyproject.toml"),
        _batch("b_core", "repobrain/output_md.py"),
        _batch("b_docs", "docs/readme.md"),
    ]
    file_segment_map = {
        "pyproject.toml": "config_build",
        "repobrain/output_md.py": "core_code",
        "docs/readme.md": "docs",
    }
    plan_a = plan_review_fix_batches(
        batches,
        command="review",
        pr_segmentation={"file_segment_class_map": file_segment_map},
        evidence_budget_state={},
        runtime_limits={},
    )
    plan_b = plan_review_fix_batches(
        batches,
        command="review",
        pr_segmentation={"file_segment_class_map": file_segment_map},
        evidence_budget_state={},
        runtime_limits={},
    )

    assert [item.batch_id for item in plan_a.ordered_batches] == [item.batch_id for item in plan_b.ordered_batches]
    assert plan_a.as_audit_fields() == plan_b.as_audit_fields()


def test_segment_aware_batch_planner_fallback_for_unsupported_command() -> None:
    batches = [_batch("b1", "repobrain/github_flow.py")]
    plan = plan_review_fix_batches(
        batches,
        command="ask",
        pr_segmentation={"file_segment_class_map": {"repobrain/github_flow.py": "core_code"}},
        evidence_budget_state={},
        runtime_limits={},
    )

    assert [item.batch_id for item in plan.ordered_batches] == ["b1"]
    assert plan.batch_planner_used is False
    assert plan.batch_fallback_reason == "unsupported_command"
