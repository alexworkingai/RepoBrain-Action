from __future__ import annotations

from repobrain.retrieval.evidence_budget_planner import plan_evidence_budget
from repobrain.tky_provider import CandidateChunk


def _chunk(path: str, idx: int, *, score: float = 0.8) -> CandidateChunk:
    return CandidateChunk(
        chunk_id=f"{path}:{idx}",
        file_path=path,
        line_start=idx * 10 + 1,
        line_end=idx * 10 + 8,
        score=score,
        text=None,
    )


def test_budget_planner_is_command_aware() -> None:
    candidates = [_chunk(f"src/module_{idx}.py", idx) for idx in range(40)]
    context = {"changed_files": [f"src/module_{idx}.py" for idx in range(12)]}

    ask_plan = plan_evidence_budget(
        candidates,
        command="ask",
        github_context=context,
        limit_hint=30,
        incremental_scope_mode="changed_files_first",
    )
    review_plan = plan_evidence_budget(
        candidates,
        command="review",
        github_context=context,
        limit_hint=30,
        incremental_scope_mode="changed_files_first",
    )
    fix_plan = plan_evidence_budget(
        candidates,
        command="fix",
        github_context=context,
        limit_hint=30,
        incremental_scope_mode="changed_files_first",
    )

    assert ask_plan.evidence_budget_limit < review_plan.evidence_budget_limit
    assert fix_plan.evidence_budget_mode.startswith("fix_localized_strict")
    assert review_plan.evidence_budget_mode.startswith("review_risk_weighted")


def test_budget_planner_prioritizes_changed_primary_before_docs_noise() -> None:
    candidates = [
        _chunk("docs/security.md", 0),
        _chunk("docs/ops.md", 1),
        _chunk("src/auth.py", 2),
        _chunk("src/payment.py", 3),
        _chunk("README.md", 4),
    ]
    plan = plan_evidence_budget(
        candidates,
        command="ask",
        github_context={"changed_files": ["src/auth.py", "src/payment.py"]},
        limit_hint=3,
        incremental_scope_mode="changed_regions_first",
    )

    selected_paths = [item.file_path for item in plan.candidates]
    assert "src/auth.py" in selected_paths
    assert "src/payment.py" in selected_paths
    assert plan.evidence_budget_primary_selected >= 2
    assert {"dropped_docs", "cut_docs"} & set(plan.evidence_budget_cutoffs)


def test_budget_planner_applies_early_cutoff_to_low_priority_spillover() -> None:
    candidates = [
        _chunk("src/core.py", 0),
        _chunk("src/router.py", 1),
        _chunk("src/handlers.py", 2),
        _chunk("docs/guide.md", 3),
        _chunk("tests/test_core.py", 4),
        _chunk("examples/demo.py", 5),
        _chunk(".github/workflows/ci.yml", 6),
        _chunk("docs/faq.md", 7),
    ]
    plan = plan_evidence_budget(
        candidates,
        command="fix",
        github_context={"changed_files": ["src/core.py", "src/router.py", "src/handlers.py"]},
        limit_hint=4,
        incremental_scope_mode="fallback_full",
    )

    assert plan.evidence_budget_used <= plan.evidence_budget_limit
    assert plan.evidence_budget_overflow > 0
    assert "budget_exhausted" in plan.evidence_budget_cutoffs
    assert plan.evidence_budget_primary_selected >= 2


def test_budget_planner_is_deterministic() -> None:
    candidates = [_chunk("src/a.py", 0), _chunk("src/b.py", 1), _chunk("docs/notes.md", 2)]
    context = {"changed_files": ["src/a.py"]}

    first = plan_evidence_budget(
        candidates,
        command="review",
        github_context=context,
        limit_hint=6,
        incremental_scope_mode="fallback_full",
    )
    second = plan_evidence_budget(
        candidates,
        command="review",
        github_context=context,
        limit_hint=6,
        incremental_scope_mode="fallback_full",
    )

    assert [item.chunk_id for item in first.candidates] == [item.chunk_id for item in second.candidates]
    assert first.evidence_budget_mode == second.evidence_budget_mode
    assert first.evidence_budget_bucket_counts == second.evidence_budget_bucket_counts
    assert first.evidence_budget_cutoffs == second.evidence_budget_cutoffs


def test_budget_planner_can_consume_segment_hints() -> None:
    candidates = [
        _chunk("repobrain/github_flow.py", 0),
        _chunk("repobrain/output_md.py", 1),
        _chunk("tests/test_cli.py", 2),
        _chunk("docs/e2e.md", 3),
    ]
    plan = plan_evidence_budget(
        candidates,
        command="review",
        github_context={"changed_files": ["repobrain/github_flow.py"]},
        limit_hint=8,
        incremental_scope_mode="changed_files_first",
        segment_hints={
            "file_segment_class_map": {
                "repobrain/github_flow.py": "core_code",
                "repobrain/output_md.py": "core_code",
                "tests/test_cli.py": "tests",
                "docs/e2e.md": "docs",
            }
        },
    )

    assert plan.evidence_budget_used > 0
    assert plan.evidence_budget_bucket_counts["changed_primary"] >= 1
    assert plan.evidence_budget_bucket_counts["tests"] >= 1
    assert plan.evidence_budget_bucket_counts["docs"] >= 1
