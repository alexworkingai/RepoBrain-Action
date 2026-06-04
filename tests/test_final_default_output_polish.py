from __future__ import annotations

from repobrain.evidence import EvidenceItem
from repobrain.output_md import render_answer_markdown, render_patch_markdown, render_review_markdown


def test_review_default_omits_minimal_diagnostics_header() -> None:
    md = render_review_markdown(
        review={
            "summary_text": "Review summary.",
            "risk_level": "low",
            "files_block": ["- `docs/manual.md`"],
            "confirmed_findings": [],
            "possible_signals": [],
            "informational_notes": [],
            "recommendations": ["Run CI checks."],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={"command": "review", "route_final": "FAST"},
    )
    assert "<summary>Evidence and diagnostics</summary>" not in md


def test_fix_default_omits_minimal_diagnostics_header() -> None:
    md = render_patch_markdown(
        review={"summary_text": "Patch flow", "files_changed": [], "suggested_tests": []},
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
            "patch_target_files_total": 0,
            "patch_target_files_selected": 0,
            "patch_targeting_mode": "none",
            "patch_targeting_reason": "no_localized_evidence",
            "localized_patch_evidence_count": 0,
        },
    )
    assert "<summary>Evidence and diagnostics</summary>" not in md


def test_pr_ask_default_hides_evidence_and_verification_counters() -> None:
    md = render_answer_markdown(
        answer_text="PR impact summary.",
        evidence=[EvidenceItem(file_path="README.md", line_start=1, line_end=5, score=0.9)],
        audit_summary={
            "command": "ask",
            "route_final": "ASK",
            "selected": 4,
            "answer_grounding_mode": "hybrid",
            "pr_segmentation_used": True,
            "pr_segment_summary": "primary=docs:docs; support=workflow_config:.github; cross_segment=no",
        },
        next_steps="Validate docs wording.",
        command="ask",
    )
    primary = md.split("<details>", 1)[0]
    assert "Selected evidence" not in primary
    assert "Verification:" not in primary
    assert "### 📍 Evidence used" in primary


def test_verbose_mode_preserves_sanitized_details(monkeypatch) -> None:
    monkeypatch.setenv("RB_REPOBRAIN_VERBOSE_DIAGNOSTICS", "1")
    md = render_review_markdown(
        review={
            "summary_text": "Review summary.",
            "risk_level": "medium",
            "files_block": ["- `docs/manual.md`"],
            "confirmed_findings": [],
            "possible_signals": [],
            "informational_notes": [],
            "recommendations": ["Run CI checks."],
        },
        verification_report={"summary": "NOT_RUN", "checks": []},
        audit_summary={"command": "review", "route_final": "FAST"},
    )
    assert "<summary>Evidence and diagnostics</summary>" in md
