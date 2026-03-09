from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any

STRONG_SECRET_PATTERNS = (
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"BEGIN (?:RSA )?PRIVATE KEY"),
)


@dataclass
class CmdResult:
    code: int
    out: str
    err: str


@dataclass
class ScenarioResult:
    name: str
    trigger: str
    status: str
    run_id: str = "n/a"
    run_url: str = "n/a"
    conclusion: str = "n/a"
    notes: list[str] = field(default_factory=list)
    artifact_dir: str = "n/a"


def run_cmd(args: list[str], *, cwd: Path | None = None, check: bool = True) -> CmdResult:
    completed = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    result = CmdResult(code=completed.returncode, out=completed.stdout.strip(), err=completed.stderr.strip())
    if check and result.code != 0:
        cmd_text = " ".join(args)
        raise RuntimeError(f"Command failed ({result.code}): {cmd_text}\n{result.err or result.out}")
    return result


def parse_repo_slug(remote_url: str) -> str:
    value = remote_url.strip()
    if value.endswith(".git"):
        value = value[:-4]
    if value.startswith("git@github.com:"):
        return value.split("git@github.com:", 1)[1]
    if value.startswith("https://github.com/"):
        return value.split("https://github.com/", 1)[1]
    if value.startswith("http://github.com/"):
        return value.split("http://github.com/", 1)[1]
    if value.startswith("ssh://git@github.com/"):
        return value.split("ssh://git@github.com/", 1)[1]
    raise ValueError(f"Unsupported GitHub remote URL: {remote_url}")


def _iso_to_dt(value: str) -> datetime:
    cleaned = value.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    return datetime.fromisoformat(cleaned).astimezone(UTC)


def _now_utc() -> datetime:
    return datetime.now(tz=UTC)


def _ensure_gh_ready() -> None:
    run_cmd(["gh", "--version"], check=True)
    run_cmd(["gh", "auth", "status"], check=True)


def _git_default_branch(repo: str) -> str:
    result = run_cmd(
        ["gh", "repo", "view", repo, "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name"],
        check=True,
    )
    branch = result.out.strip()
    if not branch:
        raise RuntimeError("Cannot detect default branch.")
    return branch


def _find_run(
    *,
    repo: str,
    workflow: str,
    branch: str,
    event: str,
    since: datetime,
) -> tuple[dict[str, Any] | None, int]:
    result = run_cmd(
        [
            "gh",
            "run",
            "list",
            "--repo",
            repo,
            "--workflow",
            workflow,
            "--branch",
            branch,
            "--event",
            event,
            "--json",
            "databaseId,createdAt,status,conclusion,url,displayTitle,headBranch,event",
            "--limit",
            "30",
        ],
        check=True,
    )
    data = json.loads(result.out or "[]")
    if not isinstance(data, list):
        return None, 0
    run_count = len(data)
    candidates: list[dict[str, Any]] = []
    min_ts = since - timedelta(seconds=30)
    for item in data:
        if not isinstance(item, dict):
            continue
        created = str(item.get("createdAt", "") or "")
        if not created:
            continue
        try:
            dt = _iso_to_dt(created)
        except ValueError:
            continue
        if dt >= min_ts:
            candidates.append(item)
    if not candidates:
        return None, run_count
    candidates.sort(key=lambda item: str(item.get("createdAt", "")), reverse=True)
    return candidates[0], run_count


