from __future__ import annotations

from repobrain.output_md import render_answer_markdown


def test_issue_llm_quota_exhausted_rendering_is_explicit() -> None:
    md = render_answer_markdown(
        answer_text="Deterministic fallback answer.",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "ASK",
            "execution_mode": "retrieval_plus_llm",
            "llm_used": False,
            "llm_skip_reason": "budget:llm_remaining_exhausted",
            "llm_runtime_override_reason": "LLM quota/limit exhausted; request processed with deterministic fallback until limits reset.",
            "llm_decision_reason_short": "LLM used: controlled issue LLM enabled for balanced ask synthesis.",
            "llm_decision_reason_code": "CONTROLLED_ISSUE_LLM_ENABLED",
        },
        next_steps="Validate evidence",
        command="ask",
    )

    assert "- LLM: not called" in md
    assert "quota/limit exhausted" in md
    assert "- Limit status: `exhausted`" in md
    assert "- Reset: `unknown`" in md


def test_issue_llm_provider_rate_limit_attempted_state_is_explicit() -> None:
    md = render_answer_markdown(
        answer_text="Deterministic fallback answer.",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "ASK",
            "execution_mode": "retrieval_plus_llm",
            "llm_used": False,
            "llm_skip_reason": "LLM_NOT_AVAILABLE:rate_limited",
            "llm_provider_error_type": "rate_limited",
            "llm_runtime_override_reason": "LLM quota/limit exhausted during provider call; deterministic fallback used.",
            "llm_decision_reason_short": "LLM used: controlled issue LLM enabled for balanced ask synthesis.",
            "llm_decision_reason_code": "CONTROLLED_ISSUE_LLM_ENABLED",
        },
        next_steps="Validate evidence",
        command="ask",
    )

    assert "- LLM: attempted but not completed" in md
    assert "quota/limit exhausted during provider call" in md
    assert "- Limit status: `exhausted`" in md
