from repobrain.tky_stub_server import validate_payload_privacy, verify_signature


def test_validate_payload_privacy_rejects_candidate_text() -> None:
    payload = {
        "query": {"text": "Where is TKYProvider?", "signature": [1, 2]},
        "candidates": [
            {
                "chunk_id": "c1",
                "file_path": "repobrain/tky_provider.py",
                "line_start": 1,
                "line_end": 10,
                "score_local": 0.1,
                "text": "class TKYProvider",
            }
        ],
        "limits": {"max_sources": 4},
        "privacy": {"mode": "signatures_only"},
    }
    assert validate_payload_privacy(payload) is False


def test_verify_signature_stub_hmac_formula() -> None:
    body = b'{"hello":"world"}'
    # Precomputed using stub formula: HMAC(secret, sha256(body)+"."+ts+"."+nonce)
    assert (
        verify_signature(
            "secret123",
            body,
            "1700000000",
            "abc",
            "de22fa7347f6a53f249f95d4a1cf2659ee7599e6b541cc6133d7bc4adde84313",
        )
        is True
    )
