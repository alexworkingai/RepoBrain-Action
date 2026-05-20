from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from repobrain.execution_mode import decide_semantic_execution
from repobrain.topocore_deprecation import (
    TOPOCORE_LEGACY_LITE_REMOVED_REASON,
    TOPOCORE_UNSUPPORTED_LEGACY_BACKEND_REASON,
    TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON,
    TOPOCORE_V5_RUNTIME_REMOVED_REASON,
    TOPOCORE_V6_REQUIRED_REASON,
    TOPOCORE_V6_UNAVAILABLE_REASON,
)
from repobrain.topocore_v6_adapter import (
    RepoBrainTopoCoreV6Adapter,
    RepoBrainV6AdapterRuntimeError,
    RepoBrainV6CandidateRef,
    RepoBrainV6SummaryBundle,
)
from repobrain.tky_provider import CandidateChunk, TKYResult

TopoCoreBackendName = Literal["v5", "v6"]
TopoCoreBackendPolicyName = Literal["v5", "v6", "auto"]
BACKEND_V5: TopoCoreBackendName = "v5"
BACKEND_V6: TopoCoreBackendName = "v6"
BACKEND_AUTO: TopoCoreBackendPolicyName = "auto"
LEGACY_LITE_DISABLED_REASON = TOPOCORE_LEGACY_LITE_REMOVED_REASON
V6_UNAVAILABLE_V5_DISABLED_REASON = TOPOCORE_V6_UNAVAILABLE_REASON
_V5_ENGINE_TASK_TYPES = frozenset({"ask", "locate", "explain", "review"})
_V6_REQUEST_TASK_TYPES = frozenset({"ask", "locate", "explain", "review", "verify", "fix"})


class TopoCoreBackendError(ValueError):
    """Raised when backend selection or v6 execution is invalid or unsafe."""


@dataclass(frozen=True)
class TopoCoreBackendResolution:
    requested_backend: TopoCoreBackendPolicyName
    selected_backend: TopoCoreBackendName
    source_env: str
    strict_v6: bool = False
    local_path: str = ""
    deprecated_v5_allowed: bool = False


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


def _normalize_backend_policy(value: str) -> TopoCoreBackendPolicyName:
    normalized = str(value or "").strip().lower()
    if normalized in {"v5", "lite"}:
        return BACKEND_V5
    if normalized == "v6":
        return BACKEND_V6
    if normalized == "auto":
        return BACKEND_AUTO
    raise TopoCoreBackendError(
        f"Invalid backend selection: {normalized or 'empty'}."
    )


def _selected_backend_for_policy(policy_name: TopoCoreBackendPolicyName) -> TopoCoreBackendName:
    return BACKEND_V6


def _raise_unsupported_legacy_backend(
    *,
    requested_backend: TopoCoreBackendPolicyName,
    reason: str,
    source_env: str,
) -> None:
    raise TopoCoreBackendError(
        "Legacy TopoCore runtime selection is unsupported. "
        "Use RB_TOPOCORE_BACKEND=auto or RB_TOPOCORE_BACKEND=v6. "
        f"[{reason}] requested={requested_backend} source={source_env}"
    )


def _resolution(
    *,
    requested_backend: TopoCoreBackendPolicyName,
    selected_backend: TopoCoreBackendName,
    source_env: str,
    env: dict[str, str] | None,
    deprecated_v5_allowed: bool,
) -> TopoCoreBackendResolution:
    return TopoCoreBackendResolution(
        requested_backend=requested_backend,
        selected_backend=selected_backend,
        source_env=source_env,
        strict_v6=_env_bool("RB_TOPOCORE_V6_REQUIRE_LOCAL", False, env),
        local_path=_env_str("RB_TOPOCORE_V6_LOCAL_PATH", "", env),
        deprecated_v5_allowed=deprecated_v5_allowed,
    )


