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
    remaining_is_estimate: bool
    reset_time_utc_iso: str | None


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


def _estimate_remaining_from_model(model_id: str, calls_this_run: int = 1) -> int:
    model = str(model_id or "").strip().lower()
    daily_limit = 50 if "gpt-4.1" in model and "mini" not in model else 150
    return max(0, daily_limit - max(0, int(calls_this_run)))


def _extract_rate_headers(
    headers: dict[str, Any],
    *,
    model_id: str,
) -> tuple[dict[str, str], int | None, bool, str | None]:
    pairs: dict[str, str] = {}
    remaining_direct: int | None = None
    remaining_variant: int | None = None
    remaining_generic: int | None = None
    reset_raw: str | None = None
    for key, value in headers.items():
        normalized = str(key).strip().lower()
        if not normalized.startswith("x-ratelimit-"):
            continue
        value_str = str(value).strip()
        pairs[normalized] = value_str
        if normalized == "x-ratelimit-remaining" and remaining_direct is None:
            try:
                remaining_direct = int(value_str)
            except ValueError:
                remaining_direct = None
        if "remaining-requests" in normalized and remaining_variant is None:
            try:
                remaining_variant = int(value_str)
            except ValueError:
                remaining_variant = None
        if "remaining" in normalized and "tokens" not in normalized and remaining_generic is None:
            try:
                remaining_generic = int(value_str)
            except ValueError:
                remaining_generic = None
        if normalized.endswith("reset") and reset_raw is None and value_str:
            reset_raw = value_str

    reset_value: str | None = None
    if reset_raw:
        try:
            epoch = int(reset_raw)
            reset_value = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
        except ValueError:
            reset_value = reset_raw
    remaining = remaining_direct
    if remaining is None:
        remaining = remaining_variant
    if remaining is None:
        remaining = remaining_generic

    if remaining is not None:
        return pairs, remaining, False, reset_value

    estimated = _estimate_remaining_from_model(model_id=model_id, calls_this_run=1)
    return pairs, estimated, True, reset_value


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
        rate_headers, requests_remaining, remaining_is_estimate, rate_reset = _extract_rate_headers(
            dict(response.headers),
            model_id=model_id,
        )
        return LLMResponse(
            text=text,
            model_id=model_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            usage_estimated=usage_estimated,
            ratelimit_headers=rate_headers,
            requests_remaining=requests_remaining,
            remaining_is_estimate=remaining_is_estimate,
            reset_time_utc_iso=rate_reset,
        )
