from __future__ import annotations

from repobrain.evidence import EvidenceItem
from repobrain.output_md import render_answer_markdown


def test_diagnostic_table_renders_and_orders_meaningful_before_undefined() -> None:
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
            "verification_pass_count": 1,
            "verification_fail_count": 0,
            "verification_pending_count": 0,
            "verification_not_run_count": 0,
        },
        next_steps="Validate evidence",
        command="ask",
    )

    assert "| Parameter | Value | Meaning / Risk |" in md
    assert "#### A. Decision summary" in md
    assert "| Route | `DEEP` |" in md

    decision_idx = md.index("#### A. Decision summary")
    undefined_idx = md.index("#### Undefined / disabled diagnostics")
    assert decision_idx < undefined_idx
