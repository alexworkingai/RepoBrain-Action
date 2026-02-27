from repobrain.tky_contract import build_remote_request
from repobrain.tky_provider import CandidateChunk


def test_build_remote_request_is_privacy_safe_and_signature_only() -> None:
    payload = build_remote_request(
        task_type="ask",
        query_text="Where is TKYProvider?",
        query_sig=[1, 2, 3],
        candidates=[
            CandidateChunk(
                chunk_id="repobrain/tky_provider.py:1-10",
                file_path="repobrain/tky_provider.py",
                line_start=1,
                line_end=10,
                score=0.12,
                text="class TKYProvider: ...",  # present locally, must not leak
                signature=[11, 22, 33],
            )
        ],
        limits={"max_sources": 4},
        policy={"no_raw_text": True},
        repo_ctx={"repo": "owner/repo", "sha": "abc123"},
    )

    assert payload["version"] == "v1"
    assert payload["schema_version"] == "1.0"
    assert payload["capabilities_requested"] == ["route", "selection", "security", "stable_tokens"]
    assert payload["query"]["text"] == "Where is TKYProvider?"
    assert payload["query"]["signature"] == [1, 2, 3]
    assert "text" not in payload["candidates"][0]
    assert "snippet" not in payload["candidates"][0]
    assert payload["candidates"][0]["signature"] == [11, 22, 33]
    assert payload["candidates"][0]["file_path"] == "repobrain/tky_provider.py"
