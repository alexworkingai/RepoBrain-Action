from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Mapping


CONTROL_WORKER_RESULT_CONTRACT_VERSION = "repobrain.control_worker_result.v1"
CONTROL_WORKER_RESULT_MARKER_PREFIX = "<!-- repobrain:control-worker-result:v1"

_ALLOWED_RESULT_STATUSES = {"completed", "failed"}
_UNSAFE_PATTERNS = (
    re.compile(r"(?i)authorization"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]+"),
    re.compile(r"\bghp_[A-Za-z0-9_]+\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]+\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"(?i)topocore[^\n]*token"),
    re.compile(r"(?i)\\.topocore-v6"),
    re.compile(r"(?i)private[_ -]?checkout"),
    re.compile(r"(?i)api_url"),
    re.compile(r"(?i)(?:[a-z]:\\|/)[^\n\"]*topocore"),
)
_RESULT_MARKER_RE = re.compile(r"<!--\s*repobrain:control-worker-result:v1\s*(\{.*?\})\s*-->", re.DOTALL)


class ControlWorkerResultError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ControlWorkerPublicResult:
    contract_version: str
    request_id: str
    status: str
    command: str
    profile: str
    repository_full_name: str
    issue_number: int
    pull_request_number: int | None
    backend: str
    fallback: str
    score: int | None
    verdict: str | None
    blockers_summary: list[str]
    warnings_summary: list[str]
    evidence_summary: list[str]
    public_notes: list[str]
    safety_footer: list[str]
    processed_at: str
    producer: str
    error_code: str | None = None
    capability_markers: list[str] | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "contract_version": self.contract_version,
            "request_id": self.request_id,
            "status": self.status,
            "command": self.command,
            "profile": self.profile,
            "repository_full_name": self.repository_full_name,
            "issue_number": self.issue_number,
            "backend": self.backend,
            "fallback": self.fallback,
            "blockers_summary": list(self.blockers_summary),
            "warnings_summary": list(self.warnings_summary),
            "evidence_summary": list(self.evidence_summary),
            "public_notes": list(self.public_notes),
            "safety_footer": list(self.safety_footer),
            "processed_at": self.processed_at,
            "producer": self.producer,
        }
        if self.pull_request_number is not None:
            payload["pull_request_number"] = self.pull_request_number
        if self.score is not None:
            payload["score"] = self.score
        if self.verdict:
            payload["verdict"] = self.verdict
        if self.error_code:
            payload["error_code"] = self.error_code
        if self.capability_markers:
            payload["capability_markers"] = list(self.capability_markers)
        return payload


@dataclass(frozen=True)
class ControlWorkerResultParseResult:
    ok: bool
    result: ControlWorkerPublicResult | None = None
    error_code: str = ""


DEFAULT_SAFETY_FOOTER = [
    "Safety: informational only; no patch/autofix, no file changes, no branch/commit/PR created.",
    "Not a merge/security/production approval.",
    "Score authority: TopoCore.",
    "LLM does not modify score.",
]


def _safe_line_list(values: list[str] | tuple[str, ...] | None, *, fallback: str) -> list[str]:
    items = [str(item or "").strip() for item in (values or []) if str(item or "").strip()]
    return items or [fallback]


def _assert_public_safe(value: Any) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _assert_public_safe(item)
        return
    if isinstance(value, list):
        for item in value:
            _assert_public_safe(item)
        return
    if isinstance(value, str):
        for pattern in _UNSAFE_PATTERNS:
            if pattern.search(value):
                raise ControlWorkerResultError(
                    "CONTROL_WORKER_SECRET_LEAKAGE_GUARD",
                    "Control worker public result contains an unsafe token, private key, path, or internal marker.",
                )