def resolve_backend(env: dict[str, str] | None = None) -> TopoCoreBackendResolution:
    deprecated_v5_requested = _env_bool("RB_TOPOCORE_ALLOW_DEPRECATED_V5", False, env)
    explicit = _env_str("RB_TOPOCORE_BACKEND", "", env)
    if explicit:
        normalized_explicit = str(explicit or "").strip().lower()
        requested_backend = _normalize_backend_policy(explicit)
        if requested_backend == BACKEND_V5:
            reason = (
                LEGACY_LITE_DISABLED_REASON
                if normalized_explicit == "lite"
                else TOPOCORE_V5_RUNTIME_REMOVED_REASON
            )
            if deprecated_v5_requested:
                reason = TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON
            _raise_unsupported_legacy_backend(
                requested_backend=requested_backend,
                reason=reason,
                source_env="RB_TOPOCORE_BACKEND",
            )
        return _resolution(
            requested_backend=requested_backend,
            selected_backend=_selected_backend_for_policy(requested_backend),
            source_env="RB_TOPOCORE_BACKEND",
            env=env,
            deprecated_v5_allowed=False,
        )

    legacy = _env_str("RB_TKYA_BACKEND", "", env)
    if legacy:
        normalized_legacy = str(legacy or "").strip().lower()
        requested_backend = _normalize_backend_policy(legacy)
        if requested_backend == BACKEND_V5:
            reason = (
                LEGACY_LITE_DISABLED_REASON
                if normalized_legacy == "lite"
                else TOPOCORE_UNSUPPORTED_LEGACY_BACKEND_REASON
            )
            if deprecated_v5_requested:
                reason = TOPOCORE_V5_DEPRECATED_NOT_ALLOWED_REASON
            _raise_unsupported_legacy_backend(
                requested_backend=requested_backend,
                reason=reason,
                source_env="RB_TKYA_BACKEND",
            )
        return _resolution(
            requested_backend=requested_backend,
            selected_backend=_selected_backend_for_policy(requested_backend),
            source_env="RB_TKYA_BACKEND",
            env=env,
            deprecated_v5_allowed=False,
        )

    return _resolution(
        requested_backend=BACKEND_AUTO,
        selected_backend=BACKEND_V6,
        source_env="default_auto",
        env=env,
        deprecated_v5_allowed=False,
    )


def should_fallback_to_v5(exc: Exception) -> bool:
    return False


