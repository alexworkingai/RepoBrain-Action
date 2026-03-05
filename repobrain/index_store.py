from __future__ import annotations

import hashlib
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import time
from typing import TYPE_CHECKING, Any
import zipfile

import orjson

from .ai_budget_governor import QuotaSignal, build_governor_from_env
from .chunk import chunk_text
from .config import RepoBrainConfig
from .embeddings_cache import EmbeddingsCache
from .llm.github_models_embeddings import (
    GitHubModelsEmbeddingsClient,
    GitHubModelsEmbeddingsError,
)
from .scan import DEFAULT_EXCLUDE_GLOBS, scan_files
from .signatures import build_chunk_signature
from .tky_provider import CandidateChunk

if TYPE_CHECKING:
    from .ai_budget_governor import AIBudgetGovernor

MAX_FILE_SIZE_BYTES = 1_000_000
BINARY_PROBE_BYTES = 8192
INDEX_FORMAT_VERSION = "repobrain-index.v1"
MANIFEST_NAME = "manifest.json"
TOPO_MAP_NAME = "topo_map.json"
CHUNKS_NAME = "index/chunks.jsonl"
LEGACY_CHUNKS_NAME = "chunks.jsonl"
EMBEDDINGS_NAME = "index/embeddings.jsonl"


def _safe_read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def _path_hash(path: Path) -> str:
    return hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]


def _is_binary_file(path: Path, probe_bytes: int = BINARY_PROBE_BYTES) -> bool:
    try:
        with path.open("rb") as fh:
            chunk = fh.read(probe_bytes)
    except OSError:
        return True
    return b"\x00" in chunk


def _read_indexable_text(
    path: Path,
    *,
    max_file_size_bytes: int = MAX_FILE_SIZE_BYTES,
) -> tuple[str | None, str | None]:
    try:
        file_size = path.stat().st_size
    except OSError:
        return None, "stat_error"

    if file_size > max_file_size_bytes:
        return None, "too_large"
    if _is_binary_file(path):
        return None, "binary"

    text = _safe_read_text(path)
    if text is None:
        return None, "read_error"
    return text, None


def _snippet_hash(text: str | None) -> str:
    payload = (text or "").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _chunk_hash(chunk: CandidateChunk) -> str:
    normalized_text = " ".join((chunk.text or "").split())
    payload = "|".join(
        [
            "v1",
            chunk.file_path,
            str(chunk.line_start),
            str(chunk.line_end),
            chunk.chunk_id,
            normalized_text,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _commit_sha() -> str:
    value = os.getenv("GITHUB_SHA", "").strip()
    return value or "local"


def _tool_versions() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "orjson": str(getattr(orjson, "__version__", "unknown")),
        "writer": "repobrain.index_store",
    }


def _embed_enabled(cfg: RepoBrainConfig) -> bool:
    return bool(cfg.embeddings.enabled)


def _embed_model(cfg: RepoBrainConfig) -> str:
    return str(cfg.embeddings.model or "openai/text-embedding-3-small")


def _embed_batch_size(cfg: RepoBrainConfig) -> int:
    return max(1, int(cfg.embeddings.batch_size))


def _embed_cache_path(root: Path) -> Path:
    return root / "artifacts" / ".repobrain_cache" / "embeddings.sqlite"


def _build_embeddings_usage_payload(
    *,
    used: bool,
    reason: str,
    model_id: str,
    calls: list[dict[str, Any]],
    chunks_embedded: int,
    query_embedded: bool,
    budget_action: str = "n/a",
) -> dict[str, Any]:
    prompt_total = sum(int(item.get("tokens_prompt", 0) or 0) for item in calls)
    total_tokens = sum(int(item.get("tokens_total", 0) or 0) for item in calls)
    last = calls[-1] if calls else {}
    return {
        "date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "embed_used": bool(used),
        "reason": reason,
        "budget_action": budget_action,
        "model_id": model_id,
        "calls": calls,
        "totals": {
            "calls_count": len(calls),
            "tokens_prompt_total": prompt_total,
            "tokens_total_total": total_tokens,
        },
        "remaining_requests": last.get("remaining_requests", "n/a"),
        "remaining_is_estimate": bool(last.get("remaining_is_estimate", True)),
        "reset_time_utc_iso": last.get("reset_time_utc_iso"),
        "chunks_embedded": int(chunks_embedded),
        "query_embedded": bool(query_embedded),
    }


def _write_embeddings_usage(root: Path, payload: dict[str, Any]) -> None:
    path = root / "artifacts" / "embeddings_usage.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        orjson.dumps(payload, option=orjson.OPT_INDENT_2).decode("utf-8"),
        encoding="utf-8",
    )


