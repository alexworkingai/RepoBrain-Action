from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib.parse import urlparse, urlunparse

import requests

from repobrain.hosted_api_contract import (
    HOSTED_API_ENDPOINT_PATH,
    HostedApiContractError,
    sanitize_request_for_logs,
    validate_github_action_audit_request,
    validate_github_action_audit_response,
)


_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
_PLACEHOLDER_HOST_MARKERS = {
    "<trusted-repobrain-hosted-api>",
    "example.com",
    "example.invalid",
}


@dataclass(frozen=True)
class HostedApiClientConfig:
    api_url: str
    timeout_s: float = 12.0


@dataclass(frozen=True)
class HostedApiSendResult:
    response: dict[str, Any]
    http_status: int
    sanitized_endpoint: str

    @property
    def status(self) -> str:
        return str(self.response.get("status", "") or "").strip().lower()


class HostedApiClientError(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        http_status: int | None = None,
        sanitized_endpoint: str = "",
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.http_status = http_status
        self.sanitized_endpoint = sanitized_endpoint


def validate_hosted_api_url(api_url: str) -> str:
    raw = str(api_url or "").strip()
    if not raw:
        raise HostedApiClientError(
            "HOSTED_API_URL_MISSING",
            "RepoBrain self-service mode requires `api_url` for hosted API routing in Sprint 93D.",
            retryable=False,
        )

    parsed = urlparse(raw)
    scheme = str(parsed.scheme or "").strip().lower()
    hostname = str(parsed.hostname or "").strip().lower()
    lowered_raw = raw.lower()
    if scheme not in {"https", "http"}:
        raise HostedApiClientError(
            "HOSTED_API_URL_INVALID",
            "RepoBrain self-service mode requires a valid hosted API URL using HTTPS or localhost HTTP for tests.",
            retryable=False,
            sanitized_endpoint=_sanitize_endpoint(raw),
        )
    if not hostname:
        raise HostedApiClientError(
            "HOSTED_API_URL_INVALID",
            "RepoBrain self-service mode requires a valid hosted API host name.",
            retryable=False,
            sanitized_endpoint=_sanitize_endpoint(raw),
        )
    if any(marker in lowered_raw or hostname == marker for marker in _PLACEHOLDER_HOST_MARKERS):
        raise HostedApiClientError(
            "HOSTED_API_URL_PLACEHOLDER_OR_UNCONFIGURED",
            "RepoBrain hosted API URL is a placeholder or is not configured for a real external runtime.",
            retryable=False,
            sanitized_endpoint=_sanitize_endpoint(raw),
        )
    if scheme != "https" and hostname not in _LOCAL_HOSTS:
        raise HostedApiClientError(
            "HOSTED_API_URL_INVALID",
            "RepoBrain self-service mode requires HTTPS for hosted API routing outside local tests.",
            retryable=False,
            sanitized_endpoint=_sanitize_endpoint(raw),
        )
    if parsed.fragment:
        raise HostedApiClientError(
            "HOSTED_API_URL_INVALID",
            "RepoBrain self-service mode does not allow fragment components in `api_url`.",
            retryable=False,
            sanitized_endpoint=_sanitize_endpoint(raw),
        )

    path = str(parsed.path or "").rstrip("/")
    if path.endswith(HOSTED_API_ENDPOINT_PATH):
        normalized_path = path
    else:
        normalized_path = f"{path}{HOSTED_API_ENDPOINT_PATH}" if path else HOSTED_API_ENDPOINT_PATH
    return urlunparse((scheme, parsed.netloc, normalized_path, "", "", ""))


def _sanitize_endpoint(url: str) -> str:
    parsed = urlparse(str(url or "").strip())
    scheme = str(parsed.scheme or "").strip().lower() or "unknown"
    hostname = str(parsed.hostname or "").strip().lower() or "unknown"
    path = str(parsed.path or "").strip() or "/"
    return f"{scheme}://{hostname}{path}"


class HostedApiClient:
    def __init__(
        self,
        config: HostedApiClientConfig,
        *,
        request_post: Callable[..., Any] | None = None,
    ) -> None:
        self._config = config
        self._request_post = request_post or requests.post

    def send_audit_request(self, request_json: Mapping[str, Any]) -> HostedApiSendResult:
        validated_request = validate_github_action_audit_request(request_json)
        sanitize_request_for_logs(validated_request)
        endpoint_url = validate_hosted_api_url(self._config.api_url)
        sanitized_endpoint = _sanitize_endpoint(endpoint_url)
        try:
            response = self._request_post(
                endpoint_url,
                json=validated_request,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=float(self._config.timeout_s),
                allow_redirects=False,
            )
        except requests.RequestException as exc:
            raise HostedApiClientError(
                "HOSTED_API_UNAVAILABLE",
                "RepoBrain hosted API is unavailable or unreachable for self-service processing.",
                retryable=True,
                sanitized_endpoint=sanitized_endpoint,
            ) from exc

        status_code = int(getattr(response, "status_code", 0) or 0)
        if 300 <= status_code < 400:
            raise HostedApiClientError(
                "HOSTED_API_INVALID_RESPONSE",
                "RepoBrain hosted API returned an unexpected redirect response.",
                retryable=False,
                http_status=status_code,
                sanitized_endpoint=sanitized_endpoint,
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise HostedApiClientError(
                "HOSTED_API_INVALID_RESPONSE",
                "RepoBrain hosted API returned a non-JSON response.",
                retryable=status_code >= 500 or status_code == 429,
                http_status=status_code,
                sanitized_endpoint=sanitized_endpoint,
            ) from exc
        if not isinstance(payload, Mapping):
            raise HostedApiClientError(
                "HOSTED_API_INVALID_RESPONSE",
                "RepoBrain hosted API returned an invalid response shape.",
                retryable=status_code >= 500 or status_code == 429,
                http_status=status_code,
                sanitized_endpoint=sanitized_endpoint,
            )

        try:
            validated_response = validate_github_action_audit_response(payload)
        except HostedApiContractError as exc:
            raise HostedApiClientError(
                "HOSTED_API_INVALID_RESPONSE",
                exc.message,
                retryable=status_code >= 500 or status_code == 429,
                http_status=status_code,
                sanitized_endpoint=sanitized_endpoint,
            ) from exc

        if status_code >= 500:
            raise HostedApiClientError(
                "HOSTED_API_UNAVAILABLE",
                "RepoBrain hosted API returned a transient server-side failure.",
                retryable=True,
                http_status=status_code,
                sanitized_endpoint=sanitized_endpoint,
            )
        return HostedApiSendResult(
            response=dict(validated_response),
            http_status=status_code,
            sanitized_endpoint=sanitized_endpoint,
        )