def _wait_for_run(
    *,
    repo: str,
    workflow: str,
    branch: str,
    event: str,
    since: datetime,
    timeout_s: int = 480,
) -> dict[str, Any]:
    started = time.time()
    run_item: dict[str, Any] | None = None
    last_heartbeat = -10
    last_seen_count = 0
    while time.time() - started < timeout_s:
        run_item, seen_count = _find_run(
            repo=repo,
            workflow=workflow,
            branch=branch,
            event=event,
            since=since,
        )
        last_seen_count = seen_count
        if run_item is not None:
            break
        elapsed = int(time.time() - started)
        if elapsed - last_heartbeat >= 10:
            print(
                f"[wait] workflow={workflow} event={event} branch={branch} elapsed={elapsed}s "
                f"runs_seen={seen_count}",
                flush=True,
            )
            last_heartbeat = elapsed
        time.sleep(2)
    if run_item is None:
        diagnostics = run_cmd(
            [
                "gh",
                "run",
                "list",
                "--repo",
                repo,
                "--workflow",
                workflow,
                "--limit",
                "20",
            ],
            check=False,
        )
        diag_text = diagnostics.out or diagnostics.err or "no diagnostics"
        raise TimeoutError(
            "Timed out waiting for workflow run "
            f"(event={event}, branch={branch}, timeout_s={timeout_s}, runs_seen={last_seen_count}).\n"
            f"Recent runs:\n{diag_text}"
        )
    run_id = str(run_item.get("databaseId"))
    run_cmd(["gh", "run", "watch", run_id, "--repo", repo, "--interval", "10"], check=False)
    view = run_cmd(
        [
            "gh",
            "run",
            "view",
            run_id,
            "--repo",
            repo,
            "--json",
            "databaseId,status,conclusion,url,createdAt,updatedAt",
        ],
        check=True,
    )
    data = json.loads(view.out or "{}")
    if not isinstance(data, dict):
        raise RuntimeError(f"Invalid run view for run_id={run_id}")
    return data


