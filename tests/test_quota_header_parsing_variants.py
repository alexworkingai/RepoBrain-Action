from __future__ import annotations

from typing import Any

from repobrain.llm.github_models import GitHubModelsClient


class _Response:
    def __init__(
        self,
        *,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
        status_code: int = 200,
    ) -> None:
        self._payload = payload
        self.headers = headers or {}
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        return dict(self._payload)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("http error")


def _payload() -> dict[str, Any]:
    return {"choices": [{"message": {"content": "ok"}}]}


def test_quota_parsing_accepts_variant_header_names(monkeypatch) -> None:
    headers = {
        "X-RateLimit-Remaining-Requests": "19",
        "X-RateLimit-Reset": "1735689600",
    }

    def fake_post(*args, **kwargs):  # noqa: ANN002, ANN003
        return _Response(payload=_payload(), headers=headers)

    monkeypatch.setattr("repobrain.llm.github_models.requests.post", fake_post)
    client = GitHubModelsClient(token="test-token")
    response = client.chat(
        model_id="openai/gpt-4.1",
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=200,
        temperature=0.1,
    )
    assert response.requests_remaining == 19
    assert response.remaining_is_estimate is False
    assert response.reset_time_utc_iso is not None


def test_quota_parsing_falls_back_to_estimate(monkeypatch) -> None:
    def fake_post(*args, **kwargs):  # noqa: ANN002, ANN003
        return _Response(payload=_payload(), headers={})

    monkeypatch.setattr("repobrain.llm.github_models.requests.post", fake_post)
    client = GitHubModelsClient(token="test-token")
    response = client.chat(
        model_id="openai/gpt-4.1-mini",
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=200,
        temperature=0.1,
    )
    assert isinstance(response.requests_remaining, int)
    assert response.remaining_is_estimate is True
    assert response.reset_time_utc_iso is None
