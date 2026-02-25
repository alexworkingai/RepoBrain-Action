from __future__ import annotations

import json
from pathlib import Path
import tempfile

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
    tky_mode: str = "baseline",
    remote_url: str = "",
    api_key: str = "",
    comment_text: str = "",
    event_path: Path | None = None,
) -> str:
    """Run RepoBrain GitHub wiring flow and return the text that would be printed."""
    source_text = comment_text or extract_comment_text_from_event(event_path)
    parsed = parse_command(source_text)
    cmd = parsed["cmd"]
    query = parsed["query"]
    mode_label = "DRY_RUN" if dry_run else "LIVE_NOT_IMPLEMENTED"

    lines = [
        f"Mode={mode_label}",
        f"Cmd={cmd}",
        f"Query={query}",
    ]

    if cmd == "help":
        return "\n".join([*lines, "", HELP_TEXT.strip()])

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
    markdown = format_github_comment(
        result.answer_text,
        result.evidence,
        result.audit_summary,
        result.next_steps,
    )

    if not dry_run:
        lines.append("Note=Live GitHub comment publish is not implemented in Sprint 3.1")

    return "\n".join([*lines, "", markdown])
