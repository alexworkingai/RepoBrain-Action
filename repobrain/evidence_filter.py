from __future__ import annotations

from dataclasses import dataclass

from repobrain.audit_contract import _sanitize_repo_path
from repobrain.evidence import EvidenceItem
from repobrain.retrieve_pro import extract_query_terms
from repobrain.tky_provider import CandidateChunk

_DOC_EXTENSIONS = (".md", ".rst", ".txt", ".adoc")
_LOW_VALUE_PATH_TOKENS = ("node_modules/", "dist/", "build/", ".min.", "package-lock.json", "pnpm-lock.yaml")


@dataclass(frozen=True)
class EvidenceFilterResult:
    candidates: list[CandidateChunk]
    evidence_items: list[EvidenceItem]
    filtered_count: int
    reason_codes: list[str]


def _is_docs_path(path: str) -> bool:
    lower = str(path or "").strip().lower()
    if not lower:
        return False
    if lower.startswith(("docs/", "documentation/")):
        return True
    return any(lower.endswith(ext) for ext in _DOC_EXTENSIONS)


def _is_low_value_path(path: str) -> bool:
    lower = str(path or "").strip().lower()
    return any(token in lower for token in _LOW_VALUE_PATH_TOKENS)


def _is_unsafe_private_path(path: str) -> bool:
    return not _sanitize_repo_path(path)


def _region_key(path: str, line_start: int, line_end: int) -> tuple[str, int, int]:
    start_bucket = max(0, int(line_start) // 20)
    end_bucket = max(0, int(line_end) // 20)
    return (str(path), start_bucket, end_bucket)


def _explicit_doc_request(query: str) -> bool:
    query_terms = {term.strip().lower() for term in extract_query_terms(query)}
    return bool({"readme", "doc", "docs", "documentation"} & query_terms)


def _repobrain_workflow_query(query: str) -> bool:
    normalized = " ".join(str(query or "").strip().lower().split())
    if "workflow" not in normalized:
        return False
    return "repobrain" in normalized or "repo brain" in normalized


def _priority_path_rank(path: str, *, query: str) -> int:
    lowered = str(path or "").strip().lower()
    if not lowered:
        return 100
    if _repobrain_workflow_query(query):
        if lowered == ".github/workflows/repobrain.yml":
            return 0
        if lowered == ".github/repobrain.instructions.md":
            return 1
        if lowered.startswith("docs/") or lowered == "readme.md":
            return 2
        if "repobrain" in lowered and lowered.startswith(".github/workflows/"):
            return 3
        if lowered.startswith(".github/workflows/"):
            return 8
    return 50


def filter_candidate_evidence(
    candidates: list[CandidateChunk],
    *,
    command: str,
    query: str = "",
    max_items: int | None = None,
) -> EvidenceFilterResult:
    if not candidates:
        return EvidenceFilterResult([], [], 0, ["none"])

    top_score = max(float(item.score) for item in candidates)
    min_keep = max(0.01, top_score * 0.12)
    cmd = str(command or "ask").strip().lower()
    explicit_doc = _explicit_doc_request(query)
    has_non_docs_candidates = any(not _is_docs_path(item.file_path) for item in candidates)

    filtered: list[CandidateChunk] = []
    seen_regions: set[tuple[str, int, int]] = set()
    reason_codes: set[str] = set()
    dropped = 0

    for item in candidates:
        if max_items is not None and len(filtered) >= max(1, int(max_items)):
            dropped += 1
            reason_codes.add("max_items")
            continue

        if _is_unsafe_private_path(item.file_path):
            dropped += 1
            reason_codes.add("unsafe_private_path")
            continue

        score = float(item.score)
        if score < min_keep and len(filtered) >= 3:
            dropped += 1
            reason_codes.add("low_score")
            continue

        if (
            (cmd in {"review", "fix"})
            and _is_docs_path(item.file_path)
            and has_non_docs_candidates
            and not explicit_doc
            and score <= (top_score * 0.99)
        ):
            dropped += 1
            reason_codes.add("docs_noise")
            continue

        if _is_low_value_path(item.file_path) and score < (top_score * 0.85):
            dropped += 1
            reason_codes.add("low_value_path")
            continue

        region = _region_key(item.file_path, int(item.line_start), int(item.line_end))
        if region in seen_regions:
            dropped += 1
            reason_codes.add("duplicate_region")
            continue
        seen_regions.add(region)
        filtered.append(item)

    if not filtered:
        filtered = [candidates[0]]
        dropped = max(0, len(candidates) - 1)
        reason_codes.add("fallback_keep_top")

    filtered = sorted(
        filtered,
        key=lambda item: (
            _priority_path_rank(item.file_path, query=query),
            -float(item.score),
            str(item.file_path or ""),
            int(item.line_start),
        ),
    )

    evidence_items = [
        EvidenceItem(
            file_path=item.file_path,
            line_start=item.line_start,
            line_end=item.line_end,
            score=item.score,
        )
        for item in filtered
    ]
    return EvidenceFilterResult(
        candidates=filtered,
        evidence_items=evidence_items,
        filtered_count=dropped,
        reason_codes=sorted(reason_codes) or ["none"],
    )


def filter_evidence_items(
    evidence: list[EvidenceItem],
    *,
    command: str,
    query: str = "",
) -> EvidenceFilterResult:
    as_candidates = [
        CandidateChunk(
            chunk_id=f"evidence:{item.file_path}:{item.line_start}-{item.line_end}",
            file_path=item.file_path,
            line_start=item.line_start,
            line_end=item.line_end,
            score=item.score,
            text=None,
        )
        for item in evidence
    ]
    result = filter_candidate_evidence(
        as_candidates,
        command=command,
        query=query,
        max_items=len(evidence),
    )
    return EvidenceFilterResult(
        candidates=result.candidates,
        evidence_items=result.evidence_items,
        filtered_count=result.filtered_count,
        reason_codes=result.reason_codes,
    )
