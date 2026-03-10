from __future__ import annotations

from dataclasses import dataclass


EXECUTION_MODES = {
    "retrieval_only",
    "retrieval_plus_llm",
    "verification_first",
    "refuse",
}
LLM_INTENTS = {"none", "explain", "summarize", "review", "patch"}


@dataclass(frozen=True)
class ExecutionDecision:
    execution_mode: str
    llm_intent: str
    reason_short: str
    reason_code: str


def _normalize_route(route: str) -> str:
    normalized = str(route or "").strip().upper()
    if normalized in {"BLOCK", "DENY", "REJECT"}:
        return "BLOCK"
    if normalized in {"PENDING", "VERIFY_PENDING"}:
        return "WAIT"
    return normalized or "FAST"


def _fallback_from_route(route: str) -> ExecutionDecision:
    route_norm = _normalize_route(route)
    if route_norm == "WAIT":
        return ExecutionDecision(
            execution_mode="verification_first",
            llm_intent="none",
            reason_short="LLM not used: verification required before answer.",
            reason_code="ROUTE_WAIT_VERIFICATION",
        )
    if route_norm in {"REFUSE", "BLOCK"}:
        return ExecutionDecision(
            execution_mode="refuse",
            llm_intent="none",
            reason_short="LLM not used: request refused by security policy.",
            reason_code="ROUTE_REFUSE_OR_BLOCK",
        )
    return ExecutionDecision(
        execution_mode="retrieval_only",
        llm_intent="none",
        reason_short="LLM not used: direct answer available from retrieved evidence.",
        reason_code="DEFAULT_RETRIEVAL_ONLY",
    )


def decide_semantic_execution(
    *,
    task_type: str,
    route: str,
    selected_count: int,
    selected_files: int,
    top_score: float,
    score_gap: float,
    is_pr_context: bool,
    verification_pending: bool,
    verification_failed: bool,
    request_intent: str = "analysis",
) -> ExecutionDecision:
    route_norm = _normalize_route(route)
    task_norm = str(task_type or "ask").strip().lower()
    task_norm = task_norm if task_norm in {"ask", "locate", "explain", "review"} else "ask"
    intent_norm = str(request_intent or "analysis").strip().lower()

    if route_norm in {"REFUSE", "BLOCK"}:
        return ExecutionDecision(
            execution_mode="refuse",
            llm_intent="none",
            reason_short="LLM not used: request refused by security policy.",
            reason_code="ROUTE_REFUSE_OR_BLOCK",
        )
    if route_norm == "WAIT":
        return ExecutionDecision(
            execution_mode="verification_first",
            llm_intent="none",
            reason_short="LLM not used: verification required before answer.",
            reason_code="ROUTE_WAIT_VERIFICATION",
        )
    if verification_failed or verification_pending:
        return ExecutionDecision(
            execution_mode="verification_first",
            llm_intent="none",
            reason_short="LLM not used: verification required before answer.",
            reason_code="VERIFICATION_REQUIRED",
        )

    if task_norm == "locate":
        return ExecutionDecision(
            execution_mode="retrieval_only",
            llm_intent="none",
            reason_short="LLM not used: location lookup is direct from evidence.",
            reason_code="LOCATE_DIRECT_EVIDENCE",
        )

    if task_norm == "review":
        llm_intent = "patch" if intent_norm == "patch" else "review"
        reason = (
            "LLM used: patch synthesis required for proposed code changes."
            if llm_intent == "patch"
            else "LLM used: review requires multi-file synthesis."
        )
        code = "PATCH_SYNTHESIS_REQUIRED" if llm_intent == "patch" else "REVIEW_SYNTHESIS_REQUIRED"
        return ExecutionDecision(
            execution_mode="retrieval_plus_llm",
            llm_intent=llm_intent,
            reason_short=reason,
            reason_code=code,
        )

    if task_norm == "explain":
        return ExecutionDecision(
            execution_mode="retrieval_plus_llm",
            llm_intent="explain",
            reason_short="LLM used: explanation requires synthesized multi-source context.",
            reason_code="EXPLAIN_SYNTHESIS_REQUIRED",
        )

    # ask
    direct_high_conf = (
        selected_count <= 2
        and selected_files <= 1
        and top_score >= 0.09
        and score_gap >= 0.06
        and route_norm == "FAST"
        and not is_pr_context
    )
    if direct_high_conf:
        return ExecutionDecision(
            execution_mode="retrieval_only",
            llm_intent="none",
            reason_short="LLM not used: direct answer available from retrieved evidence.",
            reason_code="DIRECT_EVIDENCE_SUFFICIENT",
        )

    synthesis_needed = (
        route_norm == "DEEP"
        or selected_count >= 3
        or selected_files >= 2
        or score_gap < 0.04
        or top_score < 0.09
        or is_pr_context
    )
    if synthesis_needed:
        return ExecutionDecision(
            execution_mode="retrieval_plus_llm",
            llm_intent="summarize",
            reason_short="LLM used: multi-source synthesis required after retrieval.",
            reason_code="MULTI_SOURCE_SYNTHESIS_REQUIRED",
        )

    return ExecutionDecision(
        execution_mode="retrieval_only",
        llm_intent="none",
        reason_short="LLM not used: direct answer available from retrieved evidence.",
        reason_code="DIRECT_EVIDENCE_SUFFICIENT",
    )


def coerce_execution_decision(
    *,
    route: str,
    execution_mode: str | None,
    llm_intent: str | None,
    reason_short: str | None,
    reason_code: str | None,
) -> ExecutionDecision:
    route_norm = _normalize_route(route)
    if route_norm in {"WAIT", "REFUSE", "BLOCK"}:
        return _fallback_from_route(route_norm)

    mode = str(execution_mode or "").strip().lower()
    intent = str(llm_intent or "").strip().lower()
    short = str(reason_short or "").strip()
    code = str(reason_code or "").strip()

    if mode not in EXECUTION_MODES:
        return _fallback_from_route(route)
    if intent not in LLM_INTENTS:
        intent = "none"
    if short and code:
        return ExecutionDecision(mode, intent, short, code)

    fallback = _fallback_from_route(route)
    return ExecutionDecision(
        execution_mode=mode,
        llm_intent=intent,
        reason_short=short or fallback.reason_short,
        reason_code=code or fallback.reason_code,
    )
