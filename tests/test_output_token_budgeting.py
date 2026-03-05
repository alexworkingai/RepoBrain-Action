from __future__ import annotations

from repobrain.llm.model_selector import compute_output_token_budget


def test_fix_budget_is_higher_than_ask(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_MAX_OUTPUT_TOKENS_GLOBAL", "2000")
    monkeypatch.setenv("RB_LLM_MAX_OUTPUT_TOKENS_ASK", "1000")
    monkeypatch.setenv("RB_LLM_MAX_OUTPUT_TOKENS_FIX", "2000")

    ask_budget = compute_output_token_budget("ask", "analysis", 70)
    fix_budget = compute_output_token_budget("fix", "patch", 70)

    assert ask_budget < fix_budget
    assert fix_budget <= 2000


def test_budget_respects_global_cap(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_MAX_OUTPUT_TOKENS_GLOBAL", "900")
    monkeypatch.setenv("RB_LLM_MAX_OUTPUT_TOKENS_ASK", "1400")
    monkeypatch.setenv("RB_LLM_MAX_OUTPUT_TOKENS_REVIEW", "1600")
    monkeypatch.setenv("RB_LLM_MAX_OUTPUT_TOKENS_FIX", "2200")

    ask_budget = compute_output_token_budget("ask", "analysis", 100)
    review_budget = compute_output_token_budget("review", "review", 100)
    fix_budget = compute_output_token_budget("fix", "patch", 100)

    assert ask_budget <= 900
    assert review_budget <= 900
    assert fix_budget <= 900
