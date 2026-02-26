from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import orjson
import requests

from .hmac_auth import make_nonce, make_ts, sign_body
from .signatures import build_query_signature
from .tky_contract import build_remote_request
from .tky_provider import CandidateChunk, TKYProvider, TKYResult


class RemoteTKYError(RuntimeError):
    """Remote TKY request failed."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        short_reason: str = "",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.short_reason = short_reason or message


@dataclass
class RemoteTKYProvider(TKYProvider):
    """Remote black-box TKY provider with privacy-safe v1 payload contract."""

    endpoint_url: str
    api_key: str | None = None
    timeout_s: float = 15.0
    hmac_secret: str | None = None
    enable_hmac: bool = False
    last_status_code: int | None = None

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
        body_bytes = orjson.dumps(payload)

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

        try:
            response = requests.post(
                self.endpoint_url,
                data=body_bytes,
                headers=headers,
                timeout=(5, self.timeout_s),
            )
        except requests.RequestException as exc:
            self.last_status_code = None
            raise RemoteTKYError(
                "Remote TKY network error",
                status_code=None,
                short_reason="network",
            ) from exc

        self.last_status_code = response.status_code
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise RemoteTKYError(
                f"Remote TKY HTTP error: {response.status_code}",
                status_code=response.status_code,
                short_reason=f"http_{response.status_code}",
            ) from exc

        data = response.json()
        decision = data.get("decision", {}) if isinstance(data, dict) else {}
        selection = data.get("selection", {}) if isinstance(data, dict) else {}

        route = data.get("route", None) if isinstance(data, dict) else None
        if route is None and isinstance(decision, dict):
            route = decision.get("route", None)

        selected_chunk_ids = (
            data.get("selected_chunk_ids", None) if isinstance(data, dict) else None
        )
        if selected_chunk_ids is None and isinstance(selection, dict):
            selected_chunk_ids = selection.get("selected_chunk_ids", None)

        return TKYResult(
            selected_chunk_ids=list(selected_chunk_ids or []),
            route=str(route or "FAST"),
            compression_stats=dict(data.get("compression_stats", {})),
            rationale=str(data.get("rationale", "Remote TKY decision.")),
        )
