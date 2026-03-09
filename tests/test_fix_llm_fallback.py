from __future__ import annotations

from dataclasses import dataclass, field

from repobrain.github_flow import _maybe_generate_llm_text, _set_runtime_env_cfg
from repobrain.llm.github_models import GitHubModelsError


@dataclass(frozen=True)
class _FakeLLMResponse:
    text: str
    model_id: str
    prompt_tokens: int = 30
    completion_tokens: int = 20
    total_tokens: int = 50
    usage_estimated: bool = False
    ratelimit_headers: dict[str, str] = field(default_factory=dict)
    requests_remaining: int | None = 9
    remaining_is_estimate: bool = False
    reset_time_utc_iso: str | None = "2026-03-10T00:00:00+00:00"


def test_fix_llm_fallback_uses_alternate_model(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    _set_runtime_env_cfg(None)  # noqa: SLF001

    calls = {"primary": 0, "fallback": 0}

    def fake_chat(self, **kwargs):  # noqa: ANN001
        model_id = kwargs["model_id"]
        if model_id == "openai/gpt-4.1":
            calls["primary"] += 1
            raise GitHubModelsError(
                "primary unavailable",
                status_code=500,
                reason="server_error",
            )
        calls["fallback"] += 1
        return _FakeLLMResponse(
            text="```diff\n--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-a\n+b\n```",
            model_id=model_id,
        )

    monkeypatch.setattr("repobrain.github_flow.GitHubModelsClient.chat", fake_chat)
    monkeypatch.setattr("repobrain.github_flow.time.sleep", lambda *_args, **_kwargs: None)

    text, meta = _maybe_generate_llm_text(
        cmd="fix",
        intent="patch",
        query="Apply a small patch",
        route="FAST",
        github_context={},
        locators=[],
        candidates_count=5,
        preferred_model_id="openai/gpt-4.1",
        preferred_tier="high",
    )

    assert text is not None
    assert meta["llm_used"] is True
    assert meta["llm_primary_model_id"] == "openai/gpt-4.1"
    assert meta["llm_effective_model_id"] == "openai/gpt-4.1-mini"
    assert meta["llm_fallback_used"] is True
    assert meta["llm_provider_error_type"] == "server_error"
    assert calls["primary"] >= 1
    assert calls["fallback"] == 1
