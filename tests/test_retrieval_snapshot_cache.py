from __future__ import annotations

from pathlib import Path

from repobrain.retrieval.snapshot_cache import (
    load_retrieval_snapshot,
    store_retrieval_snapshot,
)
from repobrain.tky_provider import CandidateChunk


def _candidate(path: str, idx: int) -> CandidateChunk:
    return CandidateChunk(
        chunk_id=f"{path}:{idx}",
        file_path=path,
        line_start=idx * 10 + 1,
        line_end=idx * 10 + 9,
        score=0.5,
        text=f"chunk {path}:{idx}",
        signature=[idx + 1, idx + 7],
    )


def _context(*, head_sha: str) -> dict[str, object]:
    return {
        "is_pr": True,
        "pr_number": 101,
        "head_sha": head_sha,
        "base_sha": "base-1",
        "files": [
            {"filename": "docs/a.md", "status": "removed"},
            {"filename": "docs/b.md", "status": "removed"},
        ],
        "changed_files": ["docs/a.md", "docs/b.md"],
    }


def test_snapshot_cache_roundtrip_for_same_pr_state(tmp_path: Path) -> None:
    context = _context(head_sha="head-a")
    first = load_retrieval_snapshot(
        question="What changed?",
        command="ask",
        topk=8,
        github_context=context,
        repo_root=tmp_path,
    )

    assert first.cache_used is True
    assert first.cache_hit is False
    assert first.cache_miss_reason == "cache_key_miss"

    candidates = [_candidate("docs/a.md", 0), _candidate("docs/b.md", 1)]
    store_retrieval_snapshot(
        question="What changed?",
        command="ask",
        topk=8,
        github_context=context,
        repo_root=tmp_path,
        candidates=candidates,
        retrieval_runtime={"incremental_scope_mode": "changed_files_first"},
    )

    second = load_retrieval_snapshot(
        question="What changed?",
        command="ask",
        topk=8,
        github_context=context,
        repo_root=tmp_path,
    )

    assert second.cache_used is True
    assert second.cache_hit is True
    assert second.cache_miss_reason == "none"
    assert second.candidates is not None
    assert [item.file_path for item in second.candidates] == ["docs/a.md", "docs/b.md"]
    assert second.retrieval_runtime is not None
    assert second.retrieval_runtime.get("incremental_scope_mode") == "changed_files_first"
    runtime_fields = second.as_runtime_fields()
    assert runtime_fields["retrieval_snapshot_cache_key_kind"] == "pr_number_head_sha"
    assert runtime_fields["retrieval_snapshot_cache_age_s"] >= 0


def test_snapshot_cache_misses_when_pr_head_changes(tmp_path: Path) -> None:
    store_retrieval_snapshot(
        question="Review PR changes.",
        command="review",
        topk=16,
        github_context=_context(head_sha="head-a"),
        repo_root=tmp_path,
        candidates=[_candidate("docs/a.md", 0)],
        retrieval_runtime={"evidence_budget_mode": "review_default"},
    )

    changed_head = load_retrieval_snapshot(
        question="Review PR changes.",
        command="review",
        topk=16,
        github_context=_context(head_sha="head-b"),
        repo_root=tmp_path,
    )

    assert changed_head.cache_used is True
    assert changed_head.cache_hit is False
    assert changed_head.cache_miss_reason == "cache_key_miss"


def test_snapshot_cache_hits_when_only_base_sha_changes(tmp_path: Path) -> None:
    context_a = _context(head_sha="head-a")
    context_b = dict(context_a)
    context_b["base_sha"] = "base-2"

    store_retrieval_snapshot(
        question="Review PR changes.",
        command="review",
        topk=16,
        github_context=context_a,
        repo_root=tmp_path,
        candidates=[_candidate("docs/a.md", 0)],
        retrieval_runtime={"evidence_budget_mode": "review_default"},
    )

    loaded = load_retrieval_snapshot(
        question="Review PR changes.",
        command="review",
        topk=16,
        github_context=context_b,
        repo_root=tmp_path,
    )

    assert loaded.cache_used is True
    assert loaded.cache_hit is True
    assert loaded.cache_miss_reason == "none"