def _build_topo_map(
    *,
    file_chunk_counts: dict[str, int],
    total_chunks: int,
    skipped_counts: dict[str, int],
) -> dict[str, object]:
    chunk_edges = 0
    for count in file_chunk_counts.values():
        if count > 1:
            chunk_edges += count - 1

    files_sorted = sorted(file_chunk_counts.items())
    avg_chunks = (total_chunks / len(file_chunk_counts)) if file_chunk_counts else 0.0

    return {
        "format_version": "1.0",
        "graph": {
            "file_nodes": len(file_chunk_counts),
            "chunk_nodes": total_chunks,
            "chunk_edges": chunk_edges,
        },
        "metrics": {
            "avg_chunks_per_file": round(avg_chunks, 6),
            "max_chunks_per_file": max(file_chunk_counts.values(), default=0),
            "skipped_files": int(sum(skipped_counts.values())),
        },
        "files": [{"path": path, "chunks": count} for path, count in files_sorted],
    }


def _compute_chunk_embeddings(
    *,
    root: Path,
    chunks: list[CandidateChunk],
    governor: AIBudgetGovernor | None = None,
    cfg: RepoBrainConfig | None = None,
) -> tuple[dict[str, list[float]], dict[str, Any]]:
    active_cfg = cfg or RepoBrainConfig.from_env()
    enabled = _embed_enabled(active_cfg)
    model_id = _embed_model(active_cfg)
    batch_size = _embed_batch_size(active_cfg)
    token = str(active_cfg.workflow.github_token or "").strip()
    if not token:
        token = os.getenv("GITHUB_TOKEN", "").strip()

    base_meta = {
        "enabled": False,
        "mode": "signature_hash",
        "store_text": False,
        "model": model_id,
        "dim": 0,
        "chunks_embedded": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "calls": 0,
        "status": "DISABLED",
        "skipped_chunks": 0,
        "budget_action": "n/a",
        "reason": "disabled",
    }
    if not enabled:
        _write_embeddings_usage(
            root,
            _build_embeddings_usage_payload(
                used=False,
                reason="disabled",
                model_id=model_id,
                calls=[],
                chunks_embedded=0,
                query_embedded=False,
                budget_action="n/a",
            ),
        )
        return {}, base_meta
    if not token:
        base_meta["reason"] = "missing_github_token"
        _write_embeddings_usage(
            root,
            _build_embeddings_usage_payload(
                used=False,
                reason="missing_github_token",
                model_id=model_id,
                calls=[],
                chunks_embedded=0,
                query_embedded=False,
                budget_action="n/a",
            ),
        )
        return {}, base_meta

    cache = EmbeddingsCache(_embed_cache_path(root))
    hashes = [_chunk_hash(chunk) for chunk in chunks]
    cached = cache.get_many(hashes, model_id=model_id)
    vectors_by_chunk_id: dict[str, list[float]] = {}
    misses: list[tuple[CandidateChunk, str]] = []
    for chunk, chunk_hash in zip(chunks, hashes):
        hit = cached.get(chunk_hash)
        if hit:
            vectors_by_chunk_id[chunk.chunk_id] = hit
        else:
            misses.append((chunk, chunk_hash))

    calls: list[dict[str, Any]] = []
    budget_skipped = 0
    budget_reason = "n/a"
    budget_action = "n/a"
    if misses:
        client = GitHubModelsEmbeddingsClient(token=token)
        for start in range(0, len(misses), batch_size):
            batch = misses[start : start + batch_size]
            inputs = [item[0].text or "" for item in batch]
            if governor is not None:
                next_cost_est = max(1, int(sum(len(item) for item in inputs) / 4))
                decision = governor.can_call_embed(next_call_cost_est=next_cost_est)
                if not decision.allow or decision.disable_embeddings:
                    budget_skipped = len(misses) - start
                    budget_reason = decision.reason
                    budget_action = decision.budget_action
                    break
            try:
                response = client.embed(model_id=model_id, inputs=inputs)
            except GitHubModelsEmbeddingsError as exc:
                base_meta.update(
                    {
                        "reason": f"embed_error:{exc.reason}",
                        "cache_hits": len(chunks) - len(misses),
                        "cache_misses": len(misses),
                        "calls": len(calls),
                        "status": "PARTIAL" if vectors_by_chunk_id else "DISABLED",
                        "skipped_chunks": len(misses) - start,
                    }
                )
                _write_embeddings_usage(
                    root,
                    _build_embeddings_usage_payload(
                        used=False,
                        reason=f"embed_error:{exc.reason}",
                        model_id=model_id,
                        calls=calls,
                        chunks_embedded=len(vectors_by_chunk_id),
                        query_embedded=False,
                        budget_action=budget_action,
                    ),
                )
                return vectors_by_chunk_id, base_meta
            if len(response.vectors) != len(batch):
                base_meta["reason"] = "vector_count_mismatch"
                _write_embeddings_usage(
                    root,
                    _build_embeddings_usage_payload(
                        used=False,
                        reason="vector_count_mismatch",
                        model_id=model_id,
                        calls=calls,
                        chunks_embedded=len(vectors_by_chunk_id),
                        query_embedded=False,
                        budget_action=budget_action,
                    ),
                )
                return vectors_by_chunk_id, base_meta
            cache_rows: list[tuple[str, list[float]]] = []
            for (chunk, chunk_hash), vec in zip(batch, response.vectors):
                vec_norm = [float(item) for item in vec]
                vectors_by_chunk_id[chunk.chunk_id] = vec_norm
                cache_rows.append((chunk_hash, vec_norm))
            cache.put_many(model_id=model_id, entries=cache_rows)
            if governor is not None:
                governor.observe_embed_signal(
                    QuotaSignal(
                        remaining_requests=response.remaining_requests,
                        reset_time_utc_iso=response.reset_time_utc_iso,
                        remaining_is_estimate=response.remaining_is_estimate,
                        usage_estimated=response.usage_estimated,
                        ratelimit_headers=dict(response.ratelimit_headers),
                    ),
                    {"tokens_total": response.total_tokens},
                )
            calls.append(
                {
                    "batch_id": f"index_{start // batch_size}",
                    "tokens_prompt": response.prompt_tokens,
                    "tokens_total": response.total_tokens,
                    "remaining_requests": response.remaining_requests,
                    "remaining_is_estimate": response.remaining_is_estimate,
                    "reset_time_utc_iso": response.reset_time_utc_iso,
                    "estimate_flags": {
                        "usage_estimated": response.usage_estimated,
                        "remaining_estimated": response.remaining_is_estimate,
                    },
                }
            )

    dim = len(next(iter(vectors_by_chunk_id.values()), []))
    status = "OK" if vectors_by_chunk_id else "DISABLED"
    reason = "ok" if vectors_by_chunk_id else "no_vectors"
    if budget_skipped > 0:
        status = "PARTIAL" if vectors_by_chunk_id else "DISABLED"
        reason = f"budget:{budget_reason}"
    embed_meta = {
        "enabled": bool(vectors_by_chunk_id),
        "mode": "vector",
        "store_text": False,
        "model": model_id,
        "dim": dim,
        "chunks_embedded": len(vectors_by_chunk_id),
        "cache_hits": len(chunks) - len(misses),
        "cache_misses": len(misses),
        "calls": len(calls),
        "status": status,
        "skipped_chunks": budget_skipped,
        "budget_action": budget_action,
        "reason": reason,
    }
    _write_embeddings_usage(
        root,
        _build_embeddings_usage_payload(
            used=bool(vectors_by_chunk_id),
            reason=embed_meta["reason"],
            model_id=model_id,
            calls=calls,
            chunks_embedded=len(vectors_by_chunk_id),
            query_embedded=False,
            budget_action=budget_action,
        ),
    )
    return vectors_by_chunk_id, embed_meta


