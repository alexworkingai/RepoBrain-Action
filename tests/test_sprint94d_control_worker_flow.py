from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from repobrain.control_worker import run_control_worker_once
from repobrain.control_worker_github import InstalledRepository, IssueCommentRecord
from repobrain.control_worker_result import build_completed_result, render_control_worker_result_markdown
from repobrain.github_native_queue import build_queue_request, normalize_queue_command, render_queue_marker
from repobrain.topocore_entrypoint import TopoCoreEntrypointError, TopoCoreEntrypointResponse


ROOT = Path(__file__).resolve().parents[1]


def _queue_comment_body(
    *,
    repo_full_name: str = "owner/repo",
    comment_body: str = "/repobrain score",
    event_kind: str = "issue",
    issue_number: int = 11,
    pull_request_number: int | None = None,
    profile: str | None = None,
    source_comment_id: int = 3001,
) -> str:
    command = normalize_queue_command(comment_body, profile)
    request = build_queue_request(
        {
            "repository_full_name": repo_full_name,
            "repository_id_marker": "123",
            "event_kind": event_kind,
            "issue_number": issue_number,
            "pull_request_number": pull_request_number,
            "source_comment_id": source_comment_id,
            "source_comment_url": f"https://github.com/{repo_full_name}/issues/{issue_number}#issuecomment-{source_comment_id}",
            "actor_login": "partner-user",
            "head_sha": "headsha" if pull_request_number else "",
            "base_sha": "basesha" if pull_request_number else "",
            "created_at": "2026-06-13T12:00:00Z",
            "producer": "RepoBrain-Action",
            "producer_ref": "main",
            "workflow_run_id": "55",
            "workflow_run_attempt": "1",
        },
        command,
    )
    return render_queue_marker(request)


@dataclass
class _FakeAdapter:
    response: TopoCoreEntrypointResponse
    payloads: list[dict]

    def invoke(self, request_payload: dict) -> TopoCoreEntrypointResponse:
        self.payloads.append(dict(request_payload))
        return self.response


class _FailingAdapter:
    def __init__(self, code: str = "TOPOCORE_ENTRYPOINT_FAILED", message: str = "Private processing failed safely.") -> None:
        self.code = code
        self.message = message

    def invoke(self, request_payload: dict) -> TopoCoreEntrypointResponse:
        raise TopoCoreEntrypointError(self.code, self.message)


class _FakeGitHubClient:
    def __init__(
        self,
        *,
        repositories: list[InstalledRepository],
        comments_by_repo: dict[str, list[IssueCommentRecord]],
        contexts: dict[tuple[str, int, bool], dict],
        fail_post: bool = False,
    ) -> None:
        self._repositories = repositories
        self._comments_by_repo = comments_by_repo
        self._contexts = contexts
        self._fail_post = fail_post
        self.posted_comments: list[tuple[str, int, str]] = []

    def list_installed_repositories(self, *, max_repositories: int) -> list[InstalledRepository]:
        return self._repositories[:max_repositories]

    def list_recent_issue_comments(self, repository_full_name: str, *, limit: int) -> list[IssueCommentRecord]:
        return self._comments_by_repo.get(repository_full_name, [])[:limit]

    def get_issue_or_pull_request_context(
        self,
        repository_full_name: str,
        *,
        issue_number: int,
        is_pull_request: bool,
    ) -> dict:
        return dict(self._contexts[(repository_full_name, issue_number, is_pull_request)])

    def post_issue_comment(self, repository_full_name: str, *, issue_number: int, body_markdown: str) -> None:
        if self._fail_post:
            raise RuntimeError("post failed")
        self.posted_comments.append((repository_full_name, issue_number, body_markdown))


def _repo(full_name: str = "owner/repo") -> InstalledRepository:
    return InstalledRepository(
        full_name=full_name,
        owner=full_name.split("/", 1)[0],
        name=full_name.split("/", 1)[1],
        installation_identity_marker="install-123",
    )


def _comment(*, issue_number: int, body: str, comment_id: int = 77, repo_full_name: str = "owner/repo") -> IssueCommentRecord:
    return IssueCommentRecord(
        id=comment_id,
        repository_full_name=repo_full_name,
        issue_number=issue_number,
        body=body,
        html_url=f"https://github.com/{repo_full_name}/issues/{issue_number}#issuecomment-{comment_id}",
        user_login="partner-user",
    )


