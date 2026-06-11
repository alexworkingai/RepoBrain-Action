from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Callable, Mapping
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests


DEFAULT_OIDC_AUDIENCE = "repobrain-api"
OIDC_UNAVAILABLE_MESSAGE = (
    "GitHub OIDC is unavailable. Ensure the workflow grants permissions: id-token: write."
)
OIDC_REQUIRED_MESSAGE = (
    "RepoBrain self-service mode requires GitHub OIDC. Add `id-token: write` to the "
    "workflow permissions and retry."
)
OIDC_REQUEST_FAILED_MESSAGE = (
    "GitHub OIDC request failed. Ensure the workflow grants permissions: id-token: write "
    "and retry."
)


def normalize_oidc_audience(value: str | None) -> str:
    audience = str(value or "").strip()
    return audience or DEFAULT_OIDC_AUDIENCE


@dataclass(frozen=True)
class GitHubOidcConfig:
    audience: str = DEFAULT_OIDC_AUDIENCE
    request_url: str = ""
    request_token: str = ""

    @classmethod
    def from_env(
        cls,
        *,
        environ: Mapping[str, str] | None = None,
        audience: str | None = None,
    ) -> "GitHubOidcConfig":
        env = environ or os.environ
        return cls(
            audience=normalize_oidc_audience(audience or env.get("RB_SELF_SERVICE_OIDC_AUDIENCE")),
            request_url=str(env.get("ACTIONS_ID_TOKEN_REQUEST_URL", "") or "").strip(),
            request_token=str(env.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "") or "").strip(),
        )


@dataclass(frozen=True)
class OidcTokenResult:
    available: bool
    audience: str
    token_present: bool
    token_redacted: bool
    error_code: str
    message: str
    token: str = ""

    def redacted_dict(self) -> dict[str, Any]:
        return {
            "available": bool(self.available),
            "audience": self.audience,
            "token_present": bool(self.token_present),
            "token_redacted": bool(self.token_redacted),
            "error_code": self.error_code,
            "message": self.message,
        }


def _append_audience(url: str, audience: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["audience"] = audience
    return urlunparse(parsed._replace(query=urlencode(query)))


class GitHubOidcTokenProvider:
    def __init__(
        self,
        *,
        environ: Mapping[str, str] | None = None,
        request_get: Callable[..., Any] | None = None,
    ) -> None:
        self._environ = environ or os.environ
        self._request_get = request_get or requests.get

    def get_token(self, *, audience: str | None = None) -> OidcTokenResult:
        config = GitHubOidcConfig.from_env(
            environ=self._environ,
            audience=audience,
        )
        if not config.request_url or not config.request_token:
            return OidcTokenResult(
                available=False,
                audience=config.audience,
                token_present=False,
                token_redacted=True,
                error_code="oidc_unavailable",
                message=OIDC_UNAVAILABLE_MESSAGE,
            )

        url = _append_audience(config.request_url, config.audience)
        try:
            response = self._request_get(
                url,
                headers={
                    "Authorization": f"Bearer {config.request_token}",
                    "Accept": "application/json",
                },
                timeout=10,
            )
        except requests.RequestException:
            return OidcTokenResult(
                available=True,
                audience=config.audience,
                token_present=False,
                token_redacted=True,
                error_code="oidc_request_failed",
                message=OIDC_REQUEST_FAILED_MESSAGE,
            )

        status_code = int(getattr(response, "status_code", 200) or 200)
        if status_code >= 400:
            return OidcTokenResult(
                available=True,
                audience=config.audience,
                token_present=False,
                token_redacted=True,
                error_code=f"oidc_http_{status_code}",
                message=OIDC_REQUEST_FAILED_MESSAGE,
            )

        try:
            payload = response.json()
        except ValueError:
            payload = {}

        token = ""
        if isinstance(payload, dict):
            token = str(payload.get("value", "") or "").strip()
        if not token:
            return OidcTokenResult(
                available=True,
                audience=config.audience,
                token_present=False,
                token_redacted=True,
                error_code="oidc_missing_value",
                message=OIDC_REQUEST_FAILED_MESSAGE,
            )

        return OidcTokenResult(
            available=True,
            audience=config.audience,
            token_present=True,
            token_redacted=True,
            error_code="none",
            message="GitHub OIDC token acquired.",
            token=token,
        )
