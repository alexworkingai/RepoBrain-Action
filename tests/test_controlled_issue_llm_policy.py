from __future__ import annotations

from dataclasses import dataclass, field

from repobrain.github_flow import (
    _maybe_generate_llm_text,
    _set_runtime_env_cfg,
    is_issue_llm_enabled,
    should_use_llm_for_issue_ask_explain,
)


@dataclass(frozen=True)
class _FakeLLMResponse:
    text: str = "issue llm answer"
    model_id: str = "openai/gpt-4.1-mini"
    prompt_tokens: int = 20
    completion_tokens: int = 10
    total_tokens: int = 30
    usage_estimated: bool = False
    ratelimit_headers: dict[str, str] = field(default_factory=dict)
    requests_remaining: int | None = 15
    remaining_is_estimate: bool = False
    reset_time_utc_iso: str | None = "2026-06-04T12:00:00+00:00"


def test_issue_llm_default_enabled() -> None:
    _set_runtime_env_cfg(None)  # noqa: SLF001
    assert is_issue_llm_enabled() is True


def test_issue_ask_balanced_uses_llm_when_policy_and_provider_allow(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("RB_REPOBRAIN_ENABLE_ISSUE_LLM", "1")
    monkeypatch.setenv("RB_LLM_EXECUTION_PROFILE", "balanced")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    _set_runtime_env_cfg(None)  # noqa: SLF001

    monkeypatch.setattr("repobrain.github_flow.GitHubModelsClient.chat", lambda *_args, **_kwargs: _FakeLLMResponse())

    text, meta = _maybe_generate_llm_text(
        cmd="ask",
        intent="analysis",
        query="Analyze this repository as a product.",
        route="ASK",
        execution_mode="retrieval_plus_llm",
        llm_intent_decision="summarize",
        llm_decision_reason_short="LLM used: controlled issue LLM enabled for balanced ask synthesis.",
        llm_decision_reason_code="CONTROLLED_ISSUE_LLM_ENABLED",
        github_context={"event_name": "issue_comment", "is_pr": False},
        locators=[],
        candidates_count=4,
    )
    assert text == "issue llm answer"
    assert meta["llm_used"] is True


def test_issue_llm_disable_blocks_free_text_bypass(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("RB_REPOBRAIN_ENABLE_ISSUE_LLM", "0")
    monkeypatch.setenv("RB_LLM_EXECUTION_PROFILE", "premium")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    _set_runtime_env_cfg(None)  # noqa: SLF001

    assert should_use_llm_for_issue_ask_explain(
        cmd="ask",
        github_context={"event_name": "issue_comment", "is_pr": False},
        execution_profile="premium",
    ) is False

    def fail_if_called(*_args, **_kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("issue LLM must not run when repository policy disables it")

    monkeypatch.setattr("repobrain.github_flow.GitHubModelsClient.chat", fail_if_called)
    text, meta = _maybe_generate_llm_text(
        cmd="ask",
        intent="analysis",
        query="use LLM and explain the architecture",
        route="ASK",
        execution_mode="retrieval_plus_llm",
        llm_intent_decision="summarize",
        llm_decision_reason_short="LLM used: controlled issue LLM enabled for premium ask synthesis.",
        llm_decision_reason_code="CONTROLLED_ISSUE_LLM_ENABLED",
        github_context={"event_name": "issue_comment", "is_pr": False},
        locators=[],
        candidates_count=3,
    )
    assert text is None
    assert meta["llm_used"] is False
    assert meta["llm_skip_reason"] == "issue_llm_policy_disabled"
