from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .evidence import EvidenceItem, build_evidence
from .tky_baseline import BaselineTKYProvider
from .tky_local import LocalTKYProvider
from .tky_provider import CandidateChunk, TKYProvider, TKYResult
from .tky_remote import RemoteTKYProvider


@dataclass(frozen=True)
class AnswerResult:
    answer_text: str
    evidence: list[EvidenceItem]
    tky: TKYResult
    audit_summary: dict[str, Any]
    next_steps: str


def make_provider(
    mode: str,
    *,
    remote_url: str | None = None,
    api_key: str | None = None,
) -> TKYProvider:
    """Factory for TKY providers.

    Modes:
      - baseline: open heuristic provider
      - remote: calls an external black-box endpoint
      - local: stub (private-only)
    """
    mode = (mode or "baseline").strip().lower()
    if mode == "baseline":
        return BaselineTKYProvider()
    if mode == "remote":
        if not remote_url:
            raise ValueError("remote_url is required for mode=remote")
        return RemoteTKYProvider(endpoint_url=remote_url, api_key=api_key)
    if mode == "local":
        return LocalTKYProvider()
    raise ValueError(f"Unknown TKY mode: {mode}")


def answer_question(
    *,
    question: str,
    candidates: list[CandidateChunk],
    provider: TKYProvider,
    limits: dict[str, Any],
) -> AnswerResult:
    """MVP answering: TKY decides which chunks to use, we output short answer + evidence."""
    # `candidates` are expected to arrive from retrieval with score populated.
    # `text` may be None (e.g., privacy-preserving index package without stored text).
    tky_result = provider.compress_context(question=question, candidates=candidates, limits=limits)
    evidence = build_evidence(
        candidates=candidates,
        selected_chunk_ids=tky_result.selected_chunk_ids,
        max_items=int(limits.get("max_sources", 8)),
    )

    # MVP answer text (placeholder): in real version, feed compressed context into an LLM
    answer = (
        f"Question: {question}\n"
        f"Route: {tky_result.route}\n"
        f"Selected sources: {len(tky_result.selected_chunk_ids)}\n"
        f"Rationale: {tky_result.rationale}"
    )
    audit_summary = {
        "retrieved": len(candidates),
        "selected": len(tky_result.selected_chunk_ids),
        "route": tky_result.route,
    }
    return AnswerResult(
        answer_text=answer,
        evidence=evidence,
        tky=tky_result,
        audit_summary=audit_summary,
        next_steps="Open evidence links and verify logic",
    )
