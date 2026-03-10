from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class EngineCandidate:
    chunk_id: str
    score_local: float
    signature: list[int] | None = None
    file_path: str | None = None
    line_start: int | None = None
    line_end: int | None = None


@dataclass(frozen=True)
class EngineQuery:
    text: str
    signature: list[int] | None = None


@dataclass(frozen=True)
class EngineRequest:
    task_type: Literal["ask", "locate", "explain", "review"]
    query: EngineQuery
    candidates: list[EngineCandidate]
    limits: dict[str, Any] = field(default_factory=dict)
    policy: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EngineSecurity:
    blocked: bool
    injection_risk: str
    exfiltration_risk: str
    signals: list[str]


@dataclass(frozen=True)
class EngineDecision:
    route: str
    selected_chunk_ids: list[str]
    compression_stats: dict[str, Any]
    security: EngineSecurity
    rationale: str
    stable_tokens: list[str]
    execution_mode: str = "retrieval_only"
    llm_intent: str = "none"
    llm_decision_reason_short: str = "LLM not used: direct answer available from retrieved evidence."
    llm_decision_reason_code: str = "DEFAULT_RETRIEVAL_ONLY"


class TKYEngine(Protocol):
    def decide(self, req: EngineRequest) -> EngineDecision:
        ...
