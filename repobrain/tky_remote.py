from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

import orjson
import requests

from .hmac_auth import make_nonce, make_ts, sign_body
from .signatures import build_query_signature
from .tky_contract import build_remote_request, validate_privacy
from .tky_provider import CandidateChunk, TKYProvider, TKYResult


@dataclass(frozen=True)
class RemoteCallDiagnostics:
    ok: bool
    status_code: int | None
    latency_ms: float
    retry_count: int
    rate_limited: bool
    error_class: str | None
    fallback_reason_code: str | None


class RemoteTKYError(RuntimeError):
    """Remote TKY request failed."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        short_reason: str = "",
        error_class: str = "unknown",
        fallback_reason_code: str = "REMOTE_NETWORK",
        diagnostics: RemoteCallDiagnostics | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.short_reason = short_reason or message
        self.error_class = error_class
        self.fallback_reason_code = fallback_reason_code
        self.diagnostics = diagnostics


def _parse_retry_after_seconds(value: str | None) -> float | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    try:
        seconds = float(raw)
    except ValueError:
        return None
    return max(0.0, seconds)


def parse_remote_response(data: dict[str, Any]) -> TKYResult:
    """Parse both legacy flat and new nested response contracts."""
    decision = data.get("decision", {})
    if not isinstance(decision, dict):
        decision = {}
    selection = data.get("selection", {})
    if not isinstance(selection, dict):
        selection = {}

    route = data.get("route")
    if route is None:
        route = decision.get("route")

    selected_chunk_ids = data.get("selected_chunk_ids")
    if selected_chunk_ids is None:
        selected_chunk_ids = selection.get("selected_chunk_ids")
    if not isinstance(selected_chunk_ids, list):
        selected_chunk_ids = []

    compression_stats = data.get("compression_stats", {})
    if not isinstance(compression_stats, dict):
        compression_stats = {}

    rationale = data.get("rationale")
    if rationale is None:
        rationale = decision.get("reason")

    return TKYResult(
        selected_chunk_ids=[str(item) for item in selected_chunk_ids],
        route=str(route or "FAST"),
        compression_stats=dict(compression_stats),
        rationale=str(rationale or "Remote TKY decision."),
    )


@dataclass
class RemoteTKYProvider(TKYProvider):
    """Remote black-box TKY provider with privacy-safe v1 payload contract."""

    endpoint_url: str
    api_key: str | None = None
    timeout_s: float = 15.0
    connect_timeout_s: float = 5.0
    read_timeout_s: float = 15.0
    max_retries: int = 2
    backoff_base_s: float = 0.5
    hmac_secret: str | None = None
    enable_hmac: bool = False
    last_status_code: int | None = None
    last_diagnostics: RemoteCallDiagnostics | None = None

    def _headers(self, body_bytes: bytes) -> dict[str, str]:
        headers = {"content-type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        if self.enable_hmac:
            if not self.hmac_secret:
                raise ValueError("hmac_secret is required when enable_hmac=True")
            ts = make_ts()
            nonce = make_nonce()
            headers["x-ts"] = str(ts)
            headers["x-nonce"] = nonce
            headers["x-signature"] = sign_body(self.hmac_secret, body_bytes, ts, nonce)
        return headers

    def _diag(
        self,
        *,
        ok: bool,
        status_code: int | None,
        started_at: float,
        retry_count: int,
        rate_limited: bool,
        error_class: str | None,
        fallback_reason_code: str | None,
    ) -> RemoteCallDiagnostics:
        return RemoteCallDiagnostics(
            ok=ok,
            status_code=status_code,
            latency_ms=round((time.perf_counter() - started_at) * 1000.0, 3),
            retry_count=retry_count,
            rate_limited=rate_limited,
            error_class=error_class,
            fallback_reason_code=fallback_reason_code,
        )

    def _raise_remote_error(
        self,
        *,
        message: str,
        status_code: int | None,
        short_reason: str,
        error_class: str,
        fallback_reason_code: str,
        diagnostics: RemoteCallDiagnostics,
    ) -> None:
        self.last_status_code = status_code
        self.last_diagnostics = diagnostics
        raise RemoteTKYError(
            message,
            status_code=status_code,
            short_reason=short_reason,
            error_class=error_class,
            fallback_reason_code=fallback_reason_code,
            diagnostics=diagnostics,
        )

    def compress_context(
        self,
        *,
        question: str,
        candidates: list[CandidateChunk],
        limits: dict[str, Any],
    ) -> TKYResult:
        if not self.endpoint_url:
            raise ValueError("RemoteTKYProvider requires endpoint_url")

        task_type = str(limits.get("task_type", "ask"))
        repo_ctx = dict(limits.get("repo_ctx", {}))
        policy = dict(limits.get("policy", {}))
        privacy_mode = str(limits.get("privacy_mode", "signatures_only"))

        try:
            payload = build_remote_request(
                task_type=task_type,
                query_text=question,
                query_sig=build_query_signature(question),
                candidates=candidates,
                limits=limits,
                policy=policy,
                repo_ctx=repo_ctx,
                privacy_mode=privacy_mode,
            )
            validate_privacy(payload)
        except ValueError:
            started = time.perf_counter()
            diagnostics = self._diag(
                ok=False,
                status_code=None,
                started_at=started,
                retry_count=0,
                rate_limited=False,
                error_class="policy_violation",
                fallback_reason_code="REMOTE_POLICY",
            )
            self._raise_remote_error(
                message="Remote TKY payload policy violation",
                status_code=None,
                short_reason="policy_violation",
                error_class="policy_violation",
                fallback_reason_code="REMOTE_POLICY",
                diagnostics=diagnostics,
            )

        body_bytes = orjson.dumps(payload)
        headers = self._headers(body_bytes)
        started = time.perf_counter()
        retries_done = 0
        rate_limited = False

        for attempt in range(self.max_retries + 1):
            connect_timeout = float(self.connect_timeout_s if self.connect_timeout_s > 0 else 5.0)
            read_timeout = float(self.read_timeout_s if self.read_timeout_s > 0 else self.timeout_s)
            try:
                response = requests.post(
                    self.endpoint_url,
                    data=body_bytes,
                    headers=headers,
                    timeout=(connect_timeout, read_timeout),
                )
            except requests.Timeout:
                if attempt < self.max_retries:
                    retries_done += 1
                    sleep_s = min(float(self.backoff_base_s) * (2**attempt), 5.0)
                    time.sleep(sleep_s)
                    continue
                diagnostics = self._diag(
                    ok=False,
                    status_code=None,
                    started_at=started,
                    retry_count=retries_done,
                    rate_limited=rate_limited,
                    error_class="timeout",
                    fallback_reason_code="REMOTE_TIMEOUT",
                )
                self._raise_remote_error(
                    message="Remote TKY timeout",
                    status_code=None,
                    short_reason="timeout",
                    error_class="timeout",
                    fallback_reason_code="REMOTE_TIMEOUT",
                    diagnostics=diagnostics,
                )
            except requests.ConnectionError:
                if attempt < self.max_retries:
                    retries_done += 1
                    sleep_s = min(float(self.backoff_base_s) * (2**attempt), 5.0)
                    time.sleep(sleep_s)
                    continue
                diagnostics = self._diag(
                    ok=False,
                    status_code=None,
                    started_at=started,
                    retry_count=retries_done,
                    rate_limited=rate_limited,
                    error_class="connection",
                    fallback_reason_code="REMOTE_NETWORK",
                )
                self._raise_remote_error(
                    message="Remote TKY connection error",
                    status_code=None,
                    short_reason="connection_error",
                    error_class="connection",
                    fallback_reason_code="REMOTE_NETWORK",
                    diagnostics=diagnostics,
                )
            except requests.RequestException:
                if attempt < self.max_retries:
                    retries_done += 1
                    sleep_s = min(float(self.backoff_base_s) * (2**attempt), 5.0)
                    time.sleep(sleep_s)
                    continue
                diagnostics = self._diag(
                    ok=False,
                    status_code=None,
                    started_at=started,
                    retry_count=retries_done,
                    rate_limited=rate_limited,
                    error_class="unknown",
                    fallback_reason_code="REMOTE_NETWORK",
                )
                self._raise_remote_error(
                    message="Remote TKY network error",
                    status_code=None,
                    short_reason="network",
                    error_class="unknown",
                    fallback_reason_code="REMOTE_NETWORK",
                    diagnostics=diagnostics,
                )

            status_code = int(getattr(response, "status_code", 0))
            self.last_status_code = status_code
            if status_code == 429:
                rate_limited = True
                if attempt < self.max_retries:
                    retries_done += 1
                    retry_after = _parse_retry_after_seconds(response.headers.get("Retry-After"))
                    sleep_s = retry_after if retry_after is not None else float(self.backoff_base_s)
                    time.sleep(min(max(sleep_s, 0.0), 5.0))
                    continue
                diagnostics = self._diag(
                    ok=False,
                    status_code=status_code,
                    started_at=started,
                    retry_count=retries_done,
                    rate_limited=True,
                    error_class="http_4xx",
                    fallback_reason_code="REMOTE_429",
                )
                self._raise_remote_error(
                    message="Remote TKY rate limited",
                    status_code=status_code,
                    short_reason="http_429",
                    error_class="http_4xx",
                    fallback_reason_code="REMOTE_429",
                    diagnostics=diagnostics,
                )

            if 500 <= status_code <= 599:
                if attempt < self.max_retries:
                    retries_done += 1
                    sleep_s = min(float(self.backoff_base_s) * (2**attempt), 5.0)
                    time.sleep(sleep_s)
                    continue
                diagnostics = self._diag(
                    ok=False,
                    status_code=status_code,
                    started_at=started,
                    retry_count=retries_done,
                    rate_limited=rate_limited,
                    error_class="http_5xx",
                    fallback_reason_code="REMOTE_5XX",
                )
                self._raise_remote_error(
                    message=f"Remote TKY HTTP error: {status_code}",
                    status_code=status_code,
                    short_reason=f"http_{status_code}",
                    error_class="http_5xx",
                    fallback_reason_code="REMOTE_5XX",
                    diagnostics=diagnostics,
                )

            if 400 <= status_code <= 499:
                error_class = "policy_violation" if status_code == 422 else "http_4xx"
                reason_code = "REMOTE_POLICY" if status_code == 422 else "REMOTE_4XX"
                diagnostics = self._diag(
                    ok=False,
                    status_code=status_code,
                    started_at=started,
                    retry_count=retries_done,
                    rate_limited=rate_limited,
                    error_class=error_class,
                    fallback_reason_code=reason_code,
                )
                self._raise_remote_error(
                    message=f"Remote TKY HTTP error: {status_code}",
                    status_code=status_code,
                    short_reason=f"http_{status_code}",
                    error_class=error_class,
                    fallback_reason_code=reason_code,
                    diagnostics=diagnostics,
                )

            try:
                data = response.json()
            except ValueError:
                diagnostics = self._diag(
                    ok=False,
                    status_code=status_code,
                    started_at=started,
                    retry_count=retries_done,
                    rate_limited=rate_limited,
                    error_class="unknown",
                    fallback_reason_code="REMOTE_5XX",
                )
                self._raise_remote_error(
                    message="Remote TKY returned invalid JSON",
                    status_code=status_code,
                    short_reason="invalid_json",
                    error_class="unknown",
                    fallback_reason_code="REMOTE_5XX",
                    diagnostics=diagnostics,
                )

            if not isinstance(data, dict):
                diagnostics = self._diag(
                    ok=False,
                    status_code=status_code,
                    started_at=started,
                    retry_count=retries_done,
                    rate_limited=rate_limited,
                    error_class="unknown",
                    fallback_reason_code="REMOTE_5XX",
                )
                self._raise_remote_error(
                    message="Remote TKY returned non-object payload",
                    status_code=status_code,
                    short_reason="invalid_payload",
                    error_class="unknown",
                    fallback_reason_code="REMOTE_5XX",
                    diagnostics=diagnostics,
                )

            self.last_diagnostics = self._diag(
                ok=True,
                status_code=status_code,
                started_at=started,
                retry_count=retries_done,
                rate_limited=rate_limited,
                error_class=None,
                fallback_reason_code=None,
            )
            return parse_remote_response(data)

        diagnostics = self._diag(
            ok=False,
            status_code=None,
            started_at=started,
            retry_count=retries_done,
            rate_limited=rate_limited,
            error_class="unknown",
            fallback_reason_code="REMOTE_NETWORK",
        )
        self._raise_remote_error(
            message="Remote TKY unknown error",
            status_code=None,
            short_reason="unknown",
            error_class="unknown",
            fallback_reason_code="REMOTE_NETWORK",
            diagnostics=diagnostics,
        )
