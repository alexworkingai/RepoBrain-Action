from repobrain.tky_remote import parse_remote_response


def test_parse_remote_response_flat_format() -> None:
    result = parse_remote_response(
        {
            "selected_chunk_ids": ["c1", "c2"],
            "route": "FAST",
            "compression_stats": {"retrieved": 10, "selected": 2},
            "rationale": "flat",
        }
    )

    assert result.route == "FAST"
    assert result.selected_chunk_ids == ["c1", "c2"]
    assert result.compression_stats["selected"] == 2


def test_parse_remote_response_nested_format() -> None:
    result = parse_remote_response(
        {
            "decision": {"route": "FAST", "reason": "nested"},
            "selection": {"selected_chunk_ids": ["c9"]},
            "compression_stats": {"retrieved": 12, "selected": 1},
        }
    )

    assert result.route == "FAST"
    assert result.selected_chunk_ids == ["c9"]
    assert result.rationale == "nested"
