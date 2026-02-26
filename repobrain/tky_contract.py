from __future__ import annotations

from typing import Any

from .tky_provider import CandidateChunk

_FORBIDDEN_PRIVACY_KEYS = {"text", "snippet", "content"}


def build_remote_request(
    task_type: str,
    query_text: str,
    query_sig: list[int],
    candidates: list[CandidateChunk],
    limits: dict[str, Any],
    policy: dict[str, Any],
    repo_ctx: dict[str, Any],
    privacy_mode: str = "signatures_only",
) -> dict[str, Any]:
    """Build remote TKY request payload v1 using signatures + metadata only."""
    payload = {
        "version": "v1",
        "task_type": task_type,
        "privacy_mode": privacy_mode,
        "query": {
            "text": query_text,
            "signature": [int(item) for item in query_sig],
        },
        "candidates": [
            {
                "chunk_id": c.chunk_id,
                "file_path": c.file_path,
                "line_start": c.line_start,
                "line_end": c.line_end,
                "score": c.score,
                "score_local": c.score,
                "signature": [int(item) for item in (c.signature or [])],
            }
            for c in candidates
        ],
        "limits": dict(limits),
        "policy": dict(policy),
        "repo_ctx": dict(repo_ctx),
    }
    validate_privacy(payload)
    return payload


def validate_privacy(payload: dict[str, Any]) -> None:
    """Reject payloads that include raw text/snippets/content in forbidden locations."""

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                next_path = f"{path}.{key}" if path else str(key)
                lowered_key = str(key).lower()
                if lowered_key in _FORBIDDEN_PRIVACY_KEYS:
                    if next_path != "query.text":
                        raise ValueError(f"Privacy violation: forbidden field `{next_path}`")
                walk(item, next_path)
            return
        if isinstance(value, list):
            for idx, item in enumerate(value):
                walk(item, f"{path}[{idx}]")

    walk(payload, "")
