from __future__ import annotations

from repobrain.github_flow import _review_context_needs_batch
from repobrain.llm.prompts import build_messages_for_review
from repobrain.config import RepoBrainConfig


def test_build_messages_for_review_applies_hierarchical_compaction() -> None:
    changed_files = [f"src/module_{idx}/file_{idx}.py" for idx in range(80)]
    diff_hunks = [f"@@ -{idx},4 +{idx},6 @@\n+{'x' * 800}" for idx in range(40)]
    selected = [f"signal_{idx}" for idx in range(60)]

    messages, stats = build_messages_for_review(
        query="Review PR for risk and rollout impact",
        changed_files=changed_files,
        diff_hunks=diff_hunks,
        max_input_tokens=2200,
        selected_snippets=selected,
        max_files_context=20,
        max_findings_context=10,
        max_hunks_context=8,
    )

    assert len(messages) == 2
    assert bool(stats["review_compacted"]) is True
    assert int(stats["review_files_included"]) <= 20
    assert int(stats["review_hunks_included"]) <= 8
    assert int(stats["review_findings_included"]) <= 10
    assert int(stats["dropped_files_count"]) > 0
    assert int(stats["dropped_hunks_count"]) > 0
    assert int(stats["dropped_findings_count"]) > 0
    assert int(stats["input_budget_used_est"]) <= 2200


def test_review_context_needs_batch_when_counts_or_budget_exceed_limits(monkeypatch) -> None:
    monkeypatch.setenv("RB_LLM_MAX_INPUT_TOKENS_REVIEW_FINAL", "3000")
    monkeypatch.setenv("RB_LLM_MAX_FILES_REVIEW_CONTEXT", "30")
    monkeypatch.setenv("RB_LLM_MAX_HUNKS_REVIEW_CONTEXT", "20")
    cfg = RepoBrainConfig.from_env()

    assert _review_context_needs_batch(
        cfg=cfg,
        changed_files_count=31,
        diff_hunks_count=8,
        estimated_input_tokens=1800,
    )
    assert _review_context_needs_batch(
        cfg=cfg,
        changed_files_count=12,
        diff_hunks_count=22,
        estimated_input_tokens=1800,
    )
    assert _review_context_needs_batch(
        cfg=cfg,
        changed_files_count=12,
        diff_hunks_count=8,
        estimated_input_tokens=3400,
    )
