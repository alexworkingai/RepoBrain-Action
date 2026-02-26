from repobrain.hmac_auth import sign_body


def test_sign_body_is_stable_for_fixed_inputs() -> None:
    body = b'{"hello":"world"}'
    signature = sign_body("secret123", body, ts=1700000000, nonce="abc")
    assert signature == "98a84705b3131de61a1e9c5a97220736a7c143b3d76729bef708ee38d047a151"
