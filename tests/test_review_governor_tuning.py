from __future__ import annotations

from dataclasses import dataclass, field

from repobrain.ai_budget_governor import AIBudgetGovernor, BudgetPolicy, QuotaSignal
from repobrain.github_flow import _maybe_generate_llm_text, _set_runtime_env_cfg


@dataclass(frozen=True)
class _FakeResponse:
    text: str
    model_id: str
    prompt_tokens: int = 120
    completion_tokens: int = 90
    total_tokens: int = 210
    usage_estimated: bool = False
    ratelimit_headers: dict[str, str] = field(default_factory=dict)
    requests_remaining: int | None = 12
    remaining_is_estimate: bool = False
    reset_time_utc_iso: str | None = "2026-03-12T00:00:00+00:00"


def test_review_retains_strong_model_with_sufficient_remaining_quota(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("RB_LLM_DOWNGRADE_MIN_REMAINING_REQUESTS_REVIEW", "4")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    _set_runtime_env_cfg(None)  # noqa: SLF001

    captured_model: dict[str, str] = {"value": ""}

    def fake_chat(self, **kwargs):  # noqa: ANN001
        captured_model["value"] = str(kwargs["model_id"])
        return _FakeResponse(
            text="Review synthesis result.",
            model_id=str(kwargs["model_id"]),
        )

    monkeypatch.setattr("repobrain.github_flow.GitHubModelsClient.chat", fake_chat)

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
            remaining_requests=4,
            reset_time_utc_iso=None,
            remaining_is_estimate=False,
            usage_estimated=False,
            ratelimit_headers={},
        ),
        {"tokens_total": 100},
    )

    text, meta = _maybe_generate_llm_text(
        cmd="review",
        intent="review",
        query=("Review these PR changes and summarize risk. " * 20).strip(),
        route="DEEP",
        execution_mode="retrieval_plus_llm",
        llm_intent_decision="review",
        llm_decision_reason_short="LLM used: multi-source synthesis required after deep retrieval.",
        llm_decision_reason_code="MULTI_SOURCE_SYNTHESIS_REQUIRED",
        github_context={"changed_files": [f"repobrain/module_{i}.py" for i in range(6)]},
        locators=[],
        candidates_count=48,
        governor=governor,
    )

    assert text is not None
    assert captured_model["value"] == "openai/gpt-4.1"
    assert meta["llm_model_used"] == "openai/gpt-4.1"
    assert meta["llm_model_downgrade_reason"] == "n/a"
    assert "review synthesis retained strong model" in str(
        meta["llm_retained_preferred_model_reason"]
    ).lower()
    assert "preferred model retained" in str(meta["llm_budget_action"]).lower()


def test_review_low_quota_still_downgrades_to_mini(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("RB_LLM_DOWNGRADE_MIN_REMAINING_REQUESTS_REVIEW", "4")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    _set_runtime_env_cfg(None)  # noqa: SLF001

    captured_model: dict[str, str] = {"value": ""}

    def fake_chat(self, **kwargs):  # noqa: ANN001
        captured_model["value"] = str(kwargs["model_id"])
        return _FakeResponse(
            text="Review synthesis result.",
            model_id=str(kwargs["model_id"]),
        )

    monkeypatch.setattr("repobrain.github_flow.GitHubModelsClient.chat", fake_chat)

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

    text, meta = _maybe_generate_llm_text(
        cmd="review",
        intent="review",
        query=("Review these PR changes and summarize risk. " * 20).strip(),
        route="DEEP",
        execution_mode="retrieval_plus_llm",
        llm_intent_decision="review",
        llm_decision_reason_short="LLM used: multi-source synthesis required after deep retrieval.",
        llm_decision_reason_code="MULTI_SOURCE_SYNTHESIS_REQUIRED",
        github_context={"changed_files": [f"repobrain/module_{i}.py" for i in range(6)]},
        locators=[],
        candidates_count=48,
        governor=governor,
    )

    assert text is not None
    assert captured_model["value"] == "openai/gpt-4.1-mini"
    assert meta["llm_model_used"] == "openai/gpt-4.1-mini"
    assert meta["llm_retained_preferred_model_reason"] == "n/a"
    assert "switched to mini" in str(meta["llm_model_downgrade_reason"]).lower()
