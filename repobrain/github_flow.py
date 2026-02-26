from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any

import requests

from repobrain.ask import answer_question, make_provider
from repobrain.commands import parse_command
from repobrain.config import load_config
from repobrain.formatting import format_github_comment, format_pr_review_comment, format_refusal_comment
from repobrain.index_store import build_index, load_index
from repobrain.retrieve import retrieve_adaptive
from repobrain.review import build_pr_review
from repobrain.security import detect_injection_or_exfiltration
from repobrain.tky_provider import CandidateChunk

HELP_TEXT = """RepoBrain command examples:
- /repobrain help
- /repobrain ask How does provider selection work?
- /repobrain locate TKYProvider
- /repobrain explain retrieve_topk
- /repobrain review
"""

BOT_MARKER = "[bot]"


@dataclass(frozen=True)
class EventContext:
    comment_text: str = ""
    issue_number: int | None = None
    comment_id: int | None = None
    comment_user_login: str = ""
    is_pull_request: bool = False


def _load_event_payload(event_path: Path | None) -> dict[str, Any]:
    if event_path is None or not event_path.exists():
        return {}

    try:
        payload = json.loads(event_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    return payload if isinstance(payload, dict) else {}


def _parse_optional_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return parse_issue_number(value)
    return None


def parse_issue_number(value: str | None) -> int | None:
    """Parse issue number from CLI/UI input (`1` or `#1`)."""
    raw = (value or "").strip()
    if not raw or raw == "0":
        return None
    if raw.startswith("#"):
        raw = raw[1:].strip()
    if not raw.isdigit():
        raise ValueError(f"Invalid --issue-number: {value}")
    return int(raw)


def extract_event_context_from_event(event_path: Path | None) -> EventContext:
    """Extract relevant issue_comment fields from a GitHub event payload file."""
    payload = _load_event_payload(event_path)
    comment = payload.get("comment", {})
    issue = payload.get("issue", {})

    comment_body = ""
    comment_id = None
    comment_user_login = ""
    if isinstance(comment, dict):
        body = comment.get("body")
        comment_body = body if isinstance(body, str) else ""

        comment_id = _parse_optional_int(comment.get("id"))
        user = comment.get("user", {})
        if isinstance(user, dict):
            login = user.get("login")
            if isinstance(login, str):
                comment_user_login = login

    issue_number = None
    is_pull_request = False
    if isinstance(issue, dict):
        issue_number = _parse_optional_int(issue.get("number"))
        pull_request = issue.get("pull_request")
        is_pull_request = isinstance(pull_request, dict)

    return EventContext(
        comment_text=comment_body,
        issue_number=issue_number,
        comment_id=comment_id,
        comment_user_login=comment_user_login,
        is_pull_request=is_pull_request,
    )


def extract_comment_text_from_event(event_path: Path | None) -> str:
    return extract_event_context_from_event(event_path).comment_text


def extract_issue_number_from_event(event_path: Path | None) -> int | None:
    return extract_event_context_from_event(event_path).issue_number


def extract_comment_id_from_event(event_path: Path | None) -> int | None:
    return extract_event_context_from_event(event_path).comment_id


def extract_comment_user_login_from_event(event_path: Path | None) -> str:
    return extract_event_context_from_event(event_path).comment_user_login


def extract_is_pull_request_from_event(event_path: Path | None) -> bool:
    return extract_event_context_from_event(event_path).is_pull_request


def build_issue_comment_url(repo: str, issue_number: int) -> str:
    """Build GitHub REST URL for creating an issue comment."""
    return f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"


def build_reaction_url(repo: str, comment_id: int) -> str:
    """Build GitHub REST URL for adding a reaction to an issue comment."""
    return f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}/reactions"


def build_pr_files_url(repo: str, pull_number: int) -> str:
    """Build GitHub REST URL for listing PR files."""
    return f"https://api.github.com/repos/{repo}/pulls/{pull_number}/files?per_page=100"


