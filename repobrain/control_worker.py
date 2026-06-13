from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from repobrain.control_worker_github import (
    GitHubControlClientProtocol,
    InstalledRepository,
    IssueCommentRecord,
)
from repobrain.control_worker_result import (
    build_completed_result,
    build_failed_result,
    extract_control_worker_result_markers,
    render_control_worker_result_markdown,
)
from repobrain.github_native_queue import QueueRequest, extract_queue_markers
from repobrain.topocore_entrypoint import TopoCoreEntrypointAdapter, TopoCoreEntrypointError


CONTROL_WORKER_REQUEST_CONTRACT_VERSION = "repobrain.control_worker_request.v1"


@dataclass(frozen=True)
class ControlWorkerRequest:
    contract_version: str
    request_id: str
    queue_contract_version: str
    repository_full_name: str
    repository_owner: str
    repository_name: str
    issue_number: int
    pull_request_number: int | None
    event_kind: str
    command: str
    profile: str
    actor_login: str | None
    source_comment_id: int | None
    source_comment_url: str | None
    head_sha: str | None
    base_sha: str | None
    installation_identity_marker: str
    created_at: str
    observed_at: str
    requested_by: str
    transport_mode: str
    changed_files_summary: list[str]
    diff_summary: list[str]
    repository_metadata_summary: list[str]
    workflow_run_id: str | None = None
    workflow_run_attempt: str | None = None
    capability_request: dict[str, Any] | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "contract_version": self.contract_version,
            "request_id": self.request_id,
            "queue_contract_version": self.queue_contract_version,
            "repository_full_name": self.repository_full_name,
            "repository_owner": self.repository_owner,
            "repository_name": self.repository_name,
            "issue_number": self.issue_number,
            "event_kind": self.event_kind,
            "command": self.command,
            "profile": self.profile,
            "source_comment_id": self.source_comment_id,
            "source_comment_url": self.source_comment_url,
            "installation_identity_marker": self.installation_identity_marker,
            "created_at": self.created_at,
            "observed_at": self.observed_at,
            "requested_by": self.requested_by,
            "transport_mode": self.transport_mode,
            "changed_files_summary": list(self.changed_files_summary),
            "diff_summary": list(self.diff_summary),
            "repository_metadata_summary": list(self.repository_metadata_summary),
        }
        optional = {
            "pull_request_number": self.pull_request_number,
            "actor_login": self.actor_login,
            "head_sha": self.head_sha,
            "base_sha": self.base_sha,
            "workflow_run_id": self.workflow_run_id,
            "workflow_run_attempt": self.workflow_run_attempt,
            "capability_request": self.capability_request,
        }
        for key, value in optional.items():
            if value is None:
                continue
            payload[key] = value
        return payload


@dataclass(frozen=True)
class ProcessedQueueItem:
    request_id: str
    repository_full_name: str
    issue_number: int
    status: str
    command: str
    profile: str
    error_code: str | None = None


@dataclass(frozen=True)
class ControlWorkerRunSummary:
    repositories_scanned: int
    queue_markers_seen: int
    processed: int
    skipped_already_processed: int
    skipped_invalid_marker: int
    failed_topocore: int
    failed_post_result: int
    dry_run: bool
    items: list[ProcessedQueueItem]