def test_control_worker_processes_queued_score_issue_request() -> None:
    repo = _repo()
    queued_body = _queue_comment_body()
    client = _FakeGitHubClient(
        repositories=[repo],
        comments_by_repo={repo.full_name: [_comment(issue_number=11, body=queued_body)]},
        contexts={(repo.full_name, 11, False): {"repository_metadata_summary": ["Repository: owner/repo"], "diff_summary": [], "changed_files_summary": []}},
    )
    adapter = _FakeAdapter(
        response=TopoCoreEntrypointResponse(
            backend="private_topocore_stub",
            fallback="not_applicable",
            score=87,
            verdict="GOOD",
            blockers_summary=["No blockers."],
            warnings_summary=["No warnings."],
            evidence_summary=["Queue request processed safely."],
            public_notes=["Completed through private control worker."],
            capability_markers=["topocore.audit_score.v1"],
        ),
        payloads=[],
    )

    summary = run_control_worker_once(client, adapter, now=None)

    assert summary.processed == 1
    assert summary.failed_topocore == 0
    assert summary.failed_post_result == 0
    assert client.posted_comments
    posted = client.posted_comments[0][2]
    assert "rbq_" in posted
    assert "Score authority: TopoCore." in posted
    assert "LLM does not modify score." in posted
    assert "no patch/autofix" in posted
    assert adapter.payloads[0]["command"] == "score"
    assert adapter.payloads[0]["profile"] == "standard"
    assert adapter.payloads[0]["transport_mode"] == "github_app_queue"
    assert "api_url" not in adapter.payloads[0]
    assert "hosted_api" not in (ROOT / "repobrain/control_worker.py").read_text(encoding="utf-8").lower()


def test_control_worker_processes_premium_audit_pr_request() -> None:
    repo = _repo()
    queued_body = _queue_comment_body(
        comment_body="/repobrain audit --profile premium Focus on this PR.",
        event_kind="pull_request",
        issue_number=21,
        pull_request_number=21,
        profile="premium",
        source_comment_id=4001,
    )
    client = _FakeGitHubClient(
        repositories=[repo],
        comments_by_repo={repo.full_name: [_comment(issue_number=21, body=queued_body, comment_id=91)]},
        contexts={
            (repo.full_name, 21, True): {
                "repository_metadata_summary": ["Repository: owner/repo", "PR: 21"],
                "diff_summary": ["Changed files observed: 2"],
                "changed_files_summary": ["src/a.py", "tests/test_a.py"],
                "head_sha": "headsha",
                "base_sha": "basesha",
            }
        },
    )
    adapter = _FakeAdapter(
        response=TopoCoreEntrypointResponse(
            backend="private_topocore_stub",
            fallback="not_applicable",
            score=91,
            verdict="GOOD",
            blockers_summary=["No blockers."],
            warnings_summary=["Premium profile executed."],
            evidence_summary=["PR context was included."],
            public_notes=["Premium audit completed."],
            capability_markers=["topocore.audit_score.v1"],
        ),
        payloads=[],
    )

    summary = run_control_worker_once(client, adapter)

    assert summary.processed == 1
    payload = adapter.payloads[0]
    assert payload["command"] == "audit"
    assert payload["profile"] == "premium"
    assert payload["pull_request_number"] == 21
    assert payload["head_sha"] == "headsha"
    assert payload["base_sha"] == "basesha"
    assert payload["changed_files_summary"] == ["src/a.py", "tests/test_a.py"]


