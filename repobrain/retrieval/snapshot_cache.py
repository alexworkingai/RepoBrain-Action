from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import time
from typing import Any

import orjson

from repobrain.tky_provider import CandidateChunk

_CACHE_FORMAT_VERSION = "1.0"
_MAX_ENTRIES = 64


@dataclass(frozen=True)
class RetrievalSnapshotLoadResult:
    candidates: list[CandidateChunk] | None
    retrieval_runtime: dict[str, Any] | None
    cache_used: bool
    cache_hit: bool
    cache_key_kind: str
    cache_miss_reason: str
    cache_age_s: int

    def as_runtime_fields(self) -> dict[str, Any]:
        return {
            "retrieval_snapshot_cache_used": bool(self.cache_used),
            "retrieval_snapshot_cache_hit": bool(self.cache_hit),
            "retrieval_snapshot_cache_key_kind": str(self.cache_key_kind or "not_applicable"),
            "retrieval_snapshot_cache_miss_reason": str(
                self.cache_miss_reason or "not_applicable"
            ),
            "retrieval_snapshot_cache_age_s": int(self.cache_age_s or 0),
        }


def snapshot_cache_defaults(
    *,
    miss_reason: str = "not_applicable",
    cache_used: bool = False,
    cache_hit: bool = False,
    cache_key_kind: str = "not_applicable",
    cache_age_s: int = 0,
) -> dict[str, Any]:
    return {
        "retrieval_snapshot_cache_used": bool(cache_used),
        "retrieval_snapshot_cache_hit": bool(cache_hit),
        "retrieval_snapshot_cache_key_kind": str(cache_key_kind or "not_applicable"),
        "retrieval_snapshot_cache_miss_reason": str(miss_reason or "not_applicable"),
        "retrieval_snapshot_cache_age_s": int(cache_age_s or 0),
    }


def _cache_path(repo_root: Path | None) -> Path | None:
    if repo_root is None:
        return None
    return repo_root / "artifacts" / ".repobrain_cache" / "retrieval_snapshot_cache.json"


