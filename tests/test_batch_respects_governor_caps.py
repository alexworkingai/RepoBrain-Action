from __future__ import annotations

from pathlib import Path

from repobrain.ai_budget_governor import AIBudgetGovernor, BudgetPolicy, QuotaSignal
from repobrain.evidence import EvidenceItem
from repobrain.github_flow import _run_batch_llm_review_fix
from repobrain.llm.batch_planner import Batch
from repobrain.tky_provider import CandidateChunk


def test_batch_loop_is_capped_by_governor(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("RB_LLM_BATCH_ENABLE", "1")
    monkeypatch.setenv("RB_LLM_BATCH_MAX_CALLS_PER_RUN", "6")
    monkeypatch.setenv("RB_ASYNC_BATCH_ENABLE", "0")

    governor = AIBudgetGovernor(
        BudgetPolicy(
            min_remaining_buffer=1,
            max_llm_calls_per_run=10,
            disable_reduce_when_remaining_lt=0,
        )
    )
    governor.observe_llm_signal(
        QuotaSignal(
            remaining_requests=2,
            reset_time_utc_iso=None,
            remaining_is_estimate=False,
            usage_estimated=False,
            ratelimit_headers={},
        ),
        {"tokens_total": 0},
    )

    batches = [
        Batch(batch_id="b1", paths=["a.py"], diff_hunks=["@@ a"], snippet_ids=["s1"], estimated_input_tokens=500),
        Batch(batch_id="b2", paths=["b.py"], diff_hunks=["@@ b"], snippet_ids=["s2"], estimated_input_tokens=500),
        Batch(batch_id="b3", paths=["c.py"], diff_hunks=["@@ c"], snippet_ids=["s3"], estimated_input_tokens=500),
    ]
    monkeypatch.setattr("repobrain.github_flow.plan_batches", lambda *args, **kwargs: batches)

    call_counter = {"n": 0}

    def fake_llm(*args, **kwargs):  # noqa: ANN002, ANN003
        call_counter["n"] += 1
        return (
            "ok",
            {
                "llm_used": True,
                "llm_skip_reason": "n/a",
                "llm_model_used": "openai/gpt-4.1-mini",
                "llm_tier": "low",
                "llm_budget_action": "n/a",
                "llm_governor_reason": "ok",
                "llm_tokens_prompt": 10,
                "llm_tokens_completion": 5,
                "llm_tokens_total": 15,
                "llm_usage_estimated": False,
                "llm_remaining_requests": 10,
                "llm_remaining_is_estimate": False,
                "llm_reset_time_utc_iso": None,
                "llm_calls": [
                    {
                        "batch_id": "single",
                        "model_id": "openai/gpt-4.1-mini",
                        "tier": "low",
                        "tokens_prompt": 10,
                        "tokens_completion": 5,
                        "tokens_total": 15,
                        "remaining_requests": 10,
                        "remaining_is_estimate": False,
                        "reset_time_utc_iso": None,
                        "estimate_flags": {"usage_estimated": False, "remaining_estimated": False},
                    }
                ],
            },
        )

    monkeypatch.setattr("repobrain.github_flow._maybe_generate_llm_text", fake_llm)

    chunks = [
        CandidateChunk("c1", "a.py", 1, 10, 0.5),
        CandidateChunk("c2", "b.py", 1, 10, 0.4),
        CandidateChunk("c3", "c.py", 1, 10, 0.3),
    ]
    locators = [EvidenceItem(file_path=item.file_path, line_start=1, line_end=10, score=item.score) for item in chunks]

    result, _ = _run_batch_llm_review_fix(
        repo_root=tmp_path,
        cmd="review",
        intent="review",
        query="review",
        route="DEEP",
        github_context={"changed_files": ["a.py", "b.py", "c.py"], "diff_hunks": ["@@ a"]},
        selected_chunks=chunks,
        locators=locators,
        governor=governor,
    )

    assert result["planned_batches"] == 3
    assert result["executed_batches"] == 1
    assert "batch_planner_used" in result
    assert "batch_plan_mode" in result
    assert call_counter["n"] == 1
