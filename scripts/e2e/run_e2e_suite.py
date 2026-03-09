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
import zipfile

STRONG_SECRET_PATTERNS = (
    re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"BEGIN (?:RSA )?PRIVATE KEY"),
)

TRANSIENT_GH_ERROR_MARKERS = (
    "tls handshake timeout",
    "timeout",
    "temporary failure",
    "eof",
    "connection reset",
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


@dataclass(frozen=True)
class ScenarioRequirements:
    require_llm_used: bool = False
    require_embeddings_used: bool = False
    require_patch: bool = False
    require_batch_calls_min: int = 0
    require_index_embeddings: bool = False


@dataclass(frozen=True)
class ScenarioSpec:
    name: str
    command: str
    enable_llm: bool
    enable_embeddings: bool
    enable_batch_llm: bool
    batch_force: bool
    trusted_context: bool
    allow_dynamic_verify: bool
    apply_patch: bool
    create_pr: bool
    requirements: ScenarioRequirements


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


def _is_transient_gh_error(result: CmdResult) -> bool:
    blob = f"{result.err}\n{result.out}".lower()
    return any(marker in blob for marker in TRANSIENT_GH_ERROR_MARKERS)


def _run_gh_cmd_with_retries(
    args: list[str],
    *,
    retries: int,
    backoff_s: int,
    check: bool = True,
) -> tuple[CmdResult, int]:
    attempts_total = max(1, int(retries))
    base_backoff = max(1, int(backoff_s))
    last_result = CmdResult(code=1, out="", err="no result")

    for attempt in range(1, attempts_total + 1):
        result = run_cmd(args, check=False)
        last_result = result
        if result.code == 0:
            return result, attempt

        if attempt >= attempts_total or not _is_transient_gh_error(result):
            break

        sleep_for = base_backoff * (2 ** (attempt - 1))
        err_text = result.err or result.out or "unknown transient error"
        print(
            f"[gh-retry] WARN attempt {attempt}/{attempts_total} failed: {err_text}. "
            f"retrying in {sleep_for}s",
            flush=True,
        )
        time.sleep(sleep_for)

    if check and last_result.code != 0:
        cmd_text = " ".join(args)
        err_text = last_result.err or last_result.out or "no output"
        raise RuntimeError(
            f"Command failed after {attempts_total} attempt(s): {cmd_text}\n{err_text}"
        )

    return last_result, attempts_total


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
    gh_retries: int,
    gh_backoff_s: int,
) -> tuple[dict[str, Any] | None, int]:
    result, _ = _run_gh_cmd_with_retries(
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
        retries=gh_retries,
        backoff_s=gh_backoff_s,
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
    gh_retries: int = 5,
    gh_backoff_s: int = 2,
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
            gh_retries=gh_retries,
            gh_backoff_s=gh_backoff_s,
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
        diagnostics, _ = _run_gh_cmd_with_retries(
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
                "--limit",
                "20",
            ],
            retries=gh_retries,
            backoff_s=gh_backoff_s,
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
    view, _ = _run_gh_cmd_with_retries(
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
        retries=gh_retries,
        backoff_s=gh_backoff_s,
        check=True,
    )
    data = json.loads(view.out or "{}")
    if not isinstance(data, dict):
        raise RuntimeError(f"Invalid run view for run_id={run_id}")
    return data


def _download_artifacts(
    repo: str,
    run_id: str,
    out_dir: Path,
    *,
    gh_retries: int,
    gh_backoff_s: int,
) -> tuple[bool, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    result, attempts_used = _run_gh_cmd_with_retries(
        ["gh", "run", "download", run_id, "--repo", repo, "--dir", str(out_dir)],
        retries=gh_retries,
        backoff_s=gh_backoff_s,
        check=False,
    )
    if result.code != 0:
        err = result.err or result.out or "artifact download failed"
        return False, f"{err} (attempts={attempts_used})"
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


def _first_zip_with_embeddings(artifacts_root: Path) -> tuple[Path | None, bool]:
    for zip_path in sorted(artifacts_root.rglob("*.zip")):
        if not zip_path.is_file():
            continue
        try:
            with zipfile.ZipFile(zip_path, mode="r") as zf:
                if "index/embeddings.jsonl" in zf.namelist():
                    return zip_path, True
        except (OSError, zipfile.BadZipFile):
            continue
    return None, False


def _index_embeddings_evidence_status(artifacts_root: Path) -> str:
    evidence = _find_first(artifacts_root, "index_embeddings_evidence.json")
    if evidence is None:
        return ""
    try:
        payload = _load_json(evidence)
    except json.JSONDecodeError:
        return ""
    return str(payload.get("status", payload.get("index_embeddings_status", "")) or "").upper()


def _has_patch_artifact(artifacts_root: Path) -> bool:
    if _find_first(artifacts_root, "patch.diff") is not None:
        return True
    for diff_path in artifacts_root.rglob("*.diff"):
        parts = {part.lower() for part in diff_path.parts}
        if "patch_parts" in parts:
            return True
    return False


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def validate_artifacts(
    scenario: str,
    artifacts_root: Path,
    requirements: ScenarioRequirements,
) -> tuple[str, list[str]]:
    notes: list[str] = []
    status = "PASS"

    def fail(message: str) -> None:
        nonlocal status
        notes.append(f"FAIL: {message}")
        status = "FAIL"

    def pass_note(message: str) -> None:
        notes.append(f"PASS: {message}")

    config_path = _find_first(artifacts_root, "config_snapshot.json")
    if config_path is None:
        fail("config_snapshot.json is missing")
    else:
        config_text = config_path.read_text(encoding="utf-8", errors="ignore")
        if _scan_for_secrets(config_text):
            fail("config_snapshot.json contains secret-like pattern")
        else:
            pass_note("config_snapshot.json usersafe scan passed")

    llm_payload: dict[str, Any] = {}
    llm_path = _find_first(artifacts_root, "llm_usage.json")
    if llm_path is None:
        notes.append("INFO: llm_usage.json missing (allowed unless required by scenario)")
    else:
        llm_payload = _load_json(llm_path)
        if "remaining_requests" in llm_payload:
            pass_note("llm_usage.json contains remaining_requests")
        else:
            fail("llm_usage.json is missing remaining_requests")

    embed_payload: dict[str, Any] = {}
    embed_path = _find_first(artifacts_root, "embeddings_usage.json")
    if embed_path is None:
        notes.append("INFO: embeddings_usage.json missing (allowed unless required by scenario)")
    else:
        embed_payload = _load_json(embed_path)
        if "remaining_requests" in embed_payload:
            pass_note("embeddings_usage.json contains remaining_requests")
        else:
            fail("embeddings_usage.json is missing remaining_requests")
        if "reset_time_utc_iso" in embed_payload:
            pass_note("embeddings_usage.json contains reset_time_utc_iso")
        else:
            fail("embeddings_usage.json is missing reset_time_utc_iso")

    ai_path = _find_first(artifacts_root, "ai_quota_snapshot.json")
    if ai_path is None:
        fail("ai_quota_snapshot.json is missing")
    else:
        pass_note("ai_quota_snapshot.json present")

    if requirements.require_llm_used:
        if not llm_payload:
            fail("llm_usage.json is required for this scenario")
        else:
            if bool(llm_payload.get("llm_used", False)):
                pass_note("llm_used=true")
            else:
                skip_reason = str(llm_payload.get("skip_reason", "n/a") or "n/a")
                decision_route = str(llm_payload.get("decision_route", "n/a") or "n/a")
                fail(
                    "llm_used must be true "
                    f"(skip_reason={skip_reason}, route={decision_route})"
                )
            model_id = str(llm_payload.get("model_id", "") or "")
            if model_id in {"openai/gpt-4.1", "openai/gpt-4.1-mini"}:
                pass_note(f"model_id accepted: {model_id}")
            else:
                fail(f"model_id missing/unsupported: {model_id or '<empty>'}")
            if "tokens_total" in llm_payload:
                pass_note("llm_usage.json contains tokens_total")
            else:
                fail("llm_usage.json is missing tokens_total")
            if "remaining_requests" in llm_payload:
                pass_note("llm_usage.json contains remaining_requests")
            else:
                fail("llm_usage.json is missing remaining_requests")
            if "reset_time_utc_iso" in llm_payload:
                pass_note("llm_usage.json contains reset_time_utc_iso")
            else:
                fail("llm_usage.json is missing reset_time_utc_iso")

    if requirements.require_embeddings_used:
        if not embed_payload:
            fail("embeddings_usage.json is required for this scenario")
        else:
            embed_used = bool(embed_payload.get("embed_used", embed_payload.get("embeddings_used", False)))
            if embed_used:
                pass_note("embed_used=true")
            else:
                fail("embed_used must be true")
            if bool(embed_payload.get("query_embedded", False)):
                pass_note("query_embedded=true")
            else:
                fail("query_embedded must be true")
            if "remaining_requests" in embed_payload:
                pass_note("embeddings remaining_requests present")
            else:
                fail("embeddings remaining_requests missing")

    if requirements.require_index_embeddings:
        evidence_status = _index_embeddings_evidence_status(artifacts_root)
        if evidence_status in {"OK", "PARTIAL"}:
            pass_note(f"index_embeddings_evidence.status={evidence_status}")
        else:
            zip_path, has_embeddings_jsonl = _first_zip_with_embeddings(artifacts_root)
            if has_embeddings_jsonl:
                notes.append(
                    "INFO: index embeddings found in zip, but strict mode expects "
                    "index_embeddings_evidence.status in {OK, PARTIAL}"
                )
                notes.append(f"INFO: zip source={zip_path.as_posix() if zip_path else 'n/a'}")
            fail(
                "index embeddings evidence missing/invalid: expected "
                "index_embeddings_evidence.status in {OK, PARTIAL}"
            )

    if requirements.require_patch:
        if _has_patch_artifact(artifacts_root):
            pass_note("patch artifact found (patch.diff or patch_parts/*.diff)")
        else:
            debug_path = _find_first(artifacts_root, "patch_generation_debug.json")
            llm_skip_reason = str(llm_payload.get("skip_reason", "n/a") or "n/a")
            llm_route = str(llm_payload.get("decision_route", "n/a") or "n/a")
            if debug_path is not None:
                debug_payload = _load_json(debug_path)
                debug_reason = str(debug_payload.get("reason", "n/a") or "n/a")
                fail(
                    "patch artifact missing: expected patch.diff or patch_parts/*.diff "
                    f"(llm_skip_reason={llm_skip_reason}, route={llm_route}, "
                    f"patch_debug_reason={debug_reason})"
                )
            else:
                fail(
                    "patch artifact missing: expected patch.diff or patch_parts/*.diff "
                    f"(llm_skip_reason={llm_skip_reason}, route={llm_route}, "
                    "patch_generation_debug.json missing)"
                )

    if requirements.require_batch_calls_min > 0:
        if not llm_payload:
            fail("llm_usage.json is required for batch assertions")
        else:
            totals_raw = llm_payload.get("totals", {})
            totals = totals_raw if isinstance(totals_raw, dict) else {}
            calls_count = _to_int(totals.get("calls_count", len(llm_payload.get("calls", []))))
            if calls_count >= requirements.require_batch_calls_min:
                pass_note(
                    f"batch calls_count={calls_count} (required>={requirements.require_batch_calls_min})"
                )
            else:
                fail(
                    f"batch calls_count={calls_count} is below required "
                    f"{requirements.require_batch_calls_min}"
                )
            if _find_first(artifacts_root, "batch_summaries.json") is not None:
                pass_note("batch_summaries.json present")
            else:
                notes.append("INFO: batch_summaries.json missing (optional)")

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
    batch_force: bool,
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
        f"batch_force={'true' if batch_force else 'false'}",
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
    batch_force: bool,
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
        batch_force=batch_force,
        trusted_context=trusted_context,
        allow_dynamic_verify=allow_dynamic_verify,
        apply_patch=apply_patch,
        create_pr=create_pr,
        e2e_command=e2e_command,
        e2e_pr_number=e2e_pr_number,
        e2e_ref=e2e_ref,
    )
    run_cmd(args, check=True)


def _dispatch_run(
    *,
    repo: str,
    workflow: str,
    branch: str,
    e2e_command: str,
    e2e_pr_number: str,
    toggles: dict[str, bool],
    timeout_s: int,
    gh_retries: int,
    gh_backoff_s: int,
) -> tuple[dict[str, Any] | None, str]:
    since = _now_utc()
    _workflow_dispatch(
        workflow=workflow,
        ref=branch,
        enable_llm=bool(toggles.get("enable_llm", False)),
        enable_embeddings=bool(toggles.get("enable_embeddings", False)),
        enable_batch_llm=bool(toggles.get("enable_batch_llm", False)),
        batch_force=bool(toggles.get("batch_force", False)),
        trusted_context=bool(toggles.get("trusted_context", False)),
        allow_dynamic_verify=bool(toggles.get("allow_dynamic_verify", False)),
        apply_patch=bool(toggles.get("apply_patch", False)),
        create_pr=bool(toggles.get("create_pr", False)),
        e2e_command=e2e_command,
        e2e_pr_number=e2e_pr_number,
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
            gh_retries=gh_retries,
            gh_backoff_s=gh_backoff_s,
        )
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)
    return run_data, ""


