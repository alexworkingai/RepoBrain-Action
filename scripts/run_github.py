from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
from typing import Any

from repobrain.ask import answer_question
from repobrain.audit import write_audit
from repobrain.github_flow import (
    get_last_audit,
    parse_issue_number,
    question_from_command,
    run_github_flow,
)
from repobrain.stability_benchmark import write_stability_benchmark_artifacts
from repobrain.topocore_v6_adapter import classify_topocore_v6_runtime_error
from repobrain.tky_local import LocalTKYProvider
from repobrain.tky_provider import CandidateChunk
from repobrain.tkya_evidence_pack import write_tkya_evidence_pack_artifacts


def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


_LAB_COMMANDS = {"help", "ask", "review", "verify", "fix"}
_LAB_FIXTURES = {"minimal", "review", "verify", "fix", "fix_lite"}


def _env_str(name: str, default: str = "") -> str:
    return str(os.environ.get(name, default) or "").strip()


def _env_bool(name: str, default: bool = False) -> bool:
    raw = _env_str(name)
    if not raw:
        return default
    return _parse_bool(raw)


def _normalize_lab_command(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in _LAB_COMMANDS:
        return normalized
    raise ValueError(
        f"Invalid RepoBrain lab command: {normalized or 'empty'}. "
        "Allowed values: help, ask, review, verify, fix."
    )


def _normalize_lab_fixture(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in _LAB_FIXTURES:
        return normalized
    raise ValueError(
        f"Invalid RepoBrain lab fixture: {normalized or 'empty'}. "
        "Allowed values: minimal, review, verify, fix."
    )


def _workflow_dispatch_lab_enabled() -> bool:
    if _env_str("GITHUB_EVENT_NAME") != "workflow_dispatch":
        return False
    return _normalize_lab_command(_env_str("RB_REPOBRAIN_LAB_COMMAND", "help")) != "help"


def _build_lab_candidates(lab_fixture: str) -> list[CandidateChunk]:
    fixture = _normalize_lab_fixture(lab_fixture)
    if fixture == "review":
        return [
            CandidateChunk(
                chunk_id="review-1",
                file_path="repobrain/github_flow.py",
                line_start=8445,
                line_end=8725,
                score=0.93,
                signature=[11, 21, 31],
            ),
            CandidateChunk(
                chunk_id="review-2",
                file_path="repobrain/topocore_backend.py",
                line_start=418,
                line_end=620,
                score=0.81,
                signature=[12, 22, 32],
            ),
            CandidateChunk(
                chunk_id="review-3",
                file_path="tests/test_topocore_backend_review_verify.py",
                line_start=1,
                line_end=220,
                score=0.66,
                signature=[13, 23, 33],
            ),
        ]
    if fixture == "verify":
        return [
            CandidateChunk(
                chunk_id="verify-1",
                file_path="repobrain/topocore_backend.py",
                line_start=418,
                line_end=620,
                score=0.89,
                signature=[41, 51, 61],
            ),
            CandidateChunk(
                chunk_id="verify-2",
                file_path=".github/workflows/repobrain.yml",
                line_start=1,
                line_end=260,
                score=0.72,
                signature=[42, 52, 62],
            ),
            CandidateChunk(
                chunk_id="verify-3",
                file_path="tests/test_github_runtime_v6_dependency_gate.py",
                line_start=1,
                line_end=180,
                score=0.61,
                signature=[43, 53, 63],
            ),
        ]
    if fixture in {"fix", "fix_lite"}:
        return [
            CandidateChunk(
                chunk_id="fix-1",
                file_path="repobrain/topocore_backend.py",
                line_start=418,
                line_end=620,
                score=0.91,
                signature=[71, 81, 91],
            ),
            CandidateChunk(
                chunk_id="fix-2",
                file_path="repobrain/tky_local.py",
                line_start=180,
                line_end=278,
                score=0.77,
                signature=[72, 82, 92],
            ),
            CandidateChunk(
                chunk_id="fix-3",
                file_path="docs/architecture/TOPOCORE_V6_FIX_LITE_DECISION_PATH.md",
                line_start=1,
                line_end=200,
                score=0.58,
                signature=[73, 83, 93],
            ),
        ]
    return [
        CandidateChunk(
            chunk_id="minimal-1",
            file_path="repobrain/topocore_backend.py",
            line_start=418,
            line_end=620,
            score=0.95,
            signature=[101, 111, 121],
        ),
        CandidateChunk(
            chunk_id="minimal-2",
            file_path="repobrain/tky_local.py",
            line_start=180,
            line_end=278,
            score=0.84,
            signature=[102, 112, 122],
        ),
        CandidateChunk(
            chunk_id="minimal-3",
            file_path="repobrain/topocore_v6_adapter.py",
            line_start=1,
            line_end=280,
            score=0.68,
            signature=[103, 113, 123],
        ),
    ]


def _build_lab_policy_seed(lab_command: str, lab_fixture: str) -> dict[str, Any]:
    common = {
        "github_context": {
            "is_pr": lab_fixture in {"review", "fix", "fix_lite"},
            "issue_number": 49,
            "pr_number": 49 if lab_fixture in {"review", "fix", "fix_lite"} else None,
            "changed_files": [
                "repobrain/topocore_backend.py",
                "repobrain/tky_local.py",
            ],
            "diff_hunks": [],
            "base_ref": "main",
        },
        "verification_context": {
            "verification_pending": False,
            "verification_failed": False,
            "required_checks": ["ruff", "pytest"],
        },
        "patch_governance": {
            "patch_safety_mode": "decision_only",
            "patch_apply_allowed": "false",
        },
    }
    if lab_command == "review":
        common["project_audit_summary"] = {
            "review_context": "workflow_dispatch_lab",
            "risk_surface": "backend_selection",
        }
    elif lab_command == "verify":
        common["verification_summary"] = {
            "verification_context": "workflow_dispatch_lab",
            "checks_considered": ["ruff", "pytest"],
        }
    elif lab_command == "fix":
        common["fix_draft_summary"] = {
            "no_patch_reason": "fix_lite_decision_only",
            "patch_safety_notes": [
                "No patch application in workflow_dispatch lab mode.",
                "No branch, commit, or PR creation is authorized.",
            ],
        }
    return common


def _build_lab_limits(lab_command: str, lab_fixture: str) -> dict[str, Any]:
    runtime_command = lab_command
    return {
        "task_type": runtime_command,
        "requested_task_type": runtime_command,
        "max_sources": 4,
        "topk_current": 4,
        "time_budget_s": 30,
        "user_goal": "workflow_dispatch_meaningful_v6_validation",
        "policy": _build_lab_policy_seed(lab_command, lab_fixture),
        "allow_patch_apply": False,
        "changed_files": [
            "repobrain/topocore_backend.py",
            "repobrain/tky_local.py",
        ],
        "diff_hunks": [],
    }


def _sanitize_lab_evidence(
    *,
    lab_command: str,
    lab_fixture: str,
    route: str,
    compression_stats: dict[str, Any],
) -> dict[str, Any]:
    requested_backend = str(compression_stats.get("requested_backend", "unknown") or "unknown")
    resolved_backend = str(
        compression_stats.get(
            "resolved_backend",
            compression_stats.get("topocore_backend", "unknown"),
        )
        or "unknown"
    )
    fallback_reason = str(compression_stats.get("fallback_reason", "none") or "none")
    evidence = {
        "lab_command": lab_command,
        "lab_fixture": lab_fixture,
        "requested_backend": requested_backend,
        "resolved_backend": resolved_backend,
        "backend_mode": str(compression_stats.get("backend_mode", requested_backend) or requested_backend),
        "fallback_used": bool(compression_stats.get("fallback_used", False)),
        "fallback_reason": fallback_reason,
        "route": route,
        "status": str(compression_stats.get("external_status", "n/a") or "n/a"),
        "action": str(compression_stats.get("external_action", "n/a") or "n/a"),
        "message_code": str(compression_stats.get("message_code", "n/a") or "n/a"),
        "confidence_band": str(compression_stats.get("confidence_band", "n/a") or "n/a"),
        "decide_raw_used": False,
        "patch_application": False,
        "commit_branch_pr_creation": False,
    }
    if lab_command == "fix":
        evidence.update(
            {
                "patch_authorized": bool(compression_stats.get("patch_authorized", False)),
                "patch_applied": bool(compression_stats.get("patch_applied", False)),
                "files_modified": bool(compression_stats.get("files_modified", False)),
                "branch_created": bool(compression_stats.get("branch_created", False)),
                "commit_created": bool(compression_stats.get("commit_created", False)),
                "pr_created": bool(compression_stats.get("pr_created", False)),
            }
        )
    return evidence


def _write_lab_backend_evidence(repo_root: Path, evidence: dict[str, Any]) -> Path:
    path = repo_root / "artifacts" / "lab_backend_evidence" / "repobrain_lab_backend_evidence.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _print_lab_backend_evidence(evidence: dict[str, Any]) -> None:
    print("RepoBrain lab backend evidence:")
    ordered_keys = [
        "lab_command",
        "lab_fixture",
        "requested_backend",
        "resolved_backend",
        "backend_mode",
        "fallback_used",
        "fallback_reason",
        "status",
        "action",
        "message_code",
        "confidence_band",
    ]
    if evidence.get("lab_command") == "fix":
        ordered_keys.extend(
            [
                "patch_authorized",
                "patch_applied",
                "files_modified",
                "branch_created",
                "commit_created",
                "pr_created",
            ]
        )
    for key in ordered_keys:
        print(f"{key}={evidence.get(key)}")


def _build_lab_failure_evidence(
    *,
    lab_command: str,
    lab_fixture: str,
    exc: Exception,
) -> dict[str, Any]:
    category, sanitized_message = classify_topocore_v6_runtime_error(
        exc,
        local_path=_env_str("RB_TOPOCORE_V6_LOCAL_PATH", ""),
    )
    requested_backend = _env_str("RB_TOPOCORE_BACKEND", _env_str("RB_TKYA_BACKEND", "auto")) or "auto"
    evidence = {
        "lab_command": lab_command,
        "lab_fixture": lab_fixture,
        "requested_backend": requested_backend,
        "resolved_backend": "unknown",
        "fallback_used": "unknown",
        "failure_category": category,
        "error_message_sanitized": sanitized_message,
        "decide_raw_used": False,
        "patch_application": False,
        "commit_created": False,
        "branch_created": False,
        "pr_created": False,
    }
    if lab_command == "fix":
        evidence.update(
            {
                "patch_authorized": False,
                "patch_applied": False,
                "files_modified": False,
            }
        )
    return evidence


def run_workflow_dispatch_lab_command(*, repo_root: Path) -> dict[str, Any]:
    lab_command = _normalize_lab_command(_env_str("RB_REPOBRAIN_LAB_COMMAND", "help"))
    lab_fixture = _normalize_lab_fixture(_env_str("RB_REPOBRAIN_LAB_FIXTURE", "minimal"))
    lab_query = _env_str(
        "RB_REPOBRAIN_LAB_QUERY",
        "Summarize current RepoBrain TopoCore backend status.",
    )
    runtime_command = lab_command
    question = question_from_command(runtime_command, lab_query)
    try:
        result = answer_question(
            question=question,
            candidates=_build_lab_candidates(lab_fixture),
            provider=LocalTKYProvider(),
            limits=_build_lab_limits(lab_command, lab_fixture),
        )
    except Exception as exc:
        failure_evidence = _build_lab_failure_evidence(
            lab_command=lab_command,
            lab_fixture=lab_fixture,
            exc=exc,
        )
        evidence_path = _write_lab_backend_evidence(repo_root, failure_evidence)
        print("RepoBrain lab backend evidence:")
        print(f"lab_command={failure_evidence['lab_command']}")
        print(f"lab_fixture={failure_evidence['lab_fixture']}")
        print(f"requested_backend={failure_evidence['requested_backend']}")
        print(f"resolved_backend={failure_evidence['resolved_backend']}")
        print(f"fallback_used={failure_evidence['fallback_used']}")
        print(f"failure_category={failure_evidence['failure_category']}")
        print(f"error_message_sanitized={failure_evidence['error_message_sanitized']}")
        print(f"LAB_BACKEND_EVIDENCE_PATH={evidence_path.as_posix()}")
        raise ValueError(failure_evidence["error_message_sanitized"]) from exc
    compression_stats = (
        dict(result.tky.compression_stats)
        if isinstance(result.tky.compression_stats, dict)
        else {}
    )
    evidence = _sanitize_lab_evidence(
        lab_command=lab_command,
        lab_fixture=lab_fixture,
        route=result.tky.route,
        compression_stats=compression_stats,
    )
    evidence_path = _write_lab_backend_evidence(repo_root, evidence)
    _print_lab_backend_evidence(evidence)
    print(f"LAB_BACKEND_EVIDENCE_PATH={evidence_path.as_posix()}")
    return evidence


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
    if _workflow_dispatch_lab_enabled():
        try:
            run_workflow_dispatch_lab_command(repo_root=Path.cwd())
        except ValueError as exc:
            print(f"LAB_BACKEND_EVIDENCE_FAILED={exc}")
            return 1
        return 0
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
