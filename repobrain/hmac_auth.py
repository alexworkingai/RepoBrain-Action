from __future__ import annotations

import hashlib
import hmac
import secrets
import time


def make_nonce() -> str:
    """Generate a nonce for remote HMAC requests."""
    return secrets.token_hex(16)


def make_ts() -> int:
    """Unix timestamp for remote HMAC requests."""
    return int(time.time())


def sign_body(secret: str, body_bytes: bytes, ts: int, nonce: str) -> str:
    """Build HMAC-SHA256 hex signature over `ts.nonce.body`."""
    message = f"{ts}.{nonce}.".encode("utf-8") + body_bytes
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