class GitHubClient:
    """Minimal GitHub REST client for issue comments, reactions, and PR files."""

    def __init__(self, repo: str, token: str) -> None:
        self.repo = repo
        self.token = token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def create_issue_comment(self, issue_number: int, body_markdown: str) -> None:
        """POST a comment to a GitHub Issue or PR thread."""
        response = requests.post(
            build_issue_comment_url(self.repo, issue_number),
            json={"body": body_markdown},
            headers=self._headers(),
            timeout=15,
        )
        response.raise_for_status()

    def add_reaction_to_issue_comment(self, comment_id: int, content: str = "eyes") -> None:
        """Add a reaction (default 👀) to an issue comment."""
        response = requests.post(
            build_reaction_url(self.repo, comment_id),
            json={"content": content},
            headers=self._headers(),
            timeout=15,
        )
        response.raise_for_status()

    def get_pull_files(self, pull_number: int) -> list[dict[str, Any]]:
        """Fetch PR files metadata from GitHub REST API."""
        response = requests.get(
            build_pr_files_url(self.repo, pull_number),
            headers=self._headers(),
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)]


def extract_repo_from_env() -> str:
    return os.environ.get("GITHUB_REPOSITORY", "").strip()


def extract_sha_from_env() -> str:
    return os.environ.get("GITHUB_SHA", "").strip()


def _is_bot_login(login: str) -> bool:
    normalized = (login or "").strip().lower()
    return bool(normalized) and BOT_MARKER in normalized


def _build_post_client() -> GitHubClient:
    repo = extract_repo_from_env()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not repo:
        raise ValueError("GITHUB_REPOSITORY is required when dry_run=False")
    if not token:
        raise ValueError("GITHUB_TOKEN is required when dry_run=False")
    return GitHubClient(repo=repo, token=token)


def _internal_reactions_enabled() -> bool:
    return os.environ.get("RB_DISABLE_INTERNAL_REACTIONS", "").strip() != "1"


def question_from_command(cmd: str, query: str) -> str:
    """Convert parsed command into a retrieval/answering question string."""
    if cmd == "review":
        return "Review repository code and highlight issues"
    if cmd == "locate":
        return f"Locate in repository: {query}"
    if cmd == "explain":
        return f"Explain in repository: {query}"
    return query


def load_or_build_chunks(repo_root: Path, index_path: Path) -> list[CandidateChunk]:
    """Load prebuilt index, or build and persist it if missing."""
    if not should_build_index(index_path):
        return load_index(index_path)

    index_path.parent.mkdir(parents=True, exist_ok=True)
    build_index(root=repo_root, out_zip=index_path, store_text=False)
    return load_index(index_path)


def should_build_index(index_path: Path) -> bool:
    """Return True when index file is missing and needs to be built."""
    return not index_path.exists()


def _build_qa_markdown(
    *,
    repo_root: Path,
    cmd: str,
    query: str,
    tky_mode: str,
    remote_url: str,
    api_key: str,
) -> str:
    cfg = load_config(repo_root)
    index_path = repo_root / "artifacts" / "index-package.zip"
    question = question_from_command(cmd, query)
    chunks = load_or_build_chunks(repo_root, index_path)
    candidates, route_mode = retrieve_adaptive(question, chunks, cfg)

    max_sources = cfg.max_sources_fast if route_mode == "FAST" else cfg.max_sources_deep

    provider = make_provider(
        tky_mode,
        remote_url=remote_url or None,
        api_key=api_key or None,
    )
    result = answer_question(
        question=question,
        candidates=candidates,
        provider=provider,
        limits={
            "max_sources": max_sources,
            "min_score_keep": cfg.min_score_keep,
            "route_hint": route_mode,
        },
    )
    return format_github_comment(
        result.answer_text,
        result.evidence,
        result.audit_summary,
        result.next_steps,
        command=cmd,
        repo=extract_repo_from_env() or None,
        sha=extract_sha_from_env() or None,
    )


