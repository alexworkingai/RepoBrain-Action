from __future__ import annotations

from repobrain.github_flow import _build_llm_usage_payload


def test_llm_usage_payload_tracks_multi_call_totals() -> None:
    llm_meta = {
        "llm_used": True,
        "llm_skip_reason": "n/a",
        "llm_model_used": "openai/gpt-4.1",
        "llm_tier": "high",
        "llm_tokens_prompt": 300,
        "llm_tokens_completion": 120,
        "llm_tokens_total": 420,
        "llm_usage_estimated": False,
        "llm_remaining_requests": 12,
        "llm_remaining_is_estimate": False,
        "llm_reset_time_utc_iso": "2026-03-05T23:59:59+00:00",
        "llm_calls_this_run": 3,
        "llm_calls": [
            {
                "batch_id": "a",
                "model_id": "openai/gpt-4.1",
                "tier": "high",
                "tokens_prompt": 100,
                "tokens_completion": 40,
                "tokens_total": 140,
                "remaining_requests": 14,
                "remaining_is_estimate": False,
                "reset_time_utc_iso": "2026-03-05T23:59:59+00:00",
                "estimate_flags": {"usage_estimated": False, "remaining_estimated": False},
            },
            {
                "batch_id": "b",
                "model_id": "openai/gpt-4.1-mini",
                "tier": "low",
                "tokens_prompt": 80,
                "tokens_completion": 30,
                "tokens_total": 110,
                "remaining_requests": 13,
                "remaining_is_estimate": True,
                "reset_time_utc_iso": None,
                "estimate_flags": {"usage_estimated": True, "remaining_estimated": True},
            },
            {
                "batch_id": "reduce",
                "model_id": "openai/gpt-4.1",
                "tier": "high",
                "tokens_prompt": 120,
                "tokens_completion": 50,
                "tokens_total": 170,
                "remaining_requests": 12,
                "remaining_is_estimate": False,
                "reset_time_utc_iso": "2026-03-05T23:59:59+00:00",
                "estimate_flags": {"usage_estimated": False, "remaining_estimated": False},
            },
        ],
        "llm_ratelimit_headers": {},
    }

    payload = _build_llm_usage_payload(llm_meta)

    assert payload["totals"]["calls_count"] == 3
    assert payload["totals"]["tokens_prompt_total"] == 300
    assert payload["totals"]["tokens_completion_total"] == 120
    assert payload["totals"]["tokens_total_total"] == 420
    assert payload["final_remaining_requests"] == 12
    assert payload["final_reset_time_utc_iso"] == "2026-03-05T23:59:59+00:00"
