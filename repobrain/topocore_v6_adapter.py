"""Inert adapter skeleton for future TopoCore v6 public-facade integration.

This module does not import TopoCore v6, does not call TopoCore v6, and does
not change current RepoBrain runtime behavior. It only builds a safe preview
payload shape from validated RepoBrain-side summary bundles.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

_UNSAFE_CANDIDATE_METADATA_KEYS = frozenset(
    {
        "api_key",
        "dotenv",
        "env",
        "password",
        "private_key",
        "prompt",
        "raw_code",
        "raw_text",
        "secret",
        "system_prompt",
        "token",
    }
)

_FORBIDDEN_OUTPUT_KEYS = frozenset(
    {
        "compression_stats",
        "decide_raw",
        "governance_internals",
        "raw_query",
        "raw_query_text",
        "trace_internals",
    }
)


class RepoBrainV6AdapterError(ValueError):
    """Raised when the adapter preview input contains unsafe or invalid data."""


@dataclass(frozen=True)
class RepoBrainV6CandidateRef:
    """Safe candidate reference for future TopoCore v6 request previews."""

    chunk_id: str
    score_local: float
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RepoBrainV6SummaryBundle:
    """Validated RepoBrain summary bundle for future v6 adapter shaping."""

    query: str
    intent_summary: Mapping[str, Any]
    candidates: Sequence[RepoBrainV6CandidateRef] = field(default_factory=tuple)
    task_type: str | None = None
    limits: Mapping[str, Any] = field(default_factory=dict)
    pr_context_summary: Mapping[str, Any] = field(default_factory=dict)
    evidence_summary: Mapping[str, Any] = field(default_factory=dict)
    unknowns_summary: Mapping[str, Any] = field(default_factory=dict)
    risk_items: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    review_draft_summary: Mapping[str, Any] = field(default_factory=dict)
    fix_draft_summary: Mapping[str, Any] = field(default_factory=dict)
    verification_results: Mapping[str, Any] = field(default_factory=dict)
    project_audit_scorecard: Mapping[str, Any] = field(default_factory=dict)
    project_audit_findings: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    scenario_branches: Sequence[Mapping[str, Any]] = field(default_factory=tuple)


@dataclass(frozen=True)
class RepoBrainTopoCoreV6AdapterConfig:
    """Configuration for building inert TopoCore v6 request previews."""

    default_task_type: str = "unknown"
    default_limits: Mapping[str, Any] = field(
        default_factory=lambda: {
            "max_candidates": 8,
            "preview_only": True,
        }
    )


@dataclass(frozen=True)
class RepoBrainV6RequestPreview:
    """Plain request preview for future TopoCore v6 public-facade integration."""

    task_type: str
    query: str
    candidates: tuple[dict[str, Any], ...]
    limits: dict[str, Any]
    policy: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a plain Python dictionary without any runtime side effects."""

        return {
            "task_type": self.task_type,
            "query": self.query,
            "candidates": [dict(item) for item in self.candidates],
            "limits": dict(self.limits),
            "policy": dict(self.policy),
        }


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _sanitize_preview_value(value: Any) -> Any:
    if value is None or isinstance(value, (bool, float, int, str)):
        return value
    if _is_mapping(value):
        return _sanitize_preview_mapping(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return [_sanitize_preview_value(item) for item in value]
    return str(value)


def _sanitize_preview_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        normalized_key = _normalize_text(key)
        if not normalized_key:
            continue
        if normalized_key.lower() in _FORBIDDEN_OUTPUT_KEYS:
            continue
        safe[normalized_key] = _sanitize_preview_value(value)
    return safe


def _sanitize_candidate_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in metadata.items():
        normalized_key = _normalize_text(key)
        if not normalized_key:
            continue
        lowered = normalized_key.lower()
        if lowered in _UNSAFE_CANDIDATE_METADATA_KEYS:
            raise RepoBrainV6AdapterError(
                f"Unsafe candidate metadata key blocked: {normalized_key}"
            )
        if lowered in _FORBIDDEN_OUTPUT_KEYS:
            continue
        safe[normalized_key] = _sanitize_preview_value(value)
    return safe


def _build_candidate_preview(candidate: RepoBrainV6CandidateRef) -> dict[str, Any]:
    chunk_id = _normalize_text(candidate.chunk_id)
    if not chunk_id:
        raise RepoBrainV6AdapterError("Candidate chunk_id must be non-empty.")

    preview = {
        "chunk_id": chunk_id,
        "score_local": float(candidate.score_local),
    }
    metadata = _sanitize_candidate_metadata(candidate.metadata)
    if metadata:
        preview["metadata"] = metadata
    return preview


def _select_task_type(bundle: RepoBrainV6SummaryBundle, default_task_type: str) -> str:
    explicit_task_type = _normalize_text(bundle.task_type)
    if explicit_task_type:
        return explicit_task_type

    candidate_task_type = _normalize_text(bundle.intent_summary.get("task_type_candidate"))
    if candidate_task_type:
        return candidate_task_type

    command_task_type = _normalize_text(bundle.intent_summary.get("command"))
    if command_task_type:
        return command_task_type

    return default_task_type


class RepoBrainTopoCoreV6Adapter:
    """Build inert request previews for future TopoCore v6 public-facade use.

    This adapter does not import TopoCore v6, does not call TopoCore v6, and
    does not change current RepoBrain runtime behavior. It is intended only for
    future public-facade integration planning and compatibility testing.
    """

    def __init__(self, config: RepoBrainTopoCoreV6AdapterConfig | None = None) -> None:
        self._config = config or RepoBrainTopoCoreV6AdapterConfig()

    def build_policy_payload(self, bundle: RepoBrainV6SummaryBundle) -> dict[str, Any]:
        """Build a safe policy payload preview without any live v6 call."""

        return {
            "intent_summary": _sanitize_preview_mapping(bundle.intent_summary),
            "pr_context_summary": _sanitize_preview_mapping(bundle.pr_context_summary),
            "evidence_summary": _sanitize_preview_mapping(bundle.evidence_summary),
            "unknowns_summary": _sanitize_preview_mapping(bundle.unknowns_summary),
            "risk_items": [
                _sanitize_preview_mapping(item)
                for item in bundle.risk_items
            ],
            "review_draft_summary": _sanitize_preview_mapping(bundle.review_draft_summary),
            "fix_draft_summary": _sanitize_preview_mapping(bundle.fix_draft_summary),
            "verification_results": _sanitize_preview_mapping(bundle.verification_results),
            "project_audit_scorecard": _sanitize_preview_mapping(bundle.project_audit_scorecard),
            "project_audit_findings": [
                _sanitize_preview_mapping(item)
                for item in bundle.project_audit_findings
            ],
            "scenario_branches": [
                _sanitize_preview_mapping(item)
                for item in bundle.scenario_branches
            ],
        }

    def build_request_preview(self, bundle: RepoBrainV6SummaryBundle) -> RepoBrainV6RequestPreview:
        """Build a future TopoCore v6 request preview without any runtime wiring."""

        query = _normalize_text(bundle.query)
        if not query:
            raise RepoBrainV6AdapterError("Adapter preview requires a non-empty query.")

        task_type = _select_task_type(bundle, self._config.default_task_type)
        limits = dict(self._config.default_limits)
        limits.update(_sanitize_preview_mapping(bundle.limits))

        return RepoBrainV6RequestPreview(
            task_type=task_type,
            query=query,
            candidates=tuple(_build_candidate_preview(item) for item in bundle.candidates),
            limits=limits,
            policy=self.build_policy_payload(bundle),
        )


__all__ = [
    "RepoBrainTopoCoreV6Adapter",
    "RepoBrainTopoCoreV6AdapterConfig",
    "RepoBrainV6AdapterError",
    "RepoBrainV6CandidateRef",
    "RepoBrainV6RequestPreview",
    "RepoBrainV6SummaryBundle",
]
