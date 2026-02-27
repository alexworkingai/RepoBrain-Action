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
        keep_ratio = float(limits.get("keep_ratio", 0.30))
        task_type = str(limits.get("task_type", "ask")).lower()
        max_per_file = int(limits.get("max_per_file", 999))
        max_files = int(limits.get("max_files", max_sources))
        route_hint = str(limits.get("route_hint", "FAST")).upper()
        sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
        selected: list[CandidateChunk] = []
        selected_ids: set[str] = set()
        per_file_counts: dict[str, int] = {}
        used_files: set[str] = set()

        top_score = sorted_candidates[0].score if sorted_candidates else 0.0
        keep_threshold = max(min_score_keep, top_score * keep_ratio)

        if sorted_candidates:
            top = sorted_candidates[0]
            selected.append(top)
            selected_ids.add(top.chunk_id)
            per_file_counts[top.file_path] = 1
            used_files.add(top.file_path)

        for candidate in sorted_candidates[1:]:
            if len(selected) >= max_sources:
                break
            file_count = per_file_counts.get(candidate.file_path, 0)
            if file_count >= max_per_file:
                continue
            if candidate.file_path not in used_files and len(used_files) >= max_files:
                continue
            if candidate.score >= keep_threshold:
                selected.append(candidate)
                selected_ids.add(candidate.chunk_id)
                per_file_counts[candidate.file_path] = file_count + 1
                used_files.add(candidate.file_path)

        min_fill_target = 1 if task_type == "locate" else min(3, max_sources, len(sorted_candidates))
        if len(selected) < min_fill_target:
            for candidate in sorted_candidates:
                if len(selected) >= min_fill_target:
                    break
                if candidate.chunk_id in selected_ids:
                    continue
                file_count = per_file_counts.get(candidate.file_path, 0)
                if file_count >= max_per_file:
                    continue
                if candidate.file_path not in used_files and len(used_files) >= max_files:
                    continue
                selected.append(candidate)
                selected_ids.add(candidate.chunk_id)
                per_file_counts[candidate.file_path] = file_count + 1
                used_files.add(candidate.file_path)

        return TKYResult(
            selected_chunk_ids=[c.chunk_id for c in selected],
            route="DEEP" if route_hint == "DEEP" else "FAST",
            compression_stats={
                "retrieved": len(candidates),
                "selected": len(selected),
            },
            rationale="Adaptive selection based on score thresholds.",
        )
