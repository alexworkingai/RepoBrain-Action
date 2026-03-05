from __future__ import annotations

from pathlib import Path

from repobrain.evidence import EvidenceItem
from repobrain.github_flow import _run_batch_llm_review_fix
from repobrain.tky_provider import CandidateChunk


def test_batch_execution_uses_reduce_and_aggregates(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("RB_LLM_ENABLED", "1")
    monkeypatch.setenv("RB_LLM_PROVIDER", "github_models")
    monkeypatch.setenv("RB_LLM_BATCH_REDUCE_ENABLE", "1")
    monkeypatch.setenv("RB_LLM_BATCH_MAX_CALLS_PER_RUN", "4")
    monkeypatch.setenv("RB_LLM_MAX_INPUT_TOKENS", "1200")

    call_counter = {"n": 0}

    def fake_llm_call(*args, **kwargs):  # noqa: ANN002, ANN003
        call_counter["n"] += 1
        is_reduce = kwargs.get("prebuilt_messages") is not None
        if is_reduce:
            text = "Reduced executive summary"
            batch_id = "reduce"
            model = "openai/gpt-4.1"
        else:
            text = f"- finding from map call {call_counter['n']}"
            batch_id = f"map-{call_counter['n']}"
            model = "openai/gpt-4.1-mini"
        meta = {
            "llm_used": True,
            "llm_skip_reason": "n/a",
            "llm_model_used": model,
            "llm_tier": "high" if "mini" not in model else "low",
            "llm_tokens_prompt": 100,
            "llm_tokens_completion": 40,
            "llm_tokens_total": 140,
            "llm_usage_estimated": False,
            "llm_remaining_requests": 20 - call_counter["n"],
            "llm_remaining_is_estimate": False,
            "llm_reset_time_utc_iso": "2026-03-05T23:59:59+00:00",
            "llm_requests_remaining": 20 - call_counter["n"],
            "llm_rate_limit_reset": "2026-03-05T23:59:59+00:00",
            "llm_reason": "ok",
            "llm_complexity_score": 70,
            "llm_complexity_explanation": "test",
            "llm_calls_this_run": 1,
            "llm_max_output_tokens_used": 1000,
            "llm_input_budget_limit": 7600,
            "llm_input_budget_used_est": 900,
            "llm_dropped_locators_count": 0,
            "llm_dropped_hunks_count": 0,
            "llm_dropped_snippets_count": 0,
            "llm_ratelimit_headers": {},
            "llm_calls": [
                {
                    "batch_id": batch_id,
                    "model_id": model,
                    "tier": "high" if "mini" not in model else "low",
                    "tokens_prompt": 100,
                    "tokens_completion": 40,
                    "tokens_total": 140,
                    "remaining_requests": 20 - call_counter["n"],
                    "remaining_is_estimate": False,
                    "reset_time_utc_iso": "2026-03-05T23:59:59+00:00",
                    "estimate_flags": {"usage_estimated": False, "remaining_estimated": False},
                }
            ],
            "llm_model_counts": {model: 1},
        }
        return text, meta

    monkeypatch.setattr("repobrain.github_flow._maybe_generate_llm_text", fake_llm_call)

    chunks = [
        CandidateChunk(
            chunk_id=f"c{i}",
            file_path="repobrain/github_flow.py" if i % 2 == 0 else "repobrain/review.py",
            line_start=1,
            line_end=40,
            score=0.5,
        )
        for i in range(6)
    ]
    locators = [
        EvidenceItem(file_path=item.file_path, line_start=item.line_start, line_end=item.line_end, score=item.score)
        for item in chunks
    ]
    context = {
        "changed_files": ["repobrain/github_flow.py", "repobrain/review.py"],
        "diff_hunks": [f"@@ hunk_{i}\n+{('x' * 900)}" for i in range(4)],
    }

    result, llm_meta = _run_batch_llm_review_fix(
        repo_root=tmp_path,
        cmd="review",
        intent="review",
        query="Review this PR",
        route="DEEP",
        github_context=context,
        selected_chunks=chunks,
        locators=locators,
    )

    assert result["batch_used"] is True
    assert result["executed_batches"] >= 1
    assert "Reduced executive summary" in result["summary_text"]
    assert llm_meta["llm_used"] is True
    assert llm_meta["llm_calls_this_run"] >= 2
