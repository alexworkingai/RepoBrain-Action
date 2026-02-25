from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .tky_provider import CandidateChunk, TKYProvider, TKYResult


@dataclass
class BaselineTKYProvider(TKYProvider):
    """Open baseline provider (no proprietary logic).

    Picks top-N by score and returns them as selected sources.
    """

    def compress_context(
        self,
        *,
        question: str,
        candidates: list[CandidateChunk],
        limits: dict[str, Any],
    ) -> TKYResult:
        max_sources = int(limits.get("max_sources", 8))
        sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
        selected = sorted_candidates[:max_sources]

        return TKYResult(
            selected_chunk_ids=[c.chunk_id for c in selected],
            route="FAST",
            compression_stats={
                "retrieved": len(candidates),
                "selected": len(selected),
            },
            rationale="Baseline selection: top-N chunks by similarity score.",
        )
