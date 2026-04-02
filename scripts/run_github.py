from __future__ import annotations

import argparse
import os
from pathlib import Path
import time

from repobrain.audit import write_audit
from repobrain.github_flow import get_last_audit, parse_issue_number, run_github_flow
from repobrain.stability_benchmark import write_stability_benchmark_artifacts
from repobrain.tkya_evidence_pack import write_tkya_evidence_pack_artifacts


def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="github", choices=["github", "external"])
    parser.add_argument("--dry-run", default="true")
    parser.add_argument("--comment-text", default="")
    parser.add_argument("--issue-number", default="")
    parser.add_argument("--tky-mode", default="auto", choices=["auto", "baseline", "remote", "local"])
    parser.add_argument("--remote-url", default="")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--hmac-secret", default="")
    parser.add_argument("--enable-hmac", default="false")
    parser.add_argument("--query", default="")
    parser.add_argument("--command", default="ask")
    parser.add_argument("--repo-root", default=".")

    args = parser.parse_args()

    if args.mode == "external":
        from repobrain.external_flow import ExternalFlowInput, run_external_flow

        result = run_external_flow(
            ExternalFlowInput(
                repo_root=Path(args.repo_root).resolve(),
                query=args.query,
                command=args.command,
                dry_run=_parse_bool(args.dry_run),
                tky_mode=args.tky_mode,
            )
        )
        print(f"STATUS={result.status}")
        print(f"DECISION={result.decision}")
        print(result.content)
        return 0 if result.status == "success" else 1

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
        evidence = write_tkya_evidence_pack_artifacts(repo_root=Path.cwd(), audit=audit or {})
        print(f"EVIDENCE_PACK_INTERNAL_PATH={str(evidence.get('internal_path', 'n/a'))}")
        print(f"EVIDENCE_PACK_PUBLIC_SAFE_PATH={str(evidence.get('public_safe_path', 'n/a'))}")
        print(f"EVIDENCE_PACK_SUMMARY_PATH={str(evidence.get('summary_path', 'n/a'))}")
    except Exception as exc:  # pragma: no cover - evidence pack must not block main workflow
        print(f"EVIDENCE_PACK_GENERATION_FAILED={exc}")
    try:
        benchmark_json = Path("artifacts") / "benchmarks" / "repobrain_stability_benchmark.json"
        benchmark_md = Path("artifacts") / "benchmarks" / "repobrain_stability_benchmark.md"
        payload = write_stability_benchmark_artifacts(
            audit_dir=Path("artifacts") / "audit",
            output_json_path=benchmark_json,
            output_markdown_path=benchmark_md,
            history_path=Path("artifacts") / ".repobrain_cache" / "stability_benchmark_history.json",
        )
        print(f"BENCHMARK_JSON_PATH={benchmark_json.as_posix()}")
        print(f"BENCHMARK_MD_PATH={benchmark_md.as_posix()}")
        print(f"BENCHMARK_STATUS={str(payload.get('overall_status', 'not_enough_data'))}")
    except Exception as exc:  # pragma: no cover - benchmark must not block main workflow
        print(f"BENCHMARK_GENERATION_FAILED={exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())