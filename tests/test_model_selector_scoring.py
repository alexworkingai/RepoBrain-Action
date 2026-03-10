from __future__ import annotations

from repobrain.llm.model_selector import choose_model, score_complexity


def test_patch_review_deep_selects_high_tier_model() -> None:
    score = score_complexity(
        task_type="review",
        intent="patch",
        route="DEEP",
        github_context={"changed_files": [f"file_{i}.py" for i in range(12)]},
        candidates=[None] * 50,
        limits={"query_length": 600},
    )
    model_id, tier = choose_model(score)

    assert score >= 35
    assert tier == "high"
    assert model_id == "openai/gpt-4.1"


def test_small_fast_ask_selects_low_tier_model() -> None:
    score = score_complexity(
        task_type="ask",
        intent="analysis",
        route="FAST",
        github_context={"changed_files": ["repobrain/ask.py"]},
        candidates=[None] * 4,
        limits={"query_length": 80},
    )
    model_id, tier = choose_model(score)

    assert score < 35
    assert tier == "low"
    assert model_id == "openai/gpt-4.1-mini"
