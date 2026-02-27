from __future__ import annotations

import argparse
from pathlib import Path

from repobrain.ask import answer_question, make_provider
from repobrain.commands import parse_command
from repobrain.config import load_config
from repobrain.formatting import format_github_comment
from repobrain.index_store import load_index
from repobrain.retrieve import retrieve_topk
from repobrain.tky_remote import RemoteTKYError

HELP_TEXT = """RepoBrain command examples:
- /repobrain help
- /repobrain ask How does provider selection work?
- /repobrain locate baseline provider
- /repobrain explain retrieve_topk
- /repobrain review
"""


def _question_from_command(cmd: str, query: str) -> str:
    if cmd == "review":
        return "review repository"
    return query


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", default="")
    parser.add_argument("--comment-text", default="")
    parser.add_argument("--index-path", default="artifacts/index-package.zip")
    parser.add_argument("--tky-mode", default="baseline", choices=["baseline", "remote", "local"])
    parser.add_argument("--remote-url", default="")
    parser.add_argument("--api-key", default="")
    args = parser.parse_args()

    if args.comment_text:
        parsed = parse_command(args.comment_text)
    elif args.question:
        parsed = {"cmd": "ask", "query": args.question}
    else:
        parsed = {"cmd": "help", "query": ""}

    if parsed["cmd"] == "help":
        print(HELP_TEXT.strip())
        return 0

    cfg = load_config(Path.cwd())
    index_path = Path(args.index_path)
    if not index_path.exists():
        raise FileNotFoundError(
            f"Index not found: {index_path}. Run scripts/run_index.py first."
        )

    question = _question_from_command(parsed["cmd"], parsed["query"])
    chunks = load_index(index_path)
    candidates = retrieve_topk(question, chunks, topk=cfg.topk)

    provider = make_provider(
        args.tky_mode,
        remote_url=args.remote_url or None,
        api_key=args.api_key or None,
    )
    limits = {"max_sources": cfg.max_sources}
    mode_requested = args.tky_mode
    mode_used = args.tky_mode
    fallback_reason_code: str | None = None
    try:
        res = answer_question(
            question=question,
            candidates=candidates,
            provider=provider,
            limits=limits,
        )
    except RemoteTKYError as exc:
        if args.tky_mode != "remote" or not cfg.tky_remote_fail_open:
            raise
        provider = make_provider("baseline")
        res = answer_question(
            question=question,
            candidates=candidates,
            provider=provider,
            limits=limits,
        )
        mode_used = "baseline"
        fallback_reason_code = exc.fallback_reason_code or "REMOTE_NETWORK"
    audit_summary = dict(res.audit_summary)
    audit_summary.update(
        {
            "tky_engine": "topocore_lite" if mode_used == "local" else mode_used,
            "tky_mode_requested": mode_requested,
            "tky_mode_used": mode_used,
            "remote_used": args.tky_mode == "remote" and mode_used == "remote",
            "fallback_reason_code": fallback_reason_code,
        }
    )

    print(
        format_github_comment(
            res.answer_text,
            res.evidence,
            audit_summary,
            res.next_steps,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
