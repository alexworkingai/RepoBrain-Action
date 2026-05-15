"""Safe RepoBrain adapter for the public TopoCore v6 facade.

This module stays importable without ``topocore_v6`` installed. Preview
payload-building remains dependency-free and inert. Real TopoCore v6 loading is
dynamic and opt-in through explicit adapter methods only.
"""

from __future__ import annotations

import importlib
import re
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_UNSAFE_CANDIDATE_METADATA_KEYS = frozenset(
    {
        ".env",
        "api_key",
        "dotenv",
        "env",
        "hidden_prompt",
        "password",
        "private_key",
        "prompt",
        "raw_code",
        "raw_diff",
        "raw_text",
        "secret",
        "system_prompt",
        "token",
    }
)

_FORBIDDEN_OUTPUT_KEYS = frozenset(
    {
        ".env",
        "api_key",
        "compression_stats",
        "decide_raw",
        "dotenv",
        "env",
        "event_internals",
        "governance_internals",
        "hidden_prompt",
        "password",
        "private_key",
        "prompt",
        "raw_code",
        "raw_diff",
        "raw_query",
        "raw_query_text",
        "secret",
        "system_prompt",
        "token",
        "trace_internals",
    }
)

_REQUIRED_PUBLIC_SYMBOLS = (
    "create_topocore",
    "EngineRequest",
    "EngineQuery",
    "EngineCandidate",
    "ExternalDecisionView",
)

_REQUIRED_FACADE_METHODS = (
    "decide_external",
    "health",
)

_PATH_TOKEN_RE = re.compile(
    r"([A-Za-z]:\\[^\\\s]+(?:\\[^\\\s]+)*)|(/[^/\s]+(?:/[^/\s]+)*)"
)


class RepoBrainV6AdapterError(ValueError):
    """Raised when adapter input or API usage is unsafe or invalid."""


class RepoBrainV6AdapterRuntimeError(RepoBrainV6AdapterError):
    """Raised when dynamic TopoCore v6 loading or invocation fails safely."""


@dataclass(frozen=True)
class RepoBrainV6CandidateRef:
    """Safe candidate reference for RepoBrain preview and real v6 requests."""

    chunk_id: str
    score_local: float
    signature: Sequence[int] | None = None
    file_path: str | None = None
    line_start: int | None = None
    line_end: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RepoBrainV6SummaryBundle:
    """Validated RepoBrain summary bundle for preview and real v6 shaping."""

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
    """Configuration for future preview and real TopoCore v6 shaping."""

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
        """Return a plain dictionary without any runtime side effects."""

        return {
            "task_type": self.task_type,
            "query": self.query,
            "candidates": [dict(item) for item in self.candidates],
            "limits": dict(self.limits),
            "policy": dict(self.policy),
        }


@dataclass(frozen=True)
class RepoBrainV6RealRequestBundle:
    """Real TopoCore v6 request bundle built from safe RepoBrain summaries."""

    task_type: str
    query_text: str
    candidates: tuple[dict[str, Any], ...]
    limits: dict[str, Any]
    policy: dict[str, Any]
    engine_query: Any
    engine_candidates: tuple[Any, ...]
    engine_request: Any

    def to_debug_dict(self) -> dict[str, Any]:
        """Return a safe, JSON-serializable view of the request bundle."""

        return {
            "task_type": self.task_type,
            "query_text": self.query_text,
            "candidates": [dict(item) for item in self.candidates],
            "limits": dict(self.limits),
            "policy": dict(self.policy),
        }


@dataclass(frozen=True)
class RepoBrainV6ExternalDecision:
    """Safe RepoBrain view of TopoCore v6 external decision output."""

    status: str = ""
    action: str = ""
    reference_hash: str = ""
    selected_count: int = 0
    blocked: bool = False
    confidence_band: str = "unknown"
    message_code: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "action": self.action,
            "reference_hash": self.reference_hash,
            "selected_count": self.selected_count,
            "blocked": self.blocked,
            "confidence_band": self.confidence_band,
            "message_code": self.message_code,
        }


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def _sanitize_error_text(text: str) -> str:
    normalized = " ".join(str(text or "").split())
    return _PATH_TOKEN_RE.sub("[redacted-path]", normalized)


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


def _normalize_signature(value: Any) -> list[int] | None:
    if value is None:
        return None
    if isinstance(value, (str, bytes, bytearray)):
        raise RepoBrainV6AdapterError("Candidate signature must be a list of integers.")
    try:
        items = list(value)
    except TypeError as exc:  # pragma: no cover - defensive
        raise RepoBrainV6AdapterError("Candidate signature must be a list of integers.") from exc

    normalized: list[int] = []
    for item in items:
        try:
            normalized.append(int(item))
        except (TypeError, ValueError) as exc:
            raise RepoBrainV6AdapterError(
                "Candidate signature must contain only integers."
            ) from exc
    return normalized


def _normalize_optional_int(value: Any, *, label: str) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise RepoBrainV6AdapterError(f"{label} must be an integer when provided.") from exc


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


