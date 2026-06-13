from __future__ import annotations

from repobrain.github_native_queue import (
    QUEUE_CONTRACT_VERSION,
    TRANSPORT_MODE_GITHUB_APP_QUEUE,
    build_queue_request,
    compute_request_id,
    normalize_queue_command,
    render_queue_marker,
    validate_queue_request,
)


def test_queue_contract_version_and_request_id_are_stable() -> None:
    assert QUEUE_CONTRACT_VERSION == "repobrain.github_native_request_queue.v1"

    first = compute_request_id(["owner/repo", "41", "18", "audit", "partner-pilot"])
    second = compute_request_id(["owner/repo", "41", "18", "audit", "partner-pilot"])
    changed_comment = compute_request_id(["owner/repo", "41", "19", "audit", "partner-pilot"])
    changed_command = compute_request_id(["owner/repo", "41", "18", "score", "partner-pilot"])

    assert first == second
    assert changed_comment != first
    assert changed_command != first
    assert first.startswith("rbq_")


def test_issue_queue_request_validates_and_renders_public_safe_marker() -> None:
    command = normalize_queue_command("/repobrain audit Focus on queue safety.", "partner-pilot")
    request = build_queue_request(
        {
            "repository_full_name": "owner/repo",
            "repository_id_marker": "123",
            "event_kind": "issue",
            "issue_number": 41,
            "source_comment_id": 18,
            "source_comment_url": "https://github.com/owner/repo/issues/41#issuecomment-18",
            "actor_login": "partner-user",
            "created_at": "2026-06-13T12:00:00Z",
            "producer": "RepoBrain-Action",
            "producer_ref": "main",
            "workflow_run_id": "999",
            "workflow_run_attempt": "1",
        },
        command,
    )

    problems = validate_queue_request(request)
    marker = render_queue_marker(request, visible_markdown="RepoBrain request queued for private control-plane processing.")

    assert not problems
    assert request.to_payload()["contract_version"] == QUEUE_CONTRACT_VERSION
    assert request.to_payload()["transport_mode"] == TRANSPORT_MODE_GITHUB_APP_QUEUE
    assert "<!-- repobrain:queue:v1" in marker
    assert '"status": "queued"' in marker
    assert "RepoBrain request queued for private control-plane processing." in marker
    assert "authorization" not in marker.lower()
    assert "bearer " not in marker.lower()
    assert "ghp_" not in marker.lower()
    assert "github_pat_" not in marker.lower()
    assert ".topocore-v6" not in marker.lower()
    assert "api_url" not in marker.lower()
    assert "repobrain_hosted_api_url" not in marker.lower()


def test_pull_request_queue_request_validates() -> None:
    command = normalize_queue_command("/repobrain audit --profile premium Focus on queue safety.", "premium")
    request = build_queue_request(
        {
            "repository_full_name": "owner/repo",
            "repository_id_marker": "123",
            "event_kind": "pull_request",
            "issue_number": 52,
            "pull_request_number": 52,
            "source_comment_id": 81,
            "actor_login": "partner-user",
            "head_sha": "head456",
            "base_sha": "base123",
            "created_at": "2026-06-13T12:00:00Z",
            "producer": "RepoBrain-Action",
            "producer_ref": "main",
            "workflow_run_id": "999",
        },
        command,
    )

    assert validate_queue_request(request) == []
    payload = request.to_payload()
    assert payload["event_kind"] == "pull_request"
    assert payload["pull_request_number"] == 52
    assert payload["profile"] == "premium"


def test_queue_request_rejects_missing_repository_identity() -> None:
    command = normalize_queue_command("/repobrain score", "partner-pilot")
    request = build_queue_request(
        {
            "repository_full_name": "",
            "event_kind": "issue",
            "issue_number": 41,
            "created_at": "2026-06-13T12:00:00Z",
            "producer": "RepoBrain-Action",
        },
        command,
    )

    problems = validate_queue_request(request)
    assert "repository_full_name_missing" in problems
