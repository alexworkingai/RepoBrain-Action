from __future__ import annotations

import re

from .tky_provider import CandidateChunk

TOKEN_RE = re.compile(r"[a-zA-Z0-9_]+")


def _tokenize(value: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(value)}


def score(question: str, chunk_text_preview: str) -> float:
    """Simple Jaccard score over lowercase alnum tokens."""
    q_tokens = _tokenize(question)
    c_tokens = _tokenize(chunk_text_preview)
    if not q_tokens or not c_tokens:
        return 0.0
    union = q_tokens | c_tokens
    if not union:
        return 0.0
    return len(q_tokens & c_tokens) / len(union)


def retrieve_topk(
    question: str,
    chunks: list[CandidateChunk],
    topk: int = 30,
) -> list[CandidateChunk]:
    """Return top-k chunks with scores populated."""
    scored: list[CandidateChunk] = []
    for chunk in chunks:
        preview = chunk.text or f"{chunk.file_path} {chunk.chunk_id}"
        chunk_score = score(question, preview)
        scored.append(
            CandidateChunk(
                chunk_id=chunk.chunk_id,
                file_path=chunk.file_path,
                line_start=chunk.line_start,
                line_end=chunk.line_end,
                score=chunk_score,
                text=chunk.text,
            )
        )

    scored.sort(key=lambda c: (-c.score, c.file_path, c.line_start, c.line_end))
    return scored[: max(topk, 0)]
