from __future__ import annotations

from repobrain.ai_budget_governor import AIBudgetGovernor, BudgetPolicy, QuotaSignal
from repobrain.llm.model_selector import choose_model


def test_review_prefers_gpt41_even_with_low_score() -> None:
    model_id, tier = choose_model(
        10,
        task_type="review",
        intent="analysis",
        route="FAST",
        execution_mode="retrieval_plus_llm",
        llm_intent="review",
    )

    assert model_id == "openai/gpt-4.1"
    assert tier == "high"


def test_patch_prefers_gpt41_even_with_low_score() -> None:
    model_id, tier = choose_model(
        5,
        task_type="fix",
        intent="patch",
        route="FAST",
        execution_mode="retrieval_plus_llm",
        llm_intent="patch",
    )

    assert model_id == "openai/gpt-4.1"
    assert tier == "high"


def test_complex_deep_synthesis_prefers_gpt41() -> None:
    model_id, tier = choose_model(
        20,
        task_type="ask",
        intent="analysis",
        route="DEEP",
        execution_mode="retrieval_plus_llm",
        llm_intent="summarize",
        synthesis_required=True,
    )

    assert model_id == "openai/gpt-4.1"
    assert tier == "high"


def test_simple_ask_can_use_mini() -> None:
    model_id, tier = choose_model(
        12,
        task_type="ask",
        intent="analysis",
        route="FAST",
        execution_mode="retrieval_only",
        llm_intent="none",
        synthesis_required=False,
    )

    assert model_id == "openai/gpt-4.1-mini"
    assert tier == "low"


def test_governor_still_supports_downgrade_to_mini() -> None:
    governor = AIBudgetGovernor(
        BudgetPolicy(
            stop_at_remaining=True,
            min_remaining_buffer=1,
            switch_to_mini_when_remaining_lt=5,
            max_llm_calls_per_run=10,
            max_embed_calls_per_run=10,
        )
    )
    governor.observe_llm_signal(
        QuotaSignal(
            remaining_requests=3,
            reset_time_utc_iso=None,
            remaining_is_estimate=False,
            usage_estimated=False,
            ratelimit_headers={},
        ),
        {"tokens_total": 100},
    )

    decision = governor.can_call_llm(next_call_cost_est=200, tier="high", intent="review")
    assert decision.allow is True
    assert decision.switch_to_mini is True

