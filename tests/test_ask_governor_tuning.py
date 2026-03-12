from __future__ import annotations

from dataclasses import dataclass, field

from repobrain.ai_budget_governor import AIBudgetGovernor, BudgetPolicy
from repobrain.config import RepoBrainConfig
from repobrain.github_flow import (
    _maybe_generate_llm_text,
    _set_runtime_env_cfg,
    _should_retain_preferred_model_for_ask,
)


@dataclass(frozen=True)
class _FakeResponse:
    text: str = "Summarized answer."
    model_id: str = "openai/gpt-4.1"
    prompt_tokens: int = 120
    completion_tokens: int = 80
    total_tokens: int = 200
    usage_estimated: bool = False
    ratelimit_headers: dict[str, str] = field(default_factory=dict)
    requests_remaining: int | None = 16
    remaining_is_estimate: bool = False
    reset_time_utc_iso: str | None = "2026-03-11T00:00:00+00:00"


def test_complex_ask_retains_preferred_model_in_estimate_mode(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("RB_LLM_FORCE_STRONG_MODEL_FOR_COMPLEX_ASK", "1")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    _set_runtime_env_cfg(None)  # noqa: SLF001

    captured_model: dict[str, str] = {"value": ""}

    def fake_chat(self, **kwargs):  # noqa: ANN001
        captured_model["value"] = str(kwargs["model_id"])
        return _FakeResponse(model_id=str(kwargs["model_id"]))

    monkeypatch.setattr("repobrain.github_flow.GitHubModelsClient.chat", fake_chat)

    governor = AIBudgetGovernor(
        BudgetPolicy(
            estimate_mode_conservative=True,
            switch_to_mini_when_remaining_lt=5,
            max_llm_calls_per_run=10,
            max_embed_calls_per_run=10,
        )
    )
    text, meta = _maybe_generate_llm_text(
        cmd="ask",
        intent="analysis",
        query=("Summarize architectural impact. " * 40).strip(),
        route="DEEP",
        execution_mode="retrieval_plus_llm",
        llm_intent_decision="summarize",
        llm_decision_reason_short="LLM used: multi-source synthesis required after deep retrieval.",
        llm_decision_reason_code="MULTI_SOURCE_SYNTHESIS_REQUIRED",
        github_context={"changed_files": [f"repobrain/module_{i}.py" for i in range(4)]},
        locators=[],
        candidates_count=42,
        governor=governor,
    )

    assert text
    assert meta["llm_used"] is True
    assert captured_model["value"] == "openai/gpt-4.1"
    assert meta["llm_model_used"] == "openai/gpt-4.1"
    assert "retained preferred model" in str(meta["llm_retained_preferred_model_reason"]).lower()


def test_retain_preferred_model_is_disabled_when_remaining_below_threshold(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_FORCE_STRONG_MODEL_FOR_COMPLEX_ASK", "1")
    monkeypatch.setenv("RB_LLM_DOWNGRADE_MIN_REMAINING_REQUESTS_ASK", "8")
    cfg = RepoBrainConfig.from_env()

    retain, reason = _should_retain_preferred_model_for_ask(
        cfg=cfg,
        cmd="ask",
        execution_mode="retrieval_plus_llm",
        llm_intent="summarize",
        route="DEEP",
        complexity_score=80,
        remaining_requests=3,
        github_context={"changed_files": ["a.py", "b.py"]},
    )

    assert retain is False
    assert reason == "n/a"


def test_simple_ask_does_not_force_strong_model_retention(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_FORCE_STRONG_MODEL_FOR_COMPLEX_ASK", "1")
    cfg = RepoBrainConfig.from_env()

    retain, reason = _should_retain_preferred_model_for_ask(
        cfg=cfg,
        cmd="ask",
        execution_mode="retrieval_plus_llm",
        llm_intent="summarize",
        route="FAST",
        complexity_score=20,
        remaining_requests=20,
        github_context={"changed_files": ["single_file.py"]},
    )

    assert retain is False
    assert reason == "n/a"
