"""Sanitized decision-diff helper for future v5 primary / v6 advisory analysis.

This module is dependency-free. It does not import TopoCore v6, does not call
external systems, and does not change current RepoBrain runtime behavior.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any

_FORBIDDEN_FIELDS = frozenset(
    {
        "api_key",
        "artifact_internals",
        "compression_stats",
        "decide_raw",
        "dotenv",
        "env",
        "event_internals",
        "governance_internals",
        "password",
        "private_key",
        "prompt",
        "raw_code",
        "raw_query",
        "raw_trace",
        "secret",
        "system_prompt",
        "token",
        "trace",
    }
)

_ALLOWED_V5_FIELDS = frozenset(
    {
        "command",
        "route",
        "selected_chunk_ids",
        "execution_mode",
        "llm_intent",
        "llm_decision_reason_code",
        "verification_gate_decision",
        "verification_gate_reason",
        "safe_reason_code",
        "has_patch_candidate",
        "no_patch_reason",
    }
)

_ALLOWED_V6_FIELDS = frozenset(
    {
        "status",
        "action",
        "selected_chunk_ids",
        "safe_reason_code",
        "needs_more_information_reason",
        "blocked_reason_code",
        "confidence_hint",
        "task_type",
    }
)

_V5_PROCEED_ROUTES = frozenset({"answer", "fast", "proceed", "respond"})
_V5_BLOCKED_ROUTES = frozenset({"blocked", "no_patch", "refuse", "stop", "wait"})
_V5_NEEDS_INFO_ROUTES = frozenset({"investigate", "needs_more_information"})

_V6_PROCEED_STATUSES = frozenset({"proceed", "ready"})
_V6_PROCEED_ACTIONS = frozenset({"proceed", "respond"})
_V6_BLOCKED_STATUSES = frozenset({"blocked", "stop"})
_V6_BLOCKED_ACTIONS = frozenset({"blocked", "manual_only", "stop"})
_V6_NEEDS_INFO_STATUSES = frozenset({"needs_more_information"})
_V6_NEEDS_INFO_ACTIONS = frozenset({"investigate"})


class RepoBrainV6DecisionDiffError(ValueError):
    """Raised when decision-diff snapshots are unsafe or invalid."""


class DecisionDiffSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DecisionDiffCategory(str, Enum):
    ALIGNED = "aligned"
    ROUTE_STATUS_MISMATCH = "route_status_mismatch"
    EVIDENCE_SELECTION_MISMATCH = "evidence_selection_mismatch"
    V6_MORE_CONSERVATIVE = "v6_more_conservative"
    V6_MORE_PERMISSIVE = "v6_more_permissive"
    NEEDS_MORE_INFORMATION_MISMATCH = "needs_more_information_mismatch"
    BLOCKED_MISMATCH = "blocked_mismatch"
    FIX_GOVERNANCE_MISMATCH = "fix_governance_mismatch"
    INSUFFICIENT_DATA = "insufficient_data"
    ADAPTER_CONTRACT_ISSUE = "adapter_contract_issue"
    PLATFORM_SEMANTIC_GAP = "platform_semantic_gap"


@dataclass(frozen=True)
class RepoBrainV5DecisionSnapshot:
    command: str = ""
    route: str = ""
    selected_chunk_ids: tuple[str, ...] = field(default_factory=tuple)
    execution_mode: str = ""
    llm_intent: str = ""
    llm_decision_reason_code: str = ""
    verification_gate_decision: str = ""
    verification_gate_reason: str = ""
    safe_reason_code: str = ""
    has_patch_candidate: bool | None = None
    no_patch_reason: str = ""


@dataclass(frozen=True)
class TopoCoreV6AdvisorySnapshot:
    status: str = ""
    action: str = ""
    selected_chunk_ids: tuple[str, ...] = field(default_factory=tuple)
    safe_reason_code: str = ""
    needs_more_information_reason: str = ""
    blocked_reason_code: str = ""
    confidence_hint: str = ""
    task_type: str = ""


@dataclass(frozen=True)
class DecisionDiffFinding:
    category: DecisionDiffCategory
    severity: DecisionDiffSeverity
    message: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": dict(self.details),
        }


@dataclass(frozen=True)
class DecisionDiffReport:
    overall_severity: DecisionDiffSeverity
    command: str
    task_type: str
    v5_route: str
    v6_status: str
    v6_action: str
    overlap_count: int
    v5_selected_count: int
    v6_selected_count: int
    overlap_ids: tuple[str, ...]
    findings: tuple[DecisionDiffFinding, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_severity": self.overall_severity.value,
            "command": self.command,
            "task_type": self.task_type,
            "v5_route": self.v5_route,
            "v6_status": self.v6_status,
            "v6_action": self.v6_action,
            "overlap_count": self.overlap_count,
            "v5_selected_count": self.v5_selected_count,
            "v6_selected_count": self.v6_selected_count,
            "overlap_ids": list(self.overlap_ids),
            "findings": [item.to_dict() for item in self.findings],
        }


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_chunk_ids(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        items = [value]
    else:
        items = list(value)
    normalized = sorted({_normalize_text(item) for item in items if _normalize_text(item)})
    return tuple(normalized)


def _sanitize_mapping(mapping: Mapping[str, Any], *, allowed_fields: frozenset[str]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in mapping.items():
        normalized_key = _normalize_text(key)
        if not normalized_key:
            continue
        lowered = normalized_key.lower()
        if lowered in _FORBIDDEN_FIELDS:
            raise RepoBrainV6DecisionDiffError(
                f"Forbidden decision-diff field detected: {normalized_key}"
            )
        if normalized_key not in allowed_fields:
            continue
        safe[normalized_key] = value
    return safe


def _coerce_v5_snapshot(snapshot: RepoBrainV5DecisionSnapshot | Mapping[str, Any]) -> RepoBrainV5DecisionSnapshot:
    if isinstance(snapshot, RepoBrainV5DecisionSnapshot):
        return snapshot
    if is_dataclass(snapshot):
        snapshot = asdict(snapshot)
    if not isinstance(snapshot, Mapping):
        raise RepoBrainV6DecisionDiffError("v5 snapshot must be a mapping or RepoBrainV5DecisionSnapshot.")

    payload = _sanitize_mapping(snapshot, allowed_fields=_ALLOWED_V5_FIELDS)
    payload["command"] = _normalize_text(payload.get("command"))
    payload["route"] = _normalize_text(payload.get("route"))
    payload["selected_chunk_ids"] = _normalize_chunk_ids(payload.get("selected_chunk_ids"))
    payload["execution_mode"] = _normalize_text(payload.get("execution_mode"))
    payload["llm_intent"] = _normalize_text(payload.get("llm_intent"))
    payload["llm_decision_reason_code"] = _normalize_text(payload.get("llm_decision_reason_code"))
    payload["verification_gate_decision"] = _normalize_text(payload.get("verification_gate_decision"))
    payload["verification_gate_reason"] = _normalize_text(payload.get("verification_gate_reason"))
    payload["safe_reason_code"] = _normalize_text(payload.get("safe_reason_code"))
    payload["no_patch_reason"] = _normalize_text(payload.get("no_patch_reason"))
    return RepoBrainV5DecisionSnapshot(**payload)


def _coerce_v6_snapshot(snapshot: TopoCoreV6AdvisorySnapshot | Mapping[str, Any]) -> TopoCoreV6AdvisorySnapshot:
    if isinstance(snapshot, TopoCoreV6AdvisorySnapshot):
        return snapshot
    if is_dataclass(snapshot):
        snapshot = asdict(snapshot)
    if not isinstance(snapshot, Mapping):
        raise RepoBrainV6DecisionDiffError("v6 advisory snapshot must be a mapping or TopoCoreV6AdvisorySnapshot.")

    payload = _sanitize_mapping(snapshot, allowed_fields=_ALLOWED_V6_FIELDS)
    payload["status"] = _normalize_text(payload.get("status"))
    payload["action"] = _normalize_text(payload.get("action"))
    payload["selected_chunk_ids"] = _normalize_chunk_ids(payload.get("selected_chunk_ids"))
    payload["safe_reason_code"] = _normalize_text(payload.get("safe_reason_code"))
    payload["needs_more_information_reason"] = _normalize_text(payload.get("needs_more_information_reason"))
    payload["blocked_reason_code"] = _normalize_text(payload.get("blocked_reason_code"))
    payload["confidence_hint"] = _normalize_text(payload.get("confidence_hint"))
    payload["task_type"] = _normalize_text(payload.get("task_type"))
    return TopoCoreV6AdvisorySnapshot(**payload)


def _severity_rank(value: DecisionDiffSeverity) -> int:
    return {
        DecisionDiffSeverity.INFO: 0,
        DecisionDiffSeverity.LOW: 1,
        DecisionDiffSeverity.MEDIUM: 2,
        DecisionDiffSeverity.HIGH: 3,
    }[value]


def _max_severity(findings: tuple[DecisionDiffFinding, ...]) -> DecisionDiffSeverity:
    if not findings:
        return DecisionDiffSeverity.INFO
    return max(findings, key=lambda item: _severity_rank(item.severity)).severity


def _v5_stance(route: str) -> str:
    lowered = route.lower()
    if lowered in _V5_PROCEED_ROUTES:
        return "proceed"
    if lowered in _V5_BLOCKED_ROUTES:
        return "blocked"
    if lowered in _V5_NEEDS_INFO_ROUTES:
        return "needs_more_information"
    return "unknown"


def _v6_stance(status: str, action: str) -> str:
    lowered_status = status.lower()
    lowered_action = action.lower()
    if lowered_status in _V6_BLOCKED_STATUSES or lowered_action in _V6_BLOCKED_ACTIONS:
        return "blocked"
    if lowered_status in _V6_NEEDS_INFO_STATUSES or lowered_action in _V6_NEEDS_INFO_ACTIONS:
        return "needs_more_information"
    if lowered_status in _V6_PROCEED_STATUSES or lowered_action in _V6_PROCEED_ACTIONS:
        return "proceed"
    return "unknown"


def build_decision_diff_report(
    *,
    v5_snapshot: RepoBrainV5DecisionSnapshot | Mapping[str, Any],
    v6_advisory_snapshot: TopoCoreV6AdvisorySnapshot | Mapping[str, Any],
) -> DecisionDiffReport:
    v5 = _coerce_v5_snapshot(v5_snapshot)
    v6 = _coerce_v6_snapshot(v6_advisory_snapshot)

    findings: list[DecisionDiffFinding] = []
    v5_stance = _v5_stance(v5.route)
    v6_stance = _v6_stance(v6.status, v6.action)
    overlap_ids = tuple(sorted(set(v5.selected_chunk_ids) & set(v6.selected_chunk_ids)))

    if not v5.route or (not v6.status and not v6.action):
        findings.append(
            DecisionDiffFinding(
                category=DecisionDiffCategory.INSUFFICIENT_DATA,
                severity=DecisionDiffSeverity.MEDIUM,
                message="Insufficient sanitized decision data for a stable comparison.",
            )
        )

    if v5_stance == "proceed" and v6_stance == "proceed":
        findings.append(
            DecisionDiffFinding(
                category=DecisionDiffCategory.ALIGNED,
                severity=DecisionDiffSeverity.INFO,
                message="v5 primary and v6 advisory are both proceed-like.",
            )
        )

    if v5_stance == "proceed" and v6_stance == "needs_more_information":
        findings.extend(
            (
                DecisionDiffFinding(
                    category=DecisionDiffCategory.V6_MORE_CONSERVATIVE,
                    severity=DecisionDiffSeverity.MEDIUM,
                    message="v6 advisory is more conservative than v5 primary.",
                ),
                DecisionDiffFinding(
                    category=DecisionDiffCategory.NEEDS_MORE_INFORMATION_MISMATCH,
                    severity=DecisionDiffSeverity.MEDIUM,
                    message="v5 primary proceeds while v6 advisory requests more information.",
                ),
            )
        )

    if v5_stance == "proceed" and v6_stance == "blocked":
        findings.extend(
            (
                DecisionDiffFinding(
                    category=DecisionDiffCategory.V6_MORE_CONSERVATIVE,
                    severity=DecisionDiffSeverity.HIGH,
                    message="v6 advisory blocks an input that v5 primary would proceed with.",
                ),
                DecisionDiffFinding(
                    category=DecisionDiffCategory.BLOCKED_MISMATCH,
                    severity=DecisionDiffSeverity.HIGH,
                    message="v5 primary proceeds while v6 advisory blocks.",
                ),
            )
        )

    if v5_stance in {"blocked", "needs_more_information"} and v6_stance == "proceed":
        findings.extend(
            (
                DecisionDiffFinding(
                    category=DecisionDiffCategory.V6_MORE_PERMISSIVE,
                    severity=DecisionDiffSeverity.HIGH,
                    message="v6 advisory is more permissive than v5 primary.",
                ),
                DecisionDiffFinding(
                    category=DecisionDiffCategory.BLOCKED_MISMATCH,
                    severity=DecisionDiffSeverity.HIGH,
                    message="v5 primary blocks or waits while v6 advisory proceeds.",
                ),
            )
        )

    if v5.selected_chunk_ids or v6.selected_chunk_ids:
        if overlap_ids and (
            len(overlap_ids) != len(v5.selected_chunk_ids)
            or len(overlap_ids) != len(v6.selected_chunk_ids)
        ):
            findings.append(
                DecisionDiffFinding(
                    category=DecisionDiffCategory.EVIDENCE_SELECTION_MISMATCH,
                    severity=DecisionDiffSeverity.LOW,
                    message="v5 and v6 share some evidence selection but not complete overlap.",
                    details={
                        "overlap_count": len(overlap_ids),
                        "overlap_ids": list(overlap_ids),
                    },
                )
            )
        elif not overlap_ids and v5.selected_chunk_ids and v6.selected_chunk_ids:
            findings.append(
                DecisionDiffFinding(
                    category=DecisionDiffCategory.EVIDENCE_SELECTION_MISMATCH,
                    severity=DecisionDiffSeverity.MEDIUM,
                    message="v5 and v6 selected different safe chunk identifiers.",
                    details={
                        "overlap_count": 0,
                        "overlap_ids": [],
                    },
                )
            )

    if (v5.command.lower() == "fix" or v6.task_type.lower() == "fix") and (
        v5.no_patch_reason or v5.has_patch_candidate is False
    ) and v6_stance == "proceed":
        findings.append(
            DecisionDiffFinding(
                category=DecisionDiffCategory.FIX_GOVERNANCE_MISMATCH,
                severity=DecisionDiffSeverity.HIGH,
                message="v5 fix governance is no-patch or blocked while v6 advisory appears proceed-like.",
            )
        )

    if v5_stance == "unknown" or v6_stance == "unknown":
        findings.append(
            DecisionDiffFinding(
                category=DecisionDiffCategory.PLATFORM_SEMANTIC_GAP,
                severity=DecisionDiffSeverity.LOW,
                message="One side uses a route/status/action that does not map cleanly into the current diff taxonomy.",
            )
        )

    report = DecisionDiffReport(
        overall_severity=_max_severity(tuple(findings)),
        command=v5.command,
        task_type=v6.task_type or v5.command,
        v5_route=v5.route,
        v6_status=v6.status,
        v6_action=v6.action,
        overlap_count=len(overlap_ids),
        v5_selected_count=len(v5.selected_chunk_ids),
        v6_selected_count=len(v6.selected_chunk_ids),
        overlap_ids=overlap_ids,
        findings=tuple(findings),
    )
    return report


__all__ = [
    "DecisionDiffCategory",
    "DecisionDiffFinding",
    "DecisionDiffReport",
    "DecisionDiffSeverity",
    "RepoBrainV5DecisionSnapshot",
    "RepoBrainV6DecisionDiffError",
    "TopoCoreV6AdvisorySnapshot",
    "build_decision_diff_report",
]