def _scenario_from_run(
    *,
    scenario_name: str,
    trigger: str,
    run_data: dict[str, Any],
    artifacts_root: Path,
    requirements: ScenarioRequirements,
) -> ScenarioResult:
    run_id = str(run_data.get("databaseId", "n/a"))
    run_url = str(run_data.get("url", "n/a") or "n/a")
    conclusion = str(run_data.get("conclusion", "n/a") or "n/a")
    status = "PASS" if conclusion == "success" else "FAIL"
    validation_status, notes = validate_artifacts(scenario_name, artifacts_root, requirements)
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
    spec: ScenarioSpec,
    artifacts_dir: Path,
    timeout_s: int,
    gh_retries: int,
    gh_backoff_s: int,
) -> ScenarioResult:
    print(
        f"[scenario:start] name={spec.name} mode=workflow_dispatch "
        f"command={spec.command} branch={branch} pr={pr_number}",
        flush=True,
    )
    run_data, error = _dispatch_run(
        repo=repo,
        workflow=workflow,
        branch=branch,
        e2e_command=spec.command,
        e2e_pr_number=pr_number,
        toggles={
            "enable_llm": spec.enable_llm,
            "enable_embeddings": spec.enable_embeddings,
            "enable_batch_llm": spec.enable_batch_llm,
            "batch_force": spec.batch_force,
            "trusted_context": spec.trusted_context,
            "allow_dynamic_verify": spec.allow_dynamic_verify,
            "apply_patch": spec.apply_patch,
            "create_pr": spec.create_pr,
        },
        timeout_s=timeout_s,
        gh_retries=gh_retries,
        gh_backoff_s=gh_backoff_s,
    )
    if run_data is None:
        print(f"[scenario:fail] name={spec.name} reason={error}", flush=True)
        return ScenarioResult(
            name=spec.name,
            trigger=spec.command,
            status="FAIL",
            conclusion="timeout",
            notes=[error],
            artifact_dir=(artifacts_dir / spec.name).as_posix(),
        )
    run_id = str(run_data.get("databaseId", "n/a"))
    target_dir = artifacts_dir / spec.name / run_id
    ok, msg = _download_artifacts(
        repo,
        run_id,
        target_dir,
        gh_retries=gh_retries,
        gh_backoff_s=gh_backoff_s,
    )
    result = _scenario_from_run(
        scenario_name=spec.name,
        trigger=spec.command,
        run_data=run_data,
        artifacts_root=target_dir,
        requirements=spec.requirements,
    )
    if not ok:
        result.notes.append(f"artifact download warning: {msg}")
        if result.status == "PASS":
            result.status = "WARN"
    return result


