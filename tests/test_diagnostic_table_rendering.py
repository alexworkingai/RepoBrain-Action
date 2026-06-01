from __future__ import annotations

import pytest

from repobrain.evidence import EvidenceItem
from repobrain.output_md import render_answer_markdown


def test_diagnostic_output_is_compact_and_groups_primary_before_secondary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RB_REPOBRAIN_VERBOSE_DIAGNOSTICS", "1")
    md = render_answer_markdown(
        answer_text="Short answer",
        evidence=[
            EvidenceItem(
                file_path="repobrain/github_flow.py",
                line_start=10,
                line_end=20,
                score=0.9,
            )
        ],
        audit_summary={
            "route_final": "DEEP",
            "execution_mode": "retrieval_plus_llm",
            "llm_intent": "summarize",
            "llm_decision_reason_code": "MULTI_SOURCE_SYNTHESIS_REQUIRED",
            "tkya_backend": "v5",
            "tky_engine": "topocore_lite",
            "llm_used": True,
            "llm_model_used": "openai/gpt-4.1-mini",
            "llm_calls_this_run": 1,
            "retrieved": 12,
            "selected": 3,
            "hybrid_rerank_used": False,
            "retrieval_ranking_mode": "lexical",
            "evidence_filtered_count": 0,
            "evidence_filter_reason_codes": "none",
            "signal_calibration_used": False,
            "patch_guard_triggered": False,
            "tldr_compressed": False,
            "verification_pass_count": 1,
            "verification_fail_count": 0,
            "verification_pending_count": 0,
            "verification_not_run_count": 0,
        },
        next_steps="Validate evidence",
        command="ask",
    )

    assert "| Parameter | Value | Meaning / Risk |" not in md
    assert "### 🧾 Runtime diagnostics" in md
    assert "#### A. Decision summary" in md
    assert "- Route: `DEEP`" in md
    assert "- Hybrid rerank used: `no`" in md
    assert "- Retrieval ranking mode: `lexical`" in md
    assert "- Evidence filtered: `0`" in md
    assert "- Evidence filter reason codes: `none`" in md
    assert "- Signal calibration used: `no`" in md
    assert "- Patch guard triggered: `no`" in md
    assert "- TL;DR compressed: `no`" in md

    decision_idx = md.index("#### A. Decision summary")
    secondary_idx = md.index("### Secondary diagnostics")
    assert decision_idx < secondary_idx


def test_secondary_diagnostics_and_audit_anchors_render_cleanly_inside_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RB_REPOBRAIN_VERBOSE_DIAGNOSTICS", "1")
    md = render_answer_markdown(
        answer_text="Short answer",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "execution_mode": "retrieval_only",
            "llm_used": False,
            "retrieval_ranking_mode": "lexical",
            "hybrid_rerank_used": False,
            "remote_skipped_reason": "n/a",
            "tky_fallback_reason": "n/a",
        },
        next_steps="Validate evidence",
        command="ask",
    )

    assert "<summary>Evidence and diagnostics</summary>" in md
    assert "### Secondary diagnostics" in md
    assert "### 🧾 Audit anchors" in md
    assert "### Secondary diagnostics\n\n**" in md
    assert "### Secondary diagnostics### 🧾 Audit anchors" not in md
