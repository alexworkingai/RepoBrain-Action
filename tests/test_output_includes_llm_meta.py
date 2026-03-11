from __future__ import annotations

from repobrain.evidence import EvidenceItem
from repobrain.output_md import render_answer_markdown


def test_render_answer_markdown_includes_llm_metadata() -> None:
    md = render_answer_markdown(
        answer_text="Short answer",
        evidence=[
            EvidenceItem(
                file_path="repobrain/tky_provider.py",
                line_start=1,
                line_end=20,
                score=0.9,
            )
        ],
        audit_summary={
            "route_final": "FAST",
            "pass_count": 1,
            "retrieved": 10,
            "selected": 1,
            "llm_used": True,
            "llm_skip_reason": "n/a",
            "llm_model_used": "openai/gpt-4.1",
            "llm_tokens_prompt": 100,
            "llm_tokens_completion": 44,
            "llm_tokens_total": 144,
            "llm_usage_estimated": False,
            "llm_calls_this_run": 1,
            "llm_remaining_requests": 33,
            "llm_remaining_is_estimate": False,
            "llm_reset_time_utc_iso": "2026-03-05T23:59:59Z",
            "llm_input_budget_used_est": 800,
            "llm_input_budget_limit": 1200,
            "llm_dropped_locators_count": 0,
            "llm_dropped_hunks_count": 1,
            "llm_dropped_snippets_count": 2,
        },
        next_steps="Open evidence links and verify logic",
        command="ask",
    )

    assert "### 🤖 LLM" in md
    assert "LLM used: yes" in md
    assert "LLM model used: `openai/gpt-4.1`" in md
    assert "Tokens used: prompt=100 completion=44 total=144 (reported)" in md
    assert "Requests remaining today: 33" in md
    assert "Reset time UTC: 2026-03-05T23:59:59Z" in md
    assert "Prompt budget: used~800 / limit=1200" in md
    assert "Models used: openai/gpt-4.1 (1 call)" in md