def _status_has_tracked_deletions(status_text: str) -> bool:
    for raw_line in status_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        lower = line.lower()
        if "deleted:" in lower:
            return True
        if line.startswith("??"):
            continue
        prefix = line[:2]
        if "D" in prefix:
            return True
    return False


def _commit_and_push(paths: list[Path], message: str, branch: str) -> None:
    print(f"[prep] checking git status before staging for: {message}", flush=True)
    pre_stage_status = run_cmd(["git", "status", "--porcelain"], check=True)
    if _status_has_tracked_deletions(pre_stage_status.out):
        print("[prep] detected tracked deletions, staging them via git add -A", flush=True)
        run_cmd(["git", "add", "-A"], check=True)

    if paths:
        add_args = ["git", "add", "--"] + [path.as_posix() for path in paths]
    else:
        add_args = ["git", "add", "-A"]
    print(
        f"[prep] staging {'explicit paths' if paths else 'all changes'} for commit: {message}",
        flush=True,
    )
    run_cmd(add_args, check=True)

    staged_status = run_cmd(["git", "status", "--porcelain"], check=True)
    if not staged_status.out.strip():
        print("[prep] no changes to commit, skipping commit", flush=True)
        return

    print(f"[prep] committing changes: {message}", flush=True)
    run_cmd(["git", "commit", "-m", message], check=True)
    print(f"[prep] pushing branch: {branch}", flush=True)
    run_cmd(["git", "push", "-u", "origin", branch], check=True)


