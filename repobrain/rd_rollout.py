from __future__ import annotations

import hashlib


def stable_bucket(key: str) -> int:
    digest = hashlib.blake2s(str(key).encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "little", signed=False) % 100


def canary_enabled(*, percent: int, key: str) -> bool:
    bounded = max(0, min(100, int(percent)))
    if bounded >= 100:
        return True
    if bounded <= 0:
        return False
    return stable_bucket(key) < bounded


def resolve_rollout_mode(
    *,
    requested_mode: str,
    canary_percent: int,
    canary_key: str,
    fallback_mode: str = "lite",
) -> str:
    mode = str(requested_mode or "").strip().lower() or "lite"
    if mode != "rd":
        return mode
    if canary_enabled(percent=canary_percent, key=canary_key):
        return "rd"
    return str(fallback_mode or "lite").strip().lower() or "lite"
