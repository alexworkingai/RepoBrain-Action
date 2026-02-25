from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from .tky_provider import CandidateChunk, TKYProvider, TKYResult


@dataclass
class RemoteTKYProvider(TKYProvider):
    """Remote black-box TKY provider.

    MVP contract: send metadata + scores (optionally embeddings in future).
    IMPORTANT: do not send raw source text by default.
    """

    endpoint_url: str
    api_key: str | None = None
    timeout_s: float = 15.0

    def compress_context(
        self,
        *,
        question: str,
        candidates: list[CandidateChunk],
        limits: dict[str, Any],
    ) -> TKYResult:
        if not self.endpoint_url:
            raise ValueError("RemoteTKYProvider requires endpoint_url")

        payload = {
            "question": question,
            "limits": limits,
            "candidates": [
                {
                    "chunk_id": c.chunk_id,
                    "file_path": c.file_path,
                    "line_start": c.line_start,
                    "line_end": c.line_end,
                    "score": c.score,
                }
                for c in candidates
            ],
        }

        headers = {"content-type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        response = requests.post(
            self.endpoint_url,
            json=payload,
            headers=headers,
            timeout=self.timeout_s,
        )
        response.raise_for_status()
        data = response.json()

        # Expected minimal response:
        # {
        #   "selected_chunk_ids": [...],
        #   "route": "FAST",
        #   "compression_stats": {...},
        #   "rationale": "..."
        # }
        return TKYResult(
            selected_chunk_ids=list(data.get("selected_chunk_ids", [])),
            route=str(data.get("route", "FAST")),
            compression_stats=dict(data.get("compression_stats", {})),
            rationale=str(data.get("rationale", "Remote TKY decision.")),
        )
