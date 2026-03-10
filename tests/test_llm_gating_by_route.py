from __future__ import annotations

from repobrain.github_flow import _maybe_generate_llm_text


def test_llm_skips_for_wait_refuse_block(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fail_if_called(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("LLM client must not be called for WAIT/REFUSE/BLOCK routes")

    monkeypatch.setattr("repobrain.github_flow.GitHubModelsClient.chat", fail_if_called)

    for route in ("WAIT", "REFUSE", "BLOCK"):
        text, meta = _maybe_generate_llm_text(
            cmd="ask",
            intent="analysis",
            query="Where is TKYProvider?",
            route=route,
            github_context={},
            locators=[],
            candidates_count=0,
        )
        assert text is None
        assert meta["llm_used"] is False
        assert meta["llm_skip_reason"] == f"route={route}"
