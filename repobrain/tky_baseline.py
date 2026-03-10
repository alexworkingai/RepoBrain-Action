from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .execution_mode import decide_semantic_execution
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

        selected_ids_list = [c.chunk_id for c in selected]
        selected_file_count = len({item.file_path for item in selected if item.file_path})
        github_ctx = limits.get("github_context", {})
        is_pr_context = False
        if isinstance(github_ctx, dict):
            is_pr_context = bool(github_ctx.get("is_pr", False)) or bool(
                isinstance(github_ctx.get("changed_files"), list) and github_ctx.get("changed_files")
            )
        verification_ctx = limits.get("verification_context", {})
        verification_pending = False
        verification_failed = False
        if isinstance(verification_ctx, dict):
            checks = verification_ctx.get("checks", [])
            if isinstance(checks, list):
                for item in checks:
                    if not isinstance(item, dict):
                        continue
                    status = str(item.get("status", "")).strip().upper()
                    if status in {"PENDING", "NOT_RUN", "IN_PROGRESS"}:
                        verification_pending = True
                    if status in {"FAIL", "FAILURE", "ERROR"}:
                        verification_failed = True
        semantic = decide_semantic_execution(
            task_type=task_type,
            route="DEEP" if route_hint == "DEEP" else "FAST",
            selected_count=len(selected_ids_list),
            selected_files=selected_file_count,
            top_score=float(top_score),
            score_gap=float(top_score - sorted_candidates[1].score if len(sorted_candidates) > 1 else top_score),
            is_pr_context=is_pr_context,
            verification_pending=verification_pending,
            verification_failed=verification_failed,
            request_intent=str(limits.get("intent", "analysis") or "analysis"),
        )
        return TKYResult(
            selected_chunk_ids=selected_ids_list,
            route="DEEP" if route_hint == "DEEP" else "FAST",
            compression_stats={
                "retrieved": len(candidates),
                "selected": len(selected),
            },
            rationale="Adaptive selection based on score thresholds.",
            execution_mode=semantic.execution_mode,
            llm_intent=semantic.llm_intent,
            llm_decision_reason_short=semantic.reason_short,
            llm_decision_reason_code=semantic.reason_code,
        )