def _build_real_candidate_payload(candidate: RepoBrainV6CandidateRef) -> dict[str, Any]:
    chunk_id = _normalize_text(candidate.chunk_id)
    if not chunk_id:
        raise RepoBrainV6AdapterError("Candidate chunk_id must be non-empty.")

    metadata = _sanitize_candidate_metadata(candidate.metadata)

    signature = candidate.signature
    if signature is None and "signature" in metadata:
        signature = metadata["signature"]
    file_path = candidate.file_path
    if file_path is None and "file_path" in metadata:
        file_path = metadata["file_path"]
    line_start = candidate.line_start
    if line_start is None and "line_start" in metadata:
        line_start = metadata["line_start"]
    line_end = candidate.line_end
    if line_end is None and "line_end" in metadata:
        line_end = metadata["line_end"]

    payload: dict[str, Any] = {
        "chunk_id": chunk_id,
        "score_local": float(candidate.score_local),
    }
    normalized_signature = _normalize_signature(signature)
    if normalized_signature is not None:
        payload["signature"] = normalized_signature

    normalized_file_path = _normalize_text(file_path)
    if normalized_file_path:
        payload["file_path"] = normalized_file_path

    normalized_line_start = _normalize_optional_int(line_start, label="Candidate line_start")
    if normalized_line_start is not None:
        payload["line_start"] = normalized_line_start

    normalized_line_end = _normalize_optional_int(line_end, label="Candidate line_end")
    if normalized_line_end is not None:
        payload["line_end"] = normalized_line_end

    return payload


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


@contextmanager
def _temporary_sys_path(local_path: str | None = None) -> Iterator[None]:
    inserted = False
    candidate = ""
    try:
        if local_path:
            path_obj = Path(local_path)
            candidate = str(path_obj)
            if not path_obj.exists():
                raise RepoBrainV6AdapterRuntimeError(
                    "TopoCore v6 local path is not available."
                )
            if candidate not in sys.path:
                sys.path.insert(0, candidate)
                inserted = True
        yield
    finally:
        if inserted:
            try:
                sys.path.remove(candidate)
            except ValueError:
                pass


def load_topocore_v6_public_api(*, local_path: str | None = None) -> Any:
    """Dynamically load the public ``topocore_v6`` module.

    The load happens only on explicit adapter calls and never at module import
    time, so RepoBrain stays dependency-free in default CI.
    """

    try:
        with _temporary_sys_path(local_path):
            module = importlib.import_module("topocore_v6")
    except RepoBrainV6AdapterRuntimeError:
        raise
    except Exception as exc:  # pragma: no cover - exercised via tests
        raise RepoBrainV6AdapterRuntimeError(
            "TopoCore v6 public API is unavailable."
        ) from exc

    missing_symbols = [
        symbol for symbol in _REQUIRED_PUBLIC_SYMBOLS if not hasattr(module, symbol)
    ]
    if missing_symbols:
        joined = ",".join(sorted(missing_symbols))
        raise RepoBrainV6AdapterRuntimeError(
            f"TopoCore v6 public API is missing required symbols: {joined}"
        )
    return module


def _extract_safe_decision_text(value: Any) -> str:
    return _sanitize_error_text(_normalize_text(value))