def build_completed_result(
    *,
    request_id: str,
    command: str,
    profile: str,
    repository_full_name: str,
    issue_number: int,
    pull_request_number: int | None,
    backend: str,
    fallback: str,
    score: int | None,
    verdict: str | None,
    blockers_summary: list[str] | None,
    warnings_summary: list[str] | None,
    evidence_summary: list[str] | None,
    public_notes: list[str] | None,
    processed_at: str,
    producer: str = "RepoBrain private control worker",
    capability_markers: list[str] | None = None,
) -> ControlWorkerPublicResult:
    result = ControlWorkerPublicResult(
        contract_version=CONTROL_WORKER_RESULT_CONTRACT_VERSION,
        request_id=str(request_id or "").strip(),
        status="completed",
        command=str(command or "").strip().lower(),
        profile=str(profile or "standard").strip(),
        repository_full_name=str(repository_full_name or "").strip(),
        issue_number=int(issue_number),
        pull_request_number=pull_request_number,
        backend=str(backend or "private_topocore_entrypoint").strip(),
        fallback=str(fallback or "not_applicable").strip(),
        score=score,
        verdict=str(verdict or "").strip() or None,
        blockers_summary=_safe_line_list(blockers_summary, fallback="No blocking issues were reported."),
        warnings_summary=_safe_line_list(warnings_summary, fallback="No warning conditions were reported."),
        evidence_summary=_safe_line_list(evidence_summary, fallback="Bounded GitHub context was processed through the private control worker."),
        public_notes=_safe_line_list(public_notes, fallback="Private control worker processing completed successfully."),
        safety_footer=list(DEFAULT_SAFETY_FOOTER),
        processed_at=str(processed_at or "").strip(),
        producer=producer,
        capability_markers=[str(item).strip() for item in (capability_markers or []) if str(item).strip()] or None,
    )
    validate_control_worker_result(result)
    return result


def build_failed_result(
    *,
    request_id: str,
    command: str,
    profile: str,
    repository_full_name: str,
    issue_number: int,
    pull_request_number: int | None,
    backend: str,
    fallback: str,
    error_code: str,
    public_notes: list[str] | None,
    processed_at: str,
    producer: str = "RepoBrain private control worker",
) -> ControlWorkerPublicResult:
    result = ControlWorkerPublicResult(
        contract_version=CONTROL_WORKER_RESULT_CONTRACT_VERSION,
        request_id=str(request_id or "").strip(),
        status="failed",
        command=str(command or "").strip().lower(),
        profile=str(profile or "standard").strip(),
        repository_full_name=str(repository_full_name or "").strip(),
        issue_number=int(issue_number),
        pull_request_number=pull_request_number,
        backend=str(backend or "private_topocore_entrypoint").strip(),
        fallback=str(fallback or "not_applicable").strip(),
        score=None,
        verdict=None,
        blockers_summary=["Private control worker processing did not complete."],
        warnings_summary=["No mutation was attempted."],
        evidence_summary=["The queue request was validated, but the private worker returned a public-safe failure."],
        public_notes=_safe_line_list(public_notes, fallback="Private control worker processing failed safely."),
        safety_footer=list(DEFAULT_SAFETY_FOOTER),
        processed_at=str(processed_at or "").strip(),
        producer=producer,
        error_code=str(error_code or "TOPOCORE_ENTRYPOINT_FAILED").strip(),
    )
    validate_control_worker_result(result)
    return result


def validate_control_worker_result(result: ControlWorkerPublicResult) -> list[str]:
    problems: list[str] = []
    if result.contract_version != CONTROL_WORKER_RESULT_CONTRACT_VERSION:
        problems.append("invalid_contract_version")
    if result.status not in _ALLOWED_RESULT_STATUSES:
        problems.append("invalid_status")
    if not result.request_id.startswith("rbq_"):
        problems.append("invalid_request_id")
    if not result.repository_full_name or "/" not in result.repository_full_name:
        problems.append("invalid_repository_full_name")
    if not result.processed_at:
        problems.append("processed_at_missing")
    if not result.producer:
        problems.append("producer_missing")
    try:
        _assert_public_safe(result.to_payload())
    except ControlWorkerResultError as exc:
        problems.append(exc.code)
    if problems:
        raise ControlWorkerResultError(
            "CONTROL_WORKER_RESULT_INVALID",
            ", ".join(problems),
        )
    return []


