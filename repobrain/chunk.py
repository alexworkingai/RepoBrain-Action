from __future__ import annotations

from pathlib import Path

from .tky_provider import CandidateChunk


def chunk_text(
    path: Path,
    text: str,
    max_lines: int = 120,
    overlap: int = 20,
) -> list[CandidateChunk]:
    """Split text into overlapping line chunks.

    The caller should pass a repo-relative path so `file_path` and `chunk_id` stay stable.
    """
    if max_lines <= 0:
        raise ValueError("max_lines must be > 0")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")

    lines = text.splitlines()
    if not lines:
        return []

    effective_overlap = min(overlap, max_lines - 1) if max_lines > 1 else 0
    step = max_lines - effective_overlap
    file_path = path.as_posix()

    chunks: list[CandidateChunk] = []
    for start_idx in range(0, len(lines), step):
        end_idx = min(start_idx + max_lines, len(lines))
        if start_idx >= end_idx:
            break

        line_start = start_idx + 1
        line_end = end_idx
        chunk_body = "\n".join(lines[start_idx:end_idx])
        chunk_id = f"{file_path}:{line_start}-{line_end}"
        chunks.append(
            CandidateChunk(
                chunk_id=chunk_id,
                file_path=file_path,
                line_start=line_start,
                line_end=line_end,
                score=0.0,
                text=chunk_body,
            )
        )

        if end_idx == len(lines):
            break

    return chunks
