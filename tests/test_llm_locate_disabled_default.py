from __future__ import annotations

from dataclasses import dataclass, field

from repobrain.github_flow import _maybe_generate_llm_text


@dataclass(frozen=True)
class _FakeLLMResponse:
    text: str = "locator answer"
    model_id: str = "openai/gpt-4.1-mini"
    prompt_tokens: int = 10
    completion_tokens: int = 5
    total_tokens: int = 15
    usage_estimated: bool = False
    ratelimit_headers: dict[str, str] = field(default_factory=dict)
    requests_remaining: int | None = 20
    remaining_is_estimate: bool = False
    reset_time_utc_iso: str | None = "2026-03-05T23:59:59+00:00"


def test_llm_locate_disabled_by_default(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.delenv("RB_LLM_ALLOW_LOCATE", raising=False)

    def fail_if_called(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("LLM client must not be called for locate by default")

    monkeypatch.setattr("repobrain.github_flow.GitHubModelsClient.chat", fail_if_called)
    text, meta = _maybe_generate_llm_text(
        cmd="locate",
        intent="analysis",
        query="Locate TKYProvider",
        route="FAST",
        github_context={},
        locators=[],
        candidates_count=3,
    )
    assert text is None
    assert meta["llm_used"] is False
    assert meta["llm_skip_reason"] == "locate_disabled"


def test_llm_locate_can_be_enabled(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("RB_LLM_ALLOW_LOCATE", "1")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fake_chat(*args, **kwargs):  # noqa: ANN002, ANN003
        return _FakeLLMResponse(ratelimit_headers={})

    monkeypatch.setattr("repobrain.github_flow.GitHubModelsClient.chat", fake_chat)
    text, meta = _maybe_generate_llm_text(
        cmd="locate",
        intent="analysis",
        query="Locate TKYProvider",
        route="FAST",
        github_context={},
        locators=[],
        candidates_count=3,
    )
    assert text == "locator answer"
    assert meta["llm_used"] is True
