from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from repobrain.execution_mode import decide_semantic_execution
from repobrain.topocore_v6_adapter import (
    RepoBrainTopoCoreV6Adapter,
    RepoBrainV6AdapterRuntimeError,
    RepoBrainV6CandidateRef,
    RepoBrainV6SummaryBundle,
)
from repobrain.tky_provider import CandidateChunk, TKYResult

TopoCoreBackendName = Literal["v5", "v6"]
BACKEND_V5: TopoCoreBackendName = "v5"
BACKEND_V6: TopoCoreBackendName = "v6"


class TopoCoreBackendError(ValueError):
    """Raised when backend selection or v6 execution is invalid or unsafe."""


@dataclass(frozen=True)
class TopoCoreBackendResolution:
    selected_backend: TopoCoreBackendName
    source_env: str
    strict_v6: bool = False
    local_path: str = ""


@dataclass(frozen=True)
class TopoCoreBackendDecision:
    backend: TopoCoreBackendName
    tky_result: TKYResult


def _env_str(name: str, default: str = "", env: dict[str, str] | None = None) -> str:
    source = env if env is not None else None
    if source is None:
        import os

        source = os.environ
    return str(source.get(name, default) or "").strip()


def _env_bool(name: str, default: bool = False, env: dict[str, str] | None = None) -> bool:
    raw = _env_str(name, "", env)
    if not raw:
        return bool(default)
    return raw.lower() in {"1", "true", "yes", "y", "on"}


def _normalize_backend(value: str) -> TopoCoreBackendName:
    normalized = str(value or "").strip().lower()
    if normalized in {"v5", "lite"}:
        return BACKEND_V5
    if normalized == "v6":
        return BACKEND_V6
    raise TopoCoreBackendError(
        f"Invalid backend selection: {normalized or 'empty'}."
    )


def resolve_backend(env: dict[str, str] | None = None) -> TopoCoreBackendResolution:
    explicit = _env_str("RB_TOPOCORE_BACKEND", "", env)
    if explicit:
        backend = _normalize_backend(explicit)
        return TopoCoreBackendResolution(
            selected_backend=backend,
            source_env="RB_TOPOCORE_BACKEND",
            strict_v6=_env_bool("RB_TOPOCORE_V6_REQUIRE_LOCAL", False, env),
            local_path=_env_str("RB_TOPOCORE_V6_LOCAL_PATH", "", env),
        )

    legacy = _env_str("RB_TKYA_BACKEND", "", env)
    if legacy:
        backend = _normalize_backend(legacy)
        return TopoCoreBackendResolution(
            selected_backend=backend,
            source_env="RB_TKYA_BACKEND",
            strict_v6=_env_bool("RB_TOPOCORE_V6_REQUIRE_LOCAL", False, env),
            local_path=_env_str("RB_TOPOCORE_V6_LOCAL_PATH", "", env),
        )

    return TopoCoreBackendResolution(
        selected_backend=BACKEND_V5,
        source_env="default",
        strict_v6=_env_bool("RB_TOPOCORE_V6_REQUIRE_LOCAL", False, env),
        local_path=_env_str("RB_TOPOCORE_V6_LOCAL_PATH", "", env),
    )


def should_fallback_to_v5(exc: Exception) -> bool:
    message = str(exc).lower()
    return "unavailable" in message or "local path is not available" in message


def _sanitize_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def build_v6_summary_bundle(
    *,
    question: str,
    candidates: list[CandidateChunk],
    limits: dict[str, Any],
    policy: dict[str, Any],
) -> RepoBrainV6SummaryBundle:
    task_type = str(limits.get("task_type", "ask") or "ask").strip().lower()
    if task_type not in {"ask", "locate", "explain", "review"}:
        task_type = "ask"

    github_context = _sanitize_mapping(policy.get("github_context", {}))
    verification_context = _sanitize_mapping(policy.get("verification_context", {}))
    runtime_context = _sanitize_mapping(policy.get("runtime", {}))

    return RepoBrainV6SummaryBundle(
        query=question,
        intent_summary={
            "command": task_type,
            "task_type_candidate": task_type,
            "user_goal": str(limits.get("user_goal", "") or ""),
        },
        candidates=tuple(
            RepoBrainV6CandidateRef(
                chunk_id=item.chunk_id,
                score_local=float(item.score_local if item.score_local is not None else item.score),
                signature=item.signature,
                file_path=item.file_path,
                line_start=item.line_start,
                line_end=item.line_end,
            )
            for item in candidates
        ),
        task_type=task_type,
        limits=dict(limits),
        pr_context_summary=github_context,
        evidence_summary={"candidate_count": len(candidates)},
        unknowns_summary={},
        risk_items=(),
        review_draft_summary={},
        fix_draft_summary={},
        verification_results=verification_context,
        project_audit_scorecard=runtime_context,
        project_audit_findings=(),
        scenario_branches=(),
    )


