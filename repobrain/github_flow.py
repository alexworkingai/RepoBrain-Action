from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile

import requests

from repobrain.ask import answer_question, make_provider
from repobrain.commands import parse_command
from repobrain.config import load_config
from repobrain.formatting import format_github_comment
from repobrain.index_store import build_index, load_index
from repobrain.retrieve import retrieve_topk
from repobrain.tky_provider import CandidateChunk

HELP_TEXT = """RepoBrain command examples:
- /repobrain help
- /repobrain ask How does provider selection work?
- /repobrain locate TKYProvider
- /repobrain explain retrieve_topk
- /repobrain review
"""


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


def build_issue_comment_url(repo: str, issue_number: int) -> str:
    """Build GitHub REST URL for creating an issue comment."""
    return f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"


class GitHubClient:
    """Minimal GitHub REST client for issue comments."""

    def __init__(self, repo: str, token: str) -> None:
        self.repo = repo
        self.token = token

    def create_issue_comment(self, issue_number: int, body_markdown: str) -> None:
        """POST a comment to a GitHub Issue or PR thread."""
        url = build_issue_comment_url(self.repo, issue_number)
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        response = requests.post(
            url,
            json={"body": body_markdown},
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()


def extract_comment_text_from_event(event_path: Path | None) -> str:
    """Extract `comment.body` from a GitHub event payload file."""
    if event_path is None or not event_path.exists():
        return ""

    try:
        payload = json.loads(event_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""

    comment = payload.get("comment", {})
    if not isinstance(comment, dict):
        return ""

    body = comment.get("body")
    return body if isinstance(body, str) else ""


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
    """Load prebuilt index, or build a temporary one if missing."""
    if index_path.exists():
        return load_index(index_path)

    with tempfile.TemporaryDirectory() as tmp_dir:
        temp_index = Path(tmp_dir) / "index-package.zip"
        build_index(root=repo_root, out_zip=temp_index, store_text=True)
        return load_index(temp_index)


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
    source_text = comment_text or extract_comment_text_from_event(event_path)
    mode_label = "DRY_RUN" if dry_run else "POST_MODE"

    if not source_text.strip().startswith("/repobrain"):
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

    if cmd == "help":
        body_markdown = HELP_TEXT.strip()
    else:
        cfg = load_config(repo_root)
        index_path = repo_root / "artifacts" / "index-package.zip"
        question = question_from_command(cmd, query)
        chunks = load_or_build_chunks(repo_root, index_path)
        candidates = retrieve_topk(question, chunks, topk=cfg.topk)

        provider = make_provider(
            tky_mode,
            remote_url=remote_url or None,
            api_key=api_key or None,
        )
        result = answer_question(
            question=question,
            candidates=candidates,
            provider=provider,
            limits={"max_sources": cfg.max_sources},
        )
        body_markdown = format_github_comment(
            result.answer_text,
            result.evidence,
            result.audit_summary,
            result.next_steps,
        )

    if dry_run:
        print(body_markdown)
        return "DRY_RUN_OK"

    if issue_number is None:
        raise ValueError("issue_number is required when dry_run=False")

    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not repo:
        raise ValueError("GITHUB_REPOSITORY is required when dry_run=False")
    if not token:
        raise ValueError("GITHUB_TOKEN is required when dry_run=False")

    client = GitHubClient(repo=repo, token=token)
    client.create_issue_comment(issue_number=issue_number, body_markdown=body_markdown)
    print(f"Posted comment to issue #{issue_number}")
    return "POSTED_OK"
