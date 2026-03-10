from __future__ import annotations

from repobrain.llm.prompts import build_messages_for_review


def test_prompt_budgeting_drops_are_deterministic() -> None:
    diff_hunks = [
        f"@@ section_{i}\n+{('x' * 250)}\n-{('y' * 250)}"
        for i in range(12)
    ]
    snippets = [f"snippet_{i}: " + ("z" * 500) for i in range(10)]
    changed_files = [f"repobrain/module_{i}.py" for i in range(10)]

    messages_a, stats_a = build_messages_for_review(
        query="Review these changes deeply",
        changed_files=changed_files,
        diff_hunks=diff_hunks,
        selected_snippets=snippets,
        max_input_tokens=450,
    )
    messages_b, stats_b = build_messages_for_review(
        query="Review these changes deeply",
        changed_files=changed_files,
        diff_hunks=diff_hunks,
        selected_snippets=snippets,
        max_input_tokens=450,
    )

    assert stats_a == stats_b
    assert stats_a["input_budget_used_est"] <= stats_a["input_budget_limit"]
    assert stats_a["dropped_hunks_count"] > 0 or stats_a["dropped_snippets_count"] > 0

    user_content = messages_a[1]["content"]
    assert "section_0" in user_content
