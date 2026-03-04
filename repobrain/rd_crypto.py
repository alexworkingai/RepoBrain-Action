from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import secrets
import time


@dataclass(frozen=True)
class SignatureEnvelope:
    algorithm: str
    body_hash: str
    nonce: str
    timestamp: int
    signature: str


def make_nonce(byte_length: int = 16) -> str:
    return secrets.token_hex(max(4, int(byte_length)))


def make_timestamp() -> int:
    return int(time.time())


def derive_signing_key(
    secret: str,
    *,
    salt: bytes | None = None,
    iterations: int = 200_000,
    key_len: int = 32,
) -> bytes:
    seed = str(secret or "").encode("utf-8")
    effective_salt = salt or b"repobrain-rd-signing"
    return hashlib.pbkdf2_hmac(
        "sha256",
        seed,
        effective_salt,
        max(1000, int(iterations)),
        dklen=max(16, int(key_len)),
    )


def sign_payload(
    key: bytes,
    payload: bytes,
    *,
    ts: int | None = None,
    nonce: str | None = None,
) -> SignatureEnvelope:
    timestamp = int(make_timestamp() if ts is None else ts)
    nonce_value = str(nonce or make_nonce())
    body_hash = hashlib.sha256(payload).hexdigest()
    message = f"{body_hash}.{timestamp}.{nonce_value}".encode("utf-8")
    signature = hmac.new(key, message, hashlib.sha256).hexdigest()
    return SignatureEnvelope(
        algorithm="HMAC-SHA256",
        body_hash=body_hash,
        nonce=nonce_value,
        timestamp=timestamp,
        signature=signature,
    )


def verify_payload(key: bytes, payload: bytes, envelope: SignatureEnvelope) -> bool:
    message = f"{envelope.body_hash}.{envelope.timestamp}.{envelope.nonce}".encode("utf-8")
    expected = hmac.new(key, message, hashlib.sha256).hexdigest()
    body_hash = hashlib.sha256(payload).hexdigest()
    return body_hash == envelope.body_hash and hmac.compare_digest(expected, envelope.signature)
