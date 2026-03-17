from __future__ import annotations

from pathlib import Path

from repobrain.retrieval.incremental_index import scope_chunks_incremental
from repobrain.tky_provider import CandidateChunk


def _chunk(path: str, idx: int) -> CandidateChunk:
    return CandidateChunk(
        chunk_id=f"{path}:{idx}",
        file_path=path,
        line_start=idx * 10 + 1,
        line_end=idx * 10 + 5,
        score=0.1,
        text=f"content {path} {idx}",
        signature=[idx + 1, idx + 11],
    )


def _chunks() -> list[CandidateChunk]:
    return [
        _chunk("src/a.py", 0),
        _chunk("src/a.py", 1),
        _chunk("src/b.py", 2),
        _chunk("docs/readme.md", 3),
    ]


def test_incremental_scope_uses_changed_files_first(tmp_path: Path) -> None:
    result = scope_chunks_incremental(
        question="update src a module",
        command="ask",
        chunks=_chunks(),
        github_context={"changed_files": ["src/a.py"], "diff_hunks": ["@@ -1,1 +1,1 @@"]},
        repo_root=tmp_path,
    )

    assert result.incremental_retrieval_used is True
    assert result.incremental_scope_mode == "changed_regions_first"
    assert result.changed_files_considered == 1
    assert result.unchanged_files_skipped >= 1
    paths = {chunk.file_path for chunk in result.chunks}
    assert "src/a.py" in paths
    assert "docs/readme.md" not in paths


def test_incremental_scope_falls_back_when_changed_files_missing(tmp_path: Path) -> None:
    chunks = _chunks()
    result = scope_chunks_incremental(
        question="any",
        command="ask",
        chunks=chunks,
        github_context={},
        repo_root=tmp_path,
    )

    assert result.incremental_retrieval_used is False
    assert result.incremental_scope_mode == "fallback_full"
    assert result.incremental_fallback_reason == "missing_changed_files"
    assert len(result.chunks) == len(chunks)


def test_incremental_cache_hits_and_misses_are_deterministic(tmp_path: Path) -> None:
    chunks = _chunks()
    context = {"changed_files": ["src/a.py"], "diff_hunks": []}
    first = scope_chunks_incremental(
        question="src a",
        command="ask",
        chunks=chunks,
        github_context=context,
        repo_root=tmp_path,
    )
    second = scope_chunks_incremental(
        question="src a",
        command="ask",
        chunks=chunks,
        github_context=context,
        repo_root=tmp_path,
    )

    assert first.retrieval_cache_misses > 0
    assert first.retrieval_cache_hits == 0
    assert second.retrieval_cache_hits > 0
    assert second.retrieval_cache_misses == 0


def test_incremental_scope_falls_back_when_changed_files_not_in_index(tmp_path: Path) -> None:
    chunks = _chunks()
    result = scope_chunks_incremental(
        question="missing path",
        command="ask",
        chunks=chunks,
        github_context={"changed_files": ["src/missing.py"], "diff_hunks": []},
        repo_root=tmp_path,
    )

    assert result.incremental_retrieval_used is False
    assert result.incremental_fallback_reason == "changed_files_not_indexed"
    assert len(result.chunks) == len(chunks)
