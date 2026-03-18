from __future__ import annotations

from repobrain.output_md import render_answer_markdown, render_patch_markdown, render_review_markdown


def _primary(md: str) -> str:
    return md.split("<details>", 1)[0]


def test_ask_primary_output_is_compact_and_segment_visible() -> None:
    md = render_answer_markdown(
        answer_text="Answer summary.",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "DEEP",
            "selected": 4,
            "answer_grounding_mode": "hybrid",
            "pr_segmentation_used": True,
            "pr_segment_summary": "primary=core_code:repobrain; support=tests:tests; cross_segment=yes",
            "incremental_retrieval_used": True,
            "incremental_scope_mode": "changed_files_first",
            "evidence_budget_mode": "ask_dense_incremental",
            "evidence_budget_used": 9,
        },
        next_steps="Validate the proposed change list.",
        command="ask",
    )

    primary = _primary(md)
    assert "### 🧭 Run summary" in primary
    assert "- Segment summary: `primary=core_code:repobrain; support=tests:tests; cross_segment=yes`" in primary
    assert "### 📊 Evidence" not in primary
    assert "<summary>Details and diagnostics</summary>" in md


def test_review_primary_output_is_tiered_and_non_duplicative() -> None:
    md = render_review_markdown(
        review={
            "summary_text": "Review completed with focused risk assessment.",
            "risk_level": "medium",
            "files_block": ["- `repobrain/github_flow.py`", "- `docs/artifacts.md`"],
            "confirmed_findings": [],
            "possible_signals": ["Potential config drift"],
            "informational_notes": ["Docs updated"],
            "recommendations": ["Run CI", "Smoke test command flow"],
            "risk_drivers": ["workflow changes"],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={
            "command": "review",
            "route_final": "FAST",
            "pr_segmentation_used": True,
            "pr_segment_summary": "primary=core_code:repobrain; support=docs:docs; cross_segment=yes",
        },
    )

    primary = _primary(md)
    assert "### ✅ PR Review" in primary
    assert "- Segment summary: `primary=core_code:repobrain; support=docs:docs; cross_segment=yes`" in primary
    assert "### 🗂️ Touched files" not in primary
    assert "### ✅ Recommendations" in primary


def test_fix_primary_output_focuses_on_outcome_not_full_patch_dump() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="diff --git a/a.py b/a.py",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 5,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence",
            "localized_patch_evidence_count": 0,
            "pr_segment_summary": "primary=core_code:repobrain; support=tests:tests; cross_segment=no",
        },
    )

    primary = _primary(md)
    assert "### 🧾 Patch result" in primary
    assert "- Result: `no_patch`" in primary
    assert "### 🎯 Patch targeting" not in primary


def test_ask_output_no_long_touched_files_duplication() -> None:
    md = render_answer_markdown(
        answer_text="Answer summary.",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "touched_files": [f"repobrain/file_{idx}.py" for idx in range(10)],
            "pr_segmentation_used": True,
            "pr_segment_summary": "primary=core_code:repobrain; support=tests:tests; cross_segment=no",
        },
        next_steps="n/a",
        command="ask",
    )

    assert "Touched files:" not in _primary(md)
