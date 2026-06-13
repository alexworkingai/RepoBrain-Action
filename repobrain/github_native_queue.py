from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping, Sequence


QUEUE_CONTRACT_VERSION = "repobrain.github_native_request_queue.v1"

TRANSPORT_MODE_AUTO = "auto"
TRANSPORT_MODE_HOSTED_API = "hosted_api"
TRANSPORT_MODE_GITHUB_APP_QUEUE = "github_app_queue"

VALID_TRANSPORT_MODES = {
    TRANSPORT_MODE_AUTO,
    TRANSPORT_MODE_HOSTED_API,
    TRANSPORT_MODE_GITHUB_APP_QUEUE,
}
SUPPORTED_QUEUE_COMMANDS = {"audit", "score"}
SUPPORTED_QUEUE_STATUSES = {"queued", "processing", "completed", "failed", "superseded"}

_REDACTION_MARKER = "[redacted]"
_UNSAFE_VALUE_SNIPPETS = (
    "authorization",
    "bearer ",
    "ghp_",
    "github_pat_",
    "header.payload.",
    "private key",
    "installation token",
    ".topocore-v6",
    "topocore_v6_local_path",
    "repobrain_hosted_api_url",
    "api_url",
)


def normalize_transport_mode(value: str | None) -> str:
    text = str(value or "").strip().lower()
    return text or TRANSPORT_MODE_AUTO


def _clean_text(value: object) -> str:
    return str(value or "").strip()


def _int_or_none(value: object) -> int | None:
    if isinstance(value, int):
        return value
    text = _clean_text(value)
    if text.isdigit():
        return int(text)
    return None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class QueueCommand:
    command: str
    profile: str
    raw: str
    requested_output_kind: str


@dataclass(frozen=True)
class QueueRequest:
    contract_version: str
    request_id: str
    status: str
    command: str
    profile: str
    repository_full_name: str
    repository_id_marker: str | None
    event_kind: str
    issue_number: int | None
    pull_request_number: int | None
    source_comment_id: int | None
    source_comment_url: str | None
    actor_login: str | None
    head_sha: str | None
    base_sha: str | None
    created_at: str
    producer: str
    producer_ref: str | None
    transport_mode: str
    workflow_run_id: str | None = None
    workflow_run_attempt: str | None = None
    changed_files_count: int | None = None
    requested_output_kind: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "contract_version": self.contract_version,
            "request_id": self.request_id,
            "status": self.status,
            "command": self.command,
            "profile": self.profile,
            "repository_full_name": self.repository_full_name,
            "event_kind": self.event_kind,
            "created_at": self.created_at,
            "producer": self.producer,
            "transport_mode": self.transport_mode,
        }
        optional_fields = {
            "repository_id_marker": self.repository_id_marker,
            "issue_number": self.issue_number,
            "pull_request_number": self.pull_request_number,
            "source_comment_id": self.source_comment_id,
            "source_comment_url": self.source_comment_url,
            "actor_login": self.actor_login,
            "workflow_run_id": self.workflow_run_id,
            "workflow_run_attempt": self.workflow_run_attempt,
            "head_sha": self.head_sha,
            "base_sha": self.base_sha,
            "changed_files_count": self.changed_files_count,
            "requested_output_kind": self.requested_output_kind,
            "producer_ref": self.producer_ref,
        }
        for key, value in optional_fields.items():
            if value is None:
                continue
            if isinstance(value, str) and not value.strip():
                continue
            payload[key] = value
        return payload


def normalize_queue_command(command_text: str, profile_input: str | None = None) -> QueueCommand:
    raw = _clean_text(command_text)
    lowered = raw.lower()
    if lowered.startswith("/repobrain score"):
        command = "score"
        requested_output_kind = "repository_score"
    elif lowered.startswith("/repobrain audit"):
        command = "audit"
        requested_output_kind = "repository_audit"
    else:
        raise ValueError("unsupported_queue_command")
    profile = _clean_text(profile_input).lower()
    if not profile and "--profile premium" in lowered:
        profile = "premium"
    if not profile:
        profile = "standard"
    return QueueCommand(
        command=command,
        profile=profile,
        raw=raw,
        requested_output_kind=requested_output_kind,
    )


def compute_request_id(parts: Sequence[str]) -> str:
    normalized = [str(item or "").strip() for item in parts if str(item or "").strip()]
    digest = hashlib.sha256("|".join(normalized).encode("utf-8")).hexdigest()
    return f"rbq_{digest[:24]}"


