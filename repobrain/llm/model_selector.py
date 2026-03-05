from __future__ import annotations

from typing import Any

from repobrain.config import RepoBrainConfig

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


def _scaled_budget(score: int, low: int, high: int) -> int:
    bounded_score = max(0, min(100, int(score)))
    span = max(0, high - low)
    return int(low + (span * bounded_score / 100.0))


def compute_output_token_budget(
    task_type: str,
    intent: str,
    complexity_score: int,
    cfg: RepoBrainConfig | None = None,
) -> int:
    """Compute adaptive max_output_tokens with env overrides and global cap."""
    llm_cfg = (cfg or RepoBrainConfig.from_env()).llm
    global_cap = max(200, int(llm_cfg.max_output_tokens_global))
    ask_cap = max(200, int(llm_cfg.max_output_tokens_ask))
    review_cap = max(200, int(llm_cfg.max_output_tokens_review))
    fix_cap = max(200, int(llm_cfg.max_output_tokens_fix))

    normalized_task = str(task_type or "").strip().lower()
    normalized_intent = str(intent or "").strip().lower()

    if normalized_intent == "patch" or normalized_task == "fix":
        adaptive = _scaled_budget(complexity_score, low=1200, high=2400)
        return min(adaptive, fix_cap, global_cap)
    if normalized_task == "review":
        adaptive = _scaled_budget(complexity_score, low=800, high=1600)
        return min(adaptive, review_cap, global_cap)
    adaptive = _scaled_budget(complexity_score, low=600, high=1200)
    return min(adaptive, ask_cap, global_cap)


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
