from __future__ import annotations

from repobrain.output_md import render_answer_markdown


def test_compact_llm_block_reports_used_model_and_tokens() -> None:
    md = render_answer_markdown(
        answer_text="Answer text",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "DEEP",
            "execution_mode": "retrieval_plus_llm",
            "llm_used": True,
            "llm_model_used": "openai/gpt-5",
            "llm_tokens_total": 123,
            "llm_decision_reason_short": "multi-source synthesis required",
        },
        next_steps="Validate",
        command="ask",
    )

    assert "- LLM: used" in md
    assert "- Model: `openai/gpt-5`" in md
    assert "- Tokens: `123`" in md
    assert "Requests remaining today" not in md


def test_compact_llm_block_reports_not_called_without_contradiction() -> None:
    md = render_answer_markdown(
        answer_text="Answer text",
        evidence=[],
        audit_summary={
            "command": "ask",
            "route_final": "FAST",
            "execution_mode": "retrieval_only",
            "llm_used": False,
        },
        next_steps="Validate",
        command="ask",
    )

    assert "- LLM: not called" in md
    assert "- Tokens: `0`" in md
    assert "LLM used: yes" not in md
