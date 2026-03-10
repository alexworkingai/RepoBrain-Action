from __future__ import annotations

from repobrain.retrieval.hybrid import rank_hybrid_candidates
from repobrain.tky_provider import CandidateChunk


def test_hybrid_ranking_prefers_strong_match() -> None:
    chunks = [
        CandidateChunk(
            chunk_id="c1",
            file_path="repobrain/tky_provider.py",
            line_start=1,
            line_end=20,
            score=0.0,
            signature=[1, 2, 3],
        ),
        CandidateChunk(
            chunk_id="c2",
            file_path="README.md",
            line_start=1,
            line_end=20,
            score=0.0,
            signature=[7, 8, 9],
        ),
        CandidateChunk(
            chunk_id="c3",
            file_path="repobrain/github_flow.py",
            line_start=1,
            line_end=30,
            score=0.0,
            signature=[10, 11, 12],
        ),
    ]
    vectors = {
        "c1": [1.0, 0.0, 0.0],
        "c2": [0.3, 0.3, 0.3],
        "c3": [0.0, 1.0, 0.0],
    }
    query = [1.0, 0.0, 0.0]

    result = rank_hybrid_candidates(
        question="Where is TKYProvider logic?",
        chunks=chunks,
        topk=3,
        task_type="ask",
        chunk_vectors_by_id=vectors,
        query_vector=query,
        weight_lex=0.55,
        weight_vec=0.45,
        vector_topk=3,
        max_per_file=2,
    )

    assert result.embeddings_used is True
    assert result.reason == "ok"
    assert result.candidates
    assert result.candidates[0].file_path == "repobrain/tky_provider.py"
    assert result.candidates[0].score >= result.candidates[1].score