class RepoBrainTopoCoreV6Adapter:
    """Build inert previews and explicit real-request bundles for TopoCore v6.

    Preview-building remains dependency-free and runtime-inert. Real TopoCore
    v6 request building and decision calls are opt-in through dedicated methods.
    """

    def __init__(self, config: RepoBrainTopoCoreV6AdapterConfig | None = None) -> None:
        self._config = config or RepoBrainTopoCoreV6AdapterConfig()

    def build_policy_payload(self, bundle: RepoBrainV6SummaryBundle) -> dict[str, Any]:
        """Build the legacy preview payload without any live v6 call."""

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

    def build_real_policy_payload(self, bundle: RepoBrainV6SummaryBundle) -> dict[str, Any]:
        """Build the real TopoCore v6 summary-family policy payload."""

        evidence_summary = _sanitize_preview_mapping(bundle.evidence_summary)
        unknowns_summary = _sanitize_preview_mapping(bundle.unknowns_summary)
        unknown_items = unknowns_summary.get("unknowns")
        if isinstance(unknown_items, list) and "unknown_count" not in evidence_summary:
            evidence_summary["unknown_count"] = len(unknown_items)

        project_audit_summary = {
            "pr_context": _sanitize_preview_mapping(bundle.pr_context_summary),
            "scorecard": _sanitize_preview_mapping(bundle.project_audit_scorecard),
            "findings": [
                _sanitize_preview_mapping(item)
                for item in bundle.project_audit_findings
            ],
        }

        risk_summary = {
            "risk_items": [
                _sanitize_preview_mapping(item)
                for item in bundle.risk_items
            ],
            "risk_count": len(bundle.risk_items),
        }

        scenario_summary = {
            "unknowns_summary": unknowns_summary,
            "scenario_branches": [
                _sanitize_preview_mapping(item)
                for item in bundle.scenario_branches
            ],
            "review_draft_summary": _sanitize_preview_mapping(bundle.review_draft_summary),
            "fix_draft_summary": _sanitize_preview_mapping(bundle.fix_draft_summary),
        }

        bit_matrix_summary = {
            "candidate_count": len(bundle.candidates),
            "candidate_ids": [
                _build_real_candidate_payload(candidate)["chunk_id"]
                for candidate in bundle.candidates
            ],
        }

        return {
            "evidence_summary": evidence_summary,
            "bit_matrix_summary": bit_matrix_summary,
            "verification_summary": _sanitize_preview_mapping(bundle.verification_results),
            "project_audit_summary": project_audit_summary,
            "risk_summary": risk_summary,
            "scenario_summary": scenario_summary,
        }

    def build_request_preview(self, bundle: RepoBrainV6SummaryBundle) -> RepoBrainV6RequestPreview:
        """Build a future TopoCore v6 request preview without runtime wiring."""

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

    def build_real_engine_request(
        self,
        bundle: RepoBrainV6SummaryBundle,
        *,
        local_path: str | None = None,
        topocore_public_api: Any | None = None,
    ) -> RepoBrainV6RealRequestBundle:
        """Build real public TopoCore v6 request objects from safe RepoBrain input."""

        query_text = _normalize_text(bundle.query)
        if not query_text:
            raise RepoBrainV6AdapterError("Real TopoCore v6 request requires a non-empty query.")

        public_api = topocore_public_api or load_topocore_v6_public_api(local_path=local_path)
        task_type = _select_task_type(bundle, self._config.default_task_type)
        limits = dict(self._config.default_limits)
        limits.update(_sanitize_preview_mapping(bundle.limits))
        policy = self.build_real_policy_payload(bundle)
        candidate_payloads = tuple(
            _build_real_candidate_payload(candidate)
            for candidate in bundle.candidates
        )

        try:
            engine_query = public_api.EngineQuery(text=query_text)
            engine_candidates = tuple(
                public_api.EngineCandidate(**payload)
                for payload in candidate_payloads
            )
            engine_request = public_api.EngineRequest(
                task_type=task_type,
                query=engine_query,
                candidates=list(engine_candidates),
                limits=limits,
                policy=policy,
            )
        except RepoBrainV6AdapterError:
            raise
        except Exception as exc:  # pragma: no cover - exercised through tests
            raise RepoBrainV6AdapterRuntimeError(
                "TopoCore v6 request construction failed."
            ) from exc

        return RepoBrainV6RealRequestBundle(
            task_type=task_type,
            query_text=query_text,
            candidates=candidate_payloads,
            limits=limits,
            policy=policy,
            engine_query=engine_query,
            engine_candidates=engine_candidates,
            engine_request=engine_request,
        )

    def decide_external_local(
        self,
        bundle: RepoBrainV6SummaryBundle,
        *,
        local_path: str | None = None,
        topocore_public_api: Any | None = None,
    ) -> RepoBrainV6ExternalDecision:
        """Call ``decide_external`` through the public facade for local/manual use."""

        public_api = topocore_public_api or load_topocore_v6_public_api(local_path=local_path)
        request_bundle = self.build_real_engine_request(
            bundle,
            local_path=local_path,
            topocore_public_api=public_api,
        )
        try:
            facade = public_api.create_topocore()
        except Exception as exc:  # pragma: no cover - exercised through tests
            raise RepoBrainV6AdapterRuntimeError(
                "TopoCore v6 facade creation failed."
            ) from exc

        missing_methods = [
            method for method in _REQUIRED_FACADE_METHODS if not hasattr(facade, method)
        ]
        if missing_methods:
            joined = ",".join(sorted(missing_methods))
            raise RepoBrainV6AdapterRuntimeError(
                f"TopoCore v6 facade is missing required methods: {joined}"
            )

        try:
            external_result = facade.decide_external(request_bundle.engine_request)
        except Exception as exc:  # pragma: no cover - exercised through tests
            raise RepoBrainV6AdapterRuntimeError(
                "TopoCore v6 external decision call failed."
            ) from exc

        return RepoBrainV6ExternalDecision(
            status=_extract_safe_decision_text(getattr(external_result, "status", "")),
            action=_extract_safe_decision_text(getattr(external_result, "action", "")),
            reference_hash=_extract_safe_decision_text(
                getattr(external_result, "reference_hash", "")
            ),
            selected_count=int(getattr(external_result, "selected_count", 0) or 0),
            blocked=bool(getattr(external_result, "blocked", False)),
            confidence_band=_extract_safe_decision_text(
                getattr(external_result, "confidence_band", "unknown")
            )
            or "unknown",
            message_code=_extract_safe_decision_text(
                getattr(external_result, "message_code", "")
            ),
        )


__all__ = [
    "RepoBrainTopoCoreV6Adapter",
    "RepoBrainTopoCoreV6AdapterConfig",
    "RepoBrainV6AdapterError",
    "RepoBrainV6AdapterRuntimeError",
    "RepoBrainV6CandidateRef",
    "RepoBrainV6ExternalDecision",
    "RepoBrainV6RealRequestBundle",
    "RepoBrainV6RequestPreview",
    "RepoBrainV6SummaryBundle",
    "load_topocore_v6_public_api",
]
