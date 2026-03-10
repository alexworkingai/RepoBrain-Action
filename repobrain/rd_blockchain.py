from __future__ import annotations

from dataclasses import dataclass
import hashlib
import time
from typing import Any


def _hash(value: str, *, size: int = 12) -> str:
    return hashlib.blake2s(value.encode("utf-8"), digest_size=size).hexdigest()


@dataclass(frozen=True)
class ChainRecord:
    event_id: str
    timestamp: int
    payload_hash: str
    signature_hash: str
    prev_hash: str
    chain_hash: str


class InMemoryChainAdapter:
    """In-memory append-only attestation chain with idempotent event ids."""

    def __init__(self, chain_id: str = "repobrain-rd-local") -> None:
        self.chain_id = str(chain_id or "repobrain-rd-local")
        self._records: list[ChainRecord] = []
        self._index: dict[str, ChainRecord] = {}

    def append_event(
        self,
        *,
        event_id: str,
        payload_hash: str,
        signature: str,
        timestamp: int | None = None,
    ) -> ChainRecord:
        normalized_id = str(event_id or "").strip()
        if not normalized_id:
            raise ValueError("event_id is required")
        existing = self._index.get(normalized_id)
        if existing is not None:
            return existing

        ts = int(time.time()) if timestamp is None else int(timestamp)
        prev_hash = self._records[-1].chain_hash if self._records else _hash(self.chain_id, size=16)
        signature_hash = _hash(str(signature or ""), size=16)
        chain_hash = _hash(
            "|".join(
                [
                    self.chain_id,
                    normalized_id,
                    str(ts),
                    str(payload_hash),
                    signature_hash,
                    prev_hash,
                ]
            ),
            size=16,
        )
        record = ChainRecord(
            event_id=normalized_id,
            timestamp=ts,
            payload_hash=str(payload_hash),
            signature_hash=signature_hash,
            prev_hash=prev_hash,
            chain_hash=chain_hash,
        )
        self._records.append(record)
        self._index[normalized_id] = record
        return record

    def export_summary(self) -> dict[str, Any]:
        event_ids_joined = ",".join(record.event_id for record in self._records)
        return {
            "chain_id": self.chain_id,
            "length": len(self._records),
            "head_hash": self._records[-1].chain_hash if self._records else "",
            "event_ids_hash": _hash(event_ids_joined, size=16),
        }


def build_attestation_record(
    *,
    run_id: str,
    artifact_hash: str,
    signature_hash: str,
    chain_hash: str | None = None,
) -> dict[str, str]:
    payload = "|".join([str(run_id), str(artifact_hash), str(signature_hash), str(chain_hash or "")])
    return {
        "run_id_hash": _hash(str(run_id), size=12),
        "artifact_hash": str(artifact_hash),
        "signature_hash": str(signature_hash),
        "chain_hash": str(chain_hash or ""),
        "record_hash": _hash(payload, size=16),
    }
