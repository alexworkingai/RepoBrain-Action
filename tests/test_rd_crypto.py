from repobrain.rd_crypto import derive_signing_key, sign_payload, verify_payload


def test_sign_payload_is_stable_for_fixed_nonce_ts() -> None:
    key = derive_signing_key("secret")
    payload = b"artifact-content"
    e1 = sign_payload(key, payload, ts=1_700_000_000, nonce="abc")
    e2 = sign_payload(key, payload, ts=1_700_000_000, nonce="abc")
    assert e1.signature == e2.signature
    assert e1.body_hash == e2.body_hash


def test_verify_payload_checks_integrity() -> None:
    key = derive_signing_key("secret")
    payload = b"artifact-content"
    envelope = sign_payload(key, payload, ts=1_700_000_000, nonce="abc")
    assert verify_payload(key, payload, envelope) is True
    assert verify_payload(key, b"tampered", envelope) is False
