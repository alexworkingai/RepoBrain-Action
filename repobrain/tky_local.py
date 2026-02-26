from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .signatures import build_query_signature
from .topocore_lite import TopoCoreLite
from .tky_engine import EngineCandidate, EngineQuery, EngineRequest
from .tky_provider import CandidateChunk, TKYProvider, TKYResult


@dataclass
class LocalTKYProvider(TKYProvider):
    """Local TKY provider stub.

    This skeleton intentionally does NOT include proprietary TKY code.
    In private deployments, replace TopoCoreLite with your internal TopoCore engine.
    """

    def compress_context(
        self,
        *,
        question: str,
        candidates: list[CandidateChunk],
        limits: dict[str, Any],
    ) -> TKYResult:
        engine = TopoCoreLite()
        task_type = str(limits.get("task_type", "ask")).lower()
        if task_type not in {"ask", "locate", "explain", "review"}:
            task_type = "ask"

        req = EngineRequest(
            task_type=task_type,  # type: ignore[arg-type]
            query=EngineQuery(text=question, signature=build_query_signature(question)),
            candidates=[
                EngineCandidate(
                    chunk_id=c.chunk_id,
                    score_local=float(c.score),
                    signature=c.signature,
                    file_path=c.file_path,
                    line_start=c.line_start,
                    line_end=c.line_end,
                )
                for c in candidates
            ],
            limits=dict(limits),
            policy={"corelocked": True},
        )
        decision = engine.decide(req)
        return TKYResult(
            selected_chunk_ids=decision.selected_chunk_ids,
            route=decision.route,
            compression_stats=dict(decision.compression_stats),
            rationale=decision.rationale,
        )