def _normalize_pr_number(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return str(int(text))
    except (TypeError, ValueError):
        return ""


def _normalize_changed_file_rows(github_context: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    files_raw = github_context.get("files", [])
    if isinstance(files_raw, list):
        for item in files_raw:
            if not isinstance(item, dict):
                continue
            filename = str(item.get("filename", "") or "").strip()
            status = str(item.get("status", "modified") or "modified").strip().lower()
            if filename:
                rows.append(f"{filename}|{status}")
    changed_files_raw = github_context.get("changed_files", [])
    if isinstance(changed_files_raw, list):
        for item in changed_files_raw:
            if isinstance(item, dict):
                filename = str(item.get("filename", "") or "").strip()
                status = str(item.get("status", "modified") or "modified").strip().lower()
                if filename:
                    rows.append(f"{filename}|{status}")
            else:
                filename = str(item).strip()
                if filename:
                    rows.append(f"{filename}|modified")
    return sorted(set(rows))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _build_cache_key(
    *,
    question: str,
    command: str,
    topk: int,
    github_context: dict[str, Any] | None,
) -> tuple[str | None, str, str]:
    if not isinstance(github_context, dict):
        return None, "not_applicable", "missing_github_context"

    pr_number = _normalize_pr_number(github_context.get("pr_number"))
    head_sha = str(github_context.get("head_sha", "") or "").strip()
    changed_rows = _normalize_changed_file_rows(github_context)
    changed_digest = _sha256_text("\n".join(changed_rows)) if changed_rows else ""

    if not changed_digest:
        return None, "not_applicable", "missing_changed_files"
    if not pr_number and not head_sha:
        return None, "not_applicable", "missing_pr_identity"

    if pr_number and head_sha:
        key_kind = "pr_number_head_sha"
    elif head_sha:
        key_kind = "head_sha_only"
    else:
        key_kind = "pr_number_only"

    key_payload = {
        "version": "retrieval_snapshot_v1",
        "key_kind": key_kind,
        "pr_number": pr_number or "n/a",
        "head_sha": head_sha or "n/a",
        "changed_digest": changed_digest,
        "command": str(command or "").strip().lower(),
        "question_hash": _sha256_text(" ".join(str(question or "").split())),
        "topk": int(topk or 0),
    }
    key = _sha256_text(orjson.dumps(key_payload, option=orjson.OPT_SORT_KEYS).decode("utf-8"))
    return key, key_kind, "cache_key_miss"


def _load_cache(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {"format_version": _CACHE_FORMAT_VERSION, "entries": {}}
    try:
        payload = orjson.loads(path.read_bytes())
    except (OSError, ValueError):
        return {"format_version": _CACHE_FORMAT_VERSION, "entries": {}}
    if not isinstance(payload, dict):
        return {"format_version": _CACHE_FORMAT_VERSION, "entries": {}}
    entries = payload.get("entries", {})
    if not isinstance(entries, dict):
        entries = {}
    return {
        "format_version": str(payload.get("format_version", _CACHE_FORMAT_VERSION) or _CACHE_FORMAT_VERSION),
        "entries": entries,
    }


def _save_cache(path: Path | None, payload: dict[str, Any]) -> None:
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS))
    except OSError:
        return


def _candidate_to_row(chunk: CandidateChunk) -> dict[str, Any]:
    return {
        "chunk_id": str(chunk.chunk_id),
        "file_path": str(chunk.file_path),
        "line_start": int(chunk.line_start),
        "line_end": int(chunk.line_end),
        "score": float(chunk.score),
        "text": chunk.text,
        "signature": list(chunk.signature) if isinstance(chunk.signature, list) else None,
        "score_local": float(chunk.score_local) if chunk.score_local is not None else None,
        "score_vec": float(chunk.score_vec) if chunk.score_vec is not None else None,
    }


def _candidate_from_row(row: dict[str, Any]) -> CandidateChunk | None:
    if not isinstance(row, dict):
        return None
    chunk_id = str(row.get("chunk_id", "") or "").strip()
    file_path = str(row.get("file_path", "") or "").strip()
    if not chunk_id or not file_path:
        return None
    try:
        line_start = int(row.get("line_start", 1) or 1)
        line_end = int(row.get("line_end", 1) or 1)
        score = float(row.get("score", 0.0) or 0.0)
    except (TypeError, ValueError):
        return None
    signature_raw = row.get("signature", None)
    signature = [int(item) for item in signature_raw] if isinstance(signature_raw, list) else None
    score_local_raw = row.get("score_local", None)
    score_vec_raw = row.get("score_vec", None)
    score_local = float(score_local_raw) if score_local_raw is not None else None
    score_vec = float(score_vec_raw) if score_vec_raw is not None else None
    text_raw = row.get("text", None)
    text = str(text_raw) if isinstance(text_raw, str) else None
    return CandidateChunk(
        chunk_id=chunk_id,
        file_path=file_path,
        line_start=line_start,
        line_end=line_end,
        score=score,
        text=text,
        signature=signature,
        score_local=score_local,
        score_vec=score_vec,
    )


def load_retrieval_snapshot(
    *,
    question: str,
    command: str,
    topk: int,
    github_context: dict[str, Any] | None,
    repo_root: Path | None,
) -> RetrievalSnapshotLoadResult:
    key, key_kind, miss_reason = _build_cache_key(
        question=question,
        command=command,
        topk=topk,
        github_context=github_context,
    )
    if key is None:
        return RetrievalSnapshotLoadResult(
            candidates=None,
            retrieval_runtime=None,
            cache_used=False,
            cache_hit=False,
            cache_key_kind=key_kind,
            cache_miss_reason=miss_reason,
            cache_age_s=0,
        )

    path = _cache_path(repo_root)
    payload = _load_cache(path)
    entries = payload.get("entries", {})
    if not isinstance(entries, dict):
        entries = {}
    entry = entries.get(key)
    if not isinstance(entry, dict):
        return RetrievalSnapshotLoadResult(
            candidates=None,
            retrieval_runtime=None,
            cache_used=True,
            cache_hit=False,
            cache_key_kind=key_kind,
            cache_miss_reason=miss_reason,
            cache_age_s=0,
        )

    candidates_rows = entry.get("candidates", [])
    if not isinstance(candidates_rows, list):
        candidates_rows = []
    candidates: list[CandidateChunk] = []
    for row in candidates_rows:
        candidate = _candidate_from_row(row)
        if candidate is not None:
            candidates.append(candidate)
    if not candidates:
        return RetrievalSnapshotLoadResult(
            candidates=None,
            retrieval_runtime=None,
            cache_used=True,
            cache_hit=False,
            cache_key_kind=key_kind,
            cache_miss_reason="empty_snapshot",
            cache_age_s=0,
        )

    runtime_raw = entry.get("retrieval_runtime", {})
    retrieval_runtime = dict(runtime_raw) if isinstance(runtime_raw, dict) else {}
    created_epoch = entry.get("created_epoch_s", 0)
    try:
        age_s = max(0, int(time.time() - float(created_epoch)))
    except (TypeError, ValueError):
        age_s = 0
    return RetrievalSnapshotLoadResult(
        candidates=candidates,
        retrieval_runtime=retrieval_runtime,
        cache_used=True,
        cache_hit=True,
        cache_key_kind=key_kind,
        cache_miss_reason="none",
        cache_age_s=age_s,
    )


def store_retrieval_snapshot(
    *,
    question: str,
    command: str,
    topk: int,
    github_context: dict[str, Any] | None,
    repo_root: Path | None,
    candidates: list[CandidateChunk],
    retrieval_runtime: dict[str, Any],
) -> None:
    key, key_kind, _ = _build_cache_key(
        question=question,
        command=command,
        topk=topk,
        github_context=github_context,
    )
    if key is None:
        return
    path = _cache_path(repo_root)
    payload = _load_cache(path)
    entries_raw = payload.get("entries", {})
    entries: dict[str, Any] = dict(entries_raw) if isinstance(entries_raw, dict) else {}
    created_epoch_s = int(time.time())
    entries[key] = {
        "key_kind": key_kind,
        "created_epoch_s": created_epoch_s,
        "command": str(command or "").strip().lower(),
        "topk": int(topk or 0),
        "candidates": [_candidate_to_row(candidate) for candidate in candidates],
        "retrieval_runtime": {
            str(name): value
            for name, value in dict(retrieval_runtime or {}).items()
            if not str(name).startswith("retrieval_snapshot_cache_")
        },
    }
    if len(entries) > _MAX_ENTRIES:
        ordered_keys = sorted(
            entries.keys(),
            key=lambda entry_key: int(entries.get(entry_key, {}).get("created_epoch_s", 0) or 0),
            reverse=True,
        )
        entries = {entry_key: entries[entry_key] for entry_key in ordered_keys[:_MAX_ENTRIES]}
    _save_cache(
        path,
        {
            "format_version": _CACHE_FORMAT_VERSION,
            "entries": entries,
        },
    )
