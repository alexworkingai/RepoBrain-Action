from __future__ import annotations

from pathlib import Path

from repobrain.evidence import EvidenceItem
from repobrain.github_flow import _run_batch_llm_review_fix
from repobrain.tky_provider import CandidateChunk


def test_batch_force_enables_batch_and_min_batches(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("RB_LLM_BATCH_ENABLE", "1")
    monkeypatch.setenv("RB_LLM_BATCH_FORCE", "1")
    monkeypatch.setenv("RB_LLM_BATCH_MAX_CALLS_PER_RUN", "4")
    monkeypatch.setenv("RB_LLM_BATCH_REDUCE_ENABLE", "0")
    monkeypatch.setenv("RB_LLM_MAX_INPUT_TOKENS", "1200")

    call_counter = {"n": 0}

    def fake_llm_call(*args, **kwargs):  # noqa: ANN002, ANN003
        call_counter["n"] += 1
        idx = call_counter["n"]
        text = f"- batch finding {idx}"
        meta = {
            "llm_used": True,
            "llm_skip_reason": "n/a",
            "llm_model_used": "openai/gpt-4.1-mini",
            "llm_tier": "low",
            "llm_tokens_prompt": 80,
            "llm_tokens_completion": 30,
            "llm_tokens_total": 110,
            "llm_usage_estimated": False,
            "llm_remaining_requests": 20 - idx,
            "llm_remaining_is_estimate": False,
            "llm_reset_time_utc_iso": "2026-03-05T23:59:59+00:00",
            "llm_requests_remaining": 20 - idx,
            "llm_rate_limit_reset": "2026-03-05T23:59:59+00:00",
            "llm_reason": "ok",
            "llm_complexity_score": 40,
            "llm_complexity_explanation": "forced-batch-test",
            "llm_calls_this_run": 1,
            "llm_max_output_tokens_used": 800,
            "llm_input_budget_limit": 1200,
            "llm_input_budget_used_est": 500,
            "llm_dropped_locators_count": 0,
            "llm_dropped_hunks_count": 0,
            "llm_dropped_snippets_count": 0,
            "llm_ratelimit_headers": {},
            "llm_calls": [
                {
                    "batch_id": f"batch-{idx}",
                    "model_id": "openai/gpt-4.1-mini",
                    "tier": "low",
                    "tokens_prompt": 80,
                    "tokens_completion": 30,
                    "tokens_total": 110,
                    "remaining_requests": 20 - idx,
                    "remaining_is_estimate": False,
                    "reset_time_utc_iso": "2026-03-05T23:59:59+00:00",
                    "estimate_flags": {"usage_estimated": False, "remaining_estimated": False},
                }
            ],
            "llm_model_counts": {"openai/gpt-4.1-mini": 1},
        }
        return text, meta

    monkeypatch.setattr("repobrain.github_flow._maybe_generate_llm_text", fake_llm_call)

    chunks = [
        CandidateChunk(
            chunk_id="c1",
            file_path="repobrain/review.py",
            line_start=1,
            line_end=20,
            score=0.5,
        )
    ]
    locators = [EvidenceItem(file_path="repobrain/review.py", line_start=1, line_end=20, score=0.5)]
    context = {
        "changed_files": ["repobrain/review.py"],
        "diff_hunks": [],
    }

    result, llm_meta = _run_batch_llm_review_fix(
        repo_root=tmp_path,
        cmd="review",
        intent="review",
        query="Review this PR",
        route="FAST",
        github_context=context,
        selected_chunks=chunks,
        locators=locators,
    )

    assert result["batch_used"] is True
    assert int(result["planned_batches"]) >= 2
    assert int(result["executed_batches"]) >= 2
    assert int(llm_meta["llm_calls_this_run"]) >= 2
