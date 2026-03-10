from __future__ import annotations

from repobrain.ai_budget_governor import AIBudgetGovernor, BudgetPolicy, QuotaSignal


def test_governor_denies_when_remaining_zero() -> None:
    governor = AIBudgetGovernor(BudgetPolicy(min_remaining_buffer=0))
    governor.observe_llm_signal(
        QuotaSignal(
            remaining_requests=0,
            reset_time_utc_iso=None,
            remaining_is_estimate=False,
            usage_estimated=False,
            ratelimit_headers={},
        ),
        {"tokens_total": 10},
    )
    decision = governor.can_call_llm(next_call_cost_est=100, tier="high", intent="review")
    assert decision.allow is False
    assert decision.reason == "llm_remaining_exhausted"


def test_governor_respects_remaining_buffer() -> None:
    governor = AIBudgetGovernor(BudgetPolicy(min_remaining_buffer=2))
    governor.observe_llm_signal(
        QuotaSignal(
            remaining_requests=1,
            reset_time_utc_iso=None,
            remaining_is_estimate=False,
            usage_estimated=False,
            ratelimit_headers={},
        ),
        {"tokens_total": 10},
    )
    decision = governor.can_call_llm(next_call_cost_est=100, tier="low", intent="ask")
    assert decision.allow is False
    assert decision.reason == "llm_remaining_buffer"


def test_governor_downgrades_model_when_remaining_low() -> None:
    governor = AIBudgetGovernor(
        BudgetPolicy(
            min_remaining_buffer=0,
            switch_to_mini_when_remaining_lt=5,
            disable_reduce_when_remaining_lt=2,
        )
    )
    governor.observe_llm_signal(
        QuotaSignal(
            remaining_requests=4,
            reset_time_utc_iso=None,
            remaining_is_estimate=False,
            usage_estimated=False,
            ratelimit_headers={},
        ),
        {"tokens_total": 10},
    )
    decision = governor.can_call_llm(next_call_cost_est=100, tier="high", intent="review")
    assert decision.allow is True
    assert decision.switch_to_mini is True


def test_governor_disables_reduce_when_remaining_low() -> None:
    governor = AIBudgetGovernor(
        BudgetPolicy(
            min_remaining_buffer=0,
            disable_reduce_when_remaining_lt=3,
            stop_at_remaining=False,
        )
    )
    governor.observe_llm_signal(
        QuotaSignal(
            remaining_requests=2,
            reset_time_utc_iso=None,
            remaining_is_estimate=False,
            usage_estimated=False,
            ratelimit_headers={},
        ),
        {"tokens_total": 10},
    )
    decision = governor.can_call_llm(next_call_cost_est=100, tier="low", intent="review")
    assert decision.allow is True
    assert decision.disable_reduce is True
