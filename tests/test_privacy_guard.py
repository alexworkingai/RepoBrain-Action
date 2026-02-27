import pytest

from repobrain.tky_contract import validate_privacy
from repobrain.tky_provider import CandidateChunk
from repobrain.tky_remote import RemoteTKYError, RemoteTKYProvider


def test_validate_privacy_rejects_candidate_text_field() -> None:
    payload = {
        "query": {"text": "Where is provider?"},
        "candidates": [
            {
                "chunk_id": "c1",
                "file_path": "repobrain/tky_provider.py",
                "line_start": 1,
                "line_end": 10,
                "score_local": 0.1,
                "text": "leak",
            }
        ],
    }
    with pytest.raises(ValueError):
        validate_privacy(payload)


def test_remote_provider_raises_policy_violation_before_network(monkeypatch) -> None:
    provider = RemoteTKYProvider(endpoint_url="https://example.test/v1/tky/decide")

    monkeypatch.setattr(
        "repobrain.tky_remote.build_remote_request",
        lambda **_kwargs: {
            "query": {"text": "q"},
            "candidates": [{"chunk_id": "c1", "text": "forbidden"}],
        },
    )
    monkeypatch.setattr(
        "repobrain.tky_remote.requests.post",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network call must not happen")),
    )

    with pytest.raises(RemoteTKYError) as exc_info:
        provider.compress_context(
            question="Where is TKYProvider?",
            candidates=[
                CandidateChunk(
                    chunk_id="c1",
                    file_path="repobrain/tky_provider.py",
                    line_start=1,
                    line_end=10,
                    score=0.1,
                    signature=[1, 2],
                )
            ],
            limits={"task_type": "ask"},
        )

    assert exc_info.value.error_class == "policy_violation"
    assert exc_info.value.fallback_reason_code == "REMOTE_POLICY"
