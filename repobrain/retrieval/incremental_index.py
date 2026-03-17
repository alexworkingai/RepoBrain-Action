from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any

import orjson

from repobrain.retrieve_pro import extract_query_terms
from repobrain.tky_provider import CandidateChunk


@dataclass(frozen=True)
class IncrementalScopeResult:
    chunks: list[CandidateChunk]
    incremental_retrieval_used: bool
    incremental_scope_mode: str
    changed_files_considered: int
    changed_regions_considered: int
    unchanged_files_skipped: int
    unchanged_chunks_skipped: int
    retrieval_cache_hits: int
    retrieval_cache_misses: int
    incremental_fallback_reason: str


def _cache_path(repo_root: Path | None) -> Path | None:
    if repo_root is None:
        return None
    return repo_root / "artifacts" / ".repobrain_cache" / "incremental_retrieval_files.json"


def _load_cache(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    try:
        payload = orjson.loads(path.read_bytes())
    except (OSError, ValueError):
        return {}
    if not isinstance(payload, dict):
        return {}
    files = payload.get("files", {})
    if not isinstance(files, dict):
        return {}
    return {str(k): str(v) for k, v in files.items() if str(k).strip()}


def _save_cache(path: Path | None, files: dict[str, str]) -> None:
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "format_version": "1.0",
            "files": dict(sorted(files.items(), key=lambda item: item[0])),
        }
        path.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
    except OSError:
        return


def _file_fingerprint(chunks: list[CandidateChunk]) -> str:
    normalized = []
    for chunk in chunks:
        signature = ",".join(str(item) for item in (chunk.signature or []))
        normalized.append(
            "|".join(
                [
                    str(chunk.chunk_id),
                    str(chunk.line_start),
                    str(chunk.line_end),
                    signature,
                ]
            )
        )
    payload = "\n".join(sorted(normalized))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _chunks_by_file(chunks: list[CandidateChunk]) -> dict[str, list[CandidateChunk]]:
    grouped: dict[str, list[CandidateChunk]] = {}
    for chunk in chunks:
        grouped.setdefault(chunk.file_path, []).append(chunk)
    return grouped


def _normalized_changed_files(github_context: dict[str, Any] | None) -> list[str]:
    if not isinstance(github_context, dict):
        return []
    raw = github_context.get("changed_files", [])
    if not isinstance(raw, list):
        return []
    values = [str(item).strip() for item in raw if str(item).strip()]
    return sorted(set(values))


def _changed_regions_count(github_context: dict[str, Any] | None) -> int:
    if not isinstance(github_context, dict):
        return 0
    raw = github_context.get("diff_hunks", [])
    if not isinstance(raw, list):
        return 0
    return len([item for item in raw if str(item).strip()])


def _support_file_score(path: str, query_terms: list[str]) -> int:
    haystack = str(path or "").lower()
    score = 0
    for term in query_terms:
        token = str(term).strip().lower()
        if len(token) < 3:
            continue
        if token in haystack:
            score += 1
    return score


def scope_chunks_incremental(
    *,
    question: str,
    command: str,
    chunks: list[CandidateChunk],
    github_context: dict[str, Any] | None,
    repo_root: Path | None,
) -> IncrementalScopeResult:
    if not chunks:
        return IncrementalScopeResult([], False, "fallback_full", 0, 0, 0, 0, 0, 0, "empty_chunks")

    changed_files = _normalized_changed_files(github_context)
    changed_regions = _changed_regions_count(github_context)
    if not changed_files:
        return IncrementalScopeResult(
            chunks=list(chunks),
            incremental_retrieval_used=False,
            incremental_scope_mode="fallback_full",
            changed_files_considered=0,
            changed_regions_considered=changed_regions,
            unchanged_files_skipped=0,
            unchanged_chunks_skipped=0,
            retrieval_cache_hits=0,
            retrieval_cache_misses=0,
            incremental_fallback_reason="missing_changed_files",
        )

    grouped = _chunks_by_file(chunks)
    if not grouped:
        return IncrementalScopeResult(
            chunks=list(chunks),
            incremental_retrieval_used=False,
            incremental_scope_mode="fallback_full",
            changed_files_considered=0,
            changed_regions_considered=changed_regions,
            unchanged_files_skipped=0,
            unchanged_chunks_skipped=0,
            retrieval_cache_hits=0,
            retrieval_cache_misses=0,
            incremental_fallback_reason="empty_grouped_chunks",
        )

    available_files = set(grouped.keys())
    changed_in_index = [path for path in changed_files if path in available_files]
    if not changed_in_index:
        return IncrementalScopeResult(
            chunks=list(chunks),
            incremental_retrieval_used=False,
            incremental_scope_mode="fallback_full",
            changed_files_considered=0,
            changed_regions_considered=changed_regions,
            unchanged_files_skipped=0,
            unchanged_chunks_skipped=0,
            retrieval_cache_hits=0,
            retrieval_cache_misses=0,
            incremental_fallback_reason="changed_files_not_indexed",
        )

    cache_file = _cache_path(repo_root)
    previous = _load_cache(cache_file)
    current_fingerprints = {path: _file_fingerprint(file_chunks) for path, file_chunks in grouped.items()}
    cache_hits = 0
    cache_misses = 0
    for path, fingerprint in current_fingerprints.items():
        if previous.get(path) == fingerprint:
            cache_hits += 1
        else:
            cache_misses += 1
    _save_cache(cache_file, current_fingerprints)

    query_terms = extract_query_terms(question)
    unchanged_files = sorted(available_files - set(changed_in_index))
    support_cap = 8 if str(command or "").strip().lower() in {"review", "fix"} else 4
    scored_support = sorted(
        ((_support_file_score(path, query_terms), path) for path in unchanged_files),
        key=lambda item: (-item[0], item[1]),
    )
    support_files = [path for score, path in scored_support if score > 0][:support_cap]

    selected_files = set(changed_in_index) | set(support_files)
    scoped_chunks: list[CandidateChunk] = []
    unchanged_chunks_skipped = 0
    unchanged_files_skipped = 0
    for path, file_chunks in grouped.items():
        if path in selected_files:
            scoped_chunks.extend(file_chunks)
            continue
        unchanged_files_skipped += 1
        unchanged_chunks_skipped += len(file_chunks)

    if not scoped_chunks:
        return IncrementalScopeResult(
            chunks=list(chunks),
            incremental_retrieval_used=False,
            incremental_scope_mode="fallback_full",
            changed_files_considered=len(changed_in_index),
            changed_regions_considered=changed_regions,
            unchanged_files_skipped=0,
            unchanged_chunks_skipped=0,
            retrieval_cache_hits=cache_hits,
            retrieval_cache_misses=cache_misses,
            incremental_fallback_reason="empty_scoped_chunks",
        )

    mode = "changed_regions_first" if changed_regions > 0 else "changed_files_first"
    return IncrementalScopeResult(
        chunks=scoped_chunks,
        incremental_retrieval_used=True,
        incremental_scope_mode=mode,
        changed_files_considered=len(changed_in_index),
        changed_regions_considered=changed_regions,
        unchanged_files_skipped=unchanged_files_skipped,
        unchanged_chunks_skipped=unchanged_chunks_skipped,
        retrieval_cache_hits=cache_hits,
        retrieval_cache_misses=cache_misses,
        incremental_fallback_reason="none",
    )