def _clean_e2e_markers(branch: str) -> None:
    root = Path.cwd()
    markers = sorted(root.glob("e2e_marker_*.txt"))
    if markers:
        print(f"[prep] cleaning {len(markers)} marker file(s) in repo root", flush=True)
    else:
        print("[prep] no e2e marker files found in repo root", flush=True)

    for marker in markers:
        try:
            marker.unlink(missing_ok=True)
            print(f"[prep] removed marker file: {marker.name}", flush=True)
        except OSError as exc:
            print(f"[prep] marker cleanup warning for {marker.name}: {exc}", flush=True)

    run_cmd(["git", "rm", "-f", "--cached", "--", "e2e_marker_*.txt"], check=False)
    run_cmd(["git", "add", "-A"], check=True)

    status = run_cmd(["git", "status", "--porcelain"], check=True)
    if not status.out.strip():
        print("[prep] marker cleanup: no staged changes", flush=True)
        return
    if not branch.startswith("e2e/"):
        print("[prep] marker cleanup: branch is not e2e/*, skipping cleanup commit", flush=True)
        return

    print("[prep] committing marker cleanup", flush=True)
    run_cmd(["git", "commit", "-m", "e2e: cleanup markers"], check=True)
    print(f"[prep] pushing marker cleanup to branch: {branch}", flush=True)
    run_cmd(["git", "push", "-u", "origin", branch], check=True)