def _download_artifacts(repo: str, run_id: str, out_dir: Path) -> tuple[bool, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    result = run_cmd(
        ["gh", "run", "download", run_id, "--repo", repo, "--dir", str(out_dir)],
        check=False,
    )
    if result.code != 0:
        return False, result.err or result.out or "artifact download failed"
    return True, "ok"


def _find_first(root: Path, filename: str) -> Path | None:
    for path in root.rglob(filename):
        if path.is_file():
            return path
    return None


def _load_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _scan_for_secrets(text: str) -> bool:
    return any(pattern.search(text) for pattern in STRONG_SECRET_PATTERNS)


def validate_artifacts(scenario: str, artifacts_root: Path) -> tuple[str, list[str]]:
    notes: list[str] = []
    status = "PASS"
    config_path = _find_first(artifacts_root, "config_snapshot.json")
    if config_path is None:
        notes.append("config_snapshot.json: missing")
        status = "FAIL"
    else:
        config_text = config_path.read_text(encoding="utf-8", errors="ignore")
        if _scan_for_secrets(config_text):
            notes.append("config_snapshot.json: strong secret pattern detected")
            status = "FAIL"
        else:
            notes.append("config_snapshot.json: usersafe scan passed")

    llm_path = _find_first(artifacts_root, "llm_usage.json")
    if llm_path is not None:
        payload = _load_json(llm_path)
        llm_used = bool(payload.get("llm_used", False))
        if llm_used:
            model_id = str(payload.get("model_id", "") or "")
            if not model_id or model_id == "not used":
                notes.append("llm_usage.json: llm_used=true but model_id missing")
                status = "FAIL"
        if "remaining_requests" not in payload:
            notes.append("llm_usage.json: missing remaining_requests")
            status = "FAIL"
    else:
        notes.append("llm_usage.json: missing (allowed when LLM disabled)")

    embed_path = _find_first(artifacts_root, "embeddings_usage.json")
    if embed_path is not None:
        payload = _load_json(embed_path)
        if bool(payload.get("embed_used", False)):
            if "remaining_requests" not in payload:
                notes.append("embeddings_usage.json: missing remaining_requests")
                status = "FAIL"
            if "reset_time_utc_iso" not in payload:
                notes.append("embeddings_usage.json: missing reset_time_utc_iso")
                status = "FAIL"
    else:
        notes.append("embeddings_usage.json: missing (allowed when embeddings disabled)")

    ai_path = _find_first(artifacts_root, "ai_quota_snapshot.json")
    if ai_path is None:
        notes.append("ai_quota_snapshot.json: missing")
        status = "FAIL"
    else:
        notes.append("ai_quota_snapshot.json: present")

    if scenario == "fix":
        patch = _find_first(artifacts_root, "patch.diff")
        if patch is None:
            notes.append("patch.diff: not found (can be valid if no patch generated)")
        else:
            notes.append("patch.diff: present")
    return status, notes


def render_report_markdown(
    *,
    repo: str,
    pr_url: str,
    results: list[ScenarioResult],
) -> str:
    lines: list[str] = []
    lines.append("# RepoBrain E2E Report")
    lines.append("")
    lines.append(f"- Repo: `{repo}`")
    lines.append(f"- PR: {pr_url}")
    lines.append(f"- Generated at: {_now_utc().isoformat()}")
    lines.append("")
    lines.append("| Scenario | Trigger | Result | Conclusion | Run |")
    lines.append("| --- | --- | --- | --- | --- |")
    for item in results:
        run_link = item.run_url if item.run_url != "n/a" else "n/a"
        lines.append(
            f"| {item.name} | `{item.trigger}` | **{item.status}** | "
            f"`{item.conclusion}` | {run_link} |"
        )
    lines.append("")
    for item in results:
        lines.append(f"## {item.name}")
        lines.append(f"- Status: {item.status}")
        lines.append(f"- Run: {item.run_url}")
        lines.append(f"- Artifacts: `{item.artifact_dir}`")
        for note in item.notes:
            lines.append(f"- {note}")
        lines.append("")
    return "\n".join(lines)


def _build_workflow_dispatch_args(
    *,
    workflow: str,
    ref: str,
    enable_llm: bool,
    enable_embeddings: bool,
    enable_batch_llm: bool,
    trusted_context: bool,
    allow_dynamic_verify: bool,
    apply_patch: bool,
    create_pr: bool,
    e2e_command: str = "",
    e2e_pr_number: str = "",
    e2e_ref: str = "",
) -> list[str]:
    args = [
        "gh",
        "workflow",
        "run",
        workflow,
        "--ref",
        ref,
        "-f",
        f"enable_llm={'true' if enable_llm else 'false'}",
        "-f",
        f"enable_embeddings={'true' if enable_embeddings else 'false'}",
        "-f",
        f"enable_batch_llm={'true' if enable_batch_llm else 'false'}",
        "-f",
        f"trusted_context={'true' if trusted_context else 'false'}",
        "-f",
        f"allow_dynamic_verify={'true' if allow_dynamic_verify else 'false'}",
        "-f",
        f"apply_patch={'true' if apply_patch else 'false'}",
        "-f",
        f"create_pr={'true' if create_pr else 'false'}",
    ]
    if e2e_command.strip():
        args.extend(["-f", f"e2e_command={e2e_command}"])
    if e2e_pr_number.strip():
        args.extend(["-f", f"e2e_pr_number={e2e_pr_number}"])
    if e2e_ref.strip():
        args.extend(["-f", f"e2e_ref={e2e_ref}"])
    return args


def _workflow_dispatch(
    *,
    workflow: str,
    ref: str,
    enable_llm: bool,
    enable_embeddings: bool,
    enable_batch_llm: bool,
    trusted_context: bool,
    allow_dynamic_verify: bool,
    apply_patch: bool,
    create_pr: bool,
    e2e_command: str = "",
    e2e_pr_number: str = "",
    e2e_ref: str = "",
) -> None:
    args = _build_workflow_dispatch_args(
        workflow=workflow,
        ref=ref,
        enable_llm=enable_llm,
        enable_embeddings=enable_embeddings,
        enable_batch_llm=enable_batch_llm,
        trusted_context=trusted_context,
        allow_dynamic_verify=allow_dynamic_verify,
        apply_patch=apply_patch,
        create_pr=create_pr,
        e2e_command=e2e_command,
        e2e_pr_number=e2e_pr_number,
        e2e_ref=e2e_ref,
    )
    run_cmd(args, check=True)


def _scenario_from_run(
    *,
    scenario_name: str,
    trigger: str,
    run_data: dict[str, Any],
    artifacts_root: Path,
) -> ScenarioResult:
    run_id = str(run_data.get("databaseId", "n/a"))
    run_url = str(run_data.get("url", "n/a") or "n/a")
    conclusion = str(run_data.get("conclusion", "n/a") or "n/a")
    status = "PASS" if conclusion == "success" else "FAIL"
    validation_status, notes = validate_artifacts(scenario_name, artifacts_root)
    scan_result = run_cmd(
        [sys.executable, "scripts/usersafe_scan.py", artifacts_root.as_posix()],
        check=False,
    )
    if scan_result.code == 0:
        notes.append("usersafe_scan.py: passed")
    else:
        notes.append(
            "usersafe_scan.py: WARN "
            + (scan_result.err or scan_result.out or "scan execution issue")
        )
        if status == "PASS":
            status = "WARN"
    if validation_status == "FAIL":
        status = "FAIL"
    return ScenarioResult(
        name=scenario_name,
        trigger=trigger,
        status=status,
        run_id=run_id,
        run_url=run_url,
        conclusion=conclusion,
        notes=notes,
        artifact_dir=artifacts_root.as_posix(),
    )


def _scenario_dispatch_command(
    *,
    repo: str,
    workflow: str,
    branch: str,
    pr_number: str,
    command: str,
    scenario_name: str,
    artifacts_dir: Path,
    timeout_s: int,
    enable_llm: bool = False,
    enable_embeddings: bool = False,
    enable_batch_llm: bool = False,
    trusted_context: bool = False,
    allow_dynamic_verify: bool = False,
    apply_patch: bool = False,
    create_pr: bool = False,
) -> ScenarioResult:
    print(
        f"[scenario:start] name={scenario_name} mode=workflow_dispatch "
        f"command={command} branch={branch} pr={pr_number}",
        flush=True,
    )
    since = _now_utc()
    _workflow_dispatch(
        workflow=workflow,
        ref=branch,
        enable_llm=enable_llm,
        enable_embeddings=enable_embeddings,
        enable_batch_llm=enable_batch_llm,
        trusted_context=trusted_context,
        allow_dynamic_verify=allow_dynamic_verify,
        apply_patch=apply_patch,
        create_pr=create_pr,
        e2e_command=command,
        e2e_pr_number=pr_number,
        e2e_ref=branch,
    )
    try:
        run_data = _wait_for_run(
            repo=repo,
            workflow=workflow,
            branch=branch,
            event="workflow_dispatch",
            since=since,
            timeout_s=timeout_s,
        )
    except Exception as exc:
        print(f"[scenario:fail] name={scenario_name} reason={exc}", flush=True)
        return ScenarioResult(
            name=scenario_name,
            trigger=command,
            status="FAIL",
            conclusion="timeout",
            notes=[str(exc)],
            artifact_dir=(artifacts_dir / scenario_name).as_posix(),
        )
    run_id = str(run_data.get("databaseId", "n/a"))
    target_dir = artifacts_dir / scenario_name / run_id
    ok, msg = _download_artifacts(repo, run_id, target_dir)
    result = _scenario_from_run(
        scenario_name=scenario_name,
        trigger=command,
        run_data=run_data,
        artifacts_root=target_dir,
    )
    if not ok:
        result.notes.append(f"artifact download warning: {msg}")
        if result.status == "PASS":
            result.status = "WARN"
    return result


def _scenario_workflow_dispatch(
    *,
    repo: str,
    workflow: str,
    branch: str,
    pr_number: str,
    artifacts_dir: Path,
    timeout_s: int,
) -> ScenarioResult:
    return _scenario_dispatch_command(
        repo=repo,
        workflow=workflow,
        branch=branch,
        pr_number=pr_number,
        command="/repobrain ask what files changed in this PR?",
        scenario_name="workflow_dispatch_llm_embed",
        artifacts_dir=artifacts_dir,
        timeout_s=timeout_s,
        enable_llm=True,
        enable_embeddings=True,
        enable_batch_llm=False,
        trusted_context=True,
        allow_dynamic_verify=False,
        apply_patch=False,
        create_pr=False,
    )


def _create_temp_pr(*, repo: str, default_branch: str, branch: str, marker_file: Path) -> tuple[str, str]:
    marker_file.write_text(
        f"RepoBrain e2e marker: {_now_utc().isoformat()}\n",
        encoding="utf-8",
    )
    run_cmd(["git", "checkout", "-b", branch], check=True)
    run_cmd(["git", "add", marker_file.as_posix()], check=True)
    run_cmd(["git", "commit", "-m", "e2e: marker"], check=True)
    run_cmd(["git", "push", "-u", "origin", branch], check=True)
    body = "Automated E2E PR for RepoBrain scenario validation."
    pr = run_cmd(
        [
            "gh",
            "pr",
            "create",
            "--base",
            default_branch,
            "--head",
            branch,
            "--title",
            "E2E: RepoBrain suite",
            "--body",
            body,
            "--repo",
            repo,
        ],
        check=True,
    )
    pr_url = pr.out.strip().splitlines()[-1].strip()
    pr_view = run_cmd(
        ["gh", "pr", "view", pr_url, "--repo", repo, "--json", "number,url"],
        check=True,
    )
    data = json.loads(pr_view.out or "{}")
    pr_number = str(data.get("number", "") or "")
    if not pr_number:
        raise RuntimeError("Cannot get PR number.")
    return pr_number, str(data.get("url", pr_url))


def _cleanup_pr(pr_number: str, branch: str, repo: str) -> None:
    run_cmd(["gh", "pr", "close", pr_number, "--repo", repo, "--delete-branch"], check=False)
    run_cmd(["git", "checkout", "-"], check=False)
    run_cmd(["git", "branch", "-D", branch], check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleanup", action="store_true", help="Close PR and delete branch after run.")
    parser.add_argument("--workflow", default="repobrain.yml", help="Workflow filename to monitor.")
    parser.add_argument(
        "--scenario-timeout-s",
        type=int,
        default=480,
        help="Maximum wait time for each scenario run.",
    )
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts/e2e",
        help="Directory for downloaded artifacts and report.",
    )
    args = parser.parse_args()

    _ensure_gh_ready()
    remote = run_cmd(["git", "remote", "get-url", "origin"], check=True).out.strip()
    repo = parse_repo_slug(remote)
    default_branch = _git_default_branch(repo)
    short_sha = run_cmd(["git", "rev-parse", "--short", "HEAD"], check=True).out.strip()
    branch = f"e2e/{_now_utc().strftime('%Y%m%d-%H%M%S')}-{short_sha}"

    marker_file = Path(f"e2e_marker_{int(time.time())}.txt")
    artifacts_root = Path(args.artifacts_dir)
    artifacts_root.mkdir(parents=True, exist_ok=True)

    pr_number = ""
    pr_url = ""
    results: list[ScenarioResult] = []
    try:
        pr_number, pr_url = _create_temp_pr(
            repo=repo,
            default_branch=default_branch,
            branch=branch,
            marker_file=marker_file,
        )
        results.append(
            _scenario_dispatch_command(
                repo=repo,
                workflow=args.workflow,
                branch=branch,
                pr_number=pr_number,
                command="/repobrain review",
                scenario_name="review",
                artifacts_dir=artifacts_root,
                timeout_s=args.scenario_timeout_s,
            )
        )
        results.append(
            _scenario_dispatch_command(
                repo=repo,
                workflow=args.workflow,
                branch=branch,
                pr_number=pr_number,
                command="/repobrain fix improve naming in marker file",
                scenario_name="fix",
                artifacts_dir=artifacts_root,
                timeout_s=args.scenario_timeout_s,
            )
        )
        results.append(
            _scenario_dispatch_command(
                repo=repo,
                workflow=args.workflow,
                branch=branch,
                pr_number=pr_number,
                command="/repobrain ask what files changed in this PR?",
                scenario_name="ask",
                artifacts_dir=artifacts_root,
                timeout_s=args.scenario_timeout_s,
            )
        )
        results.append(
            _scenario_workflow_dispatch(
                repo=repo,
                workflow=args.workflow,
                branch=branch,
                pr_number=pr_number,
                artifacts_dir=artifacts_root,
                timeout_s=args.scenario_timeout_s,
            )
        )
    finally:
        if args.cleanup and pr_number:
            _cleanup_pr(pr_number, branch, repo)

    report = render_report_markdown(repo=repo, pr_url=pr_url or "n/a", results=results)
    report_path = artifacts_root / "e2e_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"E2E report: {report_path.as_posix()}")
    has_fail = any(item.status == "FAIL" for item in results)
    return 1 if has_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