def test_control_worker_ignores_invalid_wrong_version_and_completed_markers() -> None:
    repo = _repo()
    valid_queued = _queue_comment_body(source_comment_id=5001)
    request_id = next(line for line in valid_queued.splitlines() if '"request_id"' in line).split(":")[1].strip().strip('",')
    completed = render_control_worker_result_markdown(
        build_completed_result(
            request_id=request_id,
            command="score",
            profile="standard",
            repository_full_name=repo.full_name,
            issue_number=31,
            pull_request_number=None,
            backend="private_topocore_stub",
            fallback="not_applicable",
            score=88,
            verdict="GOOD",
            blockers_summary=["No blockers."],
            warnings_summary=["Already processed."],
            evidence_summary=["Existing result marker."],
            public_notes=["Completed earlier."],
            processed_at="2026-06-13T12:30:00Z",
        )
    )
    wrong_version = valid_queued.replace("repobrain.github_native_request_queue.v1", "repobrain.github_native_request_queue.v0", 1)
    completed_status = valid_queued.replace('"status": "queued"', '"status": "completed"', 1)
    invalid_json = "<!-- repobrain:queue:v1 {not json} -->"
    client = _FakeGitHubClient(
        repositories=[repo],
        comments_by_repo={
            repo.full_name: [
                _comment(issue_number=31, body="hello", comment_id=1),
                _comment(issue_number=31, body=invalid_json, comment_id=2),
                _comment(issue_number=31, body=wrong_version, comment_id=3),
                _comment(issue_number=31, body=completed_status, comment_id=4),
                _comment(issue_number=31, body=valid_queued, comment_id=5),
                _comment(issue_number=31, body=completed, comment_id=6),
            ]
        },
        contexts={(repo.full_name, 31, False): {"repository_metadata_summary": [], "diff_summary": [], "changed_files_summary": []}},
    )
    adapter = _FakeAdapter(
        response=TopoCoreEntrypointResponse(
            backend="private_topocore_stub",
            fallback="not_applicable",
            score=80,
            verdict="GOOD",
            blockers_summary=["No blockers."],
            warnings_summary=["No warnings."],
            evidence_summary=["Would process if not deduplicated."],
            public_notes=["No-op."],
            capability_markers=["topocore.audit_score.v1"],
        ),
        payloads=[],
    )

    summary = run_control_worker_once(client, adapter)

    assert summary.processed == 0
    assert summary.skipped_invalid_marker == 2
    assert summary.skipped_already_processed == 1
    assert not client.posted_comments
    assert not adapter.payloads


def test_control_worker_dry_run_does_not_post_results() -> None:
    repo = _repo()
    client = _FakeGitHubClient(
        repositories=[repo],
        comments_by_repo={repo.full_name: [_comment(issue_number=41, body=_queue_comment_body(issue_number=41), comment_id=401)]},
        contexts={(repo.full_name, 41, False): {"repository_metadata_summary": [], "diff_summary": [], "changed_files_summary": []}},
    )
    adapter = _FakeAdapter(
        response=TopoCoreEntrypointResponse(
            backend="private_topocore_stub",
            fallback="not_applicable",
            score=82,
            verdict="GOOD",
            blockers_summary=["No blockers."],
            warnings_summary=["No warnings."],
            evidence_summary=["Dry run only."],
            public_notes=["Dry run."],
            capability_markers=["topocore.audit_score.v1"],
        ),
        payloads=[],
    )

    summary = run_control_worker_once(client, adapter, dry_run=True)

    assert summary.dry_run is True
    assert summary.processed == 0
    assert summary.items[0].status == "dry_run"
    assert not client.posted_comments
    assert not adapter.payloads


def test_control_worker_posts_safe_failed_result_when_topocore_fails() -> None:
    repo = _repo()
    client = _FakeGitHubClient(
        repositories=[repo],
        comments_by_repo={repo.full_name: [_comment(issue_number=51, body=_queue_comment_body(issue_number=51), comment_id=501)]},
        contexts={(repo.full_name, 51, False): {"repository_metadata_summary": [], "diff_summary": [], "changed_files_summary": []}},
    )

    summary = run_control_worker_once(client, _FailingAdapter("TOPOCORE_ENTRYPOINT_FAILED", "Private processing failed safely."))

    assert summary.processed == 0
    assert summary.failed_topocore == 1
    assert client.posted_comments
    posted = client.posted_comments[0][2]
    assert "Status: `failed`" in posted
    assert "Error code: `TOPOCORE_ENTRYPOINT_FAILED`" in posted
    assert "no patch/autofix" in posted


def test_control_worker_reports_result_post_failure() -> None:
    repo = _repo()
    client = _FakeGitHubClient(
        repositories=[repo],
        comments_by_repo={repo.full_name: [_comment(issue_number=61, body=_queue_comment_body(issue_number=61), comment_id=601)]},
        contexts={(repo.full_name, 61, False): {"repository_metadata_summary": [], "diff_summary": [], "changed_files_summary": []}},
        fail_post=True,
    )
    adapter = _FakeAdapter(
        response=TopoCoreEntrypointResponse(
            backend="private_topocore_stub",
            fallback="not_applicable",
            score=79,
            verdict="GOOD",
            blockers_summary=["No blockers."],
            warnings_summary=["No warnings."],
            evidence_summary=["Post will fail."],
            public_notes=["Completed."],
            capability_markers=["topocore.audit_score.v1"],
        ),
        payloads=[],
    )

    summary = run_control_worker_once(client, adapter)

    assert summary.failed_post_result == 1
    assert summary.items[0].status == "failed_post_result"
    assert summary.items[0].error_code == "RESULT_POST_FAILED"
