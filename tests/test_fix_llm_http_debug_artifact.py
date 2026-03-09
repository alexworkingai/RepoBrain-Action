from __future__ import annotations

import json
from pathlib import Path

from repobrain.github_flow import (
    _build_llm_http_debug_payload,
    _maybe_generate_llm_text,
    _set_runtime_env_cfg,
    _write_llm_http_debug,
)
from repobrain.llm.github_models import GitHubModelsError


def test_fix_llm_http_debug_payload_written_when_both_models_fail(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    _set_runtime_env_cfg(None)  # noqa: SLF001

    def fake_chat(self, **kwargs):  # noqa: ANN001
        model_id = str(kwargs.get("model_id", ""))
        if "mini" in model_id:
            raise GitHubModelsError(
                "fallback unavailable",
                status_code=503,
                reason="server_error",
            )
        raise GitHubModelsError(
            "primary unavailable",
            status_code=500,
            reason="server_error",
        )

    monkeypatch.setattr("repobrain.github_flow.GitHubModelsClient.chat", fake_chat)
    monkeypatch.setattr("repobrain.github_flow.time.sleep", lambda *_args, **_kwargs: None)

    text, meta = _maybe_generate_llm_text(
        cmd="fix",
        intent="patch",
        query="Apply patch only",
        route="FAST",
        github_context={},
        locators=[],
        candidates_count=2,
        preferred_model_id="openai/gpt-4.1",
        preferred_tier="high",
    )

    assert text is None
    assert meta["llm_used"] is False
    assert meta["llm_fallback_used"] is True

    payload = _build_llm_http_debug_payload(
        llm_meta=meta,
        decision_route="FAST",
    )
    path = _write_llm_http_debug(tmp_path, payload)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["intent"] == "patch"
    assert data["primary_model"] == "openai/gpt-4.1"
    assert data["fallback_model"] == "openai/gpt-4.1-mini"
    assert data["provider_http_status"] in {500, 503}
    assert data["provider_error_type"] == "server_error"
    serialized = json.dumps(data, ensure_ascii=False).lower()
    assert "authorization" not in serialized
    assert "token" not in serialized
