from __future__ import annotations

import hashlib
from typing import Any

from .execution_mode import decide_semantic_execution
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
                execution_mode="refuse",
                llm_intent="none",
                llm_decision_reason_short="LLM not used: request refused by security policy.",
                llm_decision_reason_code="ROUTE_REFUSE_OR_BLOCK",
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
        selected_id_set = set(selected_ids)
        selected_candidates = [candidate for candidate in ranked if candidate.chunk_id in selected_id_set]
        selected_files = len(
            {
                str(candidate.file_path).strip()
                for candidate in selected_candidates
                if str(candidate.file_path or "").strip()
            }
        )
        github_ctx = req.policy.get("github_context", {})
        is_pr_context = False
        if isinstance(github_ctx, dict):
            if bool(github_ctx.get("is_pr", False)):
                is_pr_context = True
            changed_files = github_ctx.get("changed_files", [])
            if isinstance(changed_files, list) and changed_files:
                is_pr_context = True
        verification_pending, verification_failed = self._verification_needs_gate(req.policy)
        semantic = decide_semantic_execution(
            task_type=req.task_type,
            route=route,
            selected_count=len(selected_ids),
            selected_files=max(0, selected_files),
            top_score=top_score,
            score_gap=gap,
            is_pr_context=is_pr_context,
            verification_pending=verification_pending,
            verification_failed=verification_failed,
            request_intent=str(req.policy.get("intent", "analysis") or "analysis"),
        )

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
            execution_mode=semantic.execution_mode,
            llm_intent=semantic.llm_intent,
            llm_decision_reason_short=semantic.reason_short,
            llm_decision_reason_code=semantic.reason_code,
        )

    def _verification_needs_gate(self, policy: dict[str, Any]) -> tuple[bool, bool]:
        verification = policy.get("verification_context", {})
        if not isinstance(verification, dict):
            return False, False
        checks = verification.get("checks", [])
        pending = False
        failed = False
        if isinstance(checks, list):
            for item in checks:
                if not isinstance(item, dict):
                    continue
                status = str(item.get("status", "")).strip().upper()
                if status in {"PENDING", "NOT_RUN", "IN_PROGRESS"}:
                    pending = True
                if status in {"FAIL", "FAILURE", "ERROR"}:
                    failed = True
        if bool(verification.get("verification_pending", False)):
            pending = True
        if bool(verification.get("verification_failed", False)):
            failed = True
        return pending, failed

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
        try:
            keep_ratio = float(limits.get("keep_ratio", 0.30))
        except (TypeError, ValueError):
            keep_ratio = 0.30
        keep_threshold = max(min_keep, top_score * keep_ratio)

        try:
            max_per_file = int(limits.get("max_per_file", 999))
        except (TypeError, ValueError):
            max_per_file = 999
        try:
            max_files = int(limits.get("max_files", max_sources))
        except (TypeError, ValueError):
            max_files = max_sources
        task_type = str(limits.get("task_type", "ask")).lower()

        selected: list[EngineCandidate] = [ranked[0]]
        selected_ids = {ranked[0].chunk_id}
        per_file_counts: dict[str, int] = {ranked[0].file_path or "": 1}
        used_files: set[str] = {ranked[0].file_path or ""}

        for candidate in ranked[1:]:
            if len(selected) >= max_sources:
                break
            file_key = candidate.file_path or ""
            if per_file_counts.get(file_key, 0) >= max_per_file:
                continue
            if file_key not in used_files and len(used_files) >= max_files:
                continue
            if candidate.score_local >= keep_threshold:
                selected.append(candidate)
                selected_ids.add(candidate.chunk_id)
                per_file_counts[file_key] = per_file_counts.get(file_key, 0) + 1
                used_files.add(file_key)

        min_sources = 1 if task_type == "locate" else self.min_sources
        target_min = min(min_sources, max_sources, len(ranked))
        if len(selected) < target_min:
            for candidate in ranked:
                if len(selected) >= target_min:
                    break
                if candidate.chunk_id in selected_ids:
                    continue
                file_key = candidate.file_path or ""
                if per_file_counts.get(file_key, 0) >= max_per_file:
                    continue
                if file_key not in used_files and len(used_files) >= max_files:
                    continue
                selected.append(candidate)
                selected_ids.add(candidate.chunk_id)
                per_file_counts[file_key] = per_file_counts.get(file_key, 0) + 1
                used_files.add(file_key)

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
