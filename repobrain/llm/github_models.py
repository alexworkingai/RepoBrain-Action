from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests


ENDPOINT = "https://models.github.ai/inference/chat/completions"


class GitHubModelsError(RuntimeError):
    """Raised when GitHub Models chat call fails."""

    def __init__(self, message: str, *, status_code: int | None = None, reason: str = "unknown") -> None:
        super().__init__(message)
        self.status_code = status_code
        self.reason = reason


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model_id: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    usage_estimated: bool
    ratelimit_headers: dict[str, str]
    requests_remaining: int | None
    rate_limit_reset: str | None


def _estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / 4))


def _usage_from_json(data: dict[str, Any], *, prompt_fallback: str, completion_fallback: str) -> tuple[int, int, int, bool]:
    usage = data.get("usage", {})
    if isinstance(usage, dict) and usage:
        prompt = int(usage.get("prompt_tokens", 0) or 0)
        completion = int(usage.get("completion_tokens", 0) or 0)
        total = int(usage.get("total_tokens", prompt + completion) or (prompt + completion))
        if prompt > 0 or completion > 0 or total > 0:
            return prompt, completion, total, False
    prompt_est = _estimate_tokens(prompt_fallback)
    completion_est = _estimate_tokens(completion_fallback)
    total_est = prompt_est + completion_est
    return prompt_est, completion_est, total_est, True


def _extract_content(data: dict[str, Any]) -> str:
    choices = data.get("choices", [])
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message", {})
    if not isinstance(message, dict):
        return ""
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, dict):
                value = item.get("text", "")
                if isinstance(value, str) and value.strip():
                    chunks.append(value)
        return "\n".join(chunks)
    return ""


def _extract_rate_headers(headers: dict[str, Any]) -> tuple[dict[str, str], int | None, str | None]:
    pairs: dict[str, str] = {}
    remaining: int | None = None
    reset_raw: str | None = None
    for key, value in headers.items():
        normalized = str(key).strip().lower()
        if not normalized.startswith("x-ratelimit-"):
            continue
        pairs[normalized] = str(value)
        if normalized.endswith("remaining") and remaining is None:
            try:
                remaining = int(str(value).strip())
            except ValueError:
                remaining = None
        if normalized.endswith("reset") and reset_raw is None:
            reset_raw = str(value).strip()

    reset_value: str | None = None
    if reset_raw:
        try:
            epoch = int(reset_raw)
            reset_value = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
        except ValueError:
            reset_value = reset_raw
    return pairs, remaining, reset_value


class GitHubModelsClient:
    """Minimal GitHub Models chat-completions client."""

    def __init__(self, token: str, endpoint: str = ENDPOINT) -> None:
        self.token = token
        self.endpoint = endpoint

    def chat(
        self,
        *,
        model_id: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        stream: bool = False,
    ) -> LLMResponse:
        payload = {
            "model": model_id,
            "messages": messages,
            "max_tokens": int(max_tokens),
            "temperature": float(temperature),
            "stream": bool(stream),
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
            raise GitHubModelsError("GitHub Models request failed", reason="network") from exc

        status_code = int(getattr(response, "status_code", 0) or 0)
        if status_code in {401, 403, 404, 429} or status_code >= 500:
            reason = {
                401: "unauthorized",
                403: "forbidden",
                404: "not_found",
                429: "rate_limited",
            }.get(status_code, "server_error" if status_code >= 500 else "http_error")
            raise GitHubModelsError(
                f"GitHub Models unavailable (status={status_code})",
                status_code=status_code,
                reason=reason,
            )

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise GitHubModelsError(
                f"GitHub Models bad response (status={status_code})",
                status_code=status_code,
                reason="http_error",
            ) from exc

        data_raw = response.json()
        data = data_raw if isinstance(data_raw, dict) else {}
        text = _extract_content(data)
        prompt_fallback = "\n".join(item.get("content", "") for item in messages if isinstance(item, dict))
        prompt_tokens, completion_tokens, total_tokens, usage_estimated = _usage_from_json(
            data,
            prompt_fallback=prompt_fallback,
            completion_fallback=text,
        )
        rate_headers, requests_remaining, rate_reset = _extract_rate_headers(dict(response.headers))
        return LLMResponse(
            text=text,
            model_id=model_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            usage_estimated=usage_estimated,
            ratelimit_headers=rate_headers,
            requests_remaining=requests_remaining,
            rate_limit_reset=rate_reset,
        )