def _route_from_external_decision(*, status: str, action: str, blocked: bool) -> str:
    status_norm = str(status or "").strip().lower()
    action_norm = str(action or "").strip().lower()
    if blocked or status_norm == "blocked" or action_norm == "stop":
        return "REFUSE"
    if status_norm == "pending" or action_norm == "wait":
        return "WAIT"
    if status_norm == "needs_review" or action_norm == "review":
        return "REVIEW"
    if status_norm == "needs_more_information" or action_norm == "investigate":
        return "DEEP"
    return "FAST"


def _selected_chunk_ids(
    *,
    candidates: list[CandidateChunk],
    route: str,
    selected_count: int,
) -> list[str]:
    if route in {"REFUSE", "WAIT"}:
        return []
    keep = max(0, min(int(selected_count or 0), len(candidates)))
    if keep <= 0:
        return []
    return [item.chunk_id for item in candidates[:keep]]


def run_v6_backend(
    *,
    question: str,
    candidates: list[CandidateChunk],
    limits: dict[str, Any],
    policy: dict[str, Any],
    local_path: str = "",
) -> TopoCoreBackendDecision:
    adapter = RepoBrainTopoCoreV6Adapter()
    bundle = build_v6_summary_bundle(
        question=question,
        candidates=candidates,
        limits=limits,
        policy=policy,
    )
    try:
        decision = adapter.decide_external_local(bundle, local_path=local_path or None)
    except RepoBrainV6AdapterRuntimeError as exc:
        raise TopoCoreBackendError(str(exc)) from exc
    route = _route_from_external_decision(
        status=decision.status,
        action=decision.action,
        blocked=decision.blocked,
    )
    selected_ids = _selected_chunk_ids(
        candidates=candidates,
        route=route,
        selected_count=decision.selected_count,
    )
    selected_files = len(
        {
            item.file_path
            for item in candidates
            if item.chunk_id in set(selected_ids) and str(item.file_path or "").strip()
        }
    )
    top_score = max((float(item.score) for item in candidates), default=0.0)
    sorted_scores = sorted((float(item.score) for item in candidates), reverse=True)
    second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0.0
    verification_context = _sanitize_mapping(policy.get("verification_context", {}))
    github_context = _sanitize_mapping(policy.get("github_context", {}))
    execution = decide_semantic_execution(
        task_type=bundle.task_type or "ask",
        route=route,
        selected_count=len(selected_ids),
        selected_files=selected_files,
        top_score=top_score,
        score_gap=top_score - second_score,
        is_pr_context=bool(github_context.get("is_pr", False)),
        verification_pending=bool(verification_context.get("verification_pending", False)),
        verification_failed=bool(verification_context.get("verification_failed", False)),
        request_intent=str(bundle.intent_summary.get("command", "analysis") or "analysis"),
    )

    tky_result = TKYResult(
        selected_chunk_ids=selected_ids,
        route=route,
        compression_stats={
            "retrieved": len(candidates),
            "selected": len(selected_ids),
            "route": route,
            "backend_selected": "v6",
            "external_status": decision.status,
            "external_action": decision.action,
            "reference_hash": decision.reference_hash,
            "selected_count_external": int(decision.selected_count),
            "confidence_band": decision.confidence_band,
            "message_code": decision.message_code,
            "blocked": bool(decision.blocked),
        },
        rationale=(
            "TopoCore v6 external decision: "
            f"status={decision.status or 'unknown'} "
            f"action={decision.action or 'unknown'} "
            f"message_code={decision.message_code or 'unknown'}"
        ),
        execution_mode=execution.execution_mode,
        llm_intent=execution.llm_intent,
        llm_decision_reason_short=execution.reason_short,
        llm_decision_reason_code=execution.reason_code,
    )
    return TopoCoreBackendDecision(
        backend=BACKEND_V6,
        tky_result=tky_result,
    )


__all__ = [
    "BACKEND_V5",
    "BACKEND_V6",
    "TopoCoreBackendDecision",
    "TopoCoreBackendError",
    "TopoCoreBackendResolution",
    "build_v6_summary_bundle",
    "resolve_backend",
    "run_v6_backend",
    "should_fallback_to_v5",
]
