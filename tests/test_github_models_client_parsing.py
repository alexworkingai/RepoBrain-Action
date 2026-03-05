from __future__ import annotations

from typing import Any

from repobrain.llm.github_models import GitHubModelsClient


class _Response:
    def __init__(
        self,
        *,
        status_code: int = 200,
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}

    def json(self) -> dict[str, Any]:
        return dict(self._payload)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"status={self.status_code}")


def test_chat_parses_usage_and_rate_headers(monkeypatch) -> None:
    payload = {
        "choices": [{"message": {"content": "LLM answer"}}],
        "usage": {
            "prompt_tokens": 120,
            "completion_tokens": 45,
            "total_tokens": 165,
        },
    }
    headers = {
        "x-ratelimit-remaining": "17",
        "x-ratelimit-reset": "1735689600",
    }

    def fake_post(*args, **kwargs):  # noqa: ANN002, ANN003
        return _Response(payload=payload, headers=headers)

    monkeypatch.setattr("repobrain.llm.github_models.requests.post", fake_post)

    client = GitHubModelsClient(token="test-token")
    res = client.chat(
        model_id="openai/gpt-4.1-mini",
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=120,
        temperature=0.1,
        stream=False,
    )

    assert res.text == "LLM answer"
    assert res.prompt_tokens == 120
    assert res.completion_tokens == 45
    assert res.total_tokens == 165
    assert res.usage_estimated is False
    assert res.requests_remaining == 17
    assert res.rate_limit_reset is not None
    assert "x-ratelimit-remaining" in res.ratelimit_headers
