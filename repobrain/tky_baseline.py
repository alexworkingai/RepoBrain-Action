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
        min_score_keep = float(limits.get("min_score_keep", 0.02))
        route_hint = str(limits.get("route_hint", "FAST")).upper()
        sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
        selected: list[CandidateChunk] = []
        selected_ids: set[str] = set()

        if sorted_candidates:
            selected.append(sorted_candidates[0])
            selected_ids.add(sorted_candidates[0].chunk_id)

        for candidate in sorted_candidates[1:]:
            if len(selected) >= max_sources:
                break
            if candidate.score >= min_score_keep:
                selected.append(candidate)
                selected_ids.add(candidate.chunk_id)

        min_fill_target = min(3, max_sources, len(sorted_candidates))
        if len(selected) < min_fill_target:
            for candidate in sorted_candidates:
                if len(selected) >= min_fill_target:
                    break
                if candidate.chunk_id in selected_ids:
                    continue
                selected.append(candidate)
                selected_ids.add(candidate.chunk_id)

        return TKYResult(
            selected_chunk_ids=[c.chunk_id for c in selected],
            route="DEEP" if route_hint == "DEEP" else "FAST",
            compression_stats={
                "retrieved": len(candidates),
                "selected": len(selected),
            },
            rationale="Adaptive selection based on score thresholds.",
        )
