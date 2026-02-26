from __future__ import annotations

import re

from .signatures import build_chunk_signature, build_query_signature, compact_ascii, extract_latin_identifiers
from .tky_provider import CandidateChunk

IDENTIFIER_FALLBACK_RE = re.compile(r"[a-z0-9_]+")


def _jaccard(a: set[int], b: set[int]) -> float:
    if not a or not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _path_boost(question: str, chunk: CandidateChunk) -> float:
    haystack = f"{chunk.file_path} {chunk.chunk_id}".lower()
    compact_haystack = compact_ascii(haystack)
    boost = 0.0

    for ident in extract_latin_identifiers(question):
        if len(ident) < 3:
            continue
        if ident in haystack:
            boost = max(boost, 0.12)
            continue
        compact_ident = compact_ascii(ident)
        if compact_ident and compact_ident in compact_haystack:
            boost = max(boost, 0.10)
            continue
        for part in IDENTIFIER_FALLBACK_RE.findall(ident):
            if len(part) >= 3 and part in haystack:
                boost = max(boost, 0.06)
                break

    path_lower = chunk.file_path.lower()
    if path_lower.startswith(("repobrain/", "src/")):
        boost += 0.02
    elif path_lower.startswith("tests/"):
        boost -= 0.01
    return boost


def _chunk_signature(chunk: CandidateChunk) -> list[int]:
    if chunk.signature:
        return chunk.signature
    return build_chunk_signature(
        file_path=chunk.file_path,
        chunk_id=chunk.chunk_id,
        text=chunk.text,
        include_text=chunk.text is not None,
    )


def score(question: str, chunk: CandidateChunk) -> float:
    """Jaccard score over hashed token signatures plus lightweight path boosts."""
    q_sig = set(build_query_signature(question))
    c_sig = set(_chunk_signature(chunk))
    value = _jaccard(q_sig, c_sig) + _path_boost(question, chunk)
    return max(0.0, min(1.0, value))


def retrieve_topk(
    question: str,
    chunks: list[CandidateChunk],
    topk: int = 30,
) -> list[CandidateChunk]:
    """Return top-k chunks with scores populated."""
    scored: list[CandidateChunk] = []
    for chunk in chunks:
        chunk_score = score(question, chunk)
        scored.append(
            CandidateChunk(
                chunk_id=chunk.chunk_id,
                file_path=chunk.file_path,
                line_start=chunk.line_start,
                line_end=chunk.line_end,
                score=chunk_score,
                text=chunk.text,
                signature=chunk.signature,
            )
        )

    scored.sort(key=lambda c: (-c.score, c.file_path, c.line_start, c.line_end))
    return scored[: max(topk, 0)]
