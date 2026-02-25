from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .tky_provider import CandidateChunk, TKYProvider, TKYResult


@dataclass
class LocalTKYProvider(TKYProvider):
    """Local TKY provider stub.

    This skeleton intentionally does NOT include proprietary TKY code.
    In private deployments, this provider can import and call your internal TKY package.
    """

    def compress_context(
        self,
        *,
        question: str,
        candidates: list[CandidateChunk],
        limits: dict[str, Any],
    ) -> TKYResult:
        raise NotImplementedError(
            "LocalTKYProvider is a stub in the public skeleton. "
            "In private builds, connect it to your internal TKY Python library."
        )
