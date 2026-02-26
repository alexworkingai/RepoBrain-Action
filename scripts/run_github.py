from __future__ import annotations

import argparse
import os
from pathlib import Path
import time

from repobrain.audit import write_audit
from repobrain.github_flow import get_last_audit, parse_issue_number, run_github_flow


def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", default="true")
    parser.add_argument("--comment-text", default="")
    parser.add_argument("--issue-number", default="")
    parser.add_argument("--tky-mode", default="baseline", choices=["baseline", "remote", "local"])
    parser.add_argument("--remote-url", default="")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--hmac-secret", default="")
    parser.add_argument("--enable-hmac", default="false")
    args = parser.parse_args()

    try:
        issue_number = parse_issue_number(args.issue_number)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    event_path_raw = os.environ.get("GITHUB_EVENT_PATH", "")
    event_path = Path(event_path_raw) if event_path_raw else None
    run_github_flow(
        repo_root=Path.cwd(),
        dry_run=_parse_bool(args.dry_run),
        comment_text=args.comment_text,
        issue_number=issue_number,
        tky_mode=args.tky_mode,
        remote_url=args.remote_url,
        api_key=args.api_key,
        hmac_secret=args.hmac_secret,
        enable_hmac=_parse_bool(args.enable_hmac),
        event_path=event_path,
    )
    audit = get_last_audit()
    run_id = str(audit.get("run_id") or os.environ.get("GITHUB_RUN_ID") or int(time.time()))
    issue_tag = str(audit.get("issue_number") or "na")
    audit_path = Path("artifacts") / "audit" / f"audit_{run_id}_{issue_tag}.json"
    write_audit(audit or {}, audit_path)
    print(f"AUDIT_PATH={audit_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
