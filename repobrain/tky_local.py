from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .signatures import build_query_signature
from .tkya.engine import describe_engine_instance, get_engine
from .tky_engine import EngineCandidate, EngineQuery, EngineRequest
from .tky_provider import CandidateChunk, TKYProvider, TKYResult


@dataclass
class LocalTKYProvider(TKYProvider):
    """Local TKY provider stub.

    Local provider backed by selectable TKYA engines.
    Safe default is `RB_TKYA_BACKEND=lite`. Advanced local mode can use
    `RB_TKYA_BACKEND=v5` with vendor file `repobrain/tkya/vendor/TopoCore_TCX_v5-Advance_CAS+Git.py`.
    """

    def compress_context(
        self,
        *,
        question: str,
        candidates: list[CandidateChunk],
        limits: dict[str, Any],
    ) -> TKYResult:
        engine = get_engine()
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
        compression_stats = dict(decision.compression_stats)
        compression_stats.setdefault("tky_engine_local", describe_engine_instance(engine))
        return TKYResult(
            selected_chunk_ids=decision.selected_chunk_ids,
            route=decision.route,
            compression_stats=compression_stats,
            rationale=decision.rationale,
        )
