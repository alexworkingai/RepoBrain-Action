from __future__ import annotations

import argparse
import os
from pathlib import Path
import time

from repobrain.audit import write_audit
from repobrain.github_flow import get_last_audit, parse_issue_number, run_github_flow
from repobrain.stability_benchmark import write_stability_benchmark_artifacts


def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", default="true")
    parser.add_argument("--comment-text", default="")
    parser.add_argument("--issue-number", default="")
    parser.add_argument("--tky-mode", default="auto", choices=["auto", "baseline", "remote", "local"])
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
    try:
        benchmark_json = Path("artifacts") / "benchmarks" / "repobrain_stability_benchmark.json"
        benchmark_md = Path("artifacts") / "benchmarks" / "repobrain_stability_benchmark.md"
        payload = write_stability_benchmark_artifacts(
            audit_dir=Path("artifacts") / "audit",
            output_json_path=benchmark_json,
            output_markdown_path=benchmark_md,
        )
        print(f"BENCHMARK_JSON_PATH={benchmark_json.as_posix()}")
        print(f"BENCHMARK_MD_PATH={benchmark_md.as_posix()}")
        print(f"BENCHMARK_STATUS={str(payload.get('overall_status', 'not_enough_data'))}")
    except Exception as exc:  # pragma: no cover - benchmark must not block main workflow
        print(f"BENCHMARK_GENERATION_FAILED={exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
