from __future__ import annotations

from typing import Any

from repobrain.github_publisher import publish_check_run


class _Resp:
    def __init__(self, status_code: int, payload: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict[str, Any]:
        return dict(self._payload)


def test_publish_check_run_success(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        return _Resp(201, {"id": 1})

    monkeypatch.setattr("repobrain.github_publisher.requests.post", fake_post)
    result = publish_check_run(
        repo="o/r",
        token="t",
        name="RepoBrain Review",
        head_sha="abc",
        conclusion="success",
        summary_md="ok",
        text_md="ok",
        annotations=[],
    )
    assert result["ok"] is True
    assert result["status_code"] == 201


def test_publish_check_run_forbidden_graceful(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        return _Resp(403, {"message": "forbidden"})

    monkeypatch.setattr("repobrain.github_publisher.requests.post", fake_post)
    result = publish_check_run(
        repo="o/r",
        token="t",
        name="RepoBrain Review",
        head_sha="abc",
        conclusion="neutral",
        summary_md="ok",
        text_md="ok",
        annotations=[],
    )
    assert result["ok"] is False
    assert result["status_code"] == 403
