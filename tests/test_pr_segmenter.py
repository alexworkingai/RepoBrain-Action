from __future__ import annotations

from repobrain.pr_segmenter import build_pr_segmentation, segmentation_defaults


def test_pr_segmenter_classifies_core_docs_tests_workflow() -> None:
    result = build_pr_segmentation(
        changed_files=[
            "repobrain/github_flow.py",
            "tests/test_review.py",
            "docs/e2e_testing.md",
            ".github/workflows/repobrain.yml",
        ],
        candidate_paths=[
            "repobrain/github_flow.py",
            "repobrain/output_md.py",
            "tests/test_review.py",
        ],
    )

    assert result.pr_segmentation_used is True
    assert result.pr_segment_count >= 3
    assert "core_code" in result.pr_primary_segments
    assert "docs=" in result.pr_segment_file_counts
    assert "tests=" in result.pr_segment_file_counts
    assert "workflow_ci=" in result.pr_segment_file_counts
    assert "core_code=" in result.pr_segment_candidate_counts


def test_pr_segmenter_detects_cross_segment_changes() -> None:
    result = build_pr_segmentation(
        changed_files=[
            "repobrain/github_flow.py",
            ".github/workflows/repobrain.yml",
            "pyproject.toml",
        ],
        candidate_paths=[],
    )
    assert result.pr_cross_segment is True
    assert result.pr_primary_segments != "none"
    assert result.pr_segment_summary != "none"


def test_pr_segmenter_support_only_pr_has_support_primary() -> None:
    result = build_pr_segmentation(
        changed_files=[
            "docs/readme.md",
            "docs/usage.md",
            "tests/test_cli.py",
        ],
        candidate_paths=[],
    )

    assert result.pr_segmentation_used is True
    assert result.pr_segment_count >= 2
    assert result.pr_primary_segments != "none"
    assert result.pr_support_segments != "none"


def test_pr_segmenter_fallback_is_deterministic() -> None:
    result = build_pr_segmentation(changed_files=[], candidate_paths=[])
    defaults = segmentation_defaults(fallback_reason="missing_changed_files")

    assert result.pr_segmentation_used is False
    assert result.pr_segmentation_fallback_reason == "missing_changed_files"
    assert result.as_audit_fields()["pr_segment_count"] == defaults["pr_segment_count"]
    assert result.as_audit_fields()["pr_primary_segments"] == defaults["pr_primary_segments"]
