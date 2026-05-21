from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from repobrain.retrieve_pro import extract_query_terms
from repobrain.tky_provider import CandidateChunk

_DOC_EXTENSIONS = (".md", ".rst", ".txt", ".adoc")
_LOW_SIGNAL_PATH_TOKENS = ("node_modules/", "dist/", "build/", ".min.", "package-lock.json", "pnpm-lock.yaml")
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


@dataclass(frozen=True)
class HybridRerankResult:
    candidates: list[CandidateChunk]
    hybrid_rerank_used: bool
    retrieval_ranking_mode: str
    reason_codes: list[str]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _is_docs_path(path: str) -> bool:
    lower = str(path or "").strip().lower()
    if not lower:
        return False
    if lower.startswith(("docs/", "documentation/")):
        return True
    return any(lower.endswith(ext) for ext in _DOC_EXTENSIONS)


def _contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    lowered = str(text or "").lower()
    return any(token in lowered for token in tokens)


def _has_query_token(query_terms: list[str], allowed: set[str]) -> bool:
    return any(term in allowed for term in query_terms)


def _query_term_overlap(path: str, chunk_id: str, query_terms: list[str]) -> float:
    haystack = f"{path} {chunk_id}".lower()
    hits = 0
    for term in query_terms:
        token = term.strip().lower()
        if len(token) < 3:
            continue
        if token in haystack:
            hits += 1
    if hits <= 0:
        return 0.0
    return min(1.0, 0.25 + 0.2 * hits)


def rerank_candidates(
    candidates: list[CandidateChunk],
    query_context: dict[str, Any] | None = None,
    *,
    mode: str = "auto",
) -> HybridRerankResult:
    if not candidates:
        return HybridRerankResult([], False, "fallback_lexical", ["empty_candidates"])
    if len(candidates) == 1:
        return HybridRerankResult(list(candidates), False, "fallback_lexical", ["single_candidate"])

    ctx = dict(query_context or {})
    question = str(ctx.get("question", "") or "")
    command = str(ctx.get("command", "ask") or "ask").strip().lower()
    changed_files_raw = ctx.get("changed_files", [])
    changed_files = (
        {str(item).strip() for item in changed_files_raw if str(item).strip()}
        if isinstance(changed_files_raw, list)
        else set()
    )
    query_terms = extract_query_terms(question)
    explicit_doc_request = bool(re.search(r"\b(readme|docs?|documentation)\b", question, flags=re.IGNORECASE))
    workflow_intent = _has_query_token(query_terms, _WORKFLOW_QUERY_TOKENS)
    topocore_intent = _has_query_token(query_terms, _TOPOCORE_INTENT_TOKENS)

    try:
        ranked: list[tuple[float, CandidateChunk]] = []
        reason_codes: set[str] = set()
        for candidate in candidates:
            base = _clamp(candidate.score)
            lexical = _query_term_overlap(candidate.file_path, candidate.chunk_id, query_terms)

            structural = 0.0
            hybrid_bonus = 0.0
            if changed_files and candidate.file_path in changed_files:
                structural += 0.22
                reason_codes.add("pr_path_boost")
            if workflow_intent and candidate.file_path.lower().startswith(".github/workflows/"):
                structural += 0.45
                hybrid_bonus += 0.12
                reason_codes.add("workflow_query_boost")
            elif workflow_intent and candidate.file_path.lower().startswith(".github/"):
                structural += 0.12
                reason_codes.add("github_config_boost")
            if workflow_intent and _is_docs_path(candidate.file_path) and not explicit_doc_request:
                structural -= 0.08
                reason_codes.add("workflow_query_docs_penalty")
            if candidate.score_local is not None:
                structural += 0.06 * _clamp(candidate.score_local)
            if candidate.score_vec is not None:
                structural += 0.06 * _clamp(candidate.score_vec)
            if candidate.file_path.lower().startswith(".topocore-v6/") and not topocore_intent:
                structural -= 0.16
                reason_codes.add("private_dependency_penalty")
            if _contains_any(candidate.file_path, _LOW_SIGNAL_PATH_TOKENS):
                structural -= 0.10
                reason_codes.add("low_signal_path_penalty")
            if command in {"review", "fix"} and _is_docs_path(candidate.file_path) and not explicit_doc_request:
                structural -= 0.10
                reason_codes.add("docs_context_penalty")

            hybrid_score = _clamp(0.68 * base + 0.22 * lexical + 0.10 * _clamp(structural) + hybrid_bonus)
            ranked.append((hybrid_score, candidate))

        ranked.sort(
            key=lambda item: (
                -item[0],
                item[1].file_path,
                int(item[1].line_start),
                int(item[1].line_end),
                item[1].chunk_id,
            )
        )

        reranked = [
            CandidateChunk(
                chunk_id=item.chunk_id,
                file_path=item.file_path,
                line_start=item.line_start,
                line_end=item.line_end,
                score=score,
                text=item.text,
                signature=item.signature,
                score_local=item.score_local,
                score_vec=item.score_vec,
            )
            for score, item in ranked
        ]
        return HybridRerankResult(
            candidates=reranked,
            hybrid_rerank_used=True,
            retrieval_ranking_mode="hybrid_postrank",
            reason_codes=sorted(reason_codes) or ["hybrid_postrank"],
        )
    except Exception:
        return HybridRerankResult(
            candidates=list(candidates),
            hybrid_rerank_used=False,
            retrieval_ranking_mode="fallback_lexical",
            reason_codes=["rerank_failed"],
        )
