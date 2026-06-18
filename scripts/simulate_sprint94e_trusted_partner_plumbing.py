# ruff: noqa: E402
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from repobrain.control_worker import run_control_worker_once
from repobrain.control_worker_github import InstalledRepository, IssueCommentRecord
from repobrain.github_native_queue import build_queue_request, normalize_queue_command, render_queue_marker
from repobrain.topocore_entrypoint import TopoCoreEntrypointAdapter, TopoCoreEntrypointConfig


REPOS = (
    "alexworkingai/Elen-MCP-v.2.2.0",
    "alexworkingai/repobrain-community",
)
COMMANDS = (
    "/repobrain score",
    "/repobrain audit",
    "/repobrain audit --profile premium",
)
LEAKAGE_PATTERNS = (
    re.compile(r"authorization", re.IGNORECASE),
    re.compile(r"bearer", re.IGNORECASE),
    re.compile(r"\bghp_[A-Za-z0-9_]+\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]+\b"),
    re.compile(r"\.topocore-v6", re.IGNORECASE),
    re.compile(r"private[_ -]?checkout", re.IGNORECASE),
    re.compile(r"(?:[a-z]:\\|/)[^\n\"]*topocore", re.IGNORECASE),
)


@dataclass
class _FakeGitHubClient:
    repositories: list[InstalledRepository]
    comments_by_repo: dict[str, list[IssueCommentRecord]]
    contexts: dict[tuple[str, int, bool], dict[str, Any]]
    posted_comments: list[tuple[str, int, str]]

    def list_installed_repositories(self, *, max_repositories: int) -> list[InstalledRepository]:
        return self.repositories[:max_repositories]

    def list_recent_issue_comments(self, repository_full_name: str, *, limit: int) -> list[IssueCommentRecord]:
        return self.comments_by_repo.get(repository_full_name, [])[:limit]

    def get_issue_or_pull_request_context(
        self,
        repository_full_name: str,
        *,
        issue_number: int,
        is_pull_request: bool,
    ) -> dict[str, Any]:
        return dict(self.contexts[(repository_full_name, issue_number, is_pull_request)])

    def post_issue_comment(self, repository_full_name: str, *, issue_number: int, body_markdown: str) -> None:
        self.posted_comments.append((repository_full_name, issue_number, body_markdown))
        self.comments_by_repo.setdefault(repository_full_name, []).append(
            IssueCommentRecord(
                id=900000 + len(self.posted_comments),
                repository_full_name=repository_full_name,
                issue_number=issue_number,
                body=body_markdown,
                html_url=f"https://github.com/{repository_full_name}/issues/{issue_number}#issuecomment-{900000 + len(self.posted_comments)}",
                user_login="repobrain-bot",
            )
        )


def _build_fake_client() -> _FakeGitHubClient:
    repositories: list[InstalledRepository] = []
    comments_by_repo: dict[str, list[IssueCommentRecord]] = {}
    contexts: dict[tuple[str, int, bool], dict[str, Any]] = {}
    posted_comments: list[tuple[str, int, str]] = []
    issue_number = 10
    comment_id = 1000

    for repo_full_name in REPOS:
        owner, name = repo_full_name.split("/", 1)
        repositories.append(
            InstalledRepository(
                full_name=repo_full_name,
                owner=owner,
                name=name,
                installation_identity_marker="simulated_installation",
            )
        )
        repo_comments: list[IssueCommentRecord] = []
        for command_text in COMMANDS:
            issue_number += 1
            comment_id += 1
            command = normalize_queue_command(command_text, "premium" if "--profile premium" in command_text else None)
            request = build_queue_request(
                {
                    "repository_full_name": repo_full_name,
                    "repository_id_marker": "simulated_repo",
                    "event_kind": "issue",
                    "issue_number": issue_number,
                    "source_comment_id": comment_id,
                    "source_comment_url": f"https://github.com/{repo_full_name}/issues/{issue_number}#issuecomment-{comment_id}",
                    "actor_login": "trusted-partner-user",
                    "created_at": "2026-06-14T00:00:00Z",
                    "producer": "RepoBrain-Action",
                    "producer_ref": "validated-94e-ref",
                    "workflow_run_id": "94e-sim",
                    "workflow_run_attempt": "1",
                },
                command,
            )
            repo_comments.append(
                IssueCommentRecord(
                    id=comment_id,
                    repository_full_name=repo_full_name,
                    issue_number=issue_number,
                    body=render_queue_marker(request),
                    html_url=f"https://github.com/{repo_full_name}/issues/{issue_number}#issuecomment-{comment_id}",
                    user_login="trusted-partner-user",
                )
            )
            contexts[(repo_full_name, issue_number, False)] = {
                "repository_metadata_summary": [f"Repository: {repo_full_name}"],
                "diff_summary": [],
                "changed_files_summary": [],
            }
        comments_by_repo[repo_full_name] = repo_comments
    return _FakeGitHubClient(repositories, comments_by_repo, contexts, posted_comments)


def _leakage_scan(comments: list[tuple[str, int, str]]) -> bool:
    for _, _, body in comments:
        for pattern in LEAKAGE_PATTERNS:
            if pattern.search(body):
                return False
        if "hosted_api" in body.lower() or "api_url" in body.lower():
            return False
    return True


def main() -> int:
    client = _build_fake_client()
    adapter = TopoCoreEntrypointAdapter(TopoCoreEntrypointConfig(mode="stub"))

    first = run_control_worker_once(client, adapter, max_repositories=10, max_queue_items=20)
    second = run_control_worker_once(client, adapter, max_repositories=10, max_queue_items=20)

    queued_markers_found = sum(len(comments) for comments in client.comments_by_repo.values()) - len(client.posted_comments)
    leakage_ok = _leakage_scan(client.posted_comments)

    if first.processed != len(REPOS) * len(COMMANDS):
        print("Local simulation failed: first pass did not process all queued markers.")
        return 1
    if second.processed != 0 or second.skipped_already_processed < len(REPOS) * len(COMMANDS):
        print("Local simulation failed: idempotency check did not skip already processed markers.")
        return 1
    if not leakage_ok:
        print("Local simulation failed: leakage scan did not pass.")
        return 1

    summary = {
        "notice": "This is local plumbing simulation only and does not prove TRUSTED_PARTNER_BETA_READY.",
        "repos_simulated": list(REPOS),
        "commands_simulated": list(COMMANDS),
        "transport_mode": "github_app_queue",
        "queued_markers_found": queued_markers_found,
        "processed_count": first.processed,
        "skipped_duplicate_count": second.skipped_already_processed,
        "hosted_api_used": False,
        "api_url_used": False,
        "leakage_scan_pass": leakage_ok,
        "status": "SPRINT_94E_LOCAL_PLUMBING_SIMULATION_PASS",
    }
    print(summary["notice"])
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