def _build_review_markdown(
    *,
    is_pull_request: bool,
    issue_number: int | None,
    dry_run: bool,
    client: GitHubClient | None,
) -> str:
    if not is_pull_request:
        return "Review is available in Pull Requests. Run /repobrain review in a PR discussion."

    if issue_number is None:
        return "Review is available in Pull Requests. Pull request number was not detected."

    files: list[dict[str, Any]]
    if dry_run:
        files = []
    else:
        if client is None:
            raise ValueError("GitHub client is required for PR review in post mode")
        files = client.get_pull_files(pull_number=issue_number)

    review = build_pr_review(files)
    return format_pr_review_comment(review)


def run_github_flow(
    *,
    repo_root: Path,
    dry_run: bool,
    comment_text: str,
    issue_number: int | None,
    tky_mode: str = "baseline",
    remote_url: str = "",
    api_key: str = "",
    event_path: Path | None = None,
) -> str:
    """Run RepoBrain GitHub flow in dry-run or post mode."""
    event_ctx = extract_event_context_from_event(event_path)
    source_text = (comment_text or "").strip() or event_ctx.comment_text.strip()
    resolved_issue_number = issue_number if issue_number is not None else event_ctx.issue_number
    mode_label = "DRY_RUN" if dry_run else "POST_MODE"

    if not source_text:
        print(f"Mode={mode_label}")
        print("Cmd=help")
        print("Query=")
        print(HELP_TEXT.strip())
        return "IGNORED"

    if _is_bot_login(event_ctx.comment_user_login):
        print(f"Mode={mode_label}")
        print("Cmd=ignored_bot")
        print("Query=")
        print(f"Ignored bot comment from {event_ctx.comment_user_login}")
        return "IGNORED_BOT"

    if not source_text.startswith("/repobrain"):
        print(f"Mode={mode_label}")
        print("Cmd=ignored")
        print("Query=")
        print("Ignored: comment does not start with /repobrain")
        return "IGNORED"

    parsed = parse_command(source_text)
    cmd = parsed["cmd"]
    query = parsed["query"]
    print(f"Mode={mode_label}")
    print(f"Cmd={cmd}")
    print(f"Query={query}")

    sec = detect_injection_or_exfiltration(source_text)
    if sec["blocked"]:
        body_markdown = format_refusal_comment(
            reason="Possible prompt-injection / exfiltration attempt was blocked.",
            audit_summary={
                "route": "REFUSE",
                "security": {
                    "blocked": sec["blocked"],
                    "risk": sec["risk"],
                    "signals": sec["signals"],
                },
            },
        )

        if dry_run:
            print(body_markdown)
            return "DRY_RUN_OK"

        if resolved_issue_number is None:
            raise ValueError("issue_number is required when dry_run=False")

        client = _build_post_client()
        if _internal_reactions_enabled() and event_ctx.comment_id is not None:
            client.add_reaction_to_issue_comment(comment_id=event_ctx.comment_id, content="eyes")
        client.create_issue_comment(issue_number=resolved_issue_number, body_markdown=body_markdown)
        print(f"Posted comment to issue #{resolved_issue_number}")
        return "POSTED_OK"

    client: GitHubClient | None = None
    if not dry_run:
        if resolved_issue_number is None:
            raise ValueError("issue_number is required when dry_run=False")
        client = _build_post_client()
        if _internal_reactions_enabled() and event_ctx.comment_id is not None:
            client.add_reaction_to_issue_comment(comment_id=event_ctx.comment_id, content="eyes")

    if cmd == "help":
        body_markdown = HELP_TEXT.strip()
    elif cmd == "review":
        body_markdown = _build_review_markdown(
            is_pull_request=event_ctx.is_pull_request,
            issue_number=resolved_issue_number,
            dry_run=dry_run,
            client=client,
        )
    else:
        body_markdown = _build_qa_markdown(
            repo_root=repo_root,
            cmd=cmd,
            query=query,
            tky_mode=tky_mode,
            remote_url=remote_url,
            api_key=api_key,
        )

    if dry_run:
        print(body_markdown)
        return "DRY_RUN_OK"

    if client is None:
        raise ValueError("GitHub client was not initialized")

    client.create_issue_comment(issue_number=resolved_issue_number, body_markdown=body_markdown)
    print(f"Posted comment to issue #{resolved_issue_number}")
    return "POSTED_OK"
