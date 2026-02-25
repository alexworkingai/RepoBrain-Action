from __future__ import annotations

import argparse
import os
from pathlib import Path

from repobrain.github_flow import run_github_flow


def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", default="true")
    parser.add_argument("--tky-mode", default="baseline", choices=["baseline", "remote", "local"])
    parser.add_argument("--remote-url", default="")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--comment-text", default="")
    args = parser.parse_args()

    event_path_raw = os.environ.get("GITHUB_EVENT_PATH", "")
    event_path = Path(event_path_raw) if event_path_raw else None
    output = run_github_flow(
        repo_root=Path.cwd(),
        dry_run=_parse_bool(args.dry_run),
        tky_mode=args.tky_mode,
        remote_url=args.remote_url,
        api_key=args.api_key,
        comment_text=args.comment_text,
        event_path=event_path,
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
