from __future__ import annotations

from typing import Any

import pytest

from repobrain.llm.github_models_embeddings import (
    GitHubModelsEmbeddingsClient,
    GitHubModelsEmbeddingsError,
)


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


def test_embed_parses_vectors_usage_and_rate_headers(monkeypatch) -> None:
    payload = {
        "data": [
            {"index": 0, "embedding": [0.1, 0.2, 0.3]},
            {"index": 1, "embedding": [0.4, 0.5, 0.6]},
        ],
        "usage": {"prompt_tokens": 42, "total_tokens": 42},
    }
    headers = {
        "x-ratelimit-remaining": "13",
        "x-ratelimit-reset": "1735689600",
    }

    def fake_post(*args, **kwargs):  # noqa: ANN002, ANN003
        return _Response(payload=payload, headers=headers)

    monkeypatch.setattr("repobrain.llm.github_models_embeddings.requests.post", fake_post)

    client = GitHubModelsEmbeddingsClient(token="test-token")
    res = client.embed(model_id="openai/text-embedding-3-small", inputs=["a", "b"])

    assert len(res.vectors) == 2
    assert res.vectors[0] == [0.1, 0.2, 0.3]
    assert res.prompt_tokens == 42
    assert res.total_tokens == 42
    assert res.usage_estimated is False
    assert res.remaining_requests == 13
    assert res.remaining_is_estimate is False
    assert res.reset_time_utc_iso is not None
    assert "x-ratelimit-remaining" in res.ratelimit_headers


def test_embed_403_raises_structured_error(monkeypatch) -> None:
    def fake_post(*args, **kwargs):  # noqa: ANN002, ANN003
        return _Response(status_code=403, payload={"error": "forbidden"})

    monkeypatch.setattr("repobrain.llm.github_models_embeddings.requests.post", fake_post)

    client = GitHubModelsEmbeddingsClient(token="test-token")
    with pytest.raises(GitHubModelsEmbeddingsError) as exc:
        client.embed(model_id="openai/text-embedding-3-small", inputs=["hello"])

    assert exc.value.status_code == 403
    assert exc.value.reason == "forbidden"
