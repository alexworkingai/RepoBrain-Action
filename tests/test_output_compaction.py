from __future__ import annotations

from repobrain.output_md import render_answer_markdown, render_patch_markdown


def test_primary_diagnostics_render_without_wide_table() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "execution_mode": "retrieval_only",
            "retrieval_ranking_mode": "hybrid",
            "hybrid_rerank_used": True,
            "evidence_budget_mode": "ask_dense_incremental",
            "evidence_budget_used": 5,
            "evidence_budget_limit": 8,
        },
        next_steps="n/a",
        command="ask",
    )

    assert "### 🧾 Runtime diagnostics" in md
    assert "| Parameter | Value | Meaning / Risk |" not in md
    assert "- Retrieval ranking mode: `hybrid`" in md


def test_low_value_diagnostics_are_suppressed_from_primary_view() -> None:
    md = render_answer_markdown(
        answer_text="Answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "execution_mode": "retrieval_only",
            "remote_skipped_reason": "n/a",
            "tky_fallback_reason": "n/a",
            "retrieval_ranking_mode": "lexical",
            "hybrid_rerank_used": False,
        },
        next_steps="n/a",
        command="ask",
    )

    primary = md.split("<details>", 1)[0]
    assert "- Remote skipped reason: `n/a`" not in primary
    assert "<summary>Secondary diagnostics (defaults/noise)</summary>" in md


def test_fix_output_keeps_compact_patch_sections() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow"},
        verification_report={"summary": "NOT_RUN", "checks": []},
        patch_snippet="",
        patch_written=False,
        patch_apply_message="safe no_patch outcome",
        audit_summary={
            "command": "fix",
            "route_final": "FAST",
            "patch_generation_result": "no_patch",
            "patch_validation_result": "no_patch",
            "patch_validation_reason": "No patch generated.",
            "patch_target_files_total": 2,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence",
            "patch_grounding_mode": "pr_metadata",
        },
    )

    assert "### 🧾 Patch result" in md
    assert "| Parameter | Value | Meaning / Risk |" not in md
