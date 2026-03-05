from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any

import orjson


class EmbeddingsCache:
    """Simple sqlite-backed cache for chunk embeddings."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS embeddings_cache (
                    chunk_hash TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    dim INTEGER NOT NULL,
                    vector_json BLOB NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (chunk_hash, model_id)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings_cache(model_id)"
            )
            conn.commit()

    def get_many(self, chunk_hashes: list[str], model_id: str) -> dict[str, list[float]]:
        if not chunk_hashes:
            return {}
        unique_hashes = list(dict.fromkeys(chunk_hashes))
        placeholders = ",".join("?" for _ in unique_hashes)
        sql = (
            "SELECT chunk_hash, vector_json FROM embeddings_cache "
            f"WHERE model_id = ? AND chunk_hash IN ({placeholders})"
        )
        params: list[Any] = [model_id, *unique_hashes]
        out: dict[str, list[float]] = {}
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        for row in rows:
            chunk_hash = str(row[0])
            payload = row[1]
            try:
                vector_raw = orjson.loads(payload)
            except orjson.JSONDecodeError:
                continue
            if not isinstance(vector_raw, list):
                continue
            out[chunk_hash] = [float(item) for item in vector_raw]
        return out

    def put_many(
        self,
        *,
        model_id: str,
        entries: list[tuple[str, list[float]]],
    ) -> None:
        if not entries:
            return
        now = datetime.now(timezone.utc).isoformat()
        payload_rows = [
            (
                str(chunk_hash),
                str(model_id),
                int(len(vector)),
                orjson.dumps([float(v) for v in vector]),
                now,
            )
            for chunk_hash, vector in entries
        ]
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO embeddings_cache (chunk_hash, model_id, dim, vector_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(chunk_hash, model_id) DO UPDATE SET
                    dim=excluded.dim,
                    vector_json=excluded.vector_json,
                    updated_at=excluded.updated_at
                """,
                payload_rows,
            )
            conn.commit()
