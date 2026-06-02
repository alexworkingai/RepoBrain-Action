from __future__ import annotations

from dataclasses import dataclass, field

from repobrain.github_flow import (
    _maybe_generate_llm_text,
    _runtime_override_reason_from_skip,
    _set_runtime_env_cfg,
)
from repobrain.output_md import render_answer_markdown


@dataclass(frozen=True)
class _FakeLLMResponse:
    text: str = "issue_comment llm answer"
    model_id: str = "openai/gpt-4.1-mini"
    prompt_tokens: int = 20
    completion_tokens: int = 10
    total_tokens: int = 30
    usage_estimated: bool = False
    ratelimit_headers: dict[str, str] = field(default_factory=dict)
    requests_remaining: int | None = 18
    remaining_is_estimate: bool = False
    reset_time_utc_iso: str | None = "2026-03-11T23:59:59+00:00"


def test_issue_comment_policy_allows_llm_when_semantic_mode_requires_it(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("RB_LLM_ENABLE_ISSUE_COMMENT", "1")
    monkeypatch.setenv("RB_LLM_ENABLE_PR_COMMENTS", "1")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    _set_runtime_env_cfg(None)  # noqa: SLF001

    def fake_chat(*_args, **_kwargs):  # noqa: ANN002, ANN003
        return _FakeLLMResponse()

    monkeypatch.setattr("repobrain.github_flow.GitHubModelsClient.chat", fake_chat)
    text, meta = _maybe_generate_llm_text(
        cmd="ask",
        intent="analysis",
        query="what files changed in this PR?",
        route="DEEP",
        execution_mode="retrieval_plus_llm",
        llm_intent_decision="summarize",
        llm_decision_reason_short="LLM used: multi-source synthesis required after retrieval.",
        llm_decision_reason_code="MULTI_SOURCE_SYNTHESIS_REQUIRED",
        github_context={"event_name": "issue_comment", "is_pr": True, "pr_number": 1},
        locators=[],
        candidates_count=4,
    )
    assert text == "issue_comment llm answer"
    assert meta["llm_used"] is True


def test_retrieval_only_semantic_mode_blocks_llm_even_when_policy_enabled(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("RB_LLM_ENABLE_ISSUE_COMMENT", "1")
    monkeypatch.setenv("RB_LLM_ENABLE_PR_COMMENTS", "1")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    _set_runtime_env_cfg(None)  # noqa: SLF001

    def fail_if_called(*_args, **_kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("LLM must not run for retrieval_only execution mode")

    monkeypatch.setattr("repobrain.github_flow.GitHubModelsClient.chat", fail_if_called)
    text, meta = _maybe_generate_llm_text(
        cmd="ask",
        intent="analysis",
        query="where is provider?",
        route="FAST",
        execution_mode="retrieval_only",
        llm_intent_decision="none",
        llm_decision_reason_short="LLM not used: direct answer available from retrieved evidence.",
        llm_decision_reason_code="DIRECT_EVIDENCE_SUFFICIENT",
        github_context={"event_name": "issue_comment", "is_pr": True, "pr_number": 1},
        locators=[],
        candidates_count=1,
    )
    assert text is None
    assert meta["llm_used"] is False
    assert meta["llm_skip_reason"] == "execution_mode=retrieval_only"


def test_wait_refuse_block_routes_never_call_llm(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("RB_LLM_ENABLE_ISSUE_COMMENT", "1")
    monkeypatch.setenv("RB_LLM_ENABLE_PR_COMMENTS", "1")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    _set_runtime_env_cfg(None)  # noqa: SLF001

    def fail_if_called(*_args, **_kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("LLM must not run for WAIT/REFUSE/BLOCK")

    monkeypatch.setattr("repobrain.github_flow.GitHubModelsClient.chat", fail_if_called)
    for route in ("WAIT", "REFUSE", "BLOCK"):
        text, meta = _maybe_generate_llm_text(
            cmd="ask",
            intent="analysis",
            query="route gate",
            route=route,
            execution_mode="retrieval_plus_llm",
            llm_intent_decision="summarize",
            llm_decision_reason_short="LLM used: multi-source synthesis required after retrieval.",
            llm_decision_reason_code="MULTI_SOURCE_SYNTHESIS_REQUIRED",
            github_context={"event_name": "issue_comment", "is_pr": True, "pr_number": 1},
            locators=[],
            candidates_count=3,
        )
        assert text is None
        assert meta["llm_used"] is False


def test_issue_comment_policy_disabled_sets_runtime_override(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("RB_LLM_ENABLE_ISSUE_COMMENT", "0")
    monkeypatch.setenv("RB_LLM_ENABLE_PR_COMMENTS", "1")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    _set_runtime_env_cfg(None)  # noqa: SLF001

    def fail_if_called(*_args, **_kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("LLM must be blocked by issue_comment policy")

    monkeypatch.setattr("repobrain.github_flow.GitHubModelsClient.chat", fail_if_called)
    _text, meta = _maybe_generate_llm_text(
        cmd="ask",
        intent="analysis",
        query="what files changed?",
        route="DEEP",
        execution_mode="retrieval_plus_llm",
        llm_intent_decision="summarize",
        llm_decision_reason_short="LLM used: multi-source synthesis required after retrieval.",
        llm_decision_reason_code="MULTI_SOURCE_SYNTHESIS_REQUIRED",
        github_context={"event_name": "issue_comment", "is_pr": True, "pr_number": 42},
        locators=[],
        candidates_count=4,
    )
    assert meta["llm_used"] is False
    assert meta["llm_skip_reason"] == "issue_comment_policy_disabled"

    override = _runtime_override_reason_from_skip(meta["llm_skip_reason"])
    md = render_answer_markdown(
        answer_text="answer",
        evidence=[],
        audit_summary={
            "route_final": "DEEP",
            "pass_count": 2,
            "retrieved": 10,
            "selected": 3,
            "llm_used": False,
            "llm_skip_reason": meta["llm_skip_reason"],
            "execution_mode": "retrieval_plus_llm",
            "llm_decision_reason_short": "LLM used: multi-source synthesis required after retrieval.",
            "llm_runtime_override_reason": override,
        },
        next_steps="verify",
        command="ask",
    )
    assert "- LLM: not called" in md
    assert "- Reason: LLM blocked: issue_comment policy disabled." in md
