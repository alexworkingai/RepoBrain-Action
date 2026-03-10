from __future__ import annotations

from repobrain.github_flow import (
    _should_retry_patch_batch_after_single_call,
    _should_use_batch_mode_for_review,
)


def test_large_patch_payload_enables_patch_batching(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_PATCH_BATCH_ENABLE", "1")
    monkeypatch.setenv("RB_LLM_PATCH_BATCH_FORCE", "0")
    monkeypatch.setenv("RB_LLM_PATCH_MAX_HUNKS_PER_CALL", "4")
    monkeypatch.setenv("RB_LLM_MAX_INPUT_TOKENS_PATCH", "3200")

    enabled = _should_use_batch_mode_for_review(
        cmd="fix",
        route="FAST",
        complexity_score=20,
        changed_files_count=1,
        diff_hunks_count=9,
        estimated_patch_input_tokens=4100,
    )

    assert enabled is True


def test_single_patch_413_retries_in_batch_mode(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_PATCH_BATCH_ENABLE", "1")
    should_retry = _should_retry_patch_batch_after_single_call(
        cmd="fix",
        llm_meta={"llm_provider_http_status": 413},
    )
    assert should_retry is True

    should_not_retry = _should_retry_patch_batch_after_single_call(
        cmd="fix",
        llm_meta={"llm_provider_http_status": 500},
    )
    assert should_not_retry is False