def _sanitize_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _normalize_requested_task_type(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in _V6_REQUEST_TASK_TYPES:
        return normalized
    return "ask"


def _normalize_v5_engine_task_type(requested_task_type: str) -> str:
    normalized = _normalize_requested_task_type(requested_task_type)
    if normalized == "verify":
        return "review"
    if normalized == "fix":
        return "ask"
    if normalized in _V5_ENGINE_TASK_TYPES:
        return normalized
    return "ask"


def _safe_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _safe_string(value: Any) -> str:
    return str(value or "").strip()


def _safe_string_mapping(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    safe: dict[str, str] = {}
    for key, item in value.items():
        normalized_key = _safe_string(key)
        if not normalized_key:
            continue
        safe[normalized_key] = _safe_string(item)
    return safe


def _safe_summary_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _build_evidence_summary(
    *,
    requested_task_type: str,
    candidates: list[CandidateChunk],
    github_context: dict[str, Any],
    verification_context: dict[str, Any],
    fix_draft_summary: dict[str, Any],
) -> dict[str, Any]:
    file_paths = sorted(
        {
            str(item.file_path).strip()
            for item in candidates
            if str(item.file_path or "").strip()
        }
    )
    evidence_summary = {
        "command_family": requested_task_type,
        "candidate_count": len(candidates),
        "candidate_ids": [item.chunk_id for item in candidates[:8]],
        "candidate_file_count": len(file_paths),
        "pr_context_available": bool(github_context.get("is_pr", False)),
        "verification_context_available": bool(verification_context),
    }
    if requested_task_type == "fix":
        evidence_summary["fix_governance_present"] = bool(fix_draft_summary)
        evidence_summary["patch_safety_notes_count"] = len(
            _safe_string_list(fix_draft_summary.get("patch_safety_notes", []))
        )
    return evidence_summary


def _build_project_audit_summary(
    *,
    requested_task_type: str,
    github_context: dict[str, Any],
    runtime_context: dict[str, Any],
) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    changed_files = _safe_string_list(github_context.get("changed_files", []))
    diff_hunks = _safe_string_list(github_context.get("diff_hunks", []))
    pr_context = {
        "command_family": requested_task_type,
        "is_pr": bool(github_context.get("is_pr", False)),
        "pr_number": github_context.get("pr_number"),
        "issue_number": github_context.get("issue_number"),
        "changed_files_count": len(changed_files),
        "diff_hunk_count": len(diff_hunks),
        "base_ref": str(github_context.get("base_ref", "") or ""),
    }
    findings: tuple[dict[str, Any], ...]
    if pr_context["is_pr"]:
        findings = (
            {
                "finding": "pr_context_detected",
                "changed_files_count": len(changed_files),
                "diff_hunk_count": len(diff_hunks),
            },
        )
    else:
        findings = (
            {
                "finding": "review_verify_context_without_pr",
                "mode": str(runtime_context.get("github_actions", False)).lower(),
            },
        )
    return pr_context, findings


def _build_verification_summary(
    *,
    requested_task_type: str,
    verification_context: dict[str, Any],
) -> dict[str, Any]:
    return {
        "command_family": requested_task_type,
        "mode": str(verification_context.get("mode", "") or ""),
        "can_run_pytest": bool(verification_context.get("can_run_pytest", False)),
        "can_run_ruff": bool(verification_context.get("can_run_ruff", False)),
        "time_budget_s": int(verification_context.get("time_budget_s", 0) or 0),
        "network_allowed": bool(verification_context.get("network_allowed", False)),
        "verification_pending": bool(verification_context.get("verification_pending", False)),
        "verification_failed": bool(verification_context.get("verification_failed", False)),
    }


def _build_risk_items(
    *,
    requested_task_type: str,
    verification_context: dict[str, Any],
    github_context: dict[str, Any],
    fix_draft_summary: dict[str, Any],
    patch_governance_summary: dict[str, str],
) -> tuple[dict[str, Any], ...]:
    risk_items: list[dict[str, Any]] = []
    if requested_task_type == "verify":
        risk_items.append(
            {
                "risk_area": "verification",
                "severity_hint": "low",
                "reason_code": "verify_path_selected",
            }
        )
    if requested_task_type == "review":
        risk_items.append(
            {
                "risk_area": "review",
                "severity_hint": "low",
                "reason_code": "review_path_selected",
            }
        )
    if requested_task_type == "fix":
        risk_items.append(
            {
                "risk_area": "patch_governance",
                "severity_hint": "low",
                "reason_code": "fix_lite_decision_only",
            }
        )
        no_patch_reason = _safe_string(fix_draft_summary.get("no_patch_reason"))
        if no_patch_reason:
            risk_items.append(
                {
                    "risk_area": "patch_governance",
                    "severity_hint": "medium",
                    "reason_code": "no_patch_reason_present",
                    "detail_code": no_patch_reason,
                }
            )
        governance_reason = _safe_string(patch_governance_summary.get("governance_reason"))
        if governance_reason:
            risk_items.append(
                {
                    "risk_area": "patch_governance",
                    "severity_hint": "medium",
                    "reason_code": governance_reason,
                }
            )
        if _safe_string_list(fix_draft_summary.get("patch_safety_notes", [])):
            risk_items.append(
                {
                    "risk_area": "patch_safety",
                    "severity_hint": "medium",
                    "reason_code": "patch_safety_notes_present",
                }
            )
    if bool(verification_context.get("verification_pending", False)):
        risk_items.append(
            {
                "risk_area": "verification",
                "severity_hint": "medium",
                "reason_code": "verification_pending",
            }
        )
    if bool(verification_context.get("verification_failed", False)):
        risk_items.append(
            {
                "risk_area": "verification",
                "severity_hint": "high",
                "reason_code": "verification_failed",
            }
        )
    if not bool(github_context.get("is_pr", False)) and requested_task_type in {"review", "verify"}:
        risk_items.append(
            {
                "risk_area": "context",
                "severity_hint": "low",
                "reason_code": "pr_context_missing",
            }
        )
    return tuple(risk_items)


def _build_unknowns_summary(
    *,
    requested_task_type: str,
    candidates: list[CandidateChunk],
    github_context: dict[str, Any],
    verification_context: dict[str, Any],
    fix_draft_summary: dict[str, Any],
) -> dict[str, Any]:
    unknowns: list[str] = []
    if requested_task_type in {"review", "verify"} and not bool(github_context.get("is_pr", False)):
        unknowns.append("pr_context_missing")
    if requested_task_type == "verify" and not bool(verification_context.get("can_run_pytest", False)):
        unknowns.append("pytest_unavailable")
    if requested_task_type == "fix" and not _safe_string(fix_draft_summary.get("no_patch_reason")):
        unknowns.append("fix_governance_reason_missing")
    if not candidates:
        unknowns.append("candidate_evidence_missing")
    return {
        "command_family": requested_task_type,
        "unknowns": unknowns,
    }


def _build_scenario_branches(
    *,
    requested_task_type: str,
    engine_task_type: str,
    verification_context: dict[str, Any],
    fix_draft_summary: dict[str, Any],
) -> tuple[dict[str, Any], ...]:
    branch = {
        "command_family": requested_task_type,
        "engine_task_type": engine_task_type,
        "strict_local_v6": bool(verification_context.get("strict_local_v6", False)),
    }
    if requested_task_type == "fix":
        branch["fix_lite_decision"] = True
        branch["no_patch_reason"] = _safe_string(
            fix_draft_summary.get("no_patch_reason", "fix_lite_decision_only")
        ) or "fix_lite_decision_only"
    return (
        branch,
    )


def _build_fix_draft_summary(*, policy: dict[str, Any], limits: dict[str, Any]) -> dict[str, Any]:
    seed = _safe_summary_mapping(policy.get("fix_draft_summary", {}))
    if not seed:
        seed = _safe_summary_mapping(limits.get("fix_draft_summary", {}))
    patch_governance = _safe_string_mapping(policy.get("patch_governance", {}))
    safe_summary: dict[str, Any] = {}

    localized_target_hint = _safe_string(
        seed.get("localized_target_hint") or patch_governance.get("localized_target_hint", "")
    )
    if localized_target_hint:
        safe_summary["localized_target_hint"] = localized_target_hint

    no_patch_reason = _safe_string(
        seed.get("no_patch_reason")
        or patch_governance.get("governance_reason", "")
        or "fix_lite_decision_only"
    )
    safe_summary["no_patch_reason"] = no_patch_reason

    patch_safety_notes = _safe_string_list(seed.get("patch_safety_notes", []))
    if patch_safety_notes:
        safe_summary["patch_safety_notes"] = patch_safety_notes

    governance_reason = _safe_string(patch_governance.get("governance_reason", ""))
    if governance_reason:
        safe_summary["governance_reason"] = governance_reason

    next_safe_step = _safe_string(patch_governance.get("next_safe_step", ""))
    if next_safe_step:
        safe_summary["next_safe_step"] = next_safe_step

    patchability_class = _safe_string(patch_governance.get("patchability_class", ""))
    if patchability_class:
        safe_summary["patchability_class"] = patchability_class

    return safe_summary


def build_v6_summary_bundle(
    *,
    question: str,
    candidates: list[CandidateChunk],
    limits: dict[str, Any],
    policy: dict[str, Any],
) -> RepoBrainV6SummaryBundle:
    requested_task_type = _normalize_requested_task_type(
        limits.get("requested_task_type", limits.get("task_type", "ask"))
    )
    engine_task_type = _normalize_v5_engine_task_type(requested_task_type)

    github_context = _sanitize_mapping(policy.get("github_context", {}))
    verification_context = _sanitize_mapping(policy.get("verification_context", {}))
    runtime_context = _sanitize_mapping(policy.get("runtime", {}))
    patch_governance_summary = _safe_string_mapping(policy.get("patch_governance", {}))
    fix_draft_summary = _build_fix_draft_summary(policy=policy, limits=limits)
    verification_context.setdefault("strict_local_v6", bool(limits.get("strict_local_v6", False)))

    pr_context_summary, project_findings = _build_project_audit_summary(
        requested_task_type=requested_task_type,
        github_context=github_context,
        runtime_context=runtime_context,
    )
    evidence_summary = _build_evidence_summary(
        requested_task_type=requested_task_type,
        candidates=candidates,
        github_context=github_context,
        verification_context=verification_context,
        fix_draft_summary=fix_draft_summary,
    )
    verification_summary = _build_verification_summary(
        requested_task_type=requested_task_type,
        verification_context=verification_context,
    )
    risk_items = _build_risk_items(
        requested_task_type=requested_task_type,
        verification_context=verification_context,
        github_context=github_context,
        fix_draft_summary=fix_draft_summary,
        patch_governance_summary=patch_governance_summary,
    )
    unknowns_summary = _build_unknowns_summary(
        requested_task_type=requested_task_type,
        candidates=candidates,
        github_context=github_context,
        verification_context=verification_context,
        fix_draft_summary=fix_draft_summary,
    )
    scenario_branches = _build_scenario_branches(
        requested_task_type=requested_task_type,
        engine_task_type=engine_task_type,
        verification_context=verification_context,
        fix_draft_summary=fix_draft_summary,
    )

    return RepoBrainV6SummaryBundle(
        query=question,
        intent_summary={
            "command": requested_task_type,
            "task_type_candidate": engine_task_type,
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
        task_type=engine_task_type,
        limits=dict(limits),
        pr_context_summary=pr_context_summary,
        evidence_summary=evidence_summary,
        unknowns_summary=unknowns_summary,
        risk_items=risk_items,
        review_draft_summary={},
        fix_draft_summary=fix_draft_summary,
        verification_results=verification_summary,
        project_audit_scorecard=runtime_context,
        project_audit_findings=project_findings,
        scenario_branches=scenario_branches,
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
            **(
                {
                    "fix_lite_decision": True,
                    "patch_authorized": False,
                    "patch_applied": False,
                    "files_modified": False,
                    "branch_created": False,
                    "commit_created": False,
                    "pr_created": False,
                    "no_patch_reason": _safe_string(
                        bundle.fix_draft_summary.get("no_patch_reason", "fix_lite_decision_only")
                    )
                    or "fix_lite_decision_only",
                }
                if str(bundle.intent_summary.get("command", "") or "").strip().lower() == "fix"
                else {}
            ),
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
    "BACKEND_AUTO",
    "BACKEND_V5",
    "BACKEND_V6",
    "LEGACY_LITE_DISABLED_REASON",
    "TopoCoreBackendDecision",
    "TopoCoreBackendError",
    "TopoCoreBackendResolution",
    "V6_UNAVAILABLE_V5_DISABLED_REASON",
    "build_v6_summary_bundle",
    "resolve_backend",
    "run_v6_backend",
    "should_fallback_to_v5",
    "TOPOCORE_V6_REQUIRED_REASON",
]
