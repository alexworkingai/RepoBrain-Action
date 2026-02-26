from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
import zipfile

import orjson

from .chunk import chunk_text
from .scan import scan_files
from .signatures import build_chunk_signature
from .tky_provider import CandidateChunk

MAX_FILE_SIZE_BYTES = 1_000_000
BINARY_PROBE_BYTES = 8192


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

    for path in files:
        text, skip_reason = _read_indexable_text(path)
        if skip_reason:
            skipped_counts[skip_reason] = skipped_counts.get(skip_reason, 0) + 1
            # Hash only, do not log real path.
            _ = _path_hash(path)
            continue
        scanned_files += 1
        rel_path = path.relative_to(root)
        all_chunks.extend(chunk_text(rel_path, text))

    manifest = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "counts": {
            "files": scanned_files,
            "chunks": len(all_chunks),
        },
        "skipped": skipped_counts,
        "store_text": store_text,
    }

    with zipfile.ZipFile(out_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", orjson.dumps(manifest, option=orjson.OPT_INDENT_2))

        with zf.open("chunks.jsonl", mode="w") as raw:
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
                raw.write(orjson.dumps(row))
                raw.write(b"\n")

    if skipped_counts:
        summary = ", ".join(f"{reason}={count}" for reason, count in sorted(skipped_counts.items()))
        print(f"Index build skipped files: {summary}")


def load_index(zip_path: Path) -> list[CandidateChunk]:
    """Load chunks from a local zip index package."""
    chunks: list[CandidateChunk] = []
    with zipfile.ZipFile(zip_path, mode="r") as zf:
        with zf.open("chunks.jsonl", mode="r") as raw:
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
