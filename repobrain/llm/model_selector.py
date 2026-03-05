from __future__ import annotations

from typing import Any


def score_complexity(
    task_type: str,
    intent: str,
    route: str,
    github_context: dict[str, Any] | None,
    candidates: list[Any] | None,
    limits: dict[str, Any] | None,
) -> int:
    """Compute deterministic complexity score in range 0..100."""
    score = 0
    normalized_intent = str(intent or "").strip().lower()
    normalized_task = str(task_type or "").strip().lower()
    normalized_route = str(route or "").strip().upper()
    ctx = dict(github_context or {})
    local_limits = dict(limits or {})
    candidate_count = len(candidates or [])

    if normalized_intent == "patch":
        score += 30
    if normalized_task == "review":
        score += 25
    if normalized_route == "DEEP":
        score += 25

    changed_files_raw = ctx.get("changed_files", [])
    changed_files = changed_files_raw if isinstance(changed_files_raw, list) else []
    changed_count = len(changed_files)
    if 3 <= changed_count <= 10:
        score += 10
    elif changed_count > 10:
        score += 20

    if 16 <= candidate_count <= 40:
        score += 10
    elif candidate_count > 40:
        score += 20

    query_length = int(local_limits.get("query_length", 0) or 0)
    if query_length > 400:
        score += 10

    return max(0, min(100, score))


def choose_model(
    score: int,
    *,
    model_high: str = "openai/gpt-4.1",
    model_low: str = "openai/gpt-4.1-mini",
) -> tuple[str, str]:
    """Choose model id and tier from complexity score."""
    bounded = max(0, min(100, int(score)))
    if bounded >= 35:
        return model_high, "high"
    return model_low, "low"


def complexity_explanation(
    task_type: str,
    intent: str,
    route: str,
    changed_files_count: int,
    candidates_count: int,
    query_length: int,
    score: int,
) -> str:
    """Build short explanation string for audit diagnostics."""
    return (
        f"complexity score={int(score)} "
        f"(task={task_type}, intent={intent}, route={route}, "
        f"changed_files={int(changed_files_count)}, "
        f"candidates={int(candidates_count)}, query_len={int(query_length)})"
    )

