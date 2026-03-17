from __future__ import annotations

from repobrain.retrieval.hybrid_ranker import rerank_candidates
from repobrain.tky_provider import CandidateChunk


def _candidate(path: str, score: float, idx: int) -> CandidateChunk:
    return CandidateChunk(
        chunk_id=f"chunk-{idx}",
        file_path=path,
        line_start=1,
        line_end=20,
        score=score,
        text=None,
    )


def test_hybrid_rerank_prefers_query_and_pr_context() -> None:
    candidates = [
        _candidate("docs/security.md", 0.82, 1),
        _candidate("repobrain/github_flow.py", 0.73, 2),
        _candidate("repobrain/review_validator.py", 0.71, 3),
    ]

    result = rerank_candidates(
        candidates,
        query_context={
            "question": "how github flow routes review command",
            "command": "ask",
            "changed_files": ["repobrain/github_flow.py"],
        },
    )

    assert result.hybrid_rerank_used is True
    assert result.retrieval_ranking_mode == "hybrid_postrank"
    assert result.candidates[0].file_path == "repobrain/github_flow.py"


def test_hybrid_rerank_fallback_for_single_candidate() -> None:
    result = rerank_candidates(
        [_candidate("repobrain/config.py", 0.5, 1)],
        query_context={"question": "config", "command": "ask"},
    )

    assert result.hybrid_rerank_used is False
    assert result.retrieval_ranking_mode == "fallback_lexical"
    assert result.reason_codes == ["single_candidate"]
