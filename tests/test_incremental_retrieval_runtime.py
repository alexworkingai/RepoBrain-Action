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