def build_queue_request(context: Mapping[str, Any], command: QueueCommand) -> QueueRequest:
    repository_full_name = _clean_text(context.get("repository_full_name"))
    event_kind = _clean_text(context.get("event_kind")).lower()
    issue_number = _int_or_none(context.get("issue_number"))
    pull_request_number = _int_or_none(context.get("pull_request_number"))
    source_comment_id = _int_or_none(context.get("source_comment_id"))
    head_sha = _clean_text(context.get("head_sha")) or None
    workflow_run_id = _clean_text(context.get("workflow_run_id")) or None
    request_id = compute_request_id(
        [
            repository_full_name,
            _clean_text(context.get("repository_id_marker")),
            str(issue_number or ""),
            str(pull_request_number or ""),
            str(source_comment_id or ""),
            command.command,
            command.profile,
            head_sha or "",
            workflow_run_id or "",
        ]
    )
    return QueueRequest(
        contract_version=QUEUE_CONTRACT_VERSION,
        request_id=request_id,
        status="queued",
        command=command.command,
        profile=command.profile,
        repository_full_name=repository_full_name,
        repository_id_marker=_clean_text(context.get("repository_id_marker")) or None,
        event_kind=event_kind,
        issue_number=issue_number,
        pull_request_number=pull_request_number,
        source_comment_id=source_comment_id,
        source_comment_url=_clean_text(context.get("source_comment_url")) or None,
        actor_login=_clean_text(context.get("actor_login")) or None,
        head_sha=head_sha,
        base_sha=_clean_text(context.get("base_sha")) or None,
        created_at=_clean_text(context.get("created_at")) or _utc_now_iso(),
        producer=_clean_text(context.get("producer")) or "RepoBrain-Action",
        producer_ref=_clean_text(context.get("producer_ref")) or None,
        transport_mode=TRANSPORT_MODE_GITHUB_APP_QUEUE,
        workflow_run_id=workflow_run_id,
        workflow_run_attempt=_clean_text(context.get("workflow_run_attempt")) or None,
        changed_files_count=_int_or_none(context.get("changed_files_count")),
        requested_output_kind=command.requested_output_kind,
    )


def _redact_string(value: str) -> str:
    lowered = value.lower()
    for snippet in _UNSAFE_VALUE_SNIPPETS:
        if snippet in lowered:
            return _REDACTION_MARKER
    return value


def redact_queue_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    def _redact(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {str(key): _redact(item) for key, item in value.items()}
        if isinstance(value, list):
            return [_redact(item) for item in value]
        if isinstance(value, str):
            return _redact_string(value)
        return value

    return {str(key): _redact(value) for key, value in payload.items()}


def validate_queue_request(request: QueueRequest) -> list[str]:
    problems: list[str] = []
    payload = request.to_payload()
    if not request.repository_full_name or "/" not in request.repository_full_name:
        problems.append("repository_full_name_missing")
    if request.event_kind not in {"issue", "pull_request"}:
        problems.append("event_kind_unsupported")
    if request.event_kind == "issue" and request.issue_number is None:
        problems.append("issue_number_missing")
    if request.event_kind == "pull_request" and request.pull_request_number is None:
        problems.append("pull_request_number_missing")
    if request.command not in SUPPORTED_QUEUE_COMMANDS:
        problems.append("queue_command_unsupported")
    if not request.profile:
        problems.append("profile_missing")
    if request.status != "queued":
        problems.append("queue_status_invalid")
    if request.transport_mode != TRANSPORT_MODE_GITHUB_APP_QUEUE:
        problems.append("transport_mode_invalid")
    if not request.created_at:
        problems.append("created_at_missing")
    if not request.producer:
        problems.append("producer_missing")
    if not request.request_id.startswith("rbq_"):
        problems.append("request_id_invalid")

    serialized = json.dumps(redact_queue_payload(payload), sort_keys=True).lower()
    for snippet in _UNSAFE_VALUE_SNIPPETS:
        if snippet in serialized:
            problems.append(f"unsafe_payload_snippet:{snippet}")
    if TRANSPORT_MODE_HOSTED_API in serialized:
        problems.append("hosted_api_active_transport_forbidden")
    return problems


def render_queue_marker(request: QueueRequest, *, visible_markdown: str | None = None) -> str:
    visible = _clean_text(visible_markdown) or "RepoBrain request queued for private control-plane processing."
    payload_json = json.dumps(redact_queue_payload(request.to_payload()), indent=2)
    return (
        f"{visible}\n\n"
        "<!-- repobrain:queue:v1\n"
        f"{payload_json}\n"
        "-->"
    )