def _prepare_fixable_marker(branch: str) -> None:
    marker = Path("scripts/e2e/marker_bad.py")
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        "def add(a,b):  return a+b\n\n"
        "def loud_name(value):\n"
        "    temp=value.upper()\n"
        "    return temp\n",
        encoding="utf-8",
    )
    _commit_and_push([marker], "e2e: add fix marker", branch)


def _prepare_batch_markers(branch: str, files_count: int = 12) -> None:
    root = Path("scripts/e2e/batch_markers")
    root.mkdir(parents=True, exist_ok=True)
    changed: list[Path] = []
    stamp = int(time.time())
    for idx in range(1, files_count + 1):
        path = root / f"marker_{idx:02d}.py"
        path.write_text(
            f"def marker_{idx}(value):\n"
            f"    result = value + {idx}\n"
            f"    note = 'batch_{stamp}_{idx}'\n"
            "    return result, note\n",
            encoding="utf-8",
        )
        changed.append(path)
    _commit_and_push(changed, "e2e: add batch marker files", branch)


def _parse_bool_flag(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _build_marker_file_path(timestamp: int | None = None) -> Path:
    stamp = int(time.time()) if timestamp is None else int(timestamp)
    return Path("scripts/e2e/_markers") / f"e2e_marker_{stamp}.txt"


def _assert_marker_path_not_ignored(marker_file: Path) -> None:
    check = run_cmd(
        ["git", "check-ignore", "--quiet", marker_file.as_posix()],
        check=False,
    )
    if check.code == 0:
        raise RuntimeError(
            "E2E marker path is ignored by .gitignore: "
            f"{marker_file.as_posix()}. Use a non-ignored tracked path."
        )


def _build_scenarios(
    *,
    require_llm_used: bool,
    require_embeddings_used: bool,
    require_patch: bool,
    require_batch_calls_min: int,
) -> list[ScenarioSpec]:
    return [
        ScenarioSpec(
            name="review_dispatch",
            command="/repobrain review",
            enable_llm=False,
            enable_embeddings=False,
            enable_batch_llm=False,
            batch_force=False,
            trusted_context=False,
            allow_dynamic_verify=False,
            apply_patch=False,
            create_pr=False,
            requirements=ScenarioRequirements(),
        ),
        ScenarioSpec(
            name="llm_used_dispatch",
            command="/repobrain ask summarize the changes in this PR and highlight risks",
            enable_llm=True,
            enable_embeddings=False,
            enable_batch_llm=False,
            batch_force=False,
            trusted_context=True,
            allow_dynamic_verify=False,
            apply_patch=False,
            create_pr=False,
            requirements=ScenarioRequirements(require_llm_used=require_llm_used),
        ),
        ScenarioSpec(
            name="embeddings_warmup_dispatch",
            command="/repobrain ask warmup index embeddings",
            enable_llm=False,
            enable_embeddings=True,
            enable_batch_llm=False,
            batch_force=False,
            trusted_context=True,
            allow_dynamic_verify=False,
            apply_patch=False,
            create_pr=False,
            requirements=ScenarioRequirements(),
        ),
        ScenarioSpec(
            name="embeddings_used_dispatch",
            command="/repobrain ask list key modules related to retrieval and explain their roles",
            enable_llm=False,
            enable_embeddings=True,
            enable_batch_llm=False,
            batch_force=False,
            trusted_context=True,
            allow_dynamic_verify=False,
            apply_patch=False,
            create_pr=False,
            requirements=ScenarioRequirements(
                require_embeddings_used=require_embeddings_used,
                require_index_embeddings=require_embeddings_used,
            ),
        ),
        ScenarioSpec(
            name="fix_patch_required_dispatch",
            command=(
                "/repobrain fix apply ruff-style fixes and improve naming "
                "in scripts/e2e/marker_bad.py"
            ),
            enable_llm=True,
            enable_embeddings=False,
            enable_batch_llm=False,
            batch_force=False,
            trusted_context=True,
            allow_dynamic_verify=True,
            apply_patch=False,
            create_pr=False,
            requirements=ScenarioRequirements(
                require_llm_used=require_llm_used,
                require_patch=require_patch,
            ),
        ),
        ScenarioSpec(
            name="batch_llm_dispatch",
            command="/repobrain review",
            enable_llm=True,
            enable_embeddings=False,
            enable_batch_llm=True,
            batch_force=True,
            trusted_context=True,
            allow_dynamic_verify=False,
            apply_patch=False,
            create_pr=False,
            requirements=ScenarioRequirements(
                require_llm_used=require_llm_used,
                require_batch_calls_min=max(0, require_batch_calls_min),
            ),
        ),
    ]


def _create_temp_pr(*, repo: str, default_branch: str, branch: str, marker_file: Path) -> tuple[str, str]:
    marker_file.parent.mkdir(parents=True, exist_ok=True)
    _assert_marker_path_not_ignored(marker_file)
    marker_file.write_text(
        f"RepoBrain e2e marker: {_now_utc().isoformat()}\n",
        encoding="utf-8",
    )
    run_cmd(["git", "checkout", "-b", branch], check=True)
    run_cmd(["git", "add", "--", marker_file.as_posix()], check=True)
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
    parser.add_argument(
        "--require-llm-used",
        default="true",
        choices=["true", "false"],
        help="Require llm_used=true in llm/batch/fix scenarios.",
    )
    parser.add_argument(
        "--require-embeddings-used",
        default="true",
        choices=["true", "false"],
        help="Require embeddings usage in embeddings scenario.",
    )
    parser.add_argument(
        "--require-patch",
        default="true",
        choices=["true", "false"],
        help="Require patch artifact in fix scenario.",
    )
    parser.add_argument(
        "--require-batch-calls-min",
        type=int,
        default=2,
        help="Minimum LLM calls for batch scenario.",
    )
    parser.add_argument(
        "--gh-retries",
        type=int,
        default=5,
        help="Retries for transient gh network failures.",
    )
    parser.add_argument(
        "--gh-backoff-s",
        type=int,
        default=2,
        help="Base backoff (seconds) for gh retries.",
    )
    args = parser.parse_args()

    _ensure_gh_ready()
    remote = run_cmd(["git", "remote", "get-url", "origin"], check=True).out.strip()
    repo = parse_repo_slug(remote)
    default_branch = _git_default_branch(repo)
    short_sha = run_cmd(["git", "rev-parse", "--short", "HEAD"], check=True).out.strip()
    branch = f"e2e/{_now_utc().strftime('%Y%m%d-%H%M%S')}-{short_sha}"

    marker_file = _build_marker_file_path()
    artifacts_root = Path(args.artifacts_dir)
    artifacts_root.mkdir(parents=True, exist_ok=True)

    pr_number = ""
    pr_url = ""
    results: list[ScenarioResult] = []
    scenarios = _build_scenarios(
        require_llm_used=_parse_bool_flag(args.require_llm_used),
        require_embeddings_used=_parse_bool_flag(args.require_embeddings_used),
        require_patch=_parse_bool_flag(args.require_patch),
        require_batch_calls_min=max(0, int(args.require_batch_calls_min)),
    )
    try:
        pr_number, pr_url = _create_temp_pr(
            repo=repo,
            default_branch=default_branch,
            branch=branch,
            marker_file=marker_file,
        )
        _clean_e2e_markers(branch)
        for spec in scenarios:
            if spec.name == "fix_patch_required_dispatch":
                _clean_e2e_markers(branch)
                print("[prep] creating fixable marker file", flush=True)
                _prepare_fixable_marker(branch)
            if spec.name == "batch_llm_dispatch":
                _clean_e2e_markers(branch)
                print("[prep] creating batch marker files", flush=True)
                _prepare_batch_markers(branch, files_count=12)
            result = _scenario_dispatch_command(
                repo=repo,
                workflow=args.workflow,
                branch=branch,
                pr_number=pr_number,
                spec=spec,
                artifacts_dir=artifacts_root,
                timeout_s=args.scenario_timeout_s,
                gh_retries=args.gh_retries,
                gh_backoff_s=args.gh_backoff_s,
            )
            results.append(result)
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
