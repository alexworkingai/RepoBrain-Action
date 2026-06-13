from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Protocol
from urllib.parse import urlparse

import requests


class ControlWorkerGitHubError(RuntimeError):
    def __init__(self, code: str, message: str, *, http_status: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status


@dataclass(frozen=True)
class InstalledRepository:
    full_name: str
    owner: str
    name: str
    installation_identity_marker: str
    private: bool | None = None
    default_branch: str | None = None


@dataclass(frozen=True)
class IssueCommentRecord:
    id: int
    repository_full_name: str
    issue_number: int
    body: str
    html_url: str | None = None
    user_login: str | None = None
    updated_at: str | None = None


class GitHubControlClientProtocol(Protocol):
    def list_installed_repositories(self, *, max_repositories: int) -> list[InstalledRepository]: ...

    def list_recent_issue_comments(self, repository_full_name: str, *, limit: int) -> list[IssueCommentRecord]: ...

    def get_issue_or_pull_request_context(
        self,
        repository_full_name: str,
        *,
        issue_number: int,
        is_pull_request: bool,
    ) -> dict[str, Any]: ...

    def post_issue_comment(self, repository_full_name: str, *, issue_number: int, body_markdown: str) -> None: ...


class EnvGitHubControlClient:
    def __init__(
        self,
        token: str,
        *,
        base_url: str = "https://api.github.com",
        request_get: Any | None = None,
        request_post: Any | None = None,
        repository_allowlist: list[str] | None = None,
        installation_identity_marker: str | None = None,
    ) -> None:
        self._token = str(token or "").strip()
        self._base_url = base_url.rstrip("/")
        self._request_get = request_get or requests.get
        self._request_post = request_post or requests.post
        self._repository_allowlist = [item.strip() for item in (repository_allowlist or []) if item.strip()]
        self._installation_identity_marker = str(installation_identity_marker or "").strip() or "github_app_installation_token"
        if not self._token:
            raise ControlWorkerGitHubError(
                "CONTROL_WORKER_GITHUB_TOKEN_MISSING",
                "RepoBrain private control worker GitHub installation token is missing.",
            )

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> "EnvGitHubControlClient":
        env = environ or os.environ
        allowlist = str(env.get("REPOBRAIN_CONTROL_REPOSITORIES", "") or "").strip()
        return cls(
            str(env.get("REPOBRAIN_GITHUB_INSTALLATION_TOKEN", "") or "").strip(),
            repository_allowlist=[item.strip() for item in allowlist.split(",") if item.strip()],
            installation_identity_marker=str(env.get("REPOBRAIN_GITHUB_APP_INSTALLATION_ID", "") or "").strip() or None,
        )

    def list_installed_repositories(self, *, max_repositories: int) -> list[InstalledRepository]:
        if self._repository_allowlist:
            repos: list[InstalledRepository] = []
            for full_name in self._repository_allowlist[:max_repositories]:
                owner, name = _split_repo(full_name)
                repos.append(
                    InstalledRepository(
                        full_name=full_name,
                        owner=owner,
                        name=name,
                        installation_identity_marker=self._installation_identity_marker,
                    )
                )
            return repos
        data = self._get_json("/installation/repositories?per_page=100")
        repositories = data.get("repositories", []) if isinstance(data, dict) else []
        results: list[InstalledRepository] = []
        for repo in repositories[:max_repositories]:
            if not isinstance(repo, dict):
                continue
            full_name = str(repo.get("full_name", "") or "").strip()
            if not full_name or "/" not in full_name:
                continue
            owner, name = _split_repo(full_name)
            results.append(
                InstalledRepository(
                    full_name=full_name,
                    owner=owner,
                    name=name,
                    installation_identity_marker=self._installation_identity_marker,
                    private=bool(repo.get("private")) if "private" in repo else None,
                    default_branch=str(repo.get("default_branch", "") or "").strip() or None,
                )
            )
        return results

    def list_recent_issue_comments(self, repository_full_name: str, *, limit: int) -> list[IssueCommentRecord]:
        data = self._get_json(
            f"/repos/{repository_full_name}/issues/comments?per_page={min(max(limit, 1), 100)}&sort=updated&direction=desc"
        )
        if not isinstance(data, list):
            raise ControlWorkerGitHubError(
                "CONTROL_WORKER_QUEUE_SCAN_FAILED",
                "RepoBrain private control worker could not list repository issue comments.",
            )
        comments: list[IssueCommentRecord] = []
        for item in data[:limit]:
            if not isinstance(item, dict):
                continue
            issue_number = _parse_issue_number(item)
            if issue_number is None:
                continue
            user = item.get("user", {})
            comments.append(
                IssueCommentRecord(
                    id=int(item.get("id", 0) or 0),
                    repository_full_name=repository_full_name,
                    issue_number=issue_number,
                    body=str(item.get("body", "") or ""),
                    html_url=str(item.get("html_url", "") or "").strip() or None,
                    user_login=str(user.get("login", "") or "").strip() if isinstance(user, dict) else None,
                    updated_at=str(item.get("updated_at", "") or "").strip() or None,
                )
            )
        return comments

    def get_issue_or_pull_request_context(
        self,
        repository_full_name: str,
        *,
        issue_number: int,
        is_pull_request: bool,
    ) -> dict[str, Any]:
        issue_payload = self._get_json(f"/repos/{repository_full_name}/issues/{issue_number}")
        issue_context: dict[str, Any] = {
            "issue_title": str(issue_payload.get("title", "") or "").strip() if isinstance(issue_payload, dict) else "",
            "issue_state": str(issue_payload.get("state", "") or "").strip() if isinstance(issue_payload, dict) else "",
            "repository_metadata_summary": [f"Repository: {repository_full_name}", f"Issue number: {issue_number}"],
            "diff_summary": [],
            "changed_files_summary": [],
        }
        if not is_pull_request:
            return issue_context
        pr_payload = self._get_json(f"/repos/{repository_full_name}/pulls/{issue_number}")
        files_payload = self._get_json(f"/repos/{repository_full_name}/pulls/{issue_number}/files?per_page=100")
        changed_files: list[str] = []
        if isinstance(files_payload, list):
            changed_files = [str(item.get("filename", "") or "").strip() for item in files_payload if isinstance(item, dict)]
            changed_files = [item for item in changed_files if item]
        issue_context["head_sha"] = str(pr_payload.get("head", {}).get("sha", "") or "").strip() if isinstance(pr_payload, dict) else ""
        issue_context["base_sha"] = str(pr_payload.get("base", {}).get("sha", "") or "").strip() if isinstance(pr_payload, dict) else ""
        issue_context["changed_files_summary"] = changed_files[:20]
        issue_context["diff_summary"] = [f"Changed files observed: {len(changed_files)}"] if changed_files else []
        return issue_context

    def post_issue_comment(self, repository_full_name: str, *, issue_number: int, body_markdown: str) -> None:
        response = self._request_post(
            f"{self._base_url}/repos/{repository_full_name}/issues/{issue_number}/comments",
            headers=self._headers(),
            json={"body": str(body_markdown or "")},
            timeout=20,
        )
        status_code = int(getattr(response, "status_code", 0) or 0)
        if status_code >= 400:
            raise ControlWorkerGitHubError(
                "RESULT_POST_FAILED",
                "RepoBrain private control worker could not post the result comment.",
                http_status=status_code,
            )

    def _get_json(self, path: str) -> Any:
        response = self._request_get(
            f"{self._base_url}{path}",
            headers=self._headers(),
            timeout=20,
        )
        status_code = int(getattr(response, "status_code", 0) or 0)
        if status_code >= 400:
            raise ControlWorkerGitHubError(
                "CONTROL_WORKER_QUEUE_SCAN_FAILED",
                "RepoBrain private control worker GitHub API request failed.",
                http_status=status_code,
            )
        try:
            return response.json()
        except ValueError as exc:
            raise ControlWorkerGitHubError(
                "CONTROL_WORKER_QUEUE_SCAN_FAILED",
                "RepoBrain private control worker GitHub API returned invalid JSON.",
            ) from exc

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }


def _split_repo(full_name: str) -> tuple[str, str]:
    owner, name = str(full_name or "").strip().split("/", 1)
    return owner, name


def _parse_issue_number(payload: dict[str, Any]) -> int | None:
    issue_url = str(payload.get("issue_url", "") or "").strip()
    if issue_url:
        parsed = urlparse(issue_url)
        raw = parsed.path.rstrip("/").split("/")[-1]
        if raw.isdigit():
            return int(raw)
    html_url = str(payload.get("html_url", "") or "").strip()
    if html_url:
        parsed = urlparse(html_url)
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) >= 4 and parts[2] == "issues" and parts[3].isdigit():
            return int(parts[3])
    return None
