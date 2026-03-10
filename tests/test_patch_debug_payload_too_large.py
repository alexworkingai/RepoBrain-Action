from __future__ import annotations

from repobrain.github_flow import _build_llm_http_debug_payload


def test_patch_http_debug_includes_payload_compaction_fields() -> None:
    payload = _build_llm_http_debug_payload(
        llm_meta={
            "llm_primary_model_id": "openai/gpt-4.1",
            "llm_effective_model_id": "openai/gpt-4.1-mini",
            "llm_fallback_used": True,
            "llm_primary_status": 413,
            "llm_fallback_status": 413,
            "llm_provider_http_status": 413,
            "llm_provider_error_type": "payload_too_large",
            "llm_error_types": ["payload_too_large"],
            "llm_skip_reason": "LLM_NOT_AVAILABLE:payload_too_large",
            "llm_input_budget_used_est": 3888,
            "llm_max_output_tokens_used": 900,
            "llm_patch_batch_mode": True,
            "llm_patch_batch_count": 4,
            "llm_compacted": True,
            "llm_dropped_locators_count": 12,
            "llm_dropped_hunks_count": 7,
            "llm_dropped_snippets_count": 8,
            "llm_attempted_compaction": True,
            "llm_attempted_patch_batch": True,
        },
        decision_route="FAST",
    )

    assert payload["provider_http_status"] == 413
    assert payload["provider_error_type"] == "payload_too_large"
    assert payload["estimated_input_tokens"] == 3888
    assert payload["max_output_tokens_used"] == 900
    assert payload["patch_batch_mode"] is True
    assert payload["patch_batch_count"] == 4
    assert payload["compacted"] is True
    assert payload["attempted_compaction"] is True
    assert payload["attempted_patch_batch"] is True

