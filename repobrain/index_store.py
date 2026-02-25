from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
import zipfile

import orjson

from .chunk import chunk_text
from .scan import scan_files
from .tky_provider import CandidateChunk


def _safe_read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


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

    for path in files:
        text = _safe_read_text(path)
        if text is None:
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
                }
                if store_text:
                    row["text"] = chunk.text
                raw.write(orjson.dumps(row))
                raw.write(b"\n")


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
                    )
                )
    return chunks
