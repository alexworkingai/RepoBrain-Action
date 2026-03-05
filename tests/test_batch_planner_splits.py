from __future__ import annotations

from repobrain.llm.batch_planner import plan_batches
from repobrain.tky_provider import CandidateChunk


def test_batch_planner_splits_large_hunks_deterministically() -> None:
    chunks = [
        CandidateChunk(
            chunk_id=f"c{i}",
            file_path="repobrain/github_flow.py" if i % 2 == 0 else "repobrain/review.py",
            line_start=1,
            line_end=40,
            score=0.4,
        )
        for i in range(10)
    ]
    hunks = [f"@@ hunk_{i}\n+{('x' * 1000)}\n-{('y' * 1000)}" for i in range(12)]
    context = {
        "changed_files": ["repobrain/github_flow.py", "repobrain/review.py"],
        "diff_hunks": hunks,
    }

    batches_a = plan_batches(
        "review",
        "review",
        context,
        chunks,
        limits={"max_input_tokens": 1200},
        budgets={"max_input_tokens": 1200, "reserve_tokens": 200},
    )
    batches_b = plan_batches(
        "review",
        "review",
        context,
        chunks,
        limits={"max_input_tokens": 1200},
        budgets={"max_input_tokens": 1200, "reserve_tokens": 200},
    )

    assert len(batches_a) > 1
    assert [item.batch_id for item in batches_a] == [item.batch_id for item in batches_b]
    assert [item.paths for item in batches_a] == [item.paths for item in batches_b]
