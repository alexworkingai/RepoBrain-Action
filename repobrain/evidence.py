from __future__ import annotations

from dataclasses import dataclass

from .tky_provider import CandidateChunk


@dataclass(frozen=True)
class EvidenceItem:
    file_path: str
    line_start: int
    line_end: int
    score: float


def build_evidence(
    *,
    candidates: list[CandidateChunk],
    selected_chunk_ids: list[str],
    max_items: int = 8,
) -> list[EvidenceItem]:
    """Build an evidence list (file + line ranges) from selected chunk ids."""
    selected_set = set(selected_chunk_ids)
    chosen = [c for c in candidates if c.chunk_id in selected_set]
    chosen = sorted(chosen, key=lambda c: c.score, reverse=True)[:max_items]
    return [
        EvidenceItem(
            file_path=c.file_path,
            line_start=c.line_start,
            line_end=c.line_end,
            score=c.score,
        )
        for c in chosen
    ]
