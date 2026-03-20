from __future__ import annotations

from pathlib import Path

from repobrain.github_flow import _retrieve_candidates_with_runtime
from repobrain.tky_provider import CandidateChunk


def _chunk(path: str, idx: int) -> CandidateChunk:
    return CandidateChunk(
        chunk_id=f"{path}:{idx}",
        file_path=path,
        line_start=idx * 10 + 1,
        line_end=idx * 10 + 5,
        score=0.1,
        text=f"content {path} {idx}",
        signature=[idx + 3, idx + 9],
    )


def test_retrieve_runtime_exposes_incremental_fields(tmp_path: Path) -> None:
    chunks = [
        _chunk("src/a.py", 0),
        _chunk("src/a.py", 1),
        _chunk("src/b.py", 2),
    ]
    candidates, runtime = _retrieve_candidates_with_runtime(
        "src a",
        chunks,
        topk=5,
        cmd="ask",
        github_context={"changed_files": ["src/a.py"], "diff_hunks": ["@@"]},
        repo_root=tmp_path,
    )

    assert candidates
    assert "incremental_retrieval_used" in runtime
    assert "incremental_scope_mode" in runtime
    assert "changed_files_considered" in runtime
    assert "unchanged_files_skipped" in runtime
    assert "retrieval_cache_hits" in runtime
    assert "retrieval_cache_misses" in runtime
    assert "incremental_fallback_reason" in runtime
    assert "evidence_budget_used" in runtime
    assert "evidence_budget_limit" in runtime
    assert "evidence_budget_mode" in runtime
    assert "evidence_budget_bucket_counts" in runtime
    assert "evidence_budget_cutoffs" in runtime
    assert "evidence_budget_overflow" in runtime
    assert "evidence_budget_primary_selected" in runtime
    assert "evidence_budget_support_selected" in runtime
    assert "retrieval_snapshot_cache_used" in runtime
    assert "retrieval_snapshot_cache_hit" in runtime
    assert "retrieval_snapshot_cache_key_kind" in runtime
    assert "retrieval_snapshot_cache_miss_reason" in runtime
    assert "retrieval_snapshot_cache_age_s" in runtime


def test_retrieve_runtime_snapshot_cache_hit_on_repeat_pr_state(tmp_path: Path) -> None:
    chunks = [
        _chunk("src/a.py", 0),
        _chunk("src/a.py", 1),
        _chunk("src/b.py", 2),
    ]
    github_context = {
        "is_pr": True,
        "pr_number": 12,
        "head_sha": "head-a",
        "base_sha": "base-a",
        "files": [
            {"filename": "src/a.py", "status": "modified"},
            {"filename": "src/b.py", "status": "modified"},
        ],
        "changed_files": ["src/a.py", "src/b.py"],
        "diff_hunks": ["@@"],
    }

    _, first_runtime = _retrieve_candidates_with_runtime(
        "src a",
        chunks,
        topk=5,
        cmd="ask",
        github_context=github_context,
        repo_root=tmp_path,
    )
    _, second_runtime = _retrieve_candidates_with_runtime(
        "src a",
        chunks,
        topk=5,
        cmd="ask",
        github_context=github_context,
        repo_root=tmp_path,
    )

    assert first_runtime["retrieval_snapshot_cache_used"] is True
    assert first_runtime["retrieval_snapshot_cache_hit"] is False
    assert second_runtime["retrieval_snapshot_cache_used"] is True
    assert second_runtime["retrieval_snapshot_cache_hit"] is True
    assert second_runtime["retrieval_snapshot_cache_miss_reason"] == "none"
    assert second_runtime["retrieval_snapshot_cache_age_s"] >= 0


def test_retrieve_runtime_snapshot_cache_miss_when_pr_state_changes(tmp_path: Path) -> None:
    chunks = [
        _chunk("src/a.py", 0),
        _chunk("src/a.py", 1),
    ]
    context_a = {
        "is_pr": True,
        "pr_number": 44,
        "head_sha": "head-a",
        "base_sha": "base",
        "files": [{"filename": "src/a.py", "status": "modified"}],
        "changed_files": ["src/a.py"],
    }
    context_b = dict(context_a)
    context_b["head_sha"] = "head-b"

    _retrieve_candidates_with_runtime(
        "src a",
        chunks,
        topk=3,
        cmd="ask",
        github_context=context_a,
        repo_root=tmp_path,
    )
    _, changed_runtime = _retrieve_candidates_with_runtime(
        "src a",
        chunks,
        topk=3,
        cmd="ask",
        github_context=context_b,
        repo_root=tmp_path,
    )

    assert changed_runtime["retrieval_snapshot_cache_used"] is True
    assert changed_runtime["retrieval_snapshot_cache_hit"] is False
    assert changed_runtime["retrieval_snapshot_cache_miss_reason"] == "cache_key_miss"
