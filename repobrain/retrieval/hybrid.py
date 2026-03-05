from __future__ import annotations

from dataclasses import dataclass
import math

from repobrain.retrieve_pro import retrieve_topk_pro, score_chunk_pro
from repobrain.tky_provider import CandidateChunk


@dataclass(frozen=True)
class HybridRetrievalResult:
    candidates: list[CandidateChunk]
    embeddings_used: bool
    reason: str
    vector_topk: int


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a <= 0.0 or norm_b <= 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _minmax(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    min_v = min(values.values())
    max_v = max(values.values())
    if max_v <= min_v:
        return {key: 0.0 for key in values}
    span = max_v - min_v
    return {key: (value - min_v) / span for key, value in values.items()}


def rank_hybrid_candidates(
    *,
    question: str,
    chunks: list[CandidateChunk],
    topk: int,
    task_type: str,
    chunk_vectors_by_id: dict[str, list[float]],
    query_vector: list[float] | None,
    weight_lex: float,
    weight_vec: float,
    vector_topk: int,
    max_per_file: int = 2,
) -> HybridRetrievalResult:
    """Rank candidates by hybrid lexical+vector score, fallback lexical-only."""
    if not query_vector:
        fallback = retrieve_topk_pro(
            question,
            chunks,
            topk=topk,
            task_type=task_type,
            max_per_file=max_per_file,
        )
        return HybridRetrievalResult(
            candidates=fallback,
            embeddings_used=False,
            reason="query_vector_missing",
            vector_topk=0,
        )

    lexical_scores: dict[str, float] = {}
    vector_scores: dict[str, float] = {}
    for chunk in chunks:
        lexical_scores[chunk.chunk_id] = score_chunk_pro(question, chunk)
        vector = chunk_vectors_by_id.get(chunk.chunk_id)
        if vector:
            vector_scores[chunk.chunk_id] = _cosine_similarity(query_vector, vector)

    if not vector_scores:
        fallback = retrieve_topk_pro(
            question,
            chunks,
            topk=topk,
            task_type=task_type,
            max_per_file=max_per_file,
        )
        return HybridRetrievalResult(
            candidates=fallback,
            embeddings_used=False,
            reason="chunk_vectors_missing",
            vector_topk=0,
        )

    lex_norm = _minmax(lexical_scores)
    vec_norm = _minmax(vector_scores)
    top_vector_ids = {
        item[0]
        for item in sorted(vector_scores.items(), key=lambda kv: kv[1], reverse=True)[: max(1, int(vector_topk))]
    }

    base_candidates = retrieve_topk_pro(
        question,
        chunks,
        topk=max(topk * 2, 60),
        task_type=task_type,
        max_per_file=max_per_file,
    )
    base_ids = {item.chunk_id for item in base_candidates}
    considered_ids = base_ids | top_vector_ids

    chunk_by_id = {item.chunk_id: item for item in chunks}
    ranked: list[CandidateChunk] = []
    for chunk_id in considered_ids:
        chunk = chunk_by_id.get(chunk_id)
        if chunk is None:
            continue
        score_local = lex_norm.get(chunk_id, 0.0)
        score_vec = vec_norm.get(chunk_id, 0.0)
        hybrid = max(0.0, min(1.0, weight_lex * score_local + weight_vec * score_vec))
        ranked.append(
            CandidateChunk(
                chunk_id=chunk.chunk_id,
                file_path=chunk.file_path,
                line_start=chunk.line_start,
                line_end=chunk.line_end,
                score=hybrid,
                text=chunk.text,
                signature=chunk.signature,
                score_local=score_local,
                score_vec=score_vec,
            )
        )

    ranked.sort(key=lambda item: (-item.score, item.file_path, item.line_start, item.line_end))
    result: list[CandidateChunk] = []
    per_file: dict[str, int] = {}
    max_files = 5 if task_type == "locate" else None
    for chunk in ranked:
        if len(result) >= max(1, int(topk)):
            break
        used = per_file.get(chunk.file_path, 0)
        per_file_limit = 1 if task_type in {"locate", "explain"} else max(1, int(max_per_file))
        if used >= per_file_limit:
            continue
        if max_files is not None and chunk.file_path not in per_file and len(per_file) >= max_files:
            continue
        result.append(chunk)
        per_file[chunk.file_path] = used + 1

    return HybridRetrievalResult(
        candidates=result,
        embeddings_used=True,
        reason="ok",
        vector_topk=len(top_vector_ids),
    )
