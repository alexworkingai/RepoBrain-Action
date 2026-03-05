from __future__ import annotations

import hashlib
from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import zipfile

import orjson

from .chunk import chunk_text
from .scan import DEFAULT_EXCLUDE_GLOBS, scan_files
from .signatures import build_chunk_signature
from .tky_provider import CandidateChunk

MAX_FILE_SIZE_BYTES = 1_000_000
BINARY_PROBE_BYTES = 8192
INDEX_FORMAT_VERSION = "repobrain-index.v1"
MANIFEST_NAME = "manifest.json"
TOPO_MAP_NAME = "topo_map.json"
CHUNKS_NAME = "index/chunks.jsonl"
LEGACY_CHUNKS_NAME = "chunks.jsonl"


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


def _commit_sha() -> str:
    value = os.getenv("GITHUB_SHA", "").strip()
    return value or "local"


def _tool_versions() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "orjson": str(getattr(orjson, "__version__", "unknown")),
        "writer": "repobrain.index_store",
    }


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


def build_index(root: Path, out_zip: Path, store_text: bool = False) -> None:
    """Build a local zip index package from files under root."""
    root = root.resolve()
    out_zip = out_zip.resolve()
    out_zip.parent.mkdir(parents=True, exist_ok=True)

    files = scan_files(root, include_globs=None, exclude_globs=None)
    if not files:
        # When indexing a subdirectory (e.g. `repobrain/` in tests), repo-root-oriented
        # defaults may not match. Fallback to "all files under root" while keeping excludes.
        files = scan_files(root, include_globs=["**"], exclude_globs=None)
    all_chunks: list[CandidateChunk] = []
    scanned_files = 0
    skipped_counts: dict[str, int] = {}
    file_chunk_counts: dict[str, int] = {}

    for path in files:
        text, skip_reason = _read_indexable_text(path)
        if skip_reason:
            skipped_counts[skip_reason] = skipped_counts.get(skip_reason, 0) + 1
            # Hash only, do not log real path.
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
        "embeddings": {
            "enabled": False,
            "mode": "signature_hash",
            "store_text": bool(store_text),
        },
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
        # Backward compatibility with older loaders/tests.
        with zf.open(LEGACY_CHUNKS_NAME, mode="w") as raw:
            for payload in chunk_rows:
                raw.write(payload)
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
                    )
                )
    return chunks