def run_control_worker_once(
    github_client: GitHubControlClientProtocol,
    topocore_adapter: TopoCoreEntrypointAdapter,
    *,
    max_repositories: int = 20,
    max_queue_items: int = 50,
    dry_run: bool = False,
    now: datetime | None = None,
) -> ControlWorkerRunSummary:
    observed_at = _now_iso(now)
    repositories = github_client.list_installed_repositories(max_repositories=max_repositories)
    items: list[ProcessedQueueItem] = []
    queue_markers_seen = 0
    processed = 0
    skipped_already_processed = 0
    skipped_invalid_marker = 0
    failed_topocore = 0
    failed_post_result = 0
    global_seen = 0

    for repository in repositories:
        comments = github_client.list_recent_issue_comments(repository.full_name, limit=max_queue_items)
        result_status_by_request_id = _build_existing_result_index(comments)
        for comment in comments:
            parse_results = extract_queue_markers(comment.body)
            if not parse_results:
                continue
            for parse_result in parse_results:
                if global_seen >= max_queue_items:
                    break
                global_seen += 1
                queue_markers_seen += 1
                if not parse_result.ok or parse_result.request is None:
                    skipped_invalid_marker += 1
                    items.append(
                        ProcessedQueueItem(
                            request_id="invalid",
                            repository_full_name=repository.full_name,
                            issue_number=comment.issue_number,
                            status="skipped_invalid_marker",
                            command="unknown",
                            profile="unknown",
                            error_code=parse_result.error_code or "CONTROL_WORKER_QUEUE_MARKER_INVALID",
                        )
                    )
                    continue
                queue_request = parse_result.request
                if queue_request.status != "queued":
                    continue
                if result_status_by_request_id.get(queue_request.request_id) in {"completed", "failed", "superseded", "processing"}:
                    skipped_already_processed += 1
                    items.append(
                        ProcessedQueueItem(
                            request_id=queue_request.request_id,
                            repository_full_name=repository.full_name,
                            issue_number=comment.issue_number,
                            status="skipped_already_processed",
                            command=queue_request.command,
                            profile=queue_request.profile,
                            error_code="CONTROL_WORKER_REQUEST_ALREADY_PROCESSED",
                        )
                    )
                    continue
                control_request = build_control_worker_request(
                    repository=repository,
                    queue_request=queue_request,
                    comment=comment,
                    github_context=github_client.get_issue_or_pull_request_context(
                        repository.full_name,
                        issue_number=comment.issue_number,
                        is_pull_request=queue_request.event_kind == "pull_request",
                    ),
                    observed_at=observed_at,
                )
                if dry_run:
                    items.append(
                        ProcessedQueueItem(
                            request_id=queue_request.request_id,
                            repository_full_name=repository.full_name,
                            issue_number=comment.issue_number,
                            status="dry_run",
                            command=queue_request.command,
                            profile=queue_request.profile,
                        )
                    )
                    continue
                try:
                    adapter_result = topocore_adapter.invoke(control_request.to_payload())
                    public_result = build_completed_result(
                        request_id=control_request.request_id,
                        command=control_request.command,
                        profile=control_request.profile,
                        repository_full_name=control_request.repository_full_name,
                        issue_number=control_request.issue_number,
                        pull_request_number=control_request.pull_request_number,
                        backend=adapter_result.backend,
                        fallback=adapter_result.fallback,
                        score=adapter_result.score,
                        verdict=adapter_result.verdict,
                        blockers_summary=adapter_result.blockers_summary,
                        warnings_summary=adapter_result.warnings_summary,
                        evidence_summary=adapter_result.evidence_summary,
                        public_notes=adapter_result.public_notes,
                        processed_at=observed_at,
                        capability_markers=adapter_result.capability_markers,
                    )
                    github_client.post_issue_comment(
                        repository.full_name,
                        issue_number=control_request.issue_number,
                        body_markdown=render_control_worker_result_markdown(public_result),
                    )
                    processed += 1
                    result_status_by_request_id[queue_request.request_id] = "completed"
                    items.append(
                        ProcessedQueueItem(
                            request_id=queue_request.request_id,
                            repository_full_name=repository.full_name,
                            issue_number=comment.issue_number,
                            status="processed",
                            command=queue_request.command,
                            profile=queue_request.profile,
                        )
                    )
                except TopoCoreEntrypointError as exc:
                    failed_topocore += 1
                    failed_result = build_failed_result(
                        request_id=control_request.request_id,
                        command=control_request.command,
                        profile=control_request.profile,
                        repository_full_name=control_request.repository_full_name,
                        issue_number=control_request.issue_number,
                        pull_request_number=control_request.pull_request_number,
                        backend="private_topocore_entrypoint",
                        fallback="topocore_entrypoint_failed",
                        error_code=exc.code,
                        public_notes=[exc.message],
                        processed_at=observed_at,
                    )
                    try:
                        github_client.post_issue_comment(
                            repository.full_name,
                            issue_number=control_request.issue_number,
                            body_markdown=render_control_worker_result_markdown(failed_result),
                        )
                        result_status_by_request_id[queue_request.request_id] = "failed"
                    except Exception:
                        failed_post_result += 1
                        items.append(
                            ProcessedQueueItem(
                                request_id=queue_request.request_id,
                                repository_full_name=repository.full_name,
                                issue_number=comment.issue_number,
                                status="failed_post_result",
                                command=queue_request.command,
                                profile=queue_request.profile,
                                error_code="RESULT_POST_FAILED",
                            )
                        )
                        continue
                    items.append(
                        ProcessedQueueItem(
                            request_id=queue_request.request_id,
                            repository_full_name=repository.full_name,
                            issue_number=comment.issue_number,
                            status="failed_topocore",
                            command=queue_request.command,
                            profile=queue_request.profile,
                            error_code=exc.code,
                        )
                    )
                except Exception:
                    failed_post_result += 1
                    items.append(
                        ProcessedQueueItem(
                            request_id=queue_request.request_id,
                            repository_full_name=repository.full_name,
                            issue_number=comment.issue_number,
                            status="failed_post_result",
                            command=queue_request.command,
                            profile=queue_request.profile,
                            error_code="RESULT_POST_FAILED",
                        )
                    )
            if global_seen >= max_queue_items:
                break
        if global_seen >= max_queue_items:
            break

    return ControlWorkerRunSummary(
        repositories_scanned=len(repositories),
        queue_markers_seen=queue_markers_seen,
        processed=processed,
        skipped_already_processed=skipped_already_processed,
        skipped_invalid_marker=skipped_invalid_marker,
        failed_topocore=failed_topocore,
        failed_post_result=failed_post_result,
        dry_run=bool(dry_run),
        items=items,
    )