def render_control_worker_result_markdown(result: ControlWorkerPublicResult) -> str:
    validate_control_worker_result(result)
    title = "### ✅ RepoBrain private control result" if result.status == "completed" else "### 🛑 RepoBrain private control result"
    lines = [
        title,
        f"- Request ID: `{result.request_id}`",
        f"- Status: `{result.status}`",
        f"- Command: `{result.command}`",
        f"- Profile: `{result.profile}`",
        f"- Repository: `{result.repository_full_name}`",
        f"- Backend: `{result.backend}`",
        f"- Fallback: `{result.fallback}`",
    ]
    if result.score is not None:
        lines.append(f"- Score: `{result.score}`")
    if result.verdict:
        lines.append(f"- Verdict: `{result.verdict}`")
    if result.error_code:
        lines.append(f"- Error code: `{result.error_code}`")
    lines.extend([
        "",
        "### Blockers",
        *(f"- {item}" for item in result.blockers_summary),
        "",
        "### Warnings",
        *(f"- {item}" for item in result.warnings_summary),
        "",
        "### Evidence summary",
        *(f"- {item}" for item in result.evidence_summary),
        "",
        "### Public notes",
        *(f"- {item}" for item in result.public_notes),
        "",
        "### Safety",
        *(f"- {item}" for item in result.safety_footer),
        "",
        CONTROL_WORKER_RESULT_MARKER_PREFIX,
        json.dumps(result.to_payload(), indent=2, ensure_ascii=False),
        "-->",
    ])
    return "\n".join(lines)


def extract_control_worker_result_markers(text: str) -> list[ControlWorkerResultParseResult]:
    results: list[ControlWorkerResultParseResult] = []
    body = str(text or "")
    for match in _RESULT_MARKER_RE.finditer(body):
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            results.append(ControlWorkerResultParseResult(ok=False, error_code="invalid_control_worker_result_json"))
            continue
        if not isinstance(payload, Mapping):
            results.append(ControlWorkerResultParseResult(ok=False, error_code="invalid_control_worker_result_shape"))
            continue
        try:
            result = ControlWorkerPublicResult(
                contract_version=str(payload.get("contract_version", "") or "").strip(),
                request_id=str(payload.get("request_id", "") or "").strip(),
                status=str(payload.get("status", "") or "").strip().lower(),
                command=str(payload.get("command", "") or "").strip().lower(),
                profile=str(payload.get("profile", "") or "").strip(),
                repository_full_name=str(payload.get("repository_full_name", "") or "").strip(),
                issue_number=int(payload.get("issue_number", 0) or 0),
                pull_request_number=payload.get("pull_request_number"),
                backend=str(payload.get("backend", "") or "").strip(),
                fallback=str(payload.get("fallback", "") or "").strip(),
                score=payload.get("score") if isinstance(payload.get("score"), int) else None,
                verdict=str(payload.get("verdict", "") or "").strip() or None,
                blockers_summary=[str(item).strip() for item in payload.get("blockers_summary", []) if str(item).strip()],
                warnings_summary=[str(item).strip() for item in payload.get("warnings_summary", []) if str(item).strip()],
                evidence_summary=[str(item).strip() for item in payload.get("evidence_summary", []) if str(item).strip()],
                public_notes=[str(item).strip() for item in payload.get("public_notes", []) if str(item).strip()],
                safety_footer=[str(item).strip() for item in payload.get("safety_footer", []) if str(item).strip()],
                processed_at=str(payload.get("processed_at", "") or "").strip(),
                producer=str(payload.get("producer", "") or "").strip(),
                error_code=str(payload.get("error_code", "") or "").strip() or None,
                capability_markers=[str(item).strip() for item in payload.get("capability_markers", []) if str(item).strip()] or None,
            )
            validate_control_worker_result(result)
        except Exception:
            results.append(ControlWorkerResultParseResult(ok=False, error_code="invalid_control_worker_result_payload"))
            continue
        results.append(ControlWorkerResultParseResult(ok=True, result=result))
    return results
