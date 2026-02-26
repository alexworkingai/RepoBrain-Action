from __future__ import annotations

import hashlib
from typing import Any

from .security import detect_injection_or_exfiltration
from .tky_engine import (
    EngineCandidate,
    EngineDecision,
    EngineRequest,
    EngineSecurity,
    TKYEngine,
)


class TopoCoreLite(TKYEngine):
    """Public placeholder engine that mimics a minimal TKY decision pipeline."""

    def __init__(
        self,
        *,
        min_fast_score: float = 0.05,
        min_keep_score: float = 0.02,
        min_sources: int = 3,
        max_sources_default: int = 8,
    ) -> None:
        self.min_fast_score = min_fast_score
        self.min_keep_score = min_keep_score
        self.min_sources = min_sources
        self.max_sources_default = max_sources_default

    def decide(self, req: EngineRequest) -> EngineDecision:
        sec = detect_injection_or_exfiltration(req.query.text)
        security = EngineSecurity(
            blocked=bool(sec["blocked"]),
            injection_risk="high" if sec["blocked"] else "low",
            exfiltration_risk=sec["risk"],
            signals=list(sec["signals"]),
        )
        if security.blocked:
            return EngineDecision(
                route="REFUSE",
                selected_chunk_ids=[],
                compression_stats={
                    "retrieved": len(req.candidates),
                    "selected": 0,
                    "top_score": 0.0,
                    "route": "REFUSE",
                },
                security=security,
                rationale="CoreLocked: blocked by security policy.",
                stable_tokens=[],
            )

        ranked = sorted(req.candidates, key=lambda c: c.score_local, reverse=True)
        top_score = ranked[0].score_local if ranked else 0.0
        second_score = ranked[1].score_local if len(ranked) > 1 else 0.0
        gap = top_score - second_score
        mass = sum(max(c.score_local, 0.0) for c in ranked)

        if req.task_type == "review":
            route = "REVIEW"
        elif top_score < self.min_fast_score:
            route = "DEEP"
        else:
            route = "FAST"

        selected_ids = self._select_candidates(ranked, req.limits, top_score=top_score)
        stable_tokens = self._stable_tokens(req.query.signature, selected_ids)

        rationale = {
            "FAST": "CoreLocked: high-confidence structural match.",
            "DEEP": "CoreLocked: low-confidence match; expanded search recommended.",
            "REVIEW": "CoreLocked: review mode; file-level heuristics applied.",
        }.get(route, "CoreLocked: decision completed.")

        compression_stats: dict[str, Any] = {
            "retrieved": len(ranked),
            "selected": len(selected_ids),
            "top_score": round(top_score, 6),
            "second_score": round(second_score, 6),
            "gap": round(gap, 6),
            "score_mass": round(mass, 6),
            "route": route,
        }

        return EngineDecision(
            route=route,
            selected_chunk_ids=selected_ids,
            compression_stats=compression_stats,
            security=security,
            rationale=rationale,
            stable_tokens=stable_tokens,
        )

    def _select_candidates(
        self,
        ranked: list[EngineCandidate],
        limits: dict[str, Any],
        *,
        top_score: float,
    ) -> list[str]:
        if not ranked:
            return []

        try:
            max_sources = int(limits.get("max_sources", self.max_sources_default))
        except (TypeError, ValueError):
            max_sources = self.max_sources_default
        max_sources = max(1, max_sources)

        try:
            min_keep = float(limits.get("min_score_keep", self.min_keep_score))
        except (TypeError, ValueError):
            min_keep = self.min_keep_score
        keep_threshold = max(min_keep, top_score * 0.30)

        selected: list[EngineCandidate] = [ranked[0]]
        selected_ids = {ranked[0].chunk_id}

        for candidate in ranked[1:]:
            if len(selected) >= max_sources:
                break
            if candidate.score_local >= keep_threshold:
                selected.append(candidate)
                selected_ids.add(candidate.chunk_id)

        target_min = min(self.min_sources, max_sources, len(ranked))
        if len(selected) < target_min:
            for candidate in ranked:
                if len(selected) >= target_min:
                    break
                if candidate.chunk_id in selected_ids:
                    continue
                selected.append(candidate)
                selected_ids.add(candidate.chunk_id)

        return [c.chunk_id for c in selected]

    def _stable_tokens(self, query_signature: list[int] | None, selected_ids: list[str]) -> list[str]:
        if not selected_ids:
            return []

        q_sig = ",".join(str(x) for x in (query_signature or []))
        selected = ",".join(selected_ids)
        tokens: list[str] = []
        for material in (f"q:{q_sig}", f"s:{selected}"):
            digest = hashlib.blake2s(material.encode("utf-8"), digest_size=8).hexdigest()
            tokens.append(digest)
        return tokens[:2]
