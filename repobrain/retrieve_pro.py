from __future__ import annotations

import re
from typing import Iterable

from .signatures import build_chunk_signature, hash_token32
from .tky_provider import CandidateChunk

TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)
IDENT_SPLIT_RE = re.compile(r"[\/.\-_]+")
CAMEL_RE = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+")

STOP_WORDS = {
    # EN
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "what",
    "where",
    "with",
    "why",
    # RU
    "а",
    "в",
    "во",
    "где",
    "для",
    "и",
    "из",
    "как",
    "к",
    "ли",
    "на",
    "но",
    "о",
    "по",
    "с",
    "со",
    "у",
    "что",
    "это",
    "эта",
    "этот",
}

_WORKFLOW_QUERY_TOKENS = {
    "workflow",
    "workflows",
    "config",
    "configuration",
    "configure",
    "configured",
    "github",
    "action",
    "actions",
    "pipeline",
    "pipelines",
    "repobrain",
}
_TOPOCORE_INTENT_TOKENS = {
    "topocore",
    "tkya",
    "dependency",
    "dependencies",
    "backend",
    "v6",
}


def _dedupe_keep_order(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))


def extract_query_terms(text: str) -> list[str]:
    """Extract RU/EN query terms including CamelCase and snake_case subparts."""
    raw_tokens = TOKEN_RE.findall(text or "")
    terms: list[str] = []

    for raw in raw_tokens:
        token = raw.lower()
        if token and token not in STOP_WORDS:
            terms.append(token)

        if "_" in raw:
            snake = raw.lower()
            if snake not in STOP_WORDS:
                terms.append(snake)
            parts = [part for part in snake.split("_") if part and part not in STOP_WORDS]
            terms.extend(parts)
            collapsed = "".join(parts)
            if collapsed and collapsed not in STOP_WORDS:
                terms.append(collapsed)

        camel_parts = [part.lower() for part in CAMEL_RE.findall(raw) if part]
        terms.extend(part for part in camel_parts if part not in STOP_WORDS)

    return _dedupe_keep_order(term for term in terms if term)


def _chunk_signature(chunk: CandidateChunk) -> list[int]:
    if chunk.signature:
        return chunk.signature
    return build_chunk_signature(
        file_path=chunk.file_path,
        chunk_id=chunk.chunk_id,
        text=chunk.text,
        include_text=chunk.text is not None,
    )


def _path_terms(file_path: str) -> list[str]:
    parts = [part for part in IDENT_SPLIT_RE.split((file_path or "").lower()) if part]
    terms = list(parts)
    for part in parts:
        if "_" in part:
            bits = [bit for bit in part.split("_") if bit]
            terms.extend(bits)
            collapsed = "".join(bits)
            if collapsed:
                terms.append(collapsed)
    return _dedupe_keep_order(term for term in terms if term and term not in STOP_WORDS)


def _has_query_token(query_terms: list[str], allowed: set[str]) -> bool:
    return any(term in allowed for term in query_terms)


def _jaccard(a: set[int], b: set[int]) -> float:
    if not a or not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _exact_boost(query_terms: list[str], chunk: CandidateChunk) -> float:
    haystack = f"{chunk.file_path} {chunk.chunk_id}".lower()
    hits = 0
    for term in query_terms:
        if len(term) < 3:
            continue
        if term in haystack:
            hits += 1
    if hits <= 0:
        return 0.0
    return min(0.15, 0.05 + 0.02 * (hits - 1))


def score_chunk_pro(question: str, chunk: CandidateChunk) -> float:
    """Hybrid retrieval score: signature overlap + path overlap + exact hits + priors."""
    query_terms = extract_query_terms(question)
    query_sig = {hash_token32(term) for term in query_terms}
    chunk_sig = set(_chunk_signature(chunk))
    path_sig = {hash_token32(term) for term in _path_terms(chunk.file_path)}

    base_overlap = _jaccard(query_sig, chunk_sig)
    path_overlap = _jaccard(query_sig, path_sig)
    exact_hits = _exact_boost(query_terms, chunk)

    priors = 0.0
    path_lower = chunk.file_path.lower()
    workflow_intent = _has_query_token(query_terms, _WORKFLOW_QUERY_TOKENS)
    topocore_intent = _has_query_token(query_terms, _TOPOCORE_INTENT_TOKENS)
    if path_lower.startswith(("repobrain/", "src/")):
        priors += 0.02
    elif path_lower.startswith("tests/"):
        priors -= 0.01
    if workflow_intent and path_lower.startswith(".github/workflows/"):
        priors += 0.12
    elif workflow_intent and path_lower.startswith(".github/"):
        priors += 0.05
    if path_lower.startswith(".topocore-v6/") and not topocore_intent:
        priors -= 0.10

    score = 0.70 * base_overlap + 0.25 * path_overlap + exact_hits + priors
    return max(0.0, min(1.0, score))


def group_by_file(candidates: list[CandidateChunk]) -> dict[str, list[CandidateChunk]]:
    grouped: dict[str, list[CandidateChunk]] = {}
    for candidate in candidates:
        grouped.setdefault(candidate.file_path, []).append(candidate)
    return grouped


def retrieve_topk_pro(
    question: str,
    chunks: list[CandidateChunk],
    topk: int = 30,
    *,
    task_type: str = "ask",
    max_per_file: int = 2,
) -> list[CandidateChunk]:
    """Return top-k retrieval candidates with file-level diversity control."""
    scored: list[CandidateChunk] = []
    for chunk in chunks:
        chunk_score = score_chunk_pro(question, chunk)
        scored.append(
            CandidateChunk(
                chunk_id=chunk.chunk_id,
                file_path=chunk.file_path,
                line_start=chunk.line_start,
                line_end=chunk.line_end,
                score=chunk_score,
                text=chunk.text,
                signature=chunk.signature,
                score_local=chunk_score,
                score_vec=None,
            )
        )

    scored.sort(key=lambda c: (-c.score, c.file_path, c.line_start, c.line_end))
    per_file_limit = max(1, max_per_file)
    max_files = 5 if task_type == "locate" else None
    if task_type in {"locate", "explain"}:
        per_file_limit = 1

    result: list[CandidateChunk] = []
    per_file_counts: dict[str, int] = {}
    unique_files: set[str] = set()
    for candidate in scored:
        if len(result) >= max(topk, 0):
            break
        file_count = per_file_counts.get(candidate.file_path, 0)
        if file_count >= per_file_limit:
            continue
        if max_files is not None and candidate.file_path not in unique_files and len(unique_files) >= max_files:
            continue
        result.append(candidate)
        per_file_counts[candidate.file_path] = file_count + 1
        unique_files.add(candidate.file_path)

    return result
