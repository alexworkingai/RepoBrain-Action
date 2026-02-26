from repobrain.tky_stub_server import build_response_from_payload


def test_stub_server_builds_engine_based_response_shape() -> None:
    payload = {
        "task_type": "ask",
        "query": {"text": "Where is TKYProvider?", "signature": [1, 2, 3]},
        "candidates": [
            {
                "chunk_id": "c1",
                "file_path": "repobrain/tky_provider.py",
                "line_start": 1,
                "line_end": 20,
                "score_local": 0.12,
                "signature": [10, 20],
            },
            {
                "chunk_id": "c2",
                "file_path": "README.md",
                "line_start": 1,
                "line_end": 20,
                "score_local": 0.01,
                "signature": [30],
            },
        ],
        "limits": {"max_sources": 4, "min_score_keep": 0.02},
        "privacy": {"mode": "signatures_only"},
    }

    response = build_response_from_payload(payload)

    assert "decision" in response
    assert "selection" in response
    assert "security" in response
    assert isinstance(response["selection"]["selected_chunk_ids"], list)
    assert response["decision"]["route"] in {"FAST", "DEEP", "REFUSE", "REVIEW"}
