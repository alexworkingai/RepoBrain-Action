from __future__ import annotations

from repobrain.llm.prompts import build_messages_for_fix


def test_patch_prompt_budgeting_uses_strict_limits() -> None:
    diff_hunks = [f"@@ hunk_{idx}\n+{('x' * 1200)}" for idx in range(8)]
    selected = [f"snippet_{idx}" for idx in range(40)]

    messages, stats = build_messages_for_fix(
        query="Apply minimal fix for style and naming issues",
        changed_files=["scripts/e2e/marker_bad.py", "repobrain/github_flow.py"],
        diff_hunks=diff_hunks,
        max_input_tokens=3200,
        selected_snippets=selected,
        max_hunks=3,
    )

    assert isinstance(messages, list)
    assert len(messages) == 2
    assert int(stats["input_budget_limit"]) == 3200
    assert int(stats["input_budget_used_est"]) <= 3200
    # 8 hunks with max_hunks=3 should drop at least 5 hunks deterministically.
    assert int(stats["dropped_hunks_count"]) >= 5
    assert bool(stats["compacted"]) is True

