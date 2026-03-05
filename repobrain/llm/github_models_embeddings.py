from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests


EMBED_ENDPOINT = "https://models.github.ai/inference/embeddings"


class GitHubModelsEmbeddingsError(RuntimeError):
    """Raised when GitHub Models embeddings request cannot be completed."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        reason: str = "unknown",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.reason = reason


@dataclass(frozen=True)
class EmbeddingsResponse:
    vectors: list[list[float]]
    model_id: str
    prompt_tokens: int
    total_tokens: int
    usage_estimated: bool
    ratelimit_headers: dict[str, str]
    remaining_requests: int | None
    remaining_is_estimate: bool
    reset_time_utc_iso: str | None


def _estimate_tokens(texts: list[str]) -> int:
    return max(1, int(sum(len(text) for text in texts) / 4))


def _usage_tokens(data: dict[str, Any], *, texts: list[str]) -> tuple[int, int, bool]:
    usage = data.get("usage", {})
    if isinstance(usage, dict):
        prompt = int(usage.get("prompt_tokens", 0) or 0)
        total = int(usage.get("total_tokens", prompt) or prompt)
        if prompt > 0 or total > 0:
            return prompt, total, False
    estimated = _estimate_tokens(texts)
    return estimated, estimated, True


def _rate_headers(
    headers: dict[str, Any],
) -> tuple[dict[str, str], int | None, bool, str | None]:
    pairs: dict[str, str] = {}
    remaining: int | None = None
    reset_raw: str | None = None
    for key, value in headers.items():
        normalized = str(key).strip().lower()
        if not normalized.startswith("x-ratelimit-"):
            continue
        value_str = str(value).strip()
        pairs[normalized] = value_str
        if normalized == "x-ratelimit-remaining" and remaining is None:
            try:
                remaining = int(value_str)
            except ValueError:
                remaining = None
        if "remaining-requests" in normalized and remaining is None:
            try:
                remaining = int(value_str)
            except ValueError:
                remaining = None
        if normalized.endswith("reset") and reset_raw is None:
            reset_raw = value_str
    reset_time: str | None = None
    if reset_raw:
        try:
            epoch = int(reset_raw)
            reset_time = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
        except ValueError:
            reset_time = reset_raw
    return pairs, remaining, remaining is None, reset_time


class GitHubModelsEmbeddingsClient:
    """Minimal GitHub Models embeddings client with usersafe diagnostics."""

    def __init__(self, token: str, endpoint: str = EMBED_ENDPOINT) -> None:
        self.token = token
        self.endpoint = endpoint

    def embed(self, *, model_id: str, inputs: list[str]) -> EmbeddingsResponse:
        payload = {
            "model": model_id,
            "input": [str(item) for item in inputs],
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=(5, 30),
            )
        except requests.RequestException as exc:
            raise GitHubModelsEmbeddingsError("Embeddings request failed", reason="network") from exc

        status_code = int(getattr(response, "status_code", 0) or 0)
        if status_code in {401, 403, 404, 429}:
            reason_map = {
                401: "unauthorized",
                403: "forbidden",
                404: "not_found",
                429: "rate_limited",
            }
            raise GitHubModelsEmbeddingsError(
                f"Embeddings unavailable (status={status_code})",
                status_code=status_code,
                reason=reason_map.get(status_code, "http_error"),
            )
        if status_code >= 500:
            raise GitHubModelsEmbeddingsError(
                f"Embeddings server error (status={status_code})",
                status_code=status_code,
                reason="server_error",
            )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise GitHubModelsEmbeddingsError(
                f"Embeddings bad response (status={status_code})",
                status_code=status_code,
                reason="http_error",
            ) from exc

        data_raw = response.json()
        data = data_raw if isinstance(data_raw, dict) else {}
        records = data.get("data", [])
        if not isinstance(records, list):
            records = []
        indexed_vectors: list[tuple[int, list[float]]] = []
        for idx, item in enumerate(records):
            if not isinstance(item, dict):
                continue
            raw_vec = item.get("embedding", [])
            if not isinstance(raw_vec, list):
                continue
            vec = [float(v) for v in raw_vec]
            vec_index = int(item.get("index", idx) or idx)
            indexed_vectors.append((vec_index, vec))
        indexed_vectors.sort(key=lambda pair: pair[0])
        vectors = [pair[1] for pair in indexed_vectors]

        prompt_tokens, total_tokens, usage_estimated = _usage_tokens(data, texts=inputs)
        rate_headers, remaining, remaining_is_estimate, reset_time = _rate_headers(dict(response.headers))
        if remaining is None:
            remaining = max(0, 150 - 1)
            remaining_is_estimate = True

        return EmbeddingsResponse(
            vectors=vectors,
            model_id=model_id,
            prompt_tokens=prompt_tokens,
            total_tokens=total_tokens,
            usage_estimated=usage_estimated,
            ratelimit_headers=rate_headers,
            remaining_requests=remaining,
            remaining_is_estimate=remaining_is_estimate,
            reset_time_utc_iso=reset_time,
        )