def build_index(
    root: Path,
    out_zip: Path,
    store_text: bool = False,
    governor: AIBudgetGovernor | None = None,
    cfg: RepoBrainConfig | None = None,
) -> None:
    """Build a local zip index package from files under root."""
    root = root.resolve()
    out_zip = out_zip.resolve()
    out_zip.parent.mkdir(parents=True, exist_ok=True)

    files = scan_files(root, include_globs=None, exclude_globs=None)
    if not files:
        files = scan_files(root, include_globs=["**"], exclude_globs=None)
    all_chunks: list[CandidateChunk] = []
    scanned_files = 0
    skipped_counts: dict[str, int] = {}
    file_chunk_counts: dict[str, int] = {}

    for path in files:
        text, skip_reason = _read_indexable_text(path)
        if skip_reason:
            skipped_counts[skip_reason] = skipped_counts.get(skip_reason, 0) + 1
            _ = _path_hash(path)
            continue
        scanned_files += 1
        rel_path = path.relative_to(root)
        chunks = chunk_text(rel_path, text)
        all_chunks.extend(chunks)
        file_chunk_counts[rel_path.as_posix()] = len(chunks)

    all_chunks = sorted(
        all_chunks,
        key=lambda chunk: (chunk.file_path, chunk.line_start, chunk.line_end, chunk.chunk_id),
    )
    active_cfg = cfg or RepoBrainConfig.from_env()
    active_governor = governor or build_governor_from_env(cfg=active_cfg)
    vectors_by_chunk_id, embeddings_meta = _compute_chunk_embeddings(
        root=root,
        chunks=all_chunks,
        governor=active_governor,
        cfg=active_cfg,
    )

    topo_map = _build_topo_map(
        file_chunk_counts=file_chunk_counts,
        total_chunks=len(all_chunks),
        skipped_counts=skipped_counts,
    )

    manifest = {
        "format_version": INDEX_FORMAT_VERSION,
        "commit_sha": _commit_sha(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "root": root.name,
        "files_indexed": scanned_files,
        "chunks": len(all_chunks),
        "embeddings": embeddings_meta,
        "topo": {
            "format_version": str(topo_map.get("format_version", "1.0")),
            "file_nodes": int(topo_map.get("graph", {}).get("file_nodes", 0)),
            "chunk_nodes": int(topo_map.get("graph", {}).get("chunk_nodes", 0)),
            "chunk_edges": int(topo_map.get("graph", {}).get("chunk_edges", 0)),
        },
        "exclusions": {
            "default_exclude_globs": sorted(DEFAULT_EXCLUDE_GLOBS),
            "skipped": {key: skipped_counts[key] for key in sorted(skipped_counts)},
        },
        "tool_versions": _tool_versions(),
        "store_text": store_text,
    }

    with zipfile.ZipFile(out_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(MANIFEST_NAME, orjson.dumps(manifest, option=orjson.OPT_INDENT_2))
        zf.writestr(TOPO_MAP_NAME, orjson.dumps(topo_map, option=orjson.OPT_INDENT_2))

        chunk_rows: list[bytes] = []
        for chunk in all_chunks:
            row = {
                "chunk_id": chunk.chunk_id,
                "file_path": chunk.file_path,
                "line_start": chunk.line_start,
                "line_end": chunk.line_end,
                "chunk_hash": _chunk_hash(chunk),
                "text_snippet_hash": _snippet_hash(chunk.text),
                "signature": build_chunk_signature(
                    file_path=chunk.file_path,
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    include_text=store_text,
                ),
            }
            if store_text:
                row["text"] = chunk.text
            chunk_rows.append(orjson.dumps(row))

        with zf.open(CHUNKS_NAME, mode="w") as raw:
            for payload in chunk_rows:
                raw.write(payload)
                raw.write(b"\n")
        with zf.open(LEGACY_CHUNKS_NAME, mode="w") as raw:
            for payload in chunk_rows:
                raw.write(payload)
                raw.write(b"\n")
        if vectors_by_chunk_id:
            with zf.open(EMBEDDINGS_NAME, mode="w") as raw:
                for chunk in all_chunks:
                    vec = vectors_by_chunk_id.get(chunk.chunk_id)
                    if not vec:
                        continue
                        row = {
                            "chunk_id": chunk.chunk_id,
                            "chunk_hash": _chunk_hash(chunk),
                            "model_id": embeddings_meta.get("model", _embed_model(active_cfg)),
                            "dim": len(vec),
                            "vec": vec,
                        }
                    raw.write(orjson.dumps(row))
                    raw.write(b"\n")

    if skipped_counts:
        summary = ", ".join(f"{reason}={count}" for reason, count in sorted(skipped_counts.items()))
        print(f"Index build skipped files: {summary}")


def load_index(zip_path: Path) -> list[CandidateChunk]:
    """Load chunks from a local zip index package."""
    chunks: list[CandidateChunk] = []
    with zipfile.ZipFile(zip_path, mode="r") as zf:
        names = set(zf.namelist())
        chunks_name = CHUNKS_NAME if CHUNKS_NAME in names else LEGACY_CHUNKS_NAME
        with zf.open(chunks_name, mode="r") as raw:
            for line in raw:
                if not line.strip():
                    continue
                row = orjson.loads(line)
                chunks.append(
                    CandidateChunk(
                        chunk_id=str(row["chunk_id"]),
                        file_path=str(row["file_path"]),
                        line_start=int(row["line_start"]),
                        line_end=int(row["line_end"]),
                        score=0.0,
                        text=row.get("text"),
                        signature=[int(item) for item in row.get("signature", [])],
                        score_local=None,
                        score_vec=None,
                    )
                )
    return chunks


def load_index_embeddings(zip_path: Path) -> tuple[dict[str, list[float]], dict[str, Any]]:
    vectors: dict[str, list[float]] = {}
    meta: dict[str, Any] = {"enabled": False, "model": "", "dim": 0}
    with zipfile.ZipFile(zip_path, mode="r") as zf:
        names = set(zf.namelist())
        if MANIFEST_NAME in names:
            manifest = orjson.loads(zf.read(MANIFEST_NAME))
            if isinstance(manifest, dict):
                embeddings_meta = manifest.get("embeddings", {})
                if isinstance(embeddings_meta, dict):
                    meta.update(embeddings_meta)
        if EMBEDDINGS_NAME not in names:
            return {}, meta
        with zf.open(EMBEDDINGS_NAME, mode="r") as raw:
            for line in raw:
                if not line.strip():
                    continue
                row = orjson.loads(line)
                chunk_id = str(row.get("chunk_id", "") or "")
                vec_raw = row.get("vec", [])
                if not chunk_id or not isinstance(vec_raw, list):
                    continue
                vectors[chunk_id] = [float(item) for item in vec_raw]
    meta["enabled"] = bool(vectors)
    if vectors and not int(meta.get("dim", 0) or 0):
        meta["dim"] = len(next(iter(vectors.values())))
    return vectors, meta