def build_control_worker_request(
    *,
    repository: InstalledRepository,
    queue_request: QueueRequest,
    comment: IssueCommentRecord,
    github_context: dict[str, Any],
    observed_at: str,
) -> ControlWorkerRequest:
    repository_owner, repository_name = repository.full_name.split("/", 1)
    changed_files_summary = [str(item).strip() for item in github_context.get("changed_files_summary", []) if str(item).strip()][:20]
    diff_summary = [str(item).strip() for item in github_context.get("diff_summary", []) if str(item).strip()][:10]
    repo_summary = [str(item).strip() for item in github_context.get("repository_metadata_summary", []) if str(item).strip()][:10]
    return ControlWorkerRequest(
        contract_version=CONTROL_WORKER_REQUEST_CONTRACT_VERSION,
        request_id=queue_request.request_id,
        queue_contract_version=queue_request.contract_version,
        repository_full_name=repository.full_name,
        repository_owner=repository_owner,
        repository_name=repository_name,
        issue_number=comment.issue_number,
        pull_request_number=queue_request.pull_request_number,
        event_kind=queue_request.event_kind,
        command=queue_request.command,
        profile=queue_request.profile,
        actor_login=queue_request.actor_login,
        source_comment_id=queue_request.source_comment_id,
        source_comment_url=queue_request.source_comment_url or comment.html_url,
        head_sha=str(github_context.get("head_sha", "") or queue_request.head_sha or "").strip() or None,
        base_sha=str(github_context.get("base_sha", "") or queue_request.base_sha or "").strip() or None,
        installation_identity_marker=repository.installation_identity_marker,
        created_at=queue_request.created_at,
        observed_at=observed_at,
        requested_by=queue_request.actor_login or comment.user_login or "unknown",
        transport_mode=queue_request.transport_mode,
        changed_files_summary=changed_files_summary,
        diff_summary=diff_summary,
        repository_metadata_summary=repo_summary,
        workflow_run_id=queue_request.workflow_run_id,
        workflow_run_attempt=queue_request.workflow_run_attempt,
        capability_request={
            "requested_output_kind": queue_request.requested_output_kind or "repository_audit",
            "score_authority": "TopoCore",
        },
    )


def _build_existing_result_index(comments: list[IssueCommentRecord]) -> dict[str, str]:
    status_by_request_id: dict[str, str] = {}
    for comment in comments:
        for parse_result in extract_control_worker_result_markers(comment.body):
            if not parse_result.ok or parse_result.result is None:
                continue
            status_by_request_id[parse_result.result.request_id] = parse_result.result.status
    return status_by_request_id


def _now_iso(now: datetime | None) -> str:
    current = now or datetime.now(timezone.utc)
    return current.replace(microsecond=0).isoformat().replace("+00:00", "Z")
