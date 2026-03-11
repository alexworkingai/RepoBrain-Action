from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class CandidateChunk:
    """A single candidate chunk from retrieval.

    This is intentionally minimal and GitHub-friendly (file + line ranges).
    """

    chunk_id: str
    file_path: str
    line_start: int
    line_end: int
    score: float
    text: str | None = None  # Optional: keep None by default for safety
    signature: list[int] | None = None  # Hashed token signature (no raw tokens/text)
    score_local: float | None = None
    score_vec: float | None = None


@dataclass(frozen=True)
class TKYResult:
    """Result of TKY decision/compression step.

    - selected_chunk_ids: which chunks are allowed/needed for the final answer.
    - route: FAST / DEEP / VERIFY / REFUSE (simple string for MVP).
    - compression_stats: any metrics (e.g., before/after size).
    - rationale: high-level explanation without internal details.
    """

    selected_chunk_ids: list[str]
    route: str
    compression_stats: dict[str, Any]
    rationale: str
    execution_mode: str = "retrieval_only"
    llm_intent: str = "none"
    llm_decision_reason_short: str = "LLM not used: direct answer available from retrieved evidence."
    llm_decision_reason_code: str = "DEFAULT_RETRIEVAL_ONLY"


class TKYProvider(Protocol):
    """Provider interface for TKY integration.

    We keep only what the RepoBrain pipeline needs.
    """

    def compress_context(
        self,
        *,
        question: str,
        candidates: list[CandidateChunk],
        limits: dict[str, Any],
    ) -> TKYResult:
        ...
