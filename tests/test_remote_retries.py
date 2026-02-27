import requests

from repobrain.tky_provider import CandidateChunk
from repobrain.tky_remote import RemoteTKYError, RemoteTKYProvider


class _DummyResponse:
    def __init__(self, status_code: int, payload: dict, headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self) -> dict:
        return self._payload


def _sample_candidates() -> list[CandidateChunk]:
    return [
        CandidateChunk(
            chunk_id="repobrain/tky_provider.py:1-10",
            file_path="repobrain/tky_provider.py",
            line_start=1,
            line_end=10,
            score=0.2,
            signature=[1, 2, 3],
        )
    ]


def test_remote_retries_on_5xx_then_succeeds(monkeypatch) -> None:
    calls = {"n": 0}

    def fake_post(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return _DummyResponse(500, {"error": "server"})
        return _DummyResponse(
            200,
            {"selected_chunk_ids": ["repobrain/tky_provider.py:1-10"], "route": "FAST"},
        )

    monkeypatch.setattr("repobrain.tky_remote.requests.post", fake_post)
    monkeypatch.setattr("repobrain.tky_remote.time.sleep", lambda *_args, **_kwargs: None)

    provider = RemoteTKYProvider(
        endpoint_url="https://example.test/v1/tky/decide",
        max_retries=2,
        backoff_base_s=0.01,
    )
    result = provider.compress_context(
        question="Where is TKYProvider?",
        candidates=_sample_candidates(),
        limits={"task_type": "ask", "max_sources": 4},
    )

    assert result.route == "FAST"
    assert calls["n"] == 2
    assert provider.last_diagnostics is not None
    assert provider.last_diagnostics.retry_count == 1


def test_remote_retries_on_429_sets_rate_limit_flag(monkeypatch) -> None:
    calls = {"n": 0}

    def fake_post(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return _DummyResponse(429, {"error": "rate_limited"}, headers={"Retry-After": "0"})
        return _DummyResponse(
            200,
            {
                "decision": {"route": "FAST"},
                "selection": {"selected_chunk_ids": ["repobrain/tky_provider.py:1-10"]},
            },
        )

    monkeypatch.setattr("repobrain.tky_remote.requests.post", fake_post)
    monkeypatch.setattr("repobrain.tky_remote.time.sleep", lambda *_args, **_kwargs: None)

    provider = RemoteTKYProvider(
        endpoint_url="https://example.test/v1/tky/decide",
        max_retries=2,
        backoff_base_s=0.01,
    )
    result = provider.compress_context(
        question="Where is TKYProvider?",
        candidates=_sample_candidates(),
        limits={"task_type": "ask", "max_sources": 4},
    )

    assert result.route == "FAST"
    assert calls["n"] == 2
    assert provider.last_diagnostics is not None
    assert provider.last_diagnostics.rate_limited is True
    assert provider.last_diagnostics.retry_count >= 1


def test_remote_timeout_sets_reason_code(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        raise requests.Timeout("timeout")

    monkeypatch.setattr("repobrain.tky_remote.requests.post", fake_post)
    monkeypatch.setattr("repobrain.tky_remote.time.sleep", lambda *_args, **_kwargs: None)

    provider = RemoteTKYProvider(
        endpoint_url="https://example.test/v1/tky/decide",
        max_retries=1,
        backoff_base_s=0.01,
    )
    try:
        provider.compress_context(
            question="Where is TKYProvider?",
            candidates=_sample_candidates(),
            limits={"task_type": "ask", "max_sources": 4},
        )
    except RemoteTKYError as exc:
        assert exc.fallback_reason_code == "REMOTE_TIMEOUT"
        assert exc.error_class == "timeout"
    else:  # pragma: no cover
        raise AssertionError("Expected RemoteTKYError")
