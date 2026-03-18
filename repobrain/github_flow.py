from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Any
import zipfile

import requests

from repobrain.ai_budget_governor import (
    AIBudgetGovernor,
    QuotaSignal,
    build_governor_from_env,
)
from repobrain.audit import add_timing, build_audit_base, finalize_audit
from repobrain.ask import AnswerResult, answer_question, make_provider
from repobrain.commands import parse_command
from repobrain.checks_md import (
    build_check_summary_markdown,
    check_name_for_command,
    map_check_conclusion,
)
from repobrain.config import RepoBrainConfig, env_bool, env_int, load_config
from repobrain import __version__ as REPOBRAIN_VERSION
from repobrain.evidence import EvidenceItem
from repobrain.evidence_filter import filter_candidate_evidence, filter_evidence_items
from repobrain.execution_mode import coerce_execution_decision
from repobrain.fix.patch_extract import (
    extract_patch_candidate as extract_patch_candidate_normalized,
    is_unified_diff as is_unified_diff_normalized,
    normalize_patch_output as normalize_patch_output_value,
)
from repobrain.fix.patch_guard import evaluate_patch_payload
from repobrain.formatting import format_refusal_comment, format_verify_comment
from repobrain.github_publisher import (
    build_check_run_payload,
    create_pull_request,
    publish_check_run,
    publish_comment,
)
from repobrain.index_store import build_index, load_index, load_index_embeddings
from repobrain.output_md import (
    enforce_comment_limit,
    render_diagnostic_summary_markdown,
    render_answer_markdown,
    render_error_markdown,
    render_patch_markdown,
    render_refuse_markdown,
    render_review_markdown,
    render_wait_markdown,
)
from repobrain.retrieve_pro import retrieve_topk_pro
from repobrain.retrieval.hybrid import rank_hybrid_candidates
from repobrain.retrieval.hybrid_ranker import rerank_candidates
from repobrain.retrieval.evidence_budget_planner import plan_evidence_budget
from repobrain.retrieval.incremental_index import scope_chunks_incremental
from repobrain.pr_segmenter import build_pr_segmentation, segmentation_defaults
from repobrain.review import build_pr_review
from repobrain.review_validator import validate_review_findings
from repobrain.patch_validator import validate_patch_grounding
from repobrain.patch_targeting import select_patch_targets
from repobrain.security_policy import classify_security_scope
from repobrain.tky_local import LocalTKYProvider
from repobrain.tky_provider import CandidateChunk, TKYResult
from repobrain.tky_remote import RemoteTKYError, RemoteTKYProvider
from repobrain.quality_gates import compute_conclusion
from repobrain.llm.github_models import GitHubModelsClient, GitHubModelsError
from repobrain.llm.github_models_embeddings import (
    GitHubModelsEmbeddingsClient,
    GitHubModelsEmbeddingsError,
)
from repobrain.llm.batch_planner import Batch, plan_batches
from repobrain.llm.model_selector import (
    choose_model,
    complexity_explanation,
    compute_output_token_budget,
    model_selection_reason,
    score_complexity,
)
from repobrain.llm.prompts import (
    build_messages_for_ask,
    build_messages_for_fix,
    build_messages_for_review,
    estimate_tokens,
)
from repobrain.verification_runner import (
    VerificationBudgets,
    detect_capabilities,
    run_verification,
)
from repobrain.verify import build_verify_report

HELP_TEXT = """RepoBrain command examples:
- /repobrain help
- /repobrain ask How does provider selection work?
- /repobrain locate TKYProvider
- /repobrain explain retrieve_topk
- /repobrain review
- /repobrain fix Improve guard conditions in github_flow
- /repobrain verify (PR checks-based verification ladder v0)
"""

BOT_MARKER = "[bot]"
_LAST_AUDIT: dict[str, Any] | None = None
_RUNTIME_ENV_CFG: RepoBrainConfig | None = None


@dataclass(frozen=True)
class EventContext:
    comment_text: str = ""
    issue_number: int | None = None
    comment_id: int | None = None
    comment_user_login: str = ""
    is_pull_request: bool = False


def get_last_audit() -> dict[str, Any]:
    """Return the last run audit payload (copy-safe shallow clone)."""
    if _LAST_AUDIT is None:
        return {}
    return dict(_LAST_AUDIT)


def _set_last_audit(audit: dict[str, Any]) -> None:
    global _LAST_AUDIT
    _LAST_AUDIT = finalize_audit(audit)


def _set_runtime_env_cfg(cfg: RepoBrainConfig | None) -> None:
    global _RUNTIME_ENV_CFG
    _RUNTIME_ENV_CFG = cfg


def _runtime_env_cfg() -> RepoBrainConfig:
    if _RUNTIME_ENV_CFG is not None:
        return _RUNTIME_ENV_CFG
    return RepoBrainConfig.from_env()


def _load_event_payload(event_path: Path | None) -> dict[str, Any]:
    if event_path is None or not event_path.exists():
        return {}

    try:
        payload = json.loads(event_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    return payload if isinstance(payload, dict) else {}


def _parse_optional_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return parse_issue_number(value)
    return None


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


def extract_event_context_from_event(event_path: Path | None) -> EventContext:
    """Extract relevant issue_comment fields from a GitHub event payload file."""
    payload = _load_event_payload(event_path)
    comment = payload.get("comment", {})
    issue = payload.get("issue", {})

    comment_body = ""
    comment_id = None
    comment_user_login = ""
    if isinstance(comment, dict):
        body = comment.get("body")
        comment_body = body if isinstance(body, str) else ""

        comment_id = _parse_optional_int(comment.get("id"))
        user = comment.get("user", {})
        if isinstance(user, dict):
            login = user.get("login")
            if isinstance(login, str):
                comment_user_login = login

    issue_number = None
    is_pull_request = False
    if isinstance(issue, dict):
        issue_number = _parse_optional_int(issue.get("number"))
        pull_request = issue.get("pull_request")
        is_pull_request = isinstance(pull_request, dict)

    return EventContext(
        comment_text=comment_body,
        issue_number=issue_number,
        comment_id=comment_id,
        comment_user_login=comment_user_login,
        is_pull_request=is_pull_request,
    )


def extract_comment_text_from_event(event_path: Path | None) -> str:
    return extract_event_context_from_event(event_path).comment_text


def extract_issue_number_from_event(event_path: Path | None) -> int | None:
    return extract_event_context_from_event(event_path).issue_number


def extract_comment_id_from_event(event_path: Path | None) -> int | None:
    return extract_event_context_from_event(event_path).comment_id


def extract_comment_user_login_from_event(event_path: Path | None) -> str:
    return extract_event_context_from_event(event_path).comment_user_login


def extract_is_pull_request_from_event(event_path: Path | None) -> bool:
    return extract_event_context_from_event(event_path).is_pull_request


def build_issue_comment_url(repo: str, issue_number: int) -> str:
    """Build GitHub REST URL for creating an issue comment."""
    return f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"


def build_reaction_url(repo: str, comment_id: int) -> str:
    """Build GitHub REST URL for adding a reaction to an issue comment."""
    return f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}/reactions"


def build_pr_files_url(repo: str, pull_number: int) -> str:
    """Build GitHub REST URL for listing PR files."""
    return f"https://api.github.com/repos/{repo}/pulls/{pull_number}/files?per_page=100"


class GitHubClient:
    """Minimal GitHub REST client for issue comments, reactions, and PR files."""

    def __init__(self, repo: str, token: str) -> None:
        self.repo = repo
        self.token = token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def create_issue_comment(self, issue_number: int, body_markdown: str) -> None:
        """POST a comment to a GitHub Issue or PR thread."""
        result = publish_comment(
            repo=self.repo,
            token=self.token,
            issue_or_pr=issue_number,
            markdown=body_markdown,
        )
        if not bool(result.get("ok", False)):
            status = result.get("status_code")
            raise RuntimeError(f"Failed to create issue comment (status={status})")

    def add_reaction_to_issue_comment(self, comment_id: int, content: str = "eyes") -> None:
        """Add a reaction (default 👀) to an issue comment."""
        response = requests.post(
            build_reaction_url(self.repo, comment_id),
            json={"content": content},
            headers=self._headers(),
            timeout=15,
        )
        response.raise_for_status()

    def get_pull_files(self, pull_number: int) -> list[dict[str, Any]]:
        """Fetch PR files metadata from GitHub REST API."""
        try:
            response = requests.get(
                build_pr_files_url(self.repo, pull_number),
                headers=self._headers(),
                timeout=15,
            )
        except requests.RequestException:
            print("PR files endpoint not accessible, using empty file list")
            return []
        status_code = int(getattr(response, "status_code", 200))
        if status_code in {403, 404} or status_code >= 500:
            print(f"PR files endpoint returned {status_code}, using empty file list")
            return []
        try:
            response.raise_for_status()
        except requests.HTTPError:
            print("PR files endpoint returned unexpected error, using empty file list")
            return []
        data = response.json()
        if not isinstance(data, list):
            return []
        return [item for item in data if isinstance(item, dict)]

    def get_pull(self, pull_number: int) -> dict[str, Any]:
        """Fetch PR metadata (used for head SHA lookup)."""
        try:
            response = requests.get(
                f"https://api.github.com/repos/{self.repo}/pulls/{pull_number}",
                headers=self._headers(),
                timeout=15,
            )
        except requests.RequestException:
            print("PR metadata endpoint not accessible")
            return {"_error": "network"}
        status_code = int(getattr(response, "status_code", 200))
        if status_code in {403, 404}:
            print("PR metadata endpoint not accessible (forbidden/not found)")
            return {"_error": "forbidden" if status_code == 403 else "not_found"}
        if status_code >= 500:
            print("PR metadata endpoint returned server error")
            return {"_error": f"http_{status_code}"}
        try:
            response.raise_for_status()
        except requests.HTTPError:
            return {"_error": f"http_{status_code}"}
        data = response.json()
        return data if isinstance(data, dict) else {}

    def get_check_runs(self, sha: str) -> dict[str, Any]:
        """Fetch check-runs for a commit SHA."""
        try:
            response = requests.get(
                f"https://api.github.com/repos/{self.repo}/commits/{sha}/check-runs",
                headers=self._headers(),
                timeout=15,
            )
        except requests.RequestException:
            print("Check-runs endpoint not accessible, falling back")
            return {"total_count": 0, "check_runs": [], "_error": "network"}
        status_code = int(getattr(response, "status_code", 200))
        if status_code == 403:
            print("Check-runs not accessible, falling back to combined status")
            return {"total_count": 0, "check_runs": [], "_error": "forbidden"}
        if status_code == 404:
            print("Check-runs not accessible, falling back to combined status")
            return {"total_count": 0, "check_runs": [], "_error": "not_found"}
        if status_code >= 500:
            print("Check-runs endpoint returned server error, falling back")
            return {"total_count": 0, "check_runs": [], "_error": f"http_{status_code}"}
        try:
            response.raise_for_status()
        except requests.HTTPError:
            return {"total_count": 0, "check_runs": [], "_error": f"http_{status_code}"}
        data = response.json()
        return data if isinstance(data, dict) else {"total_count": 0, "check_runs": []}

    def get_combined_status(self, sha: str) -> dict[str, Any]:
        """Fetch combined commit status (fallback when no check-runs exist)."""
        try:
            response = requests.get(
                f"https://api.github.com/repos/{self.repo}/commits/{sha}/status",
                headers=self._headers(),
                timeout=15,
            )
        except requests.RequestException:
            print("Combined status endpoint not accessible")
            return {"state": "unknown", "statuses": [], "_error": "network"}
        status_code = int(getattr(response, "status_code", 200))
        if status_code == 403:
            print("Combined status not accessible due to token permissions")
            return {"state": "unknown", "statuses": [], "_error": "forbidden"}
        if status_code == 404:
            return {"state": "unknown", "statuses": [], "_error": "not_found"}
        if status_code >= 500:
            return {"state": "unknown", "statuses": [], "_error": f"http_{status_code}"}
        try:
            response.raise_for_status()
        except requests.HTTPError:
            return {"state": "unknown", "statuses": [], "_error": f"http_{status_code}"}
        data = response.json()
        return data if isinstance(data, dict) else {"state": "unknown", "statuses": []}

    def get_workflow_runs(self, *, head_sha: str | None = None, per_page: int = 20) -> dict[str, Any]:
        """Fetch recent workflow runs (used as verify fallback source)."""
        url = f"https://api.github.com/repos/{self.repo}/actions/runs?per_page={int(per_page)}"
        try:
            response = requests.get(
                url,
                headers=self._headers(),
                timeout=15,
            )
        except requests.RequestException:
            print("Workflow runs endpoint not accessible")
            return {"total_count": 0, "workflow_runs": [], "_error": "network"}
        status_code = int(getattr(response, "status_code", 200))
        if status_code == 403:
            return {"total_count": 0, "workflow_runs": [], "_error": "forbidden"}
        if status_code == 404:
            return {"total_count": 0, "workflow_runs": [], "_error": "not_found"}
        if status_code >= 500:
            return {"total_count": 0, "workflow_runs": [], "_error": f"http_{status_code}"}
        try:
            response.raise_for_status()
        except requests.HTTPError:
            return {"total_count": 0, "workflow_runs": [], "_error": f"http_{status_code}"}
        data = response.json()
        if not isinstance(data, dict):
            return {"total_count": 0, "workflow_runs": []}
        runs = data.get("workflow_runs", [])
        if isinstance(runs, list) and head_sha:
            runs = [run for run in runs if isinstance(run, dict) and str(run.get("head_sha", "")) == head_sha]
            data = dict(data)
            data["workflow_runs"] = runs
            data["total_count"] = len(runs)
        return data


def extract_repo_from_env() -> str:
    return os.environ.get("GITHUB_REPOSITORY", "").strip()


def extract_sha_from_env() -> str:
    return os.environ.get("GITHUB_SHA", "").strip()


def extract_branch_from_env() -> str:
    name = os.environ.get("GITHUB_REF_NAME", "").strip()
    if name:
        return name
    raw_ref = os.environ.get("GITHUB_REF", "").strip()
    prefix = "refs/heads/"
    if raw_ref.startswith(prefix):
        return raw_ref[len(prefix) :]
    return "unknown"


def resolve_repo_root(start: Path | None = None, *, max_depth: int = 5) -> Path:
    """Resolve repository root by walking up until `pyproject.toml` is found."""
    current = start or Path(__file__).resolve()
    if current.is_file():
        current = current.parent

    candidate = current.resolve()
    for _ in range(max_depth + 1):
        if (candidate / "pyproject.toml").exists():
            return candidate
        if candidate.parent == candidate:
            break
        candidate = candidate.parent
    return Path.cwd().resolve()


def _extract_changed_files(payload: dict[str, Any]) -> list[str]:
    changed: list[str] = []
    files_raw = payload.get("files", [])
    if isinstance(files_raw, list):
        for item in files_raw:
            if isinstance(item, dict):
                path = str(item.get("filename", "") or "").strip()
            else:
                path = str(item).strip()
            if path:
                changed.append(path)
    changed_files_raw = payload.get("changed_files", [])
    if isinstance(changed_files_raw, list):
        for item in changed_files_raw:
            path = str(item).strip()
            if path:
                changed.append(path)
    return sorted(set(changed))


def _extract_diff_hunks(payload: dict[str, Any]) -> list[str]:
    hunks_raw = payload.get("diff_hunks", [])
    if not isinstance(hunks_raw, list):
        return []
    hunks: list[str] = []
    for item in hunks_raw:
        text = str(item).strip()
        if text:
            hunks.append(text)
    return hunks


def _build_github_context_seed(
    *,
    payload: dict[str, Any],
    event_ctx: EventContext,
    resolved_issue_number: int | None,
) -> dict[str, Any]:
    event_name = os.environ.get("GITHUB_EVENT_NAME", "").strip()
    run_id = os.environ.get("GITHUB_RUN_ID", "").strip()
    actor = os.environ.get("GITHUB_ACTOR", "").strip()
    ref = os.environ.get("GITHUB_REF", "").strip()
    repository = extract_repo_from_env()
    sha = extract_sha_from_env()

    pull = payload.get("pull_request", {})
    issue = payload.get("issue", {})
    if isinstance(issue, dict) and isinstance(issue.get("pull_request"), dict):
        pull = issue.get("pull_request", {})

    base_sha = ""
    head_sha = ""
    base_ref = ""
    head_ref = ""
    if isinstance(pull, dict):
        base = pull.get("base", {})
        head = pull.get("head", {})
        if isinstance(base, dict):
            base_sha = str(base.get("sha", "") or "")
            base_ref = str(base.get("ref", "") or "")
        if isinstance(head, dict):
            head_sha = str(head.get("sha", "") or "")
            head_ref = str(head.get("ref", "") or "")

    return {
        "event_name": event_name,
        "repository": repository,
        "sha": sha,
        "ref": ref,
        "run_id": run_id,
        "actor": actor,
        "issue_number": resolved_issue_number,
        "pr_number": resolved_issue_number if event_ctx.is_pull_request else None,
        "is_pr": event_ctx.is_pull_request,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "base_ref": base_ref,
        "head_ref": head_ref,
        "changed_files": _extract_changed_files(payload),
        "diff_hunks": _extract_diff_hunks(payload),
    }


def _safe_parse_pr_number(value: str) -> int | None:
    try:
        return parse_issue_number(value)
    except ValueError:
        print("E2E dispatch simulation ignored invalid RB_E2E_PR_NUMBER")
        return None


def _build_dispatch_pr_payload(*, repo: str, pr_number: int | None) -> dict[str, Any]:
    if not repo or pr_number is None:
        return {}
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        print("E2E dispatch simulation: missing GITHUB_TOKEN, PR context fetch skipped")
        return {
            "issue": {"number": pr_number, "pull_request": {}},
            "pull_request": {},
            "files": [],
            "changed_files": [],
            "diff_hunks": [],
        }

    client = GitHubClient(repo=repo, token=token)
    pull_payload = client.get_pull(pr_number)
    files_payload = client.get_pull_files(pr_number)
    base_raw = pull_payload.get("base", {}) if isinstance(pull_payload, dict) else {}
    head_raw = pull_payload.get("head", {}) if isinstance(pull_payload, dict) else {}
    base = base_raw if isinstance(base_raw, dict) else {}
    head = head_raw if isinstance(head_raw, dict) else {}

    files: list[dict[str, str]] = []
    changed_files: list[str] = []
    diff_hunks: list[str] = []
    for item in files_payload:
        if not isinstance(item, dict):
            continue
        filename = str(item.get("filename", "") or "").strip()
        if filename:
            files.append({"filename": filename})
            changed_files.append(filename)
        patch = item.get("patch")
        if isinstance(patch, str):
            patch_clean = patch.strip()
            if patch_clean:
                diff_hunks.append(patch_clean)

    return {
        "issue": {
            "number": pr_number,
            "pull_request": {"url": f"https://api.github.com/repos/{repo}/pulls/{pr_number}"},
        },
        "pull_request": {
            "base": {"sha": str(base.get("sha", "") or ""), "ref": str(base.get("ref", "") or "")},
            "head": {"sha": str(head.get("sha", "") or ""), "ref": str(head.get("ref", "") or "")},
        },
        "files": files,
        "changed_files": sorted(set(changed_files)),
        "diff_hunks": diff_hunks,
    }


def _resolve_workflow_dispatch_simulation(
    *,
    repo: str,
    source_text: str,
    resolved_issue_number: int | None,
    event_ctx: EventContext,
    event_payload: dict[str, Any],
) -> tuple[str, int | None, EventContext, dict[str, Any]]:
    event_name = os.environ.get("GITHUB_EVENT_NAME", "").strip()
    simulated_command = os.environ.get("RB_E2E_COMMAND", "").strip()
    if event_name != "workflow_dispatch" or not simulated_command:
        return source_text, resolved_issue_number, event_ctx, event_payload

    pr_from_env = _safe_parse_pr_number(os.environ.get("RB_E2E_PR_NUMBER", ""))
    resolved_issue = resolved_issue_number if resolved_issue_number is not None else pr_from_env
    simulated_event_ctx = EventContext(
        comment_text=simulated_command,
        issue_number=resolved_issue,
        comment_id=None,
        comment_user_login="",
        is_pull_request=resolved_issue is not None,
    )
    simulated_payload = _build_dispatch_pr_payload(repo=repo, pr_number=resolved_issue)
    print(
        "Workflow dispatch simulation enabled: "
        f"command={simulated_command} pr={resolved_issue if resolved_issue is not None else 'n/a'}"
    )
    return simulated_command, resolved_issue, simulated_event_ctx, simulated_payload


def _build_verification_context_seed(
    *,
    time_budget_s: int = 30,
    env_cfg: RepoBrainConfig | None = None,
) -> dict[str, Any]:
    repo_root = resolve_repo_root()
    can_run_pytest = (repo_root / "tests").exists()
    can_run_ruff = (repo_root / "pyproject.toml").exists()
    cfg = env_cfg or _runtime_env_cfg()
    return {
        "can_run_pytest": can_run_pytest,
        "can_run_ruff": can_run_ruff,
        "time_budget_s": int(time_budget_s),
        "mode": "ci" if cfg.workflow.github_actions else "local",
        "allow_patch_apply": bool(cfg.workflow.apply_patch),
        "network_allowed": bool(cfg.tkya.allow_remote),
        "checks": [],
        "required_checks": ["ruff", "pytest"],
    }


def _extract_verification_audit_fields(compression_stats: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    key_map = (
        "verification_pass_count",
        "verification_fail_count",
        "verification_pending_count",
        "verification_not_run_count",
        "verification_gate_decision",
        "verification_gate_reason",
        "verification_profile",
    )
    for key in key_map:
        if key in compression_stats:
            fields[key] = compression_stats[key]
    for list_key in ("verified", "not_run", "verification_failed", "verification_pending"):
        raw = compression_stats.get(list_key, [])
        if isinstance(raw, list):
            fields[list_key] = [str(item) for item in raw if str(item).strip()]
    return fields


def _write_ask_result_markdown(repo_root: Path, markdown: str) -> Path:
    path = repo_root / "artifacts" / "ask_result.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return path


def _write_diagnostic_summary_markdown(repo_root: Path, markdown: str) -> Path:
    path = repo_root / "artifacts" / "diagnostic_summary.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")
    return path


def _env_true(name: str, default: bool = False) -> bool:
    cfg = _runtime_env_cfg()
    mapping: dict[str, bool] = {
        "RB_LLM_ENABLED": cfg.llm.enabled,
        "RB_LLM_ALLOW_LOCATE": cfg.llm.allow_locate,
        "RB_EMBED_ENABLED": cfg.embeddings.enabled,
        "RB_LLM_BATCH_ENABLE": cfg.batch.enabled,
        "RB_LLM_BATCH_FORCE": cfg.batch.force,
        "RB_LLM_BATCH_REDUCE_ENABLE": cfg.batch.reduce_enable,
        "RB_LLM_PATCH_BATCH_ENABLE": cfg.batch.patch_enable,
        "RB_LLM_PATCH_BATCH_FORCE": cfg.batch.patch_force,
        "RB_TRUSTED_CONTEXT": cfg.workflow.trusted_context,
        "RB_ALLOW_DYNAMIC_VERIFY": cfg.workflow.allow_dynamic_verify,
        "RB_APPLY_PATCH": cfg.workflow.apply_patch,
        "RB_CREATE_PR": cfg.workflow.create_pr,
        "RB_REQUIRE_VERIFY_FOR_PATCH": cfg.workflow.require_verify_for_patch,
        "RB_FAIL_ON_NOT_RUN": cfg.workflow.fail_on_not_run,
        "RB_DISABLE_INTERNAL_REACTIONS": cfg.workflow.disable_internal_reactions,
        "RB_INDEX_CACHE_RESTORED": cfg.workflow.index_cache_restored,
        "RB_TKYA_ALLOW_REMOTE": cfg.tkya.allow_remote,
    }
    if name in mapping:
        return bool(mapping[name])
    return env_bool(name, default)


def _is_dispatch_e2e_simulation() -> bool:
    return (
        os.environ.get("GITHUB_EVENT_NAME", "").strip() == "workflow_dispatch"
        and bool(os.environ.get("RB_E2E_COMMAND", "").strip())
    )


def _env_int(name: str, default: int) -> int:
    cfg = _runtime_env_cfg()
    mapping: dict[str, int] = {
        "RB_VERIFY_TIME_BUDGET_S": cfg.workflow.verify_time_budget_s,
        "RB_LLM_MAX_INPUT_TOKENS": cfg.llm.max_input_tokens,
        "RB_LLM_MAX_INPUT_TOKENS_PATCH": cfg.llm.max_input_tokens_patch,
        "RB_LLM_MAX_OUTPUT_TOKENS_PATCH": cfg.llm.max_output_tokens_patch,
        "RB_LLM_BATCH_MAX_CALLS_PER_RUN": cfg.batch.max_calls_per_run,
        "RB_LLM_PATCH_BATCH_MAX_CALLS": cfg.batch.patch_max_calls,
        "RB_LLM_PATCH_MAX_HUNKS_PER_CALL": cfg.batch.patch_max_hunks_per_call,
        "RB_RETRIEVAL_VECTOR_TOPK": cfg.embeddings.vector_topk,
    }
    if name in mapping:
        return int(mapping[name])
    return env_int(name, default)


def _llm_runtime_policy(
    github_context: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    cfg = _runtime_env_cfg()
    if not bool(cfg.llm.enabled):
        return False, "disabled"
    provider = str(cfg.llm.provider or "").strip().lower()
    if provider != "github_models":
        return False, "disabled"

    context = github_context if isinstance(github_context, dict) else {}
    event_name = str(
        context.get("event_name") or os.environ.get("GITHUB_EVENT_NAME", "")
    ).strip().lower()
    is_pr_context = bool(
        context.get("is_pr")
        or context.get("pr_number")
        or context.get("pull_request")
    )

    if event_name == "issue_comment":
        if not bool(cfg.llm.enable_issue_comment):
            return False, "issue_comment_policy_disabled"
        if is_pr_context:
            if not bool(cfg.llm.enable_pr_comments):
                return False, "pr_comment_policy_disabled"
        elif not bool(cfg.llm.enable_issue_only):
            return False, "issue_only_policy_disabled"

    return True, "n/a"


def _llm_policy_context_fields(github_context: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = _runtime_env_cfg()
    context = github_context if isinstance(github_context, dict) else {}
    event_name = str(
        context.get("event_name") or os.environ.get("GITHUB_EVENT_NAME", "")
    ).strip().lower()
    is_pr_context = bool(
        context.get("is_pr")
        or context.get("pr_number")
        or context.get("pull_request")
    )
    return {
        "llm_policy_event_name": event_name or "n/a",
        "llm_policy_is_pr_context": bool(is_pr_context),
        "llm_policy_issue_comment_enabled": bool(cfg.llm.enable_issue_comment),
        "llm_policy_pr_comments_enabled": bool(cfg.llm.enable_pr_comments),
        "llm_policy_issue_only_enabled": bool(cfg.llm.enable_issue_only),
    }


def _attach_llm_policy_fields(
    llm_meta: dict[str, Any],
    *,
    github_context: dict[str, Any] | None,
    allowed: bool,
) -> dict[str, Any]:
    llm_meta.update(_llm_policy_context_fields(github_context))
    llm_meta["llm_policy_allowed"] = bool(allowed)
    return llm_meta


def _llm_enabled(github_context: dict[str, Any] | None = None) -> bool:
    allowed, _ = _llm_runtime_policy(github_context)
    return bool(allowed)


def _llm_default_meta(
    reason: str = "not used",
    *,
    execution_mode: str = "retrieval_only",
    llm_intent: str = "none",
    llm_decision_reason_short: str = "LLM not used: direct answer available from retrieved evidence.",
    llm_decision_reason_code: str = "DEFAULT_RETRIEVAL_ONLY",
) -> dict[str, Any]:
    call_entry = {
        "batch_id": "single",
        "model_id": "not used",
        "tier": "n/a",
        "tokens_prompt": 0,
        "tokens_completion": 0,
        "tokens_total": 0,
        "remaining_requests": "n/a",
        "remaining_is_estimate": True,
        "reset_time_utc_iso": None,
        "estimate_flags": {
            "usage_estimated": True,
            "remaining_estimated": True,
        },
    }
    return {
        "llm_used": False,
        "llm_skip_reason": reason,
        "execution_mode": execution_mode,
        "llm_intent": llm_intent,
        "llm_decision_reason_short": llm_decision_reason_short,
        "llm_decision_reason_code": llm_decision_reason_code,
        "llm_runtime_override_reason": "n/a",
        "llm_model_used": "not used",
        "llm_final_synthesis_model_id": "not used",
        "llm_preferred_model_id": "n/a",
        "llm_model_selection_reason": "n/a",
        "llm_model_downgrade_reason": "n/a",
        "llm_retained_preferred_model_reason": "n/a",
        "llm_final_synthesis_retained_preferred_model": False,
        "llm_intermediate_downgrade_occurred": False,
        "llm_intermediate_downgrade_reason": "n/a",
        "llm_downgrade_threshold_used": "n/a",
        "llm_primary_model_id": "not used",
        "llm_effective_model_id": "not used",
        "llm_fallback_used": False,
        "llm_tier": "n/a",
        "llm_tokens_prompt": 0,
        "llm_tokens_completion": 0,
        "llm_tokens_total": 0,
        "llm_usage_estimated": True,
        "llm_remaining_requests": "n/a",
        "llm_remaining_is_estimate": True,
        "llm_reset_time_utc_iso": None,
        "llm_reason": reason,
        "llm_decision_route": "n/a",
        "llm_budget_action": "n/a",
        "llm_governor_reason": "n/a",
        "llm_complexity_score": 0,
        "llm_complexity_explanation": "n/a",
        "llm_calls_this_run": 0,
        "llm_max_output_tokens_used": 0,
        "llm_input_budget_limit": 0,
        "llm_input_budget_used_est": 0,
        "llm_dropped_locators_count": 0,
        "llm_dropped_hunks_count": 0,
        "llm_dropped_snippets_count": 0,
        "llm_ratelimit_headers": {},
        "llm_provider_http_status": None,
        "llm_provider_error_type": "n/a",
        "llm_primary_status": None,
        "llm_fallback_status": None,
        "llm_error_types": [],
        "llm_calls": [call_entry],
        "llm_model_counts": {},
        # Backward-compatible aliases used by older formatting/tests.
        "llm_requests_remaining": "n/a",
        "llm_rate_limit_reset": "n/a",
    }


def _merge_llm_meta(target: dict[str, Any], llm_meta: dict[str, Any]) -> None:
    for key, value in llm_meta.items():
        if key.startswith("llm_") or key == "execution_mode":
            target[key] = value


def _merge_embeddings_meta(target: dict[str, Any], meta: dict[str, Any]) -> None:
    for key, value in meta.items():
        if key.startswith("embed_"):
            target[key] = value


def _is_fix_intent(cmd: str, intent: str) -> bool:
    return cmd == "fix" or intent == "patch"


def _llm_downgrade_threshold_for_command(cfg: RepoBrainConfig, cmd: str, intent: str) -> int:
    normalized_cmd = str(cmd or "").strip().lower()
    normalized_intent = str(intent or "").strip().lower()
    if _is_fix_intent(normalized_cmd, normalized_intent):
        return max(0, int(cfg.llm.downgrade_min_remaining_requests_fix))
    if normalized_cmd == "review":
        return max(0, int(cfg.llm.downgrade_min_remaining_requests_review))
    return max(0, int(cfg.llm.downgrade_min_remaining_requests_ask))


def _should_retain_preferred_model_for_ask(
    *,
    cfg: RepoBrainConfig,
    cmd: str,
    execution_mode: str,
    llm_intent: str,
    route: str,
    complexity_score: int,
    remaining_requests: int | None,
    github_context: dict[str, Any],
) -> tuple[bool, str]:
    if not bool(cfg.llm.force_strong_model_for_complex_ask):
        return False, "n/a"
    if str(cmd or "").strip().lower() not in {"ask", "explain"}:
        return False, "n/a"
    if str(execution_mode or "").strip().lower() != "retrieval_plus_llm":
        return False, "n/a"
    intent_norm = str(llm_intent or "").strip().lower()
    if intent_norm not in {"summarize", "explain"}:
        return False, "n/a"
    threshold = max(0, int(cfg.llm.downgrade_min_remaining_requests_ask))
    if remaining_requests is not None and int(remaining_requests) < threshold:
        return False, "n/a"
    route_norm = str(route or "").strip().upper()
    changed_files = github_context.get("changed_files", [])
    changed_count = len(changed_files) if isinstance(changed_files, list) else 0
    high_complexity = int(complexity_score) >= 60
    very_high_complexity = int(complexity_score) >= 75
    strong_pr_context = changed_count >= 3 and route_norm == "FAST"
    if not (high_complexity or route_norm == "DEEP" or strong_pr_context):
        return False, "n/a"
    if remaining_requests is None and not (very_high_complexity or route_norm == "DEEP"):
        return False, "n/a"
    if remaining_requests is None:
        return True, "retained preferred model: complex ask/explain in estimate mode"
    reason = (
        "retained preferred model: complex ask/explain with sufficient remaining quota"
    )
    return True, reason


def _should_retain_preferred_model_for_review(
    *,
    cfg: RepoBrainConfig,
    cmd: str,
    execution_mode: str,
    llm_intent: str,
    route: str,
    complexity_score: int,
    remaining_requests: int | None,
    github_context: dict[str, Any],
    payload_token_est: int,
    payload_token_limit: int,
) -> tuple[bool, str]:
    if str(cmd or "").strip().lower() != "review":
        return False, "n/a"
    if str(execution_mode or "").strip().lower() != "retrieval_plus_llm":
        return False, "n/a"
    intent_norm = str(llm_intent or "").strip().lower()
    if intent_norm not in {"review", "summarize", "explain"}:
        return False, "n/a"

    threshold = max(0, int(cfg.llm.downgrade_min_remaining_requests_review))
    if remaining_requests is not None and int(remaining_requests) < threshold:
        return False, "n/a"

    route_norm = str(route or "").strip().upper()
    changed_files = github_context.get("changed_files", [])
    changed_count = len(changed_files) if isinstance(changed_files, list) else 0
    complexity_gate = int(complexity_score) >= 35 or route_norm == "DEEP" or changed_count >= 2
    if not complexity_gate:
        return False, "n/a"

    payload_limit = max(1, int(payload_token_limit or 1))
    payload_est = max(0, int(payload_token_est or 0))
    payload_compact_enough = payload_est <= max(1, int(payload_limit * 0.92))
    if not payload_compact_enough:
        return False, "n/a"

    if remaining_requests is None:
        if int(complexity_score) < 60 and route_norm != "DEEP":
            return False, "n/a"
        return True, "review synthesis retained strong model in estimate mode with compact payload."

    return True, "review synthesis retained strong model under current quota."


def _normalize_fix_semantics(
    *,
    execution_mode: str,
    llm_intent: str,
    reason_code: str,
    reason_short: str,
) -> tuple[str, str, str]:
    intent = "patch"
    mapped_code = str(reason_code or "").strip().upper() or "PATCH_GROUNDING_REQUIRED"
    mapped_short = str(reason_short or "").strip()

    if mapped_code.startswith("REVIEW_"):
        mapped_code = "PATCH_" + mapped_code[len("REVIEW_") :]
    if mapped_code in {"MULTI_SOURCE_SYNTHESIS_REQUIRED", "COMPLEX_SYNTHESIS_REQUIRED"}:
        mapped_code = "PATCH_SYNTHESIS_REQUIRED"
    if mapped_code == "DEFAULT_RETRIEVAL_ONLY":
        mapped_code = "FIX_CONTEXT_INSUFFICIENT"
    if mapped_code == "DIRECT_EVIDENCE_SUFFICIENT":
        mapped_code = "PATCH_GROUNDING_REQUIRED"

    lowered = mapped_short.lower()
    if "review" in lowered:
        mapped_short = re.sub("review", "patch", mapped_short, flags=re.IGNORECASE)
    if "pr review" in lowered:
        mapped_short = re.sub("pr review", "patch", mapped_short, flags=re.IGNORECASE)

    mode_norm = str(execution_mode or "").strip().lower()
    if mode_norm == "retrieval_plus_llm":
        mapped_short = (
            mapped_short
            or "LLM used: patch synthesis required for grounded fix proposal."
        )
        if mapped_short.lower().startswith("llm not used"):
            mapped_short = "LLM used: patch synthesis required for grounded fix proposal."
        if mapped_code in {"FIX_CONTEXT_INSUFFICIENT", "PATCH_GROUNDING_REQUIRED"}:
            mapped_code = "PATCH_SYNTHESIS_REQUIRED"
    else:
        mapped_short = mapped_short or "LLM not used: fix context insufficient for grounded patch."
        if mapped_code == "PATCH_SYNTHESIS_REQUIRED":
            mapped_code = "FIX_CONTEXT_INSUFFICIENT"

    _ = llm_intent
    return intent, mapped_code, mapped_short


def _alternate_model_id(primary_model: str, *, model_high: str, model_low: str) -> str:
    primary = str(primary_model or "").strip()
    if primary.lower() == model_high.lower():
        return model_low
    if primary.lower() == model_low.lower():
        return model_high
    if "mini" in primary.lower():
        return model_high
    return model_low


def _is_retryable_llm_error(exc: GitHubModelsError) -> bool:
    status_code = int(exc.status_code or 0)
    if status_code in {429, 500, 502, 503, 504}:
        return True
    return exc.reason in {"network", "rate_limited", "server_error"}


def _review_context_needs_batch(
    *,
    cfg: RepoBrainConfig,
    changed_files_count: int,
    diff_hunks_count: int,
    estimated_input_tokens: int,
) -> bool:
    return (
        int(estimated_input_tokens) > int(cfg.llm.max_input_tokens_review_final)
        or int(changed_files_count) > int(cfg.llm.max_files_review_context)
        or int(diff_hunks_count) > int(cfg.llm.max_hunks_review_context)
    )


def _is_fallback_eligible_llm_error(exc: GitHubModelsError) -> bool:
    status_code = int(exc.status_code or 0)
    return exc.reason in {"network", "rate_limited", "server_error", "http_error"} or status_code > 0


def _apply_remaining_fallback(llm_meta: dict[str, Any]) -> None:
    if llm_meta.get("llm_remaining_requests", None) not in {None, "", "n/a"}:
        return
    tier = str(llm_meta.get("llm_tier", "low") or "low").strip().lower()
    daily_limit = 50 if tier == "high" else 150
    calls = int(llm_meta.get("llm_calls_this_run", 0) or 0)
    llm_meta["llm_remaining_requests"] = max(0, daily_limit - calls)
    llm_meta["llm_requests_remaining"] = llm_meta["llm_remaining_requests"]
    llm_meta["llm_remaining_is_estimate"] = True
    llm_meta["llm_usage_estimated"] = True


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _remaining_after_decrement(value: Any, decrement: int = 1) -> int | str:
    if isinstance(value, int):
        return max(0, value - decrement)
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return "n/a"
    return max(0, parsed - decrement)


def _build_model_counts(calls: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in calls:
        model_id = str(item.get("model_id", "") or "").strip()
        if not model_id:
            continue
        counts[model_id] = counts.get(model_id, 0) + 1
    return counts


def _compact_usage_call(
    *,
    batch_id: str,
    model_id: str,
    tier: str,
    tokens_prompt: int,
    tokens_completion: int,
    tokens_total: int,
    remaining_requests: Any,
    remaining_is_estimate: bool,
    reset_time_utc_iso: str | None,
    usage_estimated: bool,
) -> dict[str, Any]:
    return {
        "batch_id": batch_id,
        "model_id": model_id,
        "tier": tier,
        "tokens_prompt": tokens_prompt,
        "tokens_completion": tokens_completion,
        "tokens_total": tokens_total,
        "remaining_requests": remaining_requests,
        "remaining_is_estimate": remaining_is_estimate,
        "reset_time_utc_iso": reset_time_utc_iso,
        "estimate_flags": {
            "usage_estimated": usage_estimated,
            "remaining_estimated": remaining_is_estimate,
        },
    }


def _build_llm_usage_payload(llm_meta: dict[str, Any]) -> dict[str, Any]:
    calls_raw = llm_meta.get("llm_calls", [])
    calls: list[dict[str, Any]] = []
    if isinstance(calls_raw, list):
        for item in calls_raw:
            if isinstance(item, dict):
                calls.append(dict(item))
    if not calls:
        calls = [
            _compact_usage_call(
                batch_id="single",
                model_id=str(llm_meta.get("llm_model_used", "not used") or "not used"),
                tier=str(llm_meta.get("llm_tier", "n/a") or "n/a"),
                tokens_prompt=_int_or_zero(llm_meta.get("llm_tokens_prompt", 0)),
                tokens_completion=_int_or_zero(llm_meta.get("llm_tokens_completion", 0)),
                tokens_total=_int_or_zero(llm_meta.get("llm_tokens_total", 0)),
                remaining_requests=llm_meta.get("llm_remaining_requests", "n/a"),
                remaining_is_estimate=bool(llm_meta.get("llm_remaining_is_estimate", True)),
                reset_time_utc_iso=llm_meta.get("llm_reset_time_utc_iso"),
                usage_estimated=bool(llm_meta.get("llm_usage_estimated", True)),
            )
        ]

    tokens_prompt_total = sum(_int_or_zero(item.get("tokens_prompt", 0)) for item in calls)
    tokens_completion_total = sum(_int_or_zero(item.get("tokens_completion", 0)) for item in calls)
    tokens_total_total = sum(_int_or_zero(item.get("tokens_total", 0)) for item in calls)
    final_call = calls[-1] if calls else {}
    model_counts = _build_model_counts(calls)

    return {
        "date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "llm_used": bool(llm_meta.get("llm_used", False)),
        "execution_mode": str(llm_meta.get("execution_mode", "retrieval_only") or "retrieval_only"),
        "answer_grounding_mode": str(
            llm_meta.get("answer_grounding_mode", "n/a") or "n/a"
        ),
        "pr_changed_files_count": int(llm_meta.get("pr_changed_files_count", 0) or 0),
        "pr_metadata_used": bool(llm_meta.get("pr_metadata_used", False)),
        "llm_intent": str(llm_meta.get("llm_intent", "none") or "none"),
        "llm_decision_reason_short": str(
            llm_meta.get(
                "llm_decision_reason_short",
                "LLM not used: direct answer available from retrieved evidence.",
            )
            or "LLM not used: direct answer available from retrieved evidence."
        ),
        "llm_decision_reason_code": str(
            llm_meta.get("llm_decision_reason_code", "DEFAULT_RETRIEVAL_ONLY")
            or "DEFAULT_RETRIEVAL_ONLY"
        ),
        "llm_runtime_override_reason": str(
            llm_meta.get("llm_runtime_override_reason", "n/a") or "n/a"
        ),
        "policy_event_name": str(llm_meta.get("llm_policy_event_name", "n/a") or "n/a"),
        "policy_is_pr_context": bool(llm_meta.get("llm_policy_is_pr_context", False)),
        "policy_issue_comment_enabled": bool(
            llm_meta.get("llm_policy_issue_comment_enabled", True)
        ),
        "policy_pr_comments_enabled": bool(
            llm_meta.get("llm_policy_pr_comments_enabled", True)
        ),
        "policy_issue_only_enabled": bool(
            llm_meta.get("llm_policy_issue_only_enabled", False)
        ),
        "policy_allowed": bool(llm_meta.get("llm_policy_allowed", True)),
        "skip_reason": str(llm_meta.get("llm_skip_reason", "n/a") or "n/a"),
        "decision_route": str(llm_meta.get("llm_decision_route", "n/a") or "n/a"),
        "budget_action": str(llm_meta.get("llm_budget_action", "n/a") or "n/a"),
        "governor_reason": str(llm_meta.get("llm_governor_reason", "n/a") or "n/a"),
        "model_id": str(llm_meta.get("llm_model_used", "not used")),
        "final_synthesis_model_id": str(
            llm_meta.get("llm_final_synthesis_model_id", llm_meta.get("llm_model_used", "not used"))
            or "not used"
        ),
        "preferred_model_id": str(llm_meta.get("llm_preferred_model_id", "n/a") or "n/a"),
        "model_selection_reason": str(
            llm_meta.get("llm_model_selection_reason", "n/a") or "n/a"
        ),
        "model_downgrade_reason": str(
            llm_meta.get("llm_model_downgrade_reason", "n/a") or "n/a"
        ),
        "retained_preferred_model_reason": str(
            llm_meta.get("llm_retained_preferred_model_reason", "n/a") or "n/a"
        ),
        "downgrade_threshold_used": str(
            llm_meta.get("llm_downgrade_threshold_used", "n/a") or "n/a"
        ),
        "final_synthesis_retained_preferred_model": bool(
            llm_meta.get("llm_final_synthesis_retained_preferred_model", False)
        ),
        "intermediate_downgrade_occurred": bool(
            llm_meta.get("llm_intermediate_downgrade_occurred", False)
        ),
        "intermediate_downgrade_reason": str(
            llm_meta.get("llm_intermediate_downgrade_reason", "n/a") or "n/a"
        ),
        "primary_model_id": str(llm_meta.get("llm_primary_model_id", "not used") or "not used"),
        "effective_model_id": str(llm_meta.get("llm_effective_model_id", "not used") or "not used"),
        "fallback_used": bool(llm_meta.get("llm_fallback_used", False)),
        "tier": str(llm_meta.get("llm_tier", "n/a")),
        "calls_this_run": int(llm_meta.get("llm_calls_this_run", 0) or 0),
        "tokens_prompt": int(llm_meta.get("llm_tokens_prompt", 0) or 0),
        "tokens_completion": int(llm_meta.get("llm_tokens_completion", 0) or 0),
        "tokens_total": int(llm_meta.get("llm_tokens_total", 0) or 0),
        "max_output_tokens_used": int(llm_meta.get("llm_max_output_tokens_used", 0) or 0),
        "input_budget_limit": int(llm_meta.get("llm_input_budget_limit", 0) or 0),
        "input_budget_used_est": int(llm_meta.get("llm_input_budget_used_est", 0) or 0),
        "dropped_locators_count": int(llm_meta.get("llm_dropped_locators_count", 0) or 0),
        "dropped_hunks_count": int(llm_meta.get("llm_dropped_hunks_count", 0) or 0),
        "dropped_snippets_count": int(llm_meta.get("llm_dropped_snippets_count", 0) or 0),
        "remaining_requests": llm_meta.get("llm_remaining_requests", "n/a"),
        "remaining_is_estimate": bool(llm_meta.get("llm_remaining_is_estimate", True)),
        "reset_time_utc_iso": llm_meta.get("llm_reset_time_utc_iso"),
        "provider_http_status": llm_meta.get("llm_provider_http_status"),
        "provider_error_type": str(llm_meta.get("llm_provider_error_type", "n/a") or "n/a"),
        "request_mode": str(llm_meta.get("llm_request_mode", "n/a") or "n/a"),
        "patch_batch_mode": bool(llm_meta.get("llm_patch_batch_mode", False)),
        "patch_batch_count": int(llm_meta.get("llm_patch_batch_count", 0) or 0),
        "compacted": bool(llm_meta.get("llm_compacted", False)),
        "attempted_compaction": bool(llm_meta.get("llm_attempted_compaction", False)),
        "attempted_patch_batch": bool(llm_meta.get("llm_attempted_patch_batch", False)),
        "calls": calls,
        "totals": {
            "calls_count": len(calls),
            "tokens_prompt_total": tokens_prompt_total,
            "tokens_completion_total": tokens_completion_total,
            "tokens_total_total": tokens_total_total,
        },
        "model_counts": model_counts,
        "final_remaining_requests": final_call.get("remaining_requests", "n/a"),
        "final_reset_time_utc_iso": final_call.get("reset_time_utc_iso"),
        "estimate_flags": {
            "usage_estimated": bool(llm_meta.get("llm_usage_estimated", True)),
            "remaining_estimated": bool(llm_meta.get("llm_remaining_is_estimate", True)),
        },
        "ratelimit_headers_subset": dict(llm_meta.get("llm_ratelimit_headers", {})),
    }


def _write_verification_report(repo_root: Path, report: dict[str, Any]) -> Path:
    path = repo_root / "artifacts" / "verification_report.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_check_run_payload(repo_root: Path, payload: dict[str, Any]) -> Path:
    path = repo_root / "artifacts" / "check_run_payload.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_llm_usage(repo_root: Path, payload: dict[str, Any]) -> Path:
    path = repo_root / "artifacts" / "llm_usage.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _embeddings_enabled() -> bool:
    return bool(_runtime_env_cfg().embeddings.enabled)


def _embeddings_model() -> str:
    value = str(_runtime_env_cfg().embeddings.model or "").strip()
    return value or "openai/text-embedding-3-small"


def _default_embeddings_meta(reason: str) -> dict[str, Any]:
    return {
        "embed_used": False,
        "embed_reason": reason,
        "embed_model_id": _embeddings_model(),
        "embed_budget_action": "n/a",
        "embed_governor_reason": "n/a",
        "embed_tokens_prompt": 0,
        "embed_tokens_total": 0,
        "embed_usage_estimated": True,
        "embed_remaining_requests": "n/a",
        "embed_remaining_is_estimate": True,
        "embed_reset_time_utc_iso": None,
        "embed_chunks_embedded": 0,
        "embed_query_embedded": False,
        "embed_calls": [],
        "embed_calls_count": 0,
    }


def _build_embeddings_usage_payload(meta: dict[str, Any]) -> dict[str, Any]:
    calls_raw = meta.get("embed_calls", [])
    calls = [dict(item) for item in calls_raw if isinstance(item, dict)] if isinstance(calls_raw, list) else []
    prompt_total = sum(_int_or_zero(item.get("tokens_prompt", 0)) for item in calls)
    total_tokens = sum(_int_or_zero(item.get("tokens_total", 0)) for item in calls)
    last = calls[-1] if calls else {}
    return {
        "date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "embed_used": bool(meta.get("embed_used", False)),
        "reason": str(meta.get("embed_reason", "n/a") or "n/a"),
        "budget_action": str(meta.get("embed_budget_action", "n/a") or "n/a"),
        "governor_reason": str(meta.get("embed_governor_reason", "n/a") or "n/a"),
        "model_id": str(meta.get("embed_model_id", _embeddings_model())),
        "calls": calls,
        "totals": {
            "calls_count": len(calls),
            "tokens_prompt_total": prompt_total,
            "tokens_total_total": total_tokens,
        },
        "remaining_requests": meta.get("embed_remaining_requests", last.get("remaining_requests", "n/a")),
        "remaining_is_estimate": bool(
            meta.get("embed_remaining_is_estimate", last.get("remaining_is_estimate", True))
        ),
        "reset_time_utc_iso": meta.get("embed_reset_time_utc_iso", last.get("reset_time_utc_iso")),
        "chunks_embedded": int(meta.get("embed_chunks_embedded", 0) or 0),
        "query_embedded": bool(meta.get("embed_query_embedded", False)),
    }


def _write_embeddings_usage(repo_root: Path, payload: dict[str, Any]) -> Path:
    path = repo_root / "artifacts" / "embeddings_usage.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _index_zip_has_embeddings(index_path: Path) -> bool:
    if not index_path.exists():
        return False
    try:
        with zipfile.ZipFile(index_path, mode="r") as zf:
            return "index/embeddings.jsonl" in set(zf.namelist())
    except (OSError, zipfile.BadZipFile):
        return False


def _build_embeddings_runtime_truth(
    *,
    embeddings_enabled: bool,
    vectors_meta: dict[str, Any],
    embeddings_meta: dict[str, Any],
    retrieval_runtime: dict[str, Any] | None = None,
) -> dict[str, Any]:
    retrieval = dict(retrieval_runtime or {})
    chunks_with_vectors = int(
        retrieval.get(
            "chunks_with_vectors",
            vectors_meta.get("chunks_embedded", embeddings_meta.get("embed_chunks_embedded", 0)),
        )
        or 0
    )
    query_embedded = bool(retrieval.get("query_embedded", embeddings_meta.get("embed_query_embedded", False)))
    index_vectors_loaded = bool(retrieval.get("index_vectors_loaded", chunks_with_vectors > 0))
    index_vectors_used = bool(retrieval.get("index_vectors_used", False))
    embedding_model = str(
        retrieval.get("embedding_model")
        or embeddings_meta.get("embed_model_id")
        or vectors_meta.get("model")
        or "n/a"
    )
    reason = str(
        retrieval.get("evidence_reason")
        or embeddings_meta.get("embed_reason")
        or vectors_meta.get("reason")
        or "n/a"
    )
    status = str(vectors_meta.get("status", "UNKNOWN") or "UNKNOWN").upper()

    if not embeddings_enabled:
        status = "DISABLED"
        reason = "embeddings_disabled"
    elif query_embedded and index_vectors_loaded and index_vectors_used:
        status = "OK"
        reason = "index_vectors_used_for_hybrid_scoring"
    elif query_embedded and not index_vectors_loaded:
        status = "PARTIAL"
        reason = "query_embedded_but_no_index_vectors"
    elif query_embedded and index_vectors_loaded and not index_vectors_used:
        status = "PARTIAL"
        reason = "query_embedded_but_index_vectors_not_used"
    elif str(embeddings_meta.get("embed_reason", "")).startswith("embed_error:"):
        status = "UNKNOWN"
        reason = "query_embedding_error"
    elif status not in {"OK", "PARTIAL", "DISABLED", "UNKNOWN"}:
        status = "UNKNOWN"
        reason = "invalid_index_embeddings_status"
    elif reason == "n/a":
        if index_vectors_loaded:
            reason = "query_embedding_not_available"
        else:
            reason = "index_vectors_not_loaded"

    return {
        "query_embedded": query_embedded,
        "index_vectors_loaded": index_vectors_loaded,
        "index_vectors_used": index_vectors_used,
        "chunks_with_vectors": chunks_with_vectors,
        "embedding_model": embedding_model,
        "evidence_reason": reason,
        "status": status,
    }


def _build_index_embeddings_evidence_payload(
    *,
    index_path: Path,
    vectors_meta: dict[str, Any],
    embeddings_meta: dict[str, Any],
    index_vectors_used: bool,
    embeddings_runtime: dict[str, Any] | None = None,
) -> dict[str, Any]:
    runtime_truth = _build_embeddings_runtime_truth(
        embeddings_enabled=bool(_embeddings_enabled()),
        vectors_meta=vectors_meta,
        embeddings_meta=embeddings_meta,
        retrieval_runtime=embeddings_runtime,
    )
    status = str(runtime_truth.get("status", "UNKNOWN") or "UNKNOWN").upper()
    reason = str(runtime_truth.get("evidence_reason", "n/a") or "n/a")
    model = str(runtime_truth.get("embedding_model", "n/a") or "n/a")
    chunks = int(runtime_truth.get("chunks_with_vectors", 0) or 0)
    query_embedded = bool(runtime_truth.get("query_embedded", False))
    vectors_available = bool(runtime_truth.get("index_vectors_loaded", False))
    vectors_used = bool(runtime_truth.get("index_vectors_used", False) or index_vectors_used)

    if vectors_used:
        status = "OK"
        reason = "index_vectors_used_for_hybrid_scoring"
    elif query_embedded and not vectors_available:
        status = "PARTIAL"
        reason = "query_embedded_but_no_index_vectors"
    elif query_embedded and vectors_available and status == "DISABLED":
        status = "PARTIAL"
        reason = "query_embedded_but_index_vectors_not_used"

    file_present = _index_zip_has_embeddings(index_path)
    return {
        "status": status,
        "reason": reason,
        "query_embedded": query_embedded,
        "index_vectors_loaded": vectors_available,
        "index_vectors_used": vectors_used,
        "embeddings_file_present_in_zip": file_present,
        "model": model,
        "chunks_with_vectors": chunks,
        # Backward-compatible keys used by existing harness/tests.
        "index_has_embeddings_file": file_present,
        "index_embeddings_status": status,
        "index_embeddings_reason": reason,
        "index_embeddings_model": model,
        "index_embeddings_chunks": chunks,
    }


def _write_index_embeddings_evidence(repo_root: Path, payload: dict[str, Any]) -> Path:
    path = repo_root / "artifacts" / "index_embeddings_evidence.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_patch_generation_debug(repo_root: Path, payload: dict[str, Any]) -> Path:
    path = repo_root / "artifacts" / "patch_generation_debug.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_review_validation(repo_root: Path, payload: dict[str, Any]) -> Path:
    path = repo_root / "artifacts" / "review_validation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_review_generation_debug(repo_root: Path, payload: dict[str, Any]) -> Path:
    path = repo_root / "artifacts" / "review_generation_debug.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_patch_validation(repo_root: Path, payload: dict[str, Any]) -> Path:
    path = repo_root / "artifacts" / "patch_validation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_llm_http_debug(repo_root: Path, payload: dict[str, Any]) -> Path:
    path = repo_root / "artifacts" / "llm_http_debug.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _build_llm_http_debug_payload(*, llm_meta: dict[str, Any], decision_route: str) -> dict[str, Any]:
    return {
        "intent": "patch",
        "request_mode": str(llm_meta.get("llm_request_mode", "patch") or "patch"),
        "primary_model": str(llm_meta.get("llm_primary_model_id", "n/a") or "n/a"),
        "fallback_model": (
            str(llm_meta.get("llm_effective_model_id", "n/a") or "n/a")
            if bool(llm_meta.get("llm_fallback_used", False))
            else "n/a"
        ),
        "primary_status": llm_meta.get("llm_primary_status"),
        "fallback_status": llm_meta.get("llm_fallback_status"),
        "provider_http_status": llm_meta.get("llm_provider_http_status"),
        "provider_error_type": str(llm_meta.get("llm_provider_error_type", "n/a") or "n/a"),
        "error_types": list(llm_meta.get("llm_error_types", []))
        if isinstance(llm_meta.get("llm_error_types", []), list)
        else [],
        "decision_route": str(decision_route or "n/a"),
        "execution_mode": str(llm_meta.get("execution_mode", "retrieval_only") or "retrieval_only"),
        "llm_intent": str(llm_meta.get("llm_intent", "none") or "none"),
        "llm_decision_reason_short": str(
            llm_meta.get(
                "llm_decision_reason_short",
                "LLM not used: direct answer available from retrieved evidence.",
            )
            or "LLM not used: direct answer available from retrieved evidence."
        ),
        "llm_decision_reason_code": str(
            llm_meta.get("llm_decision_reason_code", "DEFAULT_RETRIEVAL_ONLY")
            or "DEFAULT_RETRIEVAL_ONLY"
        ),
        "llm_runtime_override_reason": str(
            llm_meta.get("llm_runtime_override_reason", "n/a") or "n/a"
        ),
        "llm_skip_reason": str(llm_meta.get("llm_skip_reason", "n/a") or "n/a"),
        "policy_event_name": str(llm_meta.get("llm_policy_event_name", "n/a") or "n/a"),
        "policy_allowed": bool(llm_meta.get("llm_policy_allowed", True)),
        "estimated_input_tokens": int(llm_meta.get("llm_input_budget_used_est", 0) or 0),
        "max_output_tokens_used": int(llm_meta.get("llm_max_output_tokens_used", 0) or 0),
        "patch_batch_mode": bool(llm_meta.get("llm_patch_batch_mode", False)),
        "patch_batch_count": int(llm_meta.get("llm_patch_batch_count", 0) or 0),
        "compacted": bool(llm_meta.get("llm_compacted", False)),
        "dropped_locators_count": int(llm_meta.get("llm_dropped_locators_count", 0) or 0),
        "dropped_hunks_count": int(llm_meta.get("llm_dropped_hunks_count", 0) or 0),
        "dropped_snippets_count": int(llm_meta.get("llm_dropped_snippets_count", 0) or 0),
        "attempted_compaction": bool(llm_meta.get("llm_attempted_compaction", False)),
        "attempted_patch_batch": bool(llm_meta.get("llm_attempted_patch_batch", False)),
    }


def _build_ai_quota_snapshot_payload(
    *,
    audit: dict[str, Any],
    governor: AIBudgetGovernor | None,
) -> dict[str, Any]:
    llm_payload = audit.get("llm_usage_payload", {})
    llm_usage = dict(llm_payload) if isinstance(llm_payload, dict) else {}
    embed_payload = audit.get("embeddings_usage_payload", {})
    embed_usage = dict(embed_payload) if isinstance(embed_payload, dict) else {}

    llm_totals = llm_usage.get("totals", {})
    llm_totals = dict(llm_totals) if isinstance(llm_totals, dict) else {}
    embed_totals = embed_usage.get("totals", {})
    embed_totals = dict(embed_totals) if isinstance(embed_totals, dict) else {}

    llm_model_counts = llm_usage.get("model_counts", {})
    llm_model_counts = dict(llm_model_counts) if isinstance(llm_model_counts, dict) else {}

    governor_summary = governor.summary() if governor is not None else {
        "policy": {},
        "decisions_log_summary": {"decisions_total": 0, "reason_counts": {}, "budget_action_counts": {}},
        "final_state": {},
    }

    return {
        "run_id": str(audit.get("run_id", "")),
        "date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "llm": {
            "calls_count": int(llm_totals.get("calls_count", 0) or 0),
            "tokens_total": int(llm_totals.get("tokens_total_total", 0) or 0),
            "execution_mode": str(llm_usage.get("execution_mode", "retrieval_only") or "retrieval_only"),
            "llm_intent": str(llm_usage.get("llm_intent", "none") or "none"),
            "llm_decision_reason_short": str(
                llm_usage.get(
                    "llm_decision_reason_short",
                    "LLM not used: direct answer available from retrieved evidence.",
                )
                or "LLM not used: direct answer available from retrieved evidence."
            ),
            "llm_runtime_override_reason": str(
                llm_usage.get("llm_runtime_override_reason", "n/a") or "n/a"
            ),
            "policy_event_name": str(llm_usage.get("policy_event_name", "n/a") or "n/a"),
            "policy_allowed": bool(llm_usage.get("policy_allowed", True)),
            "last_remaining": llm_usage.get(
                "final_remaining_requests",
                llm_usage.get("remaining_requests", "n/a"),
            ),
            "last_reset_iso": llm_usage.get(
                "final_reset_time_utc_iso",
                llm_usage.get("reset_time_utc_iso"),
            ),
            "estimate_flags": dict(llm_usage.get("estimate_flags", {})),
            "model_counts": llm_model_counts,
        },
        "embeddings": {
            "calls_count": int(embed_totals.get("calls_count", 0) or 0),
            "tokens_total": int(embed_totals.get("tokens_total_total", 0) or 0),
            "last_remaining": embed_usage.get("remaining_requests", "n/a"),
            "last_reset_iso": embed_usage.get("reset_time_utc_iso"),
            "estimate_flags": {
                "usage_estimated": bool(embed_usage.get("remaining_is_estimate", True)),
                "remaining_estimated": bool(embed_usage.get("remaining_is_estimate", True)),
            },
            "chunks_embedded": int(embed_usage.get("chunks_embedded", 0) or 0),
            "query_embedded": bool(embed_usage.get("query_embedded", False)),
        },
        "governor": governor_summary,
    }


def _write_ai_quota_snapshot(repo_root: Path, payload: dict[str, Any]) -> Path:
    path = repo_root / "artifacts" / "ai_quota_snapshot.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _build_config_snapshot_payload(cfg: RepoBrainConfig) -> dict[str, Any]:
    return {
        "date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "config": cfg.usersafe_dict(),
        "warnings": list(cfg.warnings),
        "feature_summary": {
            "tkya_backend": str(cfg.tkya.backend or "lite"),
            "llm_enabled": bool(cfg.llm.enabled),
            "embeddings_enabled": bool(cfg.embeddings.enabled),
            "batch_enabled": bool(cfg.batch.enabled),
            "checks_enabled": True,
            "apply_patch": bool(cfg.workflow.apply_patch),
            "create_pr": bool(cfg.workflow.create_pr),
        },
    }


def _write_config_snapshot(repo_root: Path, payload: dict[str, Any]) -> Path:
    path = repo_root / "artifacts" / "config_snapshot.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _finalize_run(
    *,
    repo_root: Path,
    audit: dict[str, Any],
    governor: AIBudgetGovernor | None,
) -> None:
    llm_usage_payload_raw = audit.get("llm_usage_payload", {})
    if isinstance(llm_usage_payload_raw, dict) and llm_usage_payload_raw:
        llm_path = _write_llm_usage(repo_root, llm_usage_payload_raw)
        audit["llm_usage_artifact"] = llm_path.as_posix()

    embeddings_usage_payload_raw = audit.get("embeddings_usage_payload", {})
    if isinstance(embeddings_usage_payload_raw, dict) and embeddings_usage_payload_raw:
        embed_path = _write_embeddings_usage(repo_root, embeddings_usage_payload_raw)
        audit["embeddings_usage_artifact"] = embed_path.as_posix()

    snapshot = _build_ai_quota_snapshot_payload(audit=audit, governor=governor)
    snapshot_path = _write_ai_quota_snapshot(repo_root, snapshot)
    audit["ai_quota_snapshot_artifact"] = snapshot_path.as_posix()
    audit["ai_governor"] = snapshot.get("governor", {})
    env_cfg = _runtime_env_cfg()
    config_snapshot = _build_config_snapshot_payload(env_cfg)
    config_snapshot_path = _write_config_snapshot(repo_root, config_snapshot)
    audit["config_snapshot_artifact"] = config_snapshot_path.as_posix()
    _set_last_audit(audit)
    _set_runtime_env_cfg(None)


def _maybe_embed_query(
    *,
    question: str,
    chunks_embedded_count: int,
    governor: AIBudgetGovernor | None = None,
) -> tuple[list[float] | None, dict[str, Any]]:
    if not _embeddings_enabled():
        meta = _default_embeddings_meta("disabled")
        meta["embed_chunks_embedded"] = chunks_embedded_count
        return None, meta
    token = str(_runtime_env_cfg().workflow.github_token or "").strip()
    if not token:
        token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        meta = _default_embeddings_meta("missing_github_token")
        meta["embed_chunks_embedded"] = chunks_embedded_count
        return None, meta
    client = GitHubModelsEmbeddingsClient(token=token)
    model_id = _embeddings_model()
    if governor is not None:
        next_cost_est = max(1, int(len(question or "") / 4))
        decision = governor.can_call_embed(next_call_cost_est=next_cost_est)
        if not decision.allow or decision.disable_embeddings:
            meta = _default_embeddings_meta(f"budget:{decision.reason}")
            meta["embed_budget_action"] = decision.budget_action
            meta["embed_governor_reason"] = decision.reason
            meta["embed_chunks_embedded"] = chunks_embedded_count
            meta["embed_model_id"] = model_id
            return None, meta
    try:
        response = client.embed(model_id=model_id, inputs=[question])
    except GitHubModelsEmbeddingsError as exc:
        meta = _default_embeddings_meta(f"embed_error:{exc.reason}")
        meta["embed_chunks_embedded"] = chunks_embedded_count
        meta["embed_model_id"] = model_id
        return None, meta
    if not response.vectors:
        meta = _default_embeddings_meta("query_vector_missing")
        meta["embed_chunks_embedded"] = chunks_embedded_count
        meta["embed_model_id"] = model_id
        return None, meta
    vector = response.vectors[0]
    call = {
        "batch_id": "query",
        "model_id": model_id,
        "tokens_prompt": response.prompt_tokens,
        "tokens_total": response.total_tokens,
        "remaining_requests": response.remaining_requests,
        "remaining_is_estimate": response.remaining_is_estimate,
        "reset_time_utc_iso": response.reset_time_utc_iso,
        "estimate_flags": {
            "usage_estimated": response.usage_estimated,
            "remaining_estimated": response.remaining_is_estimate,
        },
    }
    meta = {
        "embed_used": True,
        "embed_reason": "ok",
        "embed_model_id": model_id,
        "embed_budget_action": "n/a",
        "embed_governor_reason": "n/a",
        "embed_tokens_prompt": response.prompt_tokens,
        "embed_tokens_total": response.total_tokens,
        "embed_usage_estimated": response.usage_estimated,
        "embed_remaining_requests": response.remaining_requests,
        "embed_remaining_is_estimate": response.remaining_is_estimate,
        "embed_reset_time_utc_iso": response.reset_time_utc_iso,
        "embed_chunks_embedded": chunks_embedded_count,
        "embed_query_embedded": True,
        "embed_calls": [call],
        "embed_calls_count": 1,
    }
    if governor is not None:
        governor.observe_embed_signal(
            QuotaSignal(
                remaining_requests=response.remaining_requests,
                reset_time_utc_iso=response.reset_time_utc_iso,
                remaining_is_estimate=response.remaining_is_estimate,
                usage_estimated=response.usage_estimated,
                ratelimit_headers=dict(response.ratelimit_headers),
            ),
            {"tokens_total": response.total_tokens},
        )
    return [float(item) for item in vector], meta

def _write_batch_summaries(repo_root: Path, payload: dict[str, Any]) -> Path:
    path = repo_root / "artifacts" / "batch_summaries.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_patch_part(repo_root: Path, batch_id: str, patch_text: str) -> Path:
    folder = repo_root / "artifacts" / "patch_parts"
    folder.mkdir(parents=True, exist_ok=True)
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]", "_", batch_id)[:80] or "part"
    path = folder / f"{safe_id}.diff"
    path.write_text(patch_text, encoding="utf-8")
    return path


def _verification_context_from_report(report: dict[str, Any]) -> dict[str, Any]:
    checks_raw = report.get("checks", [])
    checks: list[dict[str, str]] = []
    if isinstance(checks_raw, list):
        for item in checks_raw:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            status = str(item.get("status", "NOT_RUN")).strip().upper()
            if not name:
                continue
            if status == "PASS":
                state = "PASS"
            elif status == "FAIL":
                state = "FAIL"
            else:
                state = "NOT_RUN"
            checks.append({"name": name, "state": state})
    return {
        "checks": checks,
        "required_checks": [item["name"] for item in checks],
        "trusted_context": bool(report.get("trusted_context", False)),
        "dynamic_allowed": bool(report.get("dynamic_allowed", False)),
        "summary": str(report.get("summary", "")),
    }


def _build_check_annotations_from_candidates(
    candidates: list[CandidateChunk],
    *,
    route: str,
    verification_report: dict[str, Any],
) -> list[dict[str, Any]]:
    checks_raw = verification_report.get("checks", [])
    checks = checks_raw if isinstance(checks_raw, list) else []
    has_fail = any(
        isinstance(item, dict) and str(item.get("status", "")).upper() == "FAIL"
        for item in checks
    )
    normalized_route = str(route or "").strip().upper()
    if normalized_route in {"BLOCK"} or has_fail:
        level = "failure"
        message = "RepoBrain detected a high-risk locator."
    elif normalized_route in {"WAIT", "REFUSE", "DEEP"}:
        level = "warning"
        message = "RepoBrain highlighted this locator for additional verification."
    else:
        level = "notice"
        message = "RepoBrain selected this locator."

    annotations: list[dict[str, Any]] = []
    for item in candidates:
        annotations.append(
            {
                "path": item.file_path,
                "start_line": item.line_start,
                "end_line": item.line_end,
                "annotation_level": level,
                "message": message,
                "title": "RepoBrain",
            }
        )
    return annotations


def _build_check_annotations_from_evidence(
    evidence: list[EvidenceItem],
    *,
    route: str,
) -> list[dict[str, Any]]:
    normalized_route = str(route or "").strip().upper()
    if normalized_route in {"REFUSE", "BLOCK"}:
        level = "failure"
        message = "RepoBrain flagged this locator as high-risk."
    elif normalized_route in {"WAIT", "DEEP"}:
        level = "warning"
        message = "RepoBrain suggests verifying this locator."
    else:
        level = "notice"
        message = "RepoBrain used this locator."
    out: list[dict[str, Any]] = []
    for item in evidence:
        out.append(
            {
                "path": item.file_path,
                "start_line": item.line_start,
                "end_line": item.line_end,
                "annotation_level": level,
                "message": message,
                "title": "RepoBrain",
            }
        )
    return out


def _run_review_verification(
    *,
    repo_root: Path,
    cmd: str,
) -> dict[str, Any]:
    cfg = _runtime_env_cfg()
    trusted = bool(cfg.workflow.trusted_context)
    allow_dynamic = bool(cfg.workflow.allow_dynamic_verify)
    time_budget_s = int(cfg.workflow.verify_time_budget_s)
    caps = detect_capabilities(repo_root)
    plan: list[str] = ["ruff"]
    if cmd == "fix":
        plan.append("pytest")
    else:
        plan.append("pytest")
    report = run_verification(
        plan=plan,
        caps=caps,
        budgets=VerificationBudgets(time_budget_s=time_budget_s, output_tail_lines=30),
        repo_root=repo_root,
        trusted=trusted,
        allow_dynamic=allow_dynamic,
    )
    return report.to_dict()


def _maybe_generate_llm_text(
    *,
    cmd: str,
    intent: str,
    query: str,
    route: str,
    execution_mode: str | None = None,
    llm_intent_decision: str | None = None,
    llm_decision_reason_short: str | None = None,
    llm_decision_reason_code: str | None = None,
    github_context: dict[str, Any],
    locators: list[EvidenceItem],
    candidates_count: int,
    selected_snippets: list[str] | None = None,
    preferred_model_id: str | None = None,
    preferred_tier: str | None = None,
    prebuilt_messages: list[dict[str, str]] | None = None,
    prebuilt_budget_stats: dict[str, Any] | None = None,
    governor: AIBudgetGovernor | None = None,
) -> tuple[str | None, dict[str, Any]]:
    normalized_route = str(route or "").strip().upper()
    legacy_semantic_default = (
        execution_mode is None
        and llm_intent_decision is None
        and llm_decision_reason_short is None
        and llm_decision_reason_code is None
    )
    legacy_route_block_reason = ""
    if legacy_semantic_default:
        if normalized_route == "WAIT":
            execution_mode = "verification_first"
            llm_intent_decision = "none"
            llm_decision_reason_short = "LLM not used: verification required before answer."
            llm_decision_reason_code = "route_wait"
            legacy_route_block_reason = "route=WAIT"
        elif normalized_route in {"REFUSE", "BLOCK"}:
            execution_mode = "refuse"
            llm_intent_decision = "none"
            llm_decision_reason_short = "LLM not used: request refused by security policy."
            llm_decision_reason_code = "route_refuse" if normalized_route == "REFUSE" else "route_block"
            legacy_route_block_reason = f"route={normalized_route}"
        else:
            # Backward compatibility for direct helper callers/tests: non-blocking routes
            # default to legacy "try LLM" behavior unless explicit semantic mode was provided.
            execution_mode = "retrieval_plus_llm"

    semantic = coerce_execution_decision(
        route=normalized_route or "FAST",
        execution_mode=execution_mode,
        llm_intent=llm_intent_decision,
        reason_short=llm_decision_reason_short,
        reason_code=llm_decision_reason_code,
    )
    normalized_execution_mode = semantic.execution_mode
    normalized_llm_intent = semantic.llm_intent
    decision_reason_short = semantic.reason_short
    decision_reason_code = semantic.reason_code

    if normalized_execution_mode != "retrieval_plus_llm":
        skip_reason = f"execution_mode={normalized_execution_mode}"
        if legacy_route_block_reason:
            skip_reason = legacy_route_block_reason
        llm_meta = _llm_default_meta(
            skip_reason,
            execution_mode=normalized_execution_mode,
            llm_intent=normalized_llm_intent,
            llm_decision_reason_short=decision_reason_short,
            llm_decision_reason_code=decision_reason_code,
        )
        llm_meta["llm_decision_route"] = normalized_route
        _apply_remaining_fallback(llm_meta)
        llm_meta["llm_remaining_is_estimate"] = True
        return None, _attach_llm_policy_fields(
            llm_meta,
            github_context=github_context,
            allowed=False,
        )

    if cmd == "locate" and not _env_true("RB_LLM_ALLOW_LOCATE", default=False):
        llm_meta = _llm_default_meta(
            "locate_disabled",
            execution_mode=normalized_execution_mode,
            llm_intent=normalized_llm_intent,
            llm_decision_reason_short=decision_reason_short,
            llm_decision_reason_code=decision_reason_code,
        )
        llm_meta["llm_decision_route"] = normalized_route or "n/a"
        _apply_remaining_fallback(llm_meta)
        llm_meta["llm_remaining_is_estimate"] = True
        return None, _attach_llm_policy_fields(
            llm_meta,
            github_context=github_context,
            allowed=False,
        )

    llm_meta = _llm_default_meta(
        "disabled",
        execution_mode=normalized_execution_mode,
        llm_intent=normalized_llm_intent,
        llm_decision_reason_short=decision_reason_short,
        llm_decision_reason_code=decision_reason_code,
    )
    llm_meta["llm_decision_route"] = normalized_route or "n/a"
    llm_allowed_by_policy, llm_policy_reason = _llm_runtime_policy(github_context)
    if not llm_allowed_by_policy:
        _apply_remaining_fallback(llm_meta)
        llm_meta["llm_remaining_is_estimate"] = True
        llm_meta["llm_skip_reason"] = str(llm_policy_reason or "disabled")
        llm_meta["llm_reason"] = str(llm_policy_reason or "disabled")
        return None, _attach_llm_policy_fields(
            llm_meta,
            github_context=github_context,
            allowed=False,
        )

    token = str(_runtime_env_cfg().workflow.github_token or "").strip()
    if not token:
        token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        llm_meta = _llm_default_meta(
            "missing_github_token",
            execution_mode=normalized_execution_mode,
            llm_intent=normalized_llm_intent,
            llm_decision_reason_short=decision_reason_short,
            llm_decision_reason_code=decision_reason_code,
        )
        llm_meta["llm_decision_route"] = normalized_route or "n/a"
        _apply_remaining_fallback(llm_meta)
        llm_meta["llm_remaining_is_estimate"] = True
        return None, _attach_llm_policy_fields(
            llm_meta,
            github_context=github_context,
            allowed=False,
        )

    cfg = _runtime_env_cfg()
    effective_intent = normalized_llm_intent if normalized_llm_intent != "none" else intent
    is_patch_request = _is_fix_intent(cmd, effective_intent)
    if is_patch_request:
        max_input_tokens = int(cfg.llm.max_input_tokens_patch)
    elif cmd == "review":
        max_input_tokens = int(cfg.llm.max_input_tokens_review_final)
    else:
        max_input_tokens = int(cfg.llm.max_input_tokens)
    model_high = str(cfg.llm.model_high or "openai/gpt-4.1")
    model_low = str(cfg.llm.model_low or "openai/gpt-4.1-mini")

    complexity_limits = {"query_length": len(query or "")}
    complexity_score = score_complexity(
        task_type=cmd,
        intent=effective_intent,
        route=normalized_route,
        github_context=github_context,
        candidates=[None] * max(0, int(candidates_count)),
        limits=complexity_limits,
    )
    changed_files_raw = github_context.get("changed_files", [])
    changed_files = [str(item) for item in changed_files_raw if str(item).strip()] if isinstance(changed_files_raw, list) else []
    diff_hunks_raw = github_context.get("diff_hunks", [])
    diff_hunks = [str(item) for item in diff_hunks_raw if str(item).strip()] if isinstance(diff_hunks_raw, list) else []
    synthesis_required = (
        normalized_route == "DEEP"
        or len(changed_files) >= 2
        or len(locators) >= 3
        or normalized_llm_intent in {"review", "patch", "explain"}
    )
    model_id, tier = choose_model(
        complexity_score,
        model_high=model_high,
        model_low=model_low,
        task_type=cmd,
        intent=effective_intent,
        route=normalized_route,
        execution_mode=normalized_execution_mode,
        llm_intent=normalized_llm_intent,
        synthesis_required=synthesis_required,
    )
    selection_reason = model_selection_reason(
        score=complexity_score,
        task_type=cmd,
        intent=effective_intent,
        route=normalized_route,
        execution_mode=normalized_execution_mode,
        llm_intent=normalized_llm_intent,
        synthesis_required=synthesis_required,
    )
    if preferred_model_id:
        model_id = preferred_model_id.strip() or model_id
        if preferred_tier:
            tier = preferred_tier
        else:
            tier = "low" if "mini" in model_id.lower() else "high"
        selection_reason = "complexity_policy: preferred model override for orchestrated call"
    preferred_model_id_resolved = model_id
    model_downgrade_reason = "n/a"
    max_output_tokens = compute_output_token_budget(
        task_type=cmd,
        intent=effective_intent,
        complexity_score=complexity_score,
        cfg=cfg,
    )
    explanation = complexity_explanation(
        task_type=cmd,
        intent=effective_intent,
        route=normalized_route,
        changed_files_count=len(github_context.get("changed_files", []))
        if isinstance(github_context.get("changed_files", []), list)
        else 0,
        candidates_count=max(0, int(candidates_count)),
        query_length=len(query or ""),
        score=complexity_score,
    )

    if prebuilt_messages is not None:
        messages = list(prebuilt_messages)
        budgeting_stats = dict(prebuilt_budget_stats or {})
    else:
        budgeting_stats: dict[str, Any]
        if is_patch_request:
            messages, budgeting_stats = build_messages_for_fix(
                query=query,
                changed_files=changed_files,
                diff_hunks=diff_hunks,
                max_input_tokens=max_input_tokens,
                selected_snippets=selected_snippets,
                max_hunks=int(cfg.batch.patch_max_hunks_per_call),
            )
        elif cmd == "review":
            messages, budgeting_stats = build_messages_for_review(
                query=query,
                changed_files=changed_files,
                diff_hunks=diff_hunks,
                max_input_tokens=max_input_tokens,
                selected_snippets=selected_snippets,
                max_files_context=int(cfg.llm.max_files_review_context),
                max_findings_context=int(cfg.llm.max_findings_review_context),
                max_hunks_context=int(cfg.llm.max_hunks_review_context),
            )
        else:
            messages, budgeting_stats = build_messages_for_ask(
                query=query,
                locators=locators,
                pr_changed_files=changed_files,
                max_input_tokens=max_input_tokens,
                selected_snippets=selected_snippets,
            )

    prompt_cost_est = int(budgeting_stats.get("input_budget_used_est", estimate_tokens(query)))
    next_call_cost_est = max(1, prompt_cost_est + int(max_output_tokens))
    governor_action = "n/a"
    governor_reason = "n/a"
    retained_preferred_model = False
    if governor is not None:
        decision = governor.can_call_llm(
            next_call_cost_est=next_call_cost_est,
            tier=tier,
            intent=effective_intent,
        )
        governor_action = decision.budget_action
        governor_reason = decision.reason
        if not decision.allow:
            llm_meta = _llm_default_meta(
                f"budget:{decision.reason}",
                execution_mode=normalized_execution_mode,
                llm_intent=normalized_llm_intent,
                llm_decision_reason_short=decision_reason_short,
                llm_decision_reason_code=decision_reason_code,
            )
            llm_meta["llm_decision_route"] = normalized_route or "n/a"
            llm_meta["llm_model_used"] = "not used"
            llm_meta["llm_final_synthesis_model_id"] = "not used"
            llm_meta["llm_preferred_model_id"] = preferred_model_id_resolved
            llm_meta["llm_model_selection_reason"] = selection_reason
            llm_meta["llm_model_downgrade_reason"] = model_downgrade_reason
            llm_meta["llm_retained_preferred_model_reason"] = "n/a"
            llm_meta["llm_downgrade_threshold_used"] = str(
                _llm_downgrade_threshold_for_command(cfg, cmd, effective_intent)
            )
            llm_meta["llm_effective_model_id"] = model_id
            llm_meta["llm_tier"] = tier
            llm_meta["llm_budget_action"] = decision.budget_action
            llm_meta["llm_governor_reason"] = decision.reason
            llm_meta["llm_complexity_score"] = complexity_score
            llm_meta["llm_complexity_explanation"] = explanation
            llm_meta["llm_calls_this_run"] = 0
            llm_meta["llm_max_output_tokens_used"] = max_output_tokens
            llm_meta["llm_request_mode"] = "patch" if is_patch_request else "normal"
            llm_meta["llm_patch_batch_mode"] = False
            llm_meta["llm_patch_batch_count"] = 0
            llm_meta["llm_compacted"] = bool(is_patch_request)
            llm_meta["llm_attempted_compaction"] = bool(is_patch_request)
            llm_meta["llm_attempted_patch_batch"] = False
            llm_meta["llm_input_budget_limit"] = int(budgeting_stats.get("input_budget_limit", 0) or 0)
            llm_meta["llm_input_budget_used_est"] = int(
                budgeting_stats.get("input_budget_used_est", 0) or 0
            )
            llm_meta["llm_dropped_locators_count"] = int(
                budgeting_stats.get("dropped_locators_count", 0) or 0
            )
            llm_meta["llm_dropped_hunks_count"] = int(
                budgeting_stats.get("dropped_hunks_count", 0) or 0
            )
            llm_meta["llm_dropped_snippets_count"] = int(
                budgeting_stats.get("dropped_snippets_count", 0) or 0
            )
            if governor.llm_last_remaining is not None:
                llm_meta["llm_remaining_requests"] = governor.llm_last_remaining
                llm_meta["llm_requests_remaining"] = governor.llm_last_remaining
                llm_meta["llm_remaining_is_estimate"] = governor.llm_remaining_is_estimate
            else:
                _apply_remaining_fallback(llm_meta)
            llm_meta["llm_calls"] = [
                _compact_usage_call(
                    batch_id="single",
                    model_id=model_id,
                    tier=tier,
                    tokens_prompt=0,
                    tokens_completion=0,
                    tokens_total=0,
                    remaining_requests=llm_meta.get("llm_remaining_requests", "n/a"),
                    remaining_is_estimate=bool(llm_meta.get("llm_remaining_is_estimate", True)),
                    reset_time_utc_iso=governor.llm_last_reset,
                    usage_estimated=True,
                )
            ]
            llm_meta["llm_model_counts"] = _build_model_counts(llm_meta["llm_calls"])
            return None, _attach_llm_policy_fields(
                llm_meta,
                github_context=github_context,
                allowed=True,
            )
        if decision.switch_to_mini and "mini" not in model_id.lower():
            downgrade_threshold = _llm_downgrade_threshold_for_command(cfg, cmd, effective_intent)
            retain_preferred = False
            retain_reason = "n/a"
            cmd_norm = str(cmd or "").strip().lower()
            if cmd_norm in {"ask", "explain"}:
                retain_preferred, retain_reason = _should_retain_preferred_model_for_ask(
                    cfg=cfg,
                    cmd=cmd,
                    execution_mode=normalized_execution_mode,
                    llm_intent=normalized_llm_intent,
                    route=normalized_route,
                    complexity_score=complexity_score,
                    remaining_requests=governor.llm_last_remaining,
                    github_context=github_context,
                )
            elif cmd_norm == "review":
                retain_preferred, retain_reason = _should_retain_preferred_model_for_review(
                    cfg=cfg,
                    cmd=cmd,
                    execution_mode=normalized_execution_mode,
                    llm_intent=normalized_llm_intent,
                    route=normalized_route,
                    complexity_score=complexity_score,
                    remaining_requests=governor.llm_last_remaining,
                    github_context=github_context,
                    payload_token_est=prompt_cost_est,
                    payload_token_limit=max_input_tokens,
                )
            if retain_preferred:
                model_downgrade_reason = "n/a"
                llm_retained_preferred_model_reason = retain_reason
                retained_preferred_model = True
            elif governor.llm_last_remaining is not None and int(governor.llm_last_remaining) >= downgrade_threshold:
                model_downgrade_reason = "n/a"
                llm_retained_preferred_model_reason = (
                    "retained preferred model: remaining quota above downgrade threshold"
                )
                retained_preferred_model = True
            else:
                model_id = model_low
                tier = "low"
                model_downgrade_reason = "budget_policy: switched to mini due remaining/quota constraints"
                llm_retained_preferred_model_reason = "n/a"
            llm_downgrade_threshold_used = str(downgrade_threshold)
        else:
            llm_retained_preferred_model_reason = "n/a"
            llm_downgrade_threshold_used = str(
                _llm_downgrade_threshold_for_command(cfg, cmd, effective_intent)
            )
        if decision.budget_action != "n/a":
            if retained_preferred_model:
                action_items = [
                    item.strip()
                    for item in str(decision.budget_action).split(";")
                    if item.strip()
                    and item.strip()
                    not in {"model_downgraded_to_mini", "model_downgraded_to_mini_estimate_mode"}
                ]
                governor_action = (
                    "; ".join(action_items)
                    if action_items
                    else "budget policy evaluated; preferred model retained"
                )
            else:
                governor_action = decision.budget_action
    else:
        llm_retained_preferred_model_reason = "n/a"
        llm_downgrade_threshold_used = str(
            _llm_downgrade_threshold_for_command(cfg, cmd, effective_intent)
        )
    client = GitHubModelsClient(token=token)
    primary_model_id = model_id
    effective_model_id = model_id
    fallback_model_id = _alternate_model_id(model_id, model_high=model_high, model_low=model_low)
    fallback_used = False
    is_fix_path = _is_fix_intent(cmd, effective_intent)
    primary_status: int | None = None
    fallback_status: int | None = None
    error_types: list[str] = []
    response = None
    final_exc: GitHubModelsError | None = None

    def _attempt_model(call_model_id: str, *, retry_count: int) -> Any:
        failures = 0
        while True:
            try:
                return client.chat(
                    model_id=call_model_id,
                    messages=messages,
                    max_tokens=max_output_tokens,
                    temperature=0.1,
                    stream=False,
                )
            except GitHubModelsError as exc:
                nonlocal primary_status, fallback_status
                if call_model_id == primary_model_id:
                    primary_status = exc.status_code
                else:
                    fallback_status = exc.status_code
                error_types.append(str(exc.reason or "unknown"))
                if failures >= retry_count or not _is_retryable_llm_error(exc):
                    raise
                failures += 1
                # Retries are only for transient provider/network failures.
                time.sleep(float(2 ** failures))

    try:
        response = _attempt_model(primary_model_id, retry_count=3 if is_fix_path else 0)
    except GitHubModelsError as exc:
        final_exc = exc
        if is_fix_path and _is_fallback_eligible_llm_error(exc):
            alt_model = str(fallback_model_id or "").strip()
            if alt_model and alt_model.lower() != primary_model_id.lower():
                fallback_used = True
                effective_model_id = alt_model
                try:
                    response = _attempt_model(alt_model, retry_count=0)
                    tier = "low" if "mini" in alt_model.lower() else "high"
                except GitHubModelsError as fallback_exc:
                    final_exc = fallback_exc

    if response is None or final_exc is not None and not fallback_used:
        active_error = final_exc if final_exc is not None else GitHubModelsError("unknown", reason="unknown")
        provider_status = fallback_status if fallback_used else primary_status
        llm_meta = _llm_default_meta(
            f"LLM_NOT_AVAILABLE:{active_error.reason}",
            execution_mode=normalized_execution_mode,
            llm_intent=normalized_llm_intent,
            llm_decision_reason_short=decision_reason_short,
            llm_decision_reason_code=decision_reason_code,
        )
        llm_meta["llm_decision_route"] = normalized_route or "n/a"
        llm_meta["llm_model_used"] = "not used"
        llm_meta["llm_final_synthesis_model_id"] = "not used"
        llm_meta["llm_preferred_model_id"] = preferred_model_id_resolved
        llm_meta["llm_model_selection_reason"] = selection_reason
        llm_meta["llm_model_downgrade_reason"] = model_downgrade_reason
        llm_meta["llm_retained_preferred_model_reason"] = llm_retained_preferred_model_reason
        llm_meta["llm_downgrade_threshold_used"] = llm_downgrade_threshold_used
        llm_meta["llm_primary_model_id"] = primary_model_id
        llm_meta["llm_effective_model_id"] = effective_model_id if fallback_used else primary_model_id
        llm_meta["llm_fallback_used"] = bool(fallback_used)
        llm_meta["llm_tier"] = tier
        llm_meta["llm_budget_action"] = governor_action
        llm_meta["llm_governor_reason"] = governor_reason
        llm_meta["llm_complexity_score"] = complexity_score
        llm_meta["llm_complexity_explanation"] = explanation
        llm_meta["llm_calls_this_run"] = 1
        llm_meta["llm_max_output_tokens_used"] = max_output_tokens
        llm_meta["llm_input_budget_limit"] = int(budgeting_stats.get("input_budget_limit", 0) or 0)
        llm_meta["llm_input_budget_used_est"] = int(
            budgeting_stats.get("input_budget_used_est", 0) or 0
        )
        llm_meta["llm_dropped_locators_count"] = int(
            budgeting_stats.get("dropped_locators_count", 0) or 0
        )
        llm_meta["llm_dropped_hunks_count"] = int(
            budgeting_stats.get("dropped_hunks_count", 0) or 0
        )
        llm_meta["llm_dropped_snippets_count"] = int(
            budgeting_stats.get("dropped_snippets_count", 0) or 0
        )
        llm_meta["llm_provider_http_status"] = provider_status
        provider_error_type = str(active_error.reason or "unknown")
        if int(provider_status or 0) == 413 and provider_error_type in {"http_error", "unknown"}:
            provider_error_type = "payload_too_large"
        llm_meta["llm_provider_error_type"] = provider_error_type
        llm_meta["llm_primary_status"] = primary_status
        llm_meta["llm_fallback_status"] = fallback_status
        llm_meta["llm_error_types"] = list(dict.fromkeys(error_types))
        llm_meta["llm_request_mode"] = "patch" if is_patch_request else "normal"
        llm_meta["llm_patch_batch_mode"] = False
        llm_meta["llm_patch_batch_count"] = 0
        llm_meta["llm_compacted"] = bool(is_patch_request)
        llm_meta["llm_attempted_compaction"] = bool(is_patch_request)
        llm_meta["llm_attempted_patch_batch"] = False
        _apply_remaining_fallback(llm_meta)
        llm_meta["llm_remaining_is_estimate"] = True
        llm_meta["llm_calls"] = [
            _compact_usage_call(
                batch_id="single",
                model_id=str(llm_meta.get("llm_effective_model_id", primary_model_id)),
                tier=tier,
                tokens_prompt=0,
                tokens_completion=0,
                tokens_total=0,
                remaining_requests=llm_meta.get("llm_remaining_requests", "n/a"),
                remaining_is_estimate=True,
                reset_time_utc_iso=None,
                usage_estimated=True,
            )
        ]
        llm_meta["llm_model_counts"] = _build_model_counts(llm_meta["llm_calls"])
        return None, _attach_llm_policy_fields(
            llm_meta,
            github_context=github_context,
            allowed=True,
        )

    llm_meta = {
        "llm_used": True,
        "llm_skip_reason": "n/a",
        "execution_mode": normalized_execution_mode,
        "llm_intent": normalized_llm_intent,
        "llm_decision_reason_short": decision_reason_short,
        "llm_decision_reason_code": decision_reason_code,
        "llm_runtime_override_reason": "n/a",
        "llm_decision_route": normalized_route or "n/a",
        "llm_model_used": response.model_id,
        "llm_final_synthesis_model_id": response.model_id,
        "llm_preferred_model_id": preferred_model_id_resolved,
        "llm_model_selection_reason": selection_reason,
        "llm_model_downgrade_reason": (
            "provider_fallback_to_alternate_model"
            if fallback_used and str(response.model_id).strip().lower() != preferred_model_id_resolved.lower()
            else model_downgrade_reason
        ),
        "llm_retained_preferred_model_reason": llm_retained_preferred_model_reason,
        "llm_downgrade_threshold_used": llm_downgrade_threshold_used,
        "llm_primary_model_id": primary_model_id,
        "llm_effective_model_id": response.model_id,
        "llm_fallback_used": bool(fallback_used),
        "llm_tier": tier,
        "llm_budget_action": governor_action,
        "llm_governor_reason": governor_reason,
        "llm_tokens_prompt": response.prompt_tokens,
        "llm_tokens_completion": response.completion_tokens,
        "llm_tokens_total": response.total_tokens,
        "llm_usage_estimated": bool(response.usage_estimated),
        "llm_remaining_requests": (
            response.requests_remaining if response.requests_remaining is not None else "n/a"
        ),
        "llm_remaining_is_estimate": bool(response.remaining_is_estimate),
        "llm_reset_time_utc_iso": response.reset_time_utc_iso,
        "llm_requests_remaining": (
            response.requests_remaining if response.requests_remaining is not None else "n/a"
        ),
        "llm_rate_limit_reset": response.reset_time_utc_iso or "n/a",
        "llm_reason": "ok",
        "llm_complexity_score": complexity_score,
        "llm_complexity_explanation": explanation,
        "llm_calls_this_run": 1,
        "llm_max_output_tokens_used": max_output_tokens,
        "llm_request_mode": "patch" if is_patch_request else "normal",
        "llm_patch_batch_mode": False,
        "llm_patch_batch_count": 0,
        "llm_compacted": bool(is_patch_request),
        "llm_attempted_compaction": bool(is_patch_request),
        "llm_attempted_patch_batch": False,
        "llm_input_budget_limit": int(budgeting_stats.get("input_budget_limit", 0) or 0),
        "llm_input_budget_used_est": int(budgeting_stats.get("input_budget_used_est", 0) or 0),
        "llm_dropped_locators_count": int(budgeting_stats.get("dropped_locators_count", 0) or 0),
        "llm_dropped_hunks_count": int(budgeting_stats.get("dropped_hunks_count", 0) or 0),
        "llm_dropped_snippets_count": int(budgeting_stats.get("dropped_snippets_count", 0) or 0),
        "llm_ratelimit_headers": dict(response.ratelimit_headers),
        "llm_provider_http_status": primary_status if fallback_used else None,
        "llm_provider_error_type": (
            error_types[-1] if fallback_used and error_types else "n/a"
        ),
        "llm_primary_status": primary_status,
        "llm_fallback_status": fallback_status,
        "llm_error_types": list(dict.fromkeys(error_types)),
    }
    if governor is not None:
        governor.observe_llm_signal(
            QuotaSignal(
                remaining_requests=response.requests_remaining,
                reset_time_utc_iso=response.reset_time_utc_iso,
                remaining_is_estimate=response.remaining_is_estimate,
                usage_estimated=response.usage_estimated,
                ratelimit_headers=dict(response.ratelimit_headers),
            ),
            {
                "tokens_total": response.total_tokens,
                "tokens_prompt": response.prompt_tokens,
                "tokens_completion": response.completion_tokens,
            },
        )
    if response.requests_remaining is None:
        _apply_remaining_fallback(llm_meta)
        llm_meta["llm_remaining_is_estimate"] = True
    if llm_meta.get("llm_remaining_requests", "n/a") in {None, "", "n/a"}:
        _apply_remaining_fallback(llm_meta)
    if llm_meta.get("llm_reset_time_utc_iso", None) in {None, ""}:
        llm_meta["llm_rate_limit_reset"] = "n/a"
    llm_meta["llm_calls"] = [
        _compact_usage_call(
            batch_id="single",
            model_id=str(response.model_id),
            tier=str(tier),
            tokens_prompt=int(response.prompt_tokens),
            tokens_completion=int(response.completion_tokens),
            tokens_total=int(response.total_tokens),
            remaining_requests=llm_meta.get("llm_remaining_requests", "n/a"),
            remaining_is_estimate=bool(llm_meta.get("llm_remaining_is_estimate", True)),
            reset_time_utc_iso=llm_meta.get("llm_reset_time_utc_iso"),
            usage_estimated=bool(response.usage_estimated),
        )
    ]
    llm_meta["llm_model_counts"] = _build_model_counts(llm_meta["llm_calls"])
    return (
        response.text.strip() or None,
        _attach_llm_policy_fields(
            llm_meta,
            github_context=github_context,
            allowed=True,
        ),
    )


def _extract_patch_from_stats(compression_stats: dict[str, Any]) -> str:
    direct_keys = ("patch_diff", "unified_diff", "suggested_patch")
    for key in direct_keys:
        value = compression_stats.get(key)
        if isinstance(value, str) and value.strip():
            return value
    list_keys = ("suggested_patches", "patches")
    for key in list_keys:
        value = compression_stats.get(key, [])
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, str) and item.strip():
                return item
            if isinstance(item, dict):
                for nested in ("unified_diff", "diff", "patch"):
                    payload = item.get(nested)
                    if isinstance(payload, str) and payload.strip():
                        return payload
    return ""


def _apply_fix_localization_gate(*, patch_text: str, no_localized_patch_target: bool) -> str:
    if no_localized_patch_target:
        return ""
    return str(patch_text or "")


def _write_patch_artifact(repo_root: Path, patch_text: str) -> Path:
    path = repo_root / "artifacts" / "patch.diff"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(patch_text, encoding="utf-8")
    return path


def _patch_snippet(patch_text: str, max_lines: int = 250) -> str:
    lines = patch_text.splitlines()
    if len(lines) <= max_lines:
        return patch_text
    return "\n".join(lines[:max_lines] + ["", "# ... truncated ..."])


def _sanitize_batch_text(text: str, *, max_lines: int = 8) -> list[str]:
    lines: list[str] = []
    for raw in str(text or "").splitlines():
        line = raw.strip().strip("`")
        if not line:
            continue
        if line.startswith(("diff --git", "--- ", "+++ ", "@@ ", "+", "-")):
            continue
        lines.append(line[:220])
        if len(lines) >= max_lines:
            break
    return lines


def _normalize_patch_output(text: str) -> str:
    return normalize_patch_output_value(text)


def _extract_json_envelope_patch(text: str) -> tuple[str, bool]:
    candidates = [_normalize_patch_output(text)]
    for match in re.finditer(r"```json\s*(.*?)```", candidates[0], flags=re.DOTALL | re.IGNORECASE):
        candidates.append(_normalize_patch_output(match.group(1)))
    for raw in candidates:
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        result = str(payload.get("result", "") or "").strip().lower()
        if result == "patch":
            diff = payload.get("diff")
            if isinstance(diff, str) and diff.strip():
                return _normalize_patch_output(diff), True
            continue
        if result in {"no_patch", "nopatch"}:
            return "", True
    return "", False


def _extract_patch_candidate(
    text: str,
) -> tuple[str, bool, bool, bool, bool, str, int]:
    extracted = extract_patch_candidate_normalized(text)
    return (
        extracted.patch_text,
        extracted.has_diff_fence,
        extracted.has_raw_diff,
        extracted.has_json_envelope,
        extracted.has_no_patch,
        extracted.extraction_path,
        extracted.response_chars,
    )


def _extract_patch_from_llm_text_with_flags(text: str) -> tuple[str, bool, bool]:
    patch, fenced, raw, *_ = _extract_patch_candidate(text)
    return patch, fenced, raw


def _extract_patch_from_llm_text(text: str) -> str:
    patch_text, *_ = _extract_patch_candidate(text)
    return patch_text


def _is_unified_diff(patch_text: str) -> bool:
    return is_unified_diff_normalized(patch_text)


def _parse_patch_ranges(patch_text: str) -> dict[str, list[tuple[int, int]]]:
    current_path = ""
    ranges: dict[str, list[tuple[int, int]]] = {}
    for line in patch_text.splitlines():
        if line.startswith("+++ "):
            raw = line[4:].strip()
            if raw.startswith("b/"):
                raw = raw[2:]
            current_path = raw if raw != "/dev/null" else ""
            if current_path:
                ranges.setdefault(current_path, [])
            continue
        if line.startswith("@@ ") and current_path:
            match = re.search(r"\+(\d+)(?:,(\d+))?", line)
            if not match:
                continue
            start = int(match.group(1))
            count = int(match.group(2) or "1")
            end = max(start, start + max(count, 1) - 1)
            ranges.setdefault(current_path, []).append((start, end))
    return ranges


def _ranges_overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
    return not (a[1] < b[0] or b[1] < a[0])


def _merge_patch_parts(
    parts: list[dict[str, Any]],
) -> tuple[str, bool, list[str]]:
    sorted_parts = sorted(parts, key=lambda item: str(item.get("batch_id", "")))
    merged: list[str] = []
    details: list[str] = []
    seen_ranges: dict[str, list[tuple[int, int]]] = {}
    has_conflict = False

    for item in sorted_parts:
        batch_id = str(item.get("batch_id", "") or "")
        patch_text = str(item.get("patch", "") or "")
        if not patch_text:
            continue
        ranges = _parse_patch_ranges(patch_text)
        for path, path_ranges in ranges.items():
            existing = seen_ranges.setdefault(path, [])
            for candidate in path_ranges:
                if any(_ranges_overlap(candidate, prev) for prev in existing):
                    has_conflict = True
                    details.append(
                        f"conflict: path={path} range={candidate[0]}-{candidate[1]} batch={batch_id}"
                    )
                existing.append(candidate)
        merged.append(patch_text.strip())
    return "\n\n".join(part for part in merged if part), has_conflict, details


def _should_use_batch_mode_for_review(
    *,
    cmd: str,
    route: str,
    complexity_score: int,
    changed_files_count: int,
    diff_hunks_count: int = 0,
    estimated_patch_input_tokens: int = 0,
) -> bool:
    if cmd not in {"review", "fix"}:
        return False
    normalized_route = str(route or "").strip().upper()
    if normalized_route in {"WAIT", "REFUSE", "BLOCK"}:
        return False
    cfg = _runtime_env_cfg()
    if cmd == "fix":
        if not bool(cfg.batch.patch_enable):
            return False
        if bool(cfg.batch.patch_force):
            return True
        if int(changed_files_count) > 1:
            return True
        if int(diff_hunks_count) > max(1, int(cfg.batch.patch_max_hunks_per_call)):
            return True
        if int(estimated_patch_input_tokens) > max(256, int(cfg.llm.max_input_tokens_patch)):
            return True
        return False

    if not bool(cfg.batch.enabled):
        return False
    if bool(cfg.batch.force):
        return True
    return normalized_route == "DEEP" or complexity_score >= 60 or changed_files_count >= 10


def _should_retry_patch_batch_after_single_call(
    *,
    cmd: str,
    llm_meta: dict[str, Any],
) -> bool:
    if cmd != "fix":
        return False
    cfg = _runtime_env_cfg()
    if not bool(cfg.batch.patch_enable):
        return False
    return _int_or_zero(llm_meta.get("llm_provider_http_status", 0)) == 413


def _split_batch_for_force_mode(batch: Batch) -> list[Batch]:
    paths = list(batch.paths)
    snippets = list(batch.snippet_ids)
    hunks = list(batch.diff_hunks)

    def split(values: list[str]) -> tuple[list[str], list[str]]:
        if not values:
            return [], []
        mid = max(1, len(values) // 2)
        return values[:mid], values[mid:]

    paths_a, paths_b = split(paths)
    snippets_a, snippets_b = split(snippets)
    hunks_a, hunks_b = split(hunks)

    if not paths_a and paths:
        paths_a = [paths[0]]
    if not paths_b and paths:
        paths_b = paths[1:] or [paths[0]]
    if not snippets_a and snippets:
        snippets_a = [snippets[0]]
    if not snippets_b and snippets:
        snippets_b = snippets[1:] or [snippets[0]]
    if not hunks_a and hunks:
        hunks_a = [hunks[0]]
    if not hunks_b and hunks:
        hunks_b = hunks[1:] or [hunks[0]]

    first = Batch(
        batch_id=f"{batch.batch_id}-f1",
        paths=paths_a or paths or ["(forced-batch)"],
        diff_hunks=hunks_a,
        snippet_ids=snippets_a,
        estimated_input_tokens=max(1, int(batch.estimated_input_tokens / 2)),
    )
    second = Batch(
        batch_id=f"{batch.batch_id}-f2",
        paths=paths_b or paths_a or paths or ["(forced-batch)"],
        diff_hunks=hunks_b,
        snippet_ids=snippets_b,
        estimated_input_tokens=max(1, batch.estimated_input_tokens - first.estimated_input_tokens),
    )
    return [first, second]


def _split_batch_by_hunk_cap(batch: Batch, *, max_hunks_per_call: int) -> list[Batch]:
    max_hunks = max(1, int(max_hunks_per_call))
    if len(batch.diff_hunks) <= max_hunks:
        return [batch]

    chunks: list[Batch] = []
    hunks = list(batch.diff_hunks)
    total_hunks = max(1, len(hunks))
    for start in range(0, len(hunks), max_hunks):
        grouped = hunks[start : start + max_hunks]
        ratio = len(grouped) / total_hunks
        estimated_tokens = max(1, int(batch.estimated_input_tokens * ratio))
        chunks.append(
            Batch(
                batch_id=f"{batch.batch_id}-h{len(chunks) + 1}",
                paths=list(batch.paths),
                diff_hunks=list(grouped),
                snippet_ids=list(batch.snippet_ids),
                estimated_input_tokens=estimated_tokens,
            )
        )
    return chunks


def _run_batch_llm_review_fix(
    *,
    repo_root: Path,
    cmd: str,
    intent: str,
    query: str,
    route: str,
    execution_mode: str | None = None,
    llm_intent_decision: str | None = None,
    llm_decision_reason_short: str | None = None,
    llm_decision_reason_code: str | None = None,
    github_context: dict[str, Any],
    selected_chunks: list[CandidateChunk],
    locators: list[EvidenceItem],
    governor: AIBudgetGovernor | None = None,
    force_patch_batch: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    route_norm = str(route or "").strip().upper()
    legacy_semantic_default = (
        execution_mode is None
        and llm_intent_decision is None
        and llm_decision_reason_short is None
        and llm_decision_reason_code is None
    )
    legacy_route_block_reason = ""
    if legacy_semantic_default:
        if route_norm == "WAIT":
            execution_mode = "verification_first"
            llm_intent_decision = "none"
            llm_decision_reason_short = "LLM not used: verification required before answer."
            llm_decision_reason_code = "route_wait"
            legacy_route_block_reason = "route=WAIT"
        elif route_norm in {"REFUSE", "BLOCK"}:
            execution_mode = "refuse"
            llm_intent_decision = "none"
            llm_decision_reason_short = "LLM not used: request refused by security policy."
            llm_decision_reason_code = "route_refuse" if route_norm == "REFUSE" else "route_block"
            legacy_route_block_reason = f"route={route_norm}"
        else:
            execution_mode = "retrieval_plus_llm"

    semantic = coerce_execution_decision(
        route=route_norm or "FAST",
        execution_mode=execution_mode,
        llm_intent=llm_intent_decision,
        reason_short=llm_decision_reason_short,
        reason_code=llm_decision_reason_code,
    )
    execution_mode_norm = semantic.execution_mode
    llm_intent_norm = semantic.llm_intent
    llm_reason_short = semantic.reason_short
    llm_reason_code = semantic.reason_code
    if execution_mode_norm != "retrieval_plus_llm":
        skip_reason = f"execution_mode={execution_mode_norm}"
        if legacy_route_block_reason:
            skip_reason = legacy_route_block_reason
        llm_meta = _llm_default_meta(
            skip_reason,
            execution_mode=execution_mode_norm,
            llm_intent=llm_intent_norm,
            llm_decision_reason_short=llm_reason_short,
            llm_decision_reason_code=llm_reason_code,
        )
        llm_meta["llm_decision_route"] = route_norm or "n/a"
        llm_meta["llm_request_mode"] = "patch" if _is_fix_intent(cmd, intent) else "normal"
        return {"batch_used": False, "summaries": [], "findings": [], "patch_parts": []}, _attach_llm_policy_fields(
            llm_meta,
            github_context=github_context,
            allowed=False,
        )

    is_patch_mode = _is_fix_intent(cmd, intent)
    llm_allowed_by_policy, llm_policy_reason = _llm_runtime_policy(github_context)
    llm_disabled = not llm_allowed_by_policy
    if llm_disabled:
        llm_meta = _llm_default_meta(
            str(llm_policy_reason or "disabled"),
            execution_mode=execution_mode_norm,
            llm_intent=llm_intent_norm,
            llm_decision_reason_short=llm_reason_short,
            llm_decision_reason_code=llm_reason_code,
        )
        llm_meta["llm_decision_route"] = route_norm or "n/a"
        llm_meta["llm_request_mode"] = "patch" if is_patch_mode else "normal"
        llm_meta["llm_patch_batch_mode"] = bool(is_patch_mode)
        llm_meta["llm_patch_batch_count"] = 0
        llm_meta["llm_compacted"] = bool(is_patch_mode)
        llm_meta["llm_attempted_compaction"] = bool(is_patch_mode)
        llm_meta["llm_attempted_patch_batch"] = bool(is_patch_mode)
        return {"batch_used": False, "summaries": [], "findings": [], "patch_parts": []}, _attach_llm_policy_fields(
            llm_meta,
            github_context=github_context,
            allowed=False,
        )

    cfg = _runtime_env_cfg()
    max_input_tokens = int(cfg.llm.max_input_tokens_patch if is_patch_mode else cfg.llm.max_input_tokens)
    reserve_tokens = 600 if is_patch_mode else 800
    planned = plan_batches(
        task_type=cmd,
        intent=intent,
        github_context=github_context,
        selected_chunks=selected_chunks,
        limits={"max_input_tokens": max_input_tokens},
        budgets={"max_input_tokens": max_input_tokens, "reserve_tokens": reserve_tokens},
    )
    force_batch = bool(cfg.batch.patch_force if is_patch_mode else cfg.batch.force)
    if force_patch_batch and is_patch_mode:
        force_batch = True
    if force_batch and len(planned) == 1:
        planned = _split_batch_for_force_mode(planned[0])
    if is_patch_mode:
        max_calls = max(1, min(int(cfg.batch.max_calls_per_run), int(cfg.batch.patch_max_calls)))
    else:
        max_calls = max(1, int(cfg.batch.max_calls_per_run))
    if is_patch_mode:
        split_planned: list[Batch] = []
        for batch in planned:
            split_planned.extend(
                _split_batch_by_hunk_cap(
                    batch,
                    max_hunks_per_call=int(cfg.batch.patch_max_hunks_per_call),
                )
            )
        planned = split_planned
    model_high = str(cfg.llm.model_high or "openai/gpt-4.1")
    model_low = str(cfg.llm.model_low or "openai/gpt-4.1-mini")
    overall_score = score_complexity(
        task_type=cmd,
        intent=intent,
        route=route_norm,
        github_context=github_context,
        candidates=[None] * max(0, len(selected_chunks)),
        limits={"query_length": len(query or "")},
    )
    changed_files_raw = github_context.get("changed_files", [])
    changed_files_count = (
        len(changed_files_raw)
        if isinstance(changed_files_raw, list)
        else 0
    )
    overall_synthesis_required = route_norm == "DEEP" or changed_files_count >= 2
    overall_model, overall_tier = choose_model(
        overall_score,
        model_high=model_high,
        model_low=model_low,
        task_type=cmd,
        intent=intent,
        route=route_norm,
        execution_mode=execution_mode_norm,
        llm_intent=llm_intent_norm,
        synthesis_required=overall_synthesis_required,
    )
    overall_selection_reason = model_selection_reason(
        score=overall_score,
        task_type=cmd,
        intent=intent,
        route=route_norm,
        execution_mode=execution_mode_norm,
        llm_intent=llm_intent_norm,
        synthesis_required=overall_synthesis_required,
    )
    overall_preferred_model = overall_model
    overall_downgrade_reason = "n/a"
    overall_retained_preferred_reason = "n/a"
    retained_preferred_model = False
    reduce_model_override = str(cfg.batch.reduce_model or "").strip()
    reduce_enable = bool(cfg.batch.reduce_enable)
    pre_batch_action = "n/a"
    pre_batch_reason = "n/a"
    planned_payload_est = max(
        (int(batch.estimated_input_tokens or 0) for batch in planned),
        default=max(1, int(max_input_tokens / 2)),
    )
    if governor is not None:
        bootstrap_decision = governor.can_call_llm(
            next_call_cost_est=max(1, int(max_input_tokens / 2)),
            tier=overall_tier,
            intent=intent,
        )
        pre_batch_action = bootstrap_decision.budget_action
        pre_batch_reason = bootstrap_decision.reason
        if not bootstrap_decision.allow:
            llm_meta = _llm_default_meta(
                f"budget:{bootstrap_decision.reason}",
                execution_mode=execution_mode_norm,
                llm_intent=llm_intent_norm,
                llm_decision_reason_short=llm_reason_short,
                llm_decision_reason_code=llm_reason_code,
            )
            llm_meta["llm_decision_route"] = route_norm or "n/a"
            llm_meta["llm_model_used"] = "not used"
            llm_meta["llm_final_synthesis_model_id"] = "not used"
            llm_meta["llm_preferred_model_id"] = overall_preferred_model
            llm_meta["llm_model_selection_reason"] = overall_selection_reason
            llm_meta["llm_model_downgrade_reason"] = overall_downgrade_reason
            llm_meta["llm_retained_preferred_model_reason"] = "n/a"
            llm_meta["llm_downgrade_threshold_used"] = str(
                _llm_downgrade_threshold_for_command(cfg, cmd, intent)
            )
            llm_meta["llm_effective_model_id"] = overall_model
            llm_meta["llm_budget_action"] = bootstrap_decision.budget_action
            llm_meta["llm_governor_reason"] = bootstrap_decision.reason
            llm_meta["llm_request_mode"] = "patch" if is_patch_mode else "normal"
            llm_meta["llm_patch_batch_mode"] = bool(is_patch_mode)
            llm_meta["llm_patch_batch_count"] = 0
            llm_meta["llm_compacted"] = bool(is_patch_mode)
            llm_meta["llm_attempted_compaction"] = bool(is_patch_mode)
            llm_meta["llm_attempted_patch_batch"] = bool(is_patch_mode)
            return {
                "batch_used": False,
                "summaries": [],
                "findings": [],
                "patch_parts": [],
            }, _attach_llm_policy_fields(
                llm_meta,
                github_context=github_context,
                allowed=True,
            )
        if bootstrap_decision.switch_to_mini:
            retain_review_preferred = False
            retain_review_reason = "n/a"
            if "mini" not in overall_model.lower() and str(cmd or "").strip().lower() == "review":
                retain_review_preferred, retain_review_reason = _should_retain_preferred_model_for_review(
                    cfg=cfg,
                    cmd=cmd,
                    execution_mode=execution_mode_norm,
                    llm_intent=llm_intent_norm,
                    route=route_norm,
                    complexity_score=overall_score,
                    remaining_requests=governor.llm_last_remaining,
                    github_context=github_context,
                    payload_token_est=planned_payload_est,
                    payload_token_limit=max_input_tokens,
                )
            if retain_review_preferred:
                retained_preferred_model = True
                overall_retained_preferred_reason = retain_review_reason
                overall_downgrade_reason = "n/a"
            else:
                if "mini" not in overall_model.lower():
                    overall_downgrade_reason = (
                        "budget_policy: switched to mini due remaining/quota constraints"
                    )
                overall_model = model_low
                overall_tier = "low"
        if bootstrap_decision.max_calls is not None:
            max_calls = min(max_calls, max(1, int(bootstrap_decision.max_calls)))
        if bootstrap_decision.disable_reduce:
            reduce_enable = False
        if pre_batch_action != "n/a" and retained_preferred_model:
            action_items = [
                item.strip()
                for item in str(pre_batch_action).split(";")
                if item.strip()
                and item.strip()
                not in {"model_downgraded_to_mini", "model_downgraded_to_mini_estimate_mode"}
            ]
            pre_batch_action = (
                "; ".join(action_items)
                if action_items
                else "budget policy evaluated; preferred model retained"
            )

    batches = planned[:max_calls]
    if not batches:
        llm_meta = _llm_default_meta(
            "no_batches",
            execution_mode=execution_mode_norm,
            llm_intent=llm_intent_norm,
            llm_decision_reason_short=llm_reason_short,
            llm_decision_reason_code=llm_reason_code,
        )
        llm_meta["llm_decision_route"] = route_norm or "n/a"
        llm_meta["llm_model_used"] = "not used"
        llm_meta["llm_final_synthesis_model_id"] = "not used"
        llm_meta["llm_preferred_model_id"] = overall_preferred_model
        llm_meta["llm_model_selection_reason"] = overall_selection_reason
        llm_meta["llm_model_downgrade_reason"] = overall_downgrade_reason
        llm_meta["llm_retained_preferred_model_reason"] = overall_retained_preferred_reason
        llm_meta["llm_downgrade_threshold_used"] = str(
            _llm_downgrade_threshold_for_command(cfg, cmd, intent)
        )
        llm_meta["llm_effective_model_id"] = overall_model
        llm_meta["llm_request_mode"] = "patch" if is_patch_mode else "normal"
        llm_meta["llm_patch_batch_mode"] = bool(is_patch_mode)
        llm_meta["llm_patch_batch_count"] = 0
        llm_meta["llm_compacted"] = bool(is_patch_mode)
        llm_meta["llm_attempted_compaction"] = bool(is_patch_mode)
        llm_meta["llm_attempted_patch_batch"] = bool(is_patch_mode)
        return {"batch_used": False, "summaries": [], "findings": [], "patch_parts": []}, _attach_llm_policy_fields(
            llm_meta,
            github_context=github_context,
            allowed=True,
        )

    calls: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    findings: list[str] = []
    patch_parts: list[dict[str, Any]] = []
    no_patch_count = 0
    last_remaining: Any = None
    last_reset: str | None = None
    llm_ratelimit_headers: dict[str, str] = {}
    dropped_locators = 0
    dropped_hunks = 0
    dropped_snippets = 0
    prompt_used_total = 0
    prompt_limit_total = 0
    max_output_tokens_max = 0
    usage_estimated_any = False
    any_used = False
    budget_actions: list[str] = []
    governor_reasons: list[str] = []
    if pre_batch_action != "n/a":
        budget_actions.append(str(pre_batch_action))
    if pre_batch_reason != "n/a":
        governor_reasons.append(str(pre_batch_reason))

    for index, batch in enumerate(batches):
        batch_context = dict(github_context)
        batch_context["changed_files"] = list(batch.paths)
        batch_context["diff_hunks"] = list(batch.diff_hunks)
        score_batch = score_complexity(
            task_type=cmd,
            intent=intent,
            route=route_norm,
            github_context=batch_context,
            candidates=[None] * max(0, len(batch.snippet_ids)),
            limits={"query_length": len(query or "")},
        )
        batch_model, batch_tier = choose_model(
            score_batch,
            model_high=model_high,
            model_low=model_low,
            task_type=cmd,
            intent=intent,
            route=route_norm,
            execution_mode=execution_mode_norm,
            llm_intent=llm_intent_norm,
            synthesis_required=(len(batch.paths) >= 2 or len(batch.diff_hunks) >= 2),
        )
        if batch.estimated_input_tokens < 900 and score_batch < 35:
            batch_model = model_low
            batch_tier = "low"
        if overall_tier == "high" and score_batch >= 35:
            batch_model = model_high
            batch_tier = "high"

        batch_locators = [item for item in locators if item.file_path in set(batch.paths)]
        batch_query = (
            f"{query}\n"
            f"Batch {index + 1}/{len(batches)}\n"
            f"Focus paths: {', '.join(batch.paths[:12])}"
        )
        text, meta = _maybe_generate_llm_text(
            cmd=cmd,
            intent=intent,
            query=batch_query,
            route=route_norm,
            execution_mode=execution_mode_norm,
            llm_intent_decision=llm_intent_norm,
            llm_decision_reason_short=llm_reason_short,
            llm_decision_reason_code=llm_reason_code,
            github_context=batch_context,
            locators=batch_locators,
            candidates_count=max(1, len(batch.snippet_ids)),
            selected_snippets=list(batch.snippet_ids),
            preferred_model_id=batch_model,
            preferred_tier=batch_tier,
            governor=governor,
        )
        call_entry_raw = meta.get("llm_calls", [])
        if isinstance(call_entry_raw, list) and call_entry_raw and isinstance(call_entry_raw[0], dict):
            call_entry = dict(call_entry_raw[0])
        else:
            call_entry = _compact_usage_call(
                batch_id=batch.batch_id,
                model_id=str(meta.get("llm_model_used", batch_model)),
                tier=str(meta.get("llm_tier", batch_tier)),
                tokens_prompt=_int_or_zero(meta.get("llm_tokens_prompt", 0)),
                tokens_completion=_int_or_zero(meta.get("llm_tokens_completion", 0)),
                tokens_total=_int_or_zero(meta.get("llm_tokens_total", 0)),
                remaining_requests=meta.get("llm_remaining_requests", "n/a"),
                remaining_is_estimate=bool(meta.get("llm_remaining_is_estimate", True)),
                reset_time_utc_iso=meta.get("llm_reset_time_utc_iso"),
                usage_estimated=bool(meta.get("llm_usage_estimated", True)),
            )
        call_entry["batch_id"] = batch.batch_id
        if bool(call_entry.get("remaining_is_estimate", True)) and last_remaining not in {None, "", "n/a"}:
            call_entry["remaining_requests"] = _remaining_after_decrement(last_remaining, decrement=1)
        last_remaining = call_entry.get("remaining_requests", last_remaining)
        last_reset = call_entry.get("reset_time_utc_iso", last_reset)
        calls.append(call_entry)

        llm_ratelimit_headers = dict(meta.get("llm_ratelimit_headers", llm_ratelimit_headers))
        dropped_locators += _int_or_zero(meta.get("llm_dropped_locators_count", 0))
        dropped_hunks += _int_or_zero(meta.get("llm_dropped_hunks_count", 0))
        dropped_snippets += _int_or_zero(meta.get("llm_dropped_snippets_count", 0))
        prompt_used_total += _int_or_zero(meta.get("llm_input_budget_used_est", 0))
        prompt_limit_total += _int_or_zero(meta.get("llm_input_budget_limit", 0))
        max_output_tokens_max = max(max_output_tokens_max, _int_or_zero(meta.get("llm_max_output_tokens_used", 0)))
        usage_estimated_any = usage_estimated_any or bool(meta.get("llm_usage_estimated", True))
        any_used = any_used or bool(meta.get("llm_used", False))
        action_value = str(meta.get("llm_budget_action", "n/a") or "n/a")
        reason_value = str(meta.get("llm_governor_reason", "n/a") or "n/a")
        if action_value != "n/a":
            budget_actions.append(action_value)
        if reason_value != "n/a":
            governor_reasons.append(reason_value)

        snippet_hashes = [
            hashlib.blake2s(value.encode("utf-8"), digest_size=8).hexdigest()
            for value in batch.snippet_ids
        ]
        summary_lines = _sanitize_batch_text(text or "")
        summaries.append(
            {
                "batch_id": batch.batch_id,
                "paths": list(batch.paths),
                "finding_bullets": summary_lines[:6],
                "locator_hashes": snippet_hashes[:20],
                "estimated_input_tokens": batch.estimated_input_tokens,
                "model_id": call_entry.get("model_id", batch_model),
            }
        )
        findings.extend(summary_lines[:4])
        if cmd == "fix":
            patch_info = _extract_patch_candidate(text or "")
            patch = patch_info[0]
            no_patch = bool(patch_info[4])
            if patch and _is_unified_diff(patch):
                patch_parts.append({"batch_id": batch.batch_id, "patch": patch})
                _write_patch_part(repo_root, batch.batch_id, patch)
            elif no_patch:
                no_patch_count += 1
                findings.append(f"batch={batch.batch_id} returned NO_PATCH")

    reduce_text: str | None = None
    if reduce_enable and len(summaries) > 1 and any_used:
        summary_lines = []
        for item in summaries[:12]:
            paths = ", ".join(item.get("paths", [])[:6]) if isinstance(item.get("paths"), list) else ""
            bullets = item.get("finding_bullets", [])
            if not isinstance(bullets, list):
                bullets = []
            summary_lines.append(f"- batch={item.get('batch_id')} paths={paths}")
            for bullet in bullets[:3]:
                summary_lines.append(f"  - {bullet}")
        reduce_messages = [
            {
                "role": "system",
                "content": (
                    "You aggregate RepoBrain batch summaries. Return concise executive summary "
                    "and prioritized checklist. Use only provided summaries."
                ),
            },
            {
                "role": "user",
                "content": "\n".join(
                    [
                        f"Task: {intent}",
                        f"Query: {query}",
                        "Batch summaries:",
                        *summary_lines,
                    ]
                ),
            },
        ]
        reduce_budget_stats = {
            "input_budget_limit": max_input_tokens,
            "input_budget_used_est": estimate_tokens(reduce_messages[1]["content"]),
            "dropped_locators_count": 0,
            "dropped_hunks_count": 0,
            "dropped_snippets_count": 0,
        }
        reduce_model = reduce_model_override or overall_model
        reduce_tier = "low" if "mini" in reduce_model.lower() else "high"
        reduce_output, reduce_meta = _maybe_generate_llm_text(
            cmd=cmd,
            intent=intent,
            query=query,
            route=route_norm,
            execution_mode=execution_mode_norm,
            llm_intent_decision=llm_intent_norm,
            llm_decision_reason_short=llm_reason_short,
            llm_decision_reason_code=llm_reason_code,
            github_context=github_context,
            locators=[],
            candidates_count=len(summaries),
            preferred_model_id=reduce_model,
            preferred_tier=reduce_tier,
            prebuilt_messages=reduce_messages,
            prebuilt_budget_stats=reduce_budget_stats,
            governor=governor,
        )
        reduce_call_raw = reduce_meta.get("llm_calls", [])
        if isinstance(reduce_call_raw, list) and reduce_call_raw and isinstance(reduce_call_raw[0], dict):
            reduce_call = dict(reduce_call_raw[0])
        else:
            reduce_call = _compact_usage_call(
                batch_id="reduce",
                model_id=reduce_model,
                tier=reduce_tier,
                tokens_prompt=_int_or_zero(reduce_meta.get("llm_tokens_prompt", 0)),
                tokens_completion=_int_or_zero(reduce_meta.get("llm_tokens_completion", 0)),
                tokens_total=_int_or_zero(reduce_meta.get("llm_tokens_total", 0)),
                remaining_requests=reduce_meta.get("llm_remaining_requests", "n/a"),
                remaining_is_estimate=bool(reduce_meta.get("llm_remaining_is_estimate", True)),
                reset_time_utc_iso=reduce_meta.get("llm_reset_time_utc_iso"),
                usage_estimated=bool(reduce_meta.get("llm_usage_estimated", True)),
            )
        reduce_call["batch_id"] = "reduce"
        if bool(reduce_call.get("remaining_is_estimate", True)) and last_remaining not in {None, "", "n/a"}:
            reduce_call["remaining_requests"] = _remaining_after_decrement(last_remaining, decrement=1)
        last_remaining = reduce_call.get("remaining_requests", last_remaining)
        last_reset = reduce_call.get("reset_time_utc_iso", last_reset)
        calls.append(reduce_call)
        llm_ratelimit_headers = dict(reduce_meta.get("llm_ratelimit_headers", llm_ratelimit_headers))
        dropped_locators += _int_or_zero(reduce_meta.get("llm_dropped_locators_count", 0))
        dropped_hunks += _int_or_zero(reduce_meta.get("llm_dropped_hunks_count", 0))
        dropped_snippets += _int_or_zero(reduce_meta.get("llm_dropped_snippets_count", 0))
        prompt_used_total += _int_or_zero(reduce_meta.get("llm_input_budget_used_est", 0))
        prompt_limit_total += _int_or_zero(reduce_meta.get("llm_input_budget_limit", 0))
        max_output_tokens_max = max(max_output_tokens_max, _int_or_zero(reduce_meta.get("llm_max_output_tokens_used", 0)))
        usage_estimated_any = usage_estimated_any or bool(reduce_meta.get("llm_usage_estimated", True))
        any_used = any_used or bool(reduce_meta.get("llm_used", False))
        action_value = str(reduce_meta.get("llm_budget_action", "n/a") or "n/a")
        reason_value = str(reduce_meta.get("llm_governor_reason", "n/a") or "n/a")
        if action_value != "n/a":
            budget_actions.append(action_value)
        if reason_value != "n/a":
            governor_reasons.append(reason_value)
        reduce_text = reduce_output

    dedup_findings = list(dict.fromkeys(item for item in findings if item))
    if reduce_text:
        final_summary = reduce_text.strip()
    else:
        final_summary = "\n".join(dedup_findings[:6]).strip()
    if not final_summary:
        final_summary = "No batch LLM summary available."

    tokens_prompt_total = sum(_int_or_zero(item.get("tokens_prompt", 0)) for item in calls)
    tokens_completion_total = sum(_int_or_zero(item.get("tokens_completion", 0)) for item in calls)
    tokens_total_total = sum(_int_or_zero(item.get("tokens_total", 0)) for item in calls)
    model_counts = _build_model_counts(calls)
    final_synthesis_model = "not used"
    if any_used and calls:
        if reduce_enable and reduce_text:
            final_synthesis_model = str(calls[-1].get("model_id", "not used") or "not used")
        else:
            final_synthesis_model = str(calls[-1].get("model_id", "not used") or "not used")
    final_remaining = calls[-1].get("remaining_requests", "n/a") if calls else "n/a"
    final_remaining_estimated = bool(calls[-1].get("remaining_is_estimate", True)) if calls else True
    final_reset = calls[-1].get("reset_time_utc_iso") if calls else None
    llm_meta = {
        "llm_used": any_used,
        "llm_skip_reason": "n/a" if any_used else "batch_calls_failed",
        "execution_mode": execution_mode_norm,
        "llm_intent": llm_intent_norm,
        "llm_decision_reason_short": llm_reason_short,
        "llm_decision_reason_code": llm_reason_code,
        "llm_runtime_override_reason": "n/a",
        "llm_decision_route": route_norm or "n/a",
        "llm_model_used": final_synthesis_model if any_used else "not used",
        "llm_final_synthesis_model_id": final_synthesis_model if any_used else "not used",
        "llm_preferred_model_id": overall_preferred_model,
        "llm_model_selection_reason": overall_selection_reason,
        "llm_model_downgrade_reason": overall_downgrade_reason,
        "llm_retained_preferred_model_reason": overall_retained_preferred_reason,
        "llm_downgrade_threshold_used": str(
            _llm_downgrade_threshold_for_command(cfg, cmd, intent)
        ),
        "llm_primary_model_id": overall_model,
        "llm_effective_model_id": final_synthesis_model if any_used else overall_model,
        "llm_fallback_used": False,
        "llm_tier": "high" if any("gpt-4.1" in key and "mini" not in key for key in model_counts) else "low",
        "llm_budget_action": "; ".join(dict.fromkeys(budget_actions)) if budget_actions else "n/a",
        "llm_governor_reason": "; ".join(dict.fromkeys(governor_reasons)) if governor_reasons else "n/a",
        "llm_tokens_prompt": tokens_prompt_total,
        "llm_tokens_completion": tokens_completion_total,
        "llm_tokens_total": tokens_total_total,
        "llm_usage_estimated": usage_estimated_any,
        "llm_remaining_requests": final_remaining,
        "llm_remaining_is_estimate": final_remaining_estimated,
        "llm_reset_time_utc_iso": final_reset,
        "llm_requests_remaining": final_remaining,
        "llm_rate_limit_reset": final_reset or "n/a",
        "llm_reason": "ok" if any_used else "batch_calls_failed",
        "llm_complexity_score": overall_score,
        "llm_complexity_explanation": (
            f"batch mode: calls={len(calls)} route={route_norm} changed_files={len(github_context.get('changed_files', []))}"
        ),
        "llm_calls_this_run": len(calls),
        "llm_max_output_tokens_used": max_output_tokens_max,
        "llm_request_mode": "patch" if is_patch_mode else "normal",
        "llm_patch_batch_mode": bool(is_patch_mode),
        "llm_patch_batch_count": len(batches) if is_patch_mode else 0,
        "llm_compacted": bool(is_patch_mode),
        "llm_attempted_compaction": bool(is_patch_mode),
        "llm_attempted_patch_batch": bool(is_patch_mode),
        "llm_input_budget_limit": prompt_limit_total,
        "llm_input_budget_used_est": prompt_used_total,
        "llm_dropped_locators_count": dropped_locators,
        "llm_dropped_hunks_count": dropped_hunks,
        "llm_dropped_snippets_count": dropped_snippets,
        "llm_ratelimit_headers": llm_ratelimit_headers,
        "llm_calls": calls,
        "llm_model_counts": model_counts,
    }
    if llm_meta["llm_remaining_requests"] in {None, "", "n/a"}:
        _apply_remaining_fallback(llm_meta)
    return {
        "batch_used": True,
        "planned_batches": len(planned),
        "executed_batches": len(batches),
        "summaries": summaries,
        "findings": dedup_findings,
        "summary_text": final_summary,
        "patch_parts": patch_parts,
        "no_patch_batches_count": no_patch_count,
        "no_patch_returned": no_patch_count > 0 and not patch_parts,
    }, _attach_llm_policy_fields(
        llm_meta,
        github_context=github_context,
        allowed=True,
    )


def _maybe_apply_patch(
    *,
    repo_root: Path,
    patch_path: Path,
) -> dict[str, Any]:
    if not _env_true("RB_APPLY_PATCH", default=False):
        return {
            "applied": False,
            "pushed": False,
            "branch": "",
            "message": "auto-apply disabled (RB_APPLY_PATCH=0)",
        }
    if not _env_true("RB_TRUSTED_CONTEXT", default=False):
        return {
            "applied": False,
            "pushed": False,
            "branch": "",
            "message": "auto-apply blocked in untrusted context",
        }

    run_id = os.getenv("GITHUB_RUN_ID", "").strip() or str(int(time.time()))
    branch = f"repobrain/patch/{run_id}"

    commands = [
        ["git", "checkout", "-b", branch],
        ["git", "apply", str(patch_path)],
        ["git", "add", "-A"],
        ["git", "commit", "-m", "RepoBrain: apply suggested patch"],
        ["git", "push", "-u", "origin", branch],
    ]
    for cmd in commands:
        try:
            completed = subprocess.run(
                cmd,
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
        except OSError:
            return {
                "applied": False,
                "pushed": False,
                "branch": branch,
                "message": "cannot apply patch in this context",
            }
        if completed.returncode != 0:
            return {
                "applied": False,
                "pushed": False,
                "branch": branch,
                "message": "cannot push from this context",
            }
    return {
        "applied": True,
        "pushed": True,
        "branch": branch,
        "message": f"patch applied and pushed to `{branch}`",
    }


def _maybe_create_patch_pr(
    *,
    repo_name: str,
    token: str,
    patch_branch: str,
    base_branch: str,
    body_markdown: str,
) -> str:
    if not _env_true("RB_CREATE_PR", default=False):
        return "auto-pr disabled (RB_CREATE_PR=0)"
    if not _env_true("RB_APPLY_PATCH", default=False):
        return "auto-pr skipped (patch was not auto-applied)"
    if not _env_true("RB_TRUSTED_CONTEXT", default=False):
        return "auto-pr blocked in untrusted context"
    if not patch_branch:
        return "auto-pr skipped (no patch branch)"

    result = create_pull_request(
        repo=repo_name,
        token=token,
        head_branch=patch_branch,
        base_branch=base_branch,
        title="RepoBrain: suggested patch",
        body_md=body_markdown,
    )
    if bool(result.get("ok", False)):
        data = result.get("data", {})
        url = data.get("html_url") if isinstance(data, dict) else None
        return f"auto-pr created: {url}" if isinstance(url, str) and url else "auto-pr created"

    status = int(result.get("status_code", 0) or 0)
    if status in {403, 404}:
        return f"cannot create PR from this context. Create PR manually from `{patch_branch}`."
    return f"auto-pr failed (status={status}). Create PR manually from `{patch_branch}`."


def _is_bot_login(login: str) -> bool:
    normalized = (login or "").strip().lower()
    return bool(normalized) and BOT_MARKER in normalized


def _build_post_client() -> GitHubClient:
    repo = extract_repo_from_env()
    token = str(_runtime_env_cfg().workflow.github_token or "").strip()
    if not token:
        token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not repo:
        raise ValueError("GITHUB_REPOSITORY is required when dry_run=False")
    if not token:
        raise ValueError("GITHUB_TOKEN is required when dry_run=False")
    return GitHubClient(repo=repo, token=token)


def _internal_reactions_enabled() -> bool:
    return not bool(_runtime_env_cfg().workflow.disable_internal_reactions)


def _provider_engine_name(provider: Any) -> str:
    if isinstance(provider, RemoteTKYProvider):
        return "remote"
    if isinstance(provider, LocalTKYProvider):
        return "topocore_local"
    return "baseline"


def _local_engine_name_from_result(result: Any) -> str | None:
    tky = getattr(result, "tky", None)
    compression_stats = getattr(tky, "compression_stats", {})
    if not isinstance(compression_stats, dict):
        return None
    value = compression_stats.get("tky_engine_local")
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _default_rd_summary(*, status: str = "n/a") -> dict[str, Any]:
    return {
        "rd_used": False,
        "rd_status": status,
        "rd_template_id": "n/a",
        "rd_intent_hash": "n/a",
        "rd_policy_hash": "n/a",
        "rd_has_signature": False,
        "rd_has_attestation": False,
        "rd_error_count": 0,
        "rd_warning_count": 0,
        "rd_record_hash": "n/a",
    }


def _extract_rd_summary_from_result(result: Any) -> dict[str, Any]:
    tky = getattr(result, "tky", None)
    compression_stats = getattr(tky, "compression_stats", {})
    if not isinstance(compression_stats, dict):
        return _default_rd_summary(status="n/a")
    summary = _default_rd_summary(status="n/a")
    for key in (
        "rd_used",
        "rd_status",
        "rd_template_id",
        "rd_intent_hash",
        "rd_policy_hash",
        "rd_has_signature",
        "rd_has_attestation",
        "rd_error_count",
        "rd_warning_count",
        "rd_record_hash",
    ):
        if key in compression_stats:
            summary[key] = compression_stats[key]
    return summary


def _extract_rd_summary_from_audit_summary(audit_summary: dict[str, Any]) -> dict[str, Any]:
    raw = audit_summary.get("rd", {})
    if isinstance(raw, dict) and raw:
        return dict(raw)

    summary = _default_rd_summary(status="n/a")
    for key in summary:
        if key in audit_summary:
            summary[key] = audit_summary[key]
    return summary


def decide_remote_usage(
    *,
    cfg: RepoBrainConfig,
    cmd: str,
    repo_name: str,
    branch_name: str,
    remote_url: str,
) -> tuple[bool, str | None]:
    """Decide if remote TKY can be used and return precise reason code when skipped."""
    if not bool(getattr(cfg, "tky_remote_enabled", False)):
        return False, "remote_disabled_by_config"

    if not (remote_url or "").strip():
        return False, "remote_url_missing"

    allowed_commands = [
        str(item).strip().lower()
        for item in getattr(cfg, "tky_remote_allow_commands", ("ask", "explain"))
        if str(item).strip()
    ]
    if allowed_commands and cmd.strip().lower() not in allowed_commands:
        return False, "command_not_allowed"

    allowed_branches = [
        str(item).strip().lower()
        for item in getattr(cfg, "tky_remote_allow_branches", ("main",))
        if str(item).strip()
    ]
    if allowed_branches and branch_name.strip().lower() not in allowed_branches:
        return False, "branch_not_allowed"

    allowed_repos = [
        str(item).strip().lower()
        for item in getattr(cfg, "tky_remote_allow_repos", ())
        if str(item).strip()
    ]
    if allowed_repos and repo_name.strip().lower() not in allowed_repos:
        return False, "repo_not_allowed"

    return True, None


def resolve_tky_mode(
    *,
    requested_mode: str,
    cfg: RepoBrainConfig,
    cmd: str,
    repo_name: str,
    branch_name: str,
    remote_url_input: str,
) -> tuple[str, str | None, str]:
    """Resolve requested TKY mode into used mode + skip reason + effective remote URL."""
    mode = (requested_mode or "auto").strip().lower()
    effective_remote_url = (remote_url_input or "").strip() or str(getattr(cfg, "tky_remote_url", "") or "").strip()

    if mode == "baseline":
        return "baseline", None, ""
    if mode == "local":
        return "local", None, ""
    if mode not in {"remote", "auto"}:
        return "baseline", None, ""

    use_remote, reason = decide_remote_usage(
        cfg=cfg,
        cmd=cmd,
        repo_name=repo_name,
        branch_name=branch_name,
        remote_url=effective_remote_url,
    )
    if use_remote:
        return "remote", None, effective_remote_url
    return "baseline", reason, ""


def _build_refuse_answer_result(question: str, reason: str) -> AnswerResult:
    tky = TKYResult(
        selected_chunk_ids=[],
        route="REFUSE",
        compression_stats={"retrieved": 0, "selected": 0},
        rationale=reason,
        execution_mode="refuse",
        llm_intent="none",
        llm_decision_reason_short="LLM not used: request refused by security policy.",
        llm_decision_reason_code="ROUTE_REFUSE_OR_BLOCK",
    )
    answer = (
        f"Question: {question}\n"
        "Route: REFUSE\n"
        "Selected sources: 0\n"
        f"Rationale: {reason}"
    )
    return AnswerResult(
        answer_text=answer,
        evidence=[],
        tky=tky,
        audit_summary={
            "retrieved": 0,
            "selected": 0,
            "route": "REFUSE",
            "execution_mode": "refuse",
            "llm_intent": "none",
            "llm_decision_reason_short": "LLM not used: request refused by security policy.",
            "llm_decision_reason_code": "ROUTE_REFUSE_OR_BLOCK",
        },
        next_steps="Open evidence links and verify logic",
    )


def _build_wait_answer_result(question: str, reason: str) -> AnswerResult:
    tky = TKYResult(
        selected_chunk_ids=[],
        route="WAIT",
        compression_stats={"retrieved": 0, "selected": 0},
        rationale=reason,
        execution_mode="verification_first",
        llm_intent="none",
        llm_decision_reason_short="LLM not used: verification required before answer.",
        llm_decision_reason_code="ROUTE_WAIT_VERIFICATION",
    )
    answer = (
        f"Question: {question}\n"
        "Route: WAIT\n"
        "Status: Verification is pending\n"
        "Selected sources: 0\n"
        f"Rationale: {reason}"
    )
    return AnswerResult(
        answer_text=answer,
        evidence=[],
        tky=tky,
        audit_summary={
            "retrieved": 0,
            "selected": 0,
            "route": "WAIT",
            "execution_mode": "verification_first",
            "llm_intent": "none",
            "llm_decision_reason_short": "LLM not used: verification required before answer.",
            "llm_decision_reason_code": "ROUTE_WAIT_VERIFICATION",
        },
        next_steps="Verification is pending. Re-run after checks complete.",
    )


def _canonical_route(route: str) -> str:
    normalized = str(route or "").strip().upper()
    if normalized in {"FAST", "DEEP", "REVIEW", "REFUSE", "WAIT"}:
        return normalized
    if normalized in {"BLOCK", "DENY", "REJECT"}:
        return "BLOCK"
    if normalized in {"PENDING", "VERIFY_PENDING"}:
        return "WAIT"
    return "FAST"


def _execution_from_tky_result(tky: TKYResult) -> dict[str, str]:
    execution = coerce_execution_decision(
        route=tky.route,
        execution_mode=getattr(tky, "execution_mode", None),
        llm_intent=getattr(tky, "llm_intent", None),
        reason_short=getattr(tky, "llm_decision_reason_short", None),
        reason_code=getattr(tky, "llm_decision_reason_code", None),
    )
    return {
        "execution_mode": execution.execution_mode,
        "llm_intent": execution.llm_intent,
        "llm_decision_reason_short": execution.reason_short,
        "llm_decision_reason_code": execution.reason_code,
    }


def _runtime_override_reason_from_skip(skip_reason: str) -> str:
    reason = str(skip_reason or "n/a")
    lowered = reason.lower()
    if reason in {"n/a", ""}:
        return "n/a"
    if lowered == "disabled":
        return "LLM blocked: disabled by runtime policy."
    if lowered == "missing_github_token":
        return "LLM blocked: missing GitHub token."
    if lowered == "locate_disabled":
        return "LLM blocked: locate mode is disabled by runtime policy."
    if lowered == "issue_comment_policy_disabled":
        return "LLM blocked: issue_comment policy disabled."
    if lowered == "pr_comment_policy_disabled":
        return "LLM blocked: PR comment LLM policy disabled."
    if lowered == "issue_only_policy_disabled":
        return "LLM blocked: non-PR issue LLM policy disabled."
    if lowered.startswith("budget:"):
        return f"LLM blocked: {reason[7:]}"
    if lowered.startswith("llm_not_available:"):
        provider_reason = reason.split(":", 1)[1]
        return f"LLM blocked: provider unavailable ({provider_reason})."
    if lowered.startswith("execution_mode="):
        return "n/a"
    return f"LLM blocked: {reason}."


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
    """Load prebuilt index, or build and persist it if missing."""
    chunks, _, _, _, _ = _normalize_chunks_meta(
        load_or_build_chunks_with_meta(repo_root, index_path)
    )
    return chunks


def load_or_build_chunks_with_meta(
    repo_root: Path,
    index_path: Path,
    governor: AIBudgetGovernor | None = None,
) -> tuple[list[CandidateChunk], str, float, dict[str, list[float]], dict[str, Any]]:
    """Load/build index and return chunks, source, elapsed_ms, vectors, vectors_meta."""
    started = time.perf_counter()
    existed_before = index_path.exists()
    cache_restored = bool(_runtime_env_cfg().workflow.index_cache_restored)

    if existed_before:
        chunks = load_index(index_path)
        vectors, vectors_meta = load_index_embeddings(index_path)
        source = "cache_hit" if cache_restored else "artifact_present"
        return chunks, source, (time.perf_counter() - started) * 1000.0, vectors, vectors_meta

    index_path.parent.mkdir(parents=True, exist_ok=True)
    env_cfg = _runtime_env_cfg()
    if governor is None:
        try:
            build_index(root=repo_root, out_zip=index_path, store_text=False, cfg=env_cfg)
        except TypeError:
            build_index(root=repo_root, out_zip=index_path, store_text=False)
    else:
        try:
            build_index(
                root=repo_root,
                out_zip=index_path,
                store_text=False,
                governor=governor,
                cfg=env_cfg,
            )
        except TypeError:
            build_index(
                root=repo_root,
                out_zip=index_path,
                store_text=False,
                governor=governor,
            )
    chunks = load_index(index_path)
    vectors, vectors_meta = load_index_embeddings(index_path)
    return chunks, "rebuilt", (time.perf_counter() - started) * 1000.0, vectors, vectors_meta


def _normalize_chunks_meta(
    value: tuple[Any, ...] | list[Any],
) -> tuple[list[CandidateChunk], str, float, dict[str, list[float]], dict[str, Any]]:
    """Normalize old/new load_or_build_chunks_with_meta return signatures."""
    if isinstance(value, tuple) and len(value) == 5:
        chunks, source, elapsed_ms, vectors, vectors_meta = value
        return (
            list(chunks),
            str(source),
            float(elapsed_ms),
            dict(vectors),
            dict(vectors_meta),
        )
    if isinstance(value, tuple) and len(value) == 3:
        chunks, source, elapsed_ms = value
        return list(chunks), str(source), float(elapsed_ms), {}, {"enabled": False}
    if isinstance(value, list) and len(value) == 5:
        chunks, source, elapsed_ms, vectors, vectors_meta = value
        return (
            list(chunks),
            str(source),
            float(elapsed_ms),
            dict(vectors),
            dict(vectors_meta),
        )
    if isinstance(value, list) and len(value) == 3:
        chunks, source, elapsed_ms = value
        return list(chunks), str(source), float(elapsed_ms), {}, {"enabled": False}
    raise ValueError("Unsupported chunks metadata shape")


def should_build_index(index_path: Path) -> bool:
    """Return True when index file is missing and needs to be built."""
    return not index_path.exists()


def _top_score(candidates: list[CandidateChunk]) -> float:
    return float(candidates[0].score) if candidates else 0.0


def _route_hint_for_candidates(candidates: list[CandidateChunk], min_score_fast: float) -> str:
    return "DEEP" if _top_score(candidates) < float(min_score_fast) else "FAST"


def _second_score(candidates: list[CandidateChunk]) -> float:
    return float(candidates[1].score) if len(candidates) > 1 else 0.0


def _selection_policy_for_candidates(
    *,
    cmd: str,
    candidates: list[CandidateChunk],
    cfg: Any,
    phase: str,
) -> dict[str, Any]:
    top_score = _top_score(candidates)
    gap = top_score - _second_score(candidates)
    min_keep_base = float(getattr(cfg, "min_score_keep", 0.02))

    if phase == "deep":
        max_sources = int(getattr(cfg, "max_sources_deep", 12))
    else:
        max_sources = int(getattr(cfg, "max_sources_fast", getattr(cfg, "max_sources", 6)))

    keep_ratio = 0.30
    max_per_file = 2
    max_files = max_sources

    if cmd == "ask":
        keep_ratio = 0.35
        if gap > 0.08:
            max_sources = min(max_sources, 3)
    elif cmd == "explain":
        keep_ratio = 0.25
        max_per_file = 1
    elif cmd == "locate":
        keep_ratio = 0.30
        max_per_file = 1
        max_files = 5
        max_sources = min(max_sources, 5)

    min_score_keep = max(min_keep_base, top_score * keep_ratio)
    return {
        "max_sources": max_sources,
        "min_score_keep": min_score_keep,
        "keep_ratio": keep_ratio,
        "max_per_file": max_per_file,
        "max_files": max_files,
    }


def _retrieve_candidates_with_runtime(
    question: str,
    chunks: list[CandidateChunk],
    *,
    topk: int,
    cmd: str,
    chunk_vectors_by_id: dict[str, list[float]] | None = None,
    query_vector: list[float] | None = None,
    github_context: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> tuple[list[CandidateChunk], dict[str, Any]]:
    vectors = chunk_vectors_by_id or {}
    incremental_scope = scope_chunks_incremental(
        question=question,
        command=cmd,
        chunks=chunks,
        github_context=github_context,
        repo_root=repo_root,
    )
    scoped_chunks = incremental_scope.chunks
    base_mode = "lexical"
    retrieval_runtime: dict[str, Any] = {
        "incremental_retrieval_used": bool(incremental_scope.incremental_retrieval_used),
        "incremental_scope_mode": str(incremental_scope.incremental_scope_mode or "fallback_full"),
        "changed_files_considered": int(incremental_scope.changed_files_considered),
        "changed_regions_considered": int(incremental_scope.changed_regions_considered),
        "unchanged_files_skipped": int(incremental_scope.unchanged_files_skipped),
        "unchanged_chunks_skipped": int(incremental_scope.unchanged_chunks_skipped),
        "retrieval_cache_hits": int(incremental_scope.retrieval_cache_hits),
        "retrieval_cache_misses": int(incremental_scope.retrieval_cache_misses),
        "incremental_fallback_reason": str(incremental_scope.incremental_fallback_reason or "none"),
    }
    if vectors and query_vector:
        env_cfg = _runtime_env_cfg()
        vector_topk = int(env_cfg.embeddings.vector_topk)
        w_lex = float(env_cfg.embeddings.weight_lexical)
        w_vec = float(env_cfg.embeddings.weight_vector)
        total = w_lex + w_vec
        if total <= 0.0:
            w_lex, w_vec = 0.55, 0.45
        else:
            w_lex, w_vec = w_lex / total, w_vec / total
        hybrid = rank_hybrid_candidates(
            question=question,
            chunks=scoped_chunks,
            topk=topk,
            task_type=cmd,
            chunk_vectors_by_id=vectors,
            query_vector=query_vector,
            weight_lex=w_lex,
            weight_vec=w_vec,
            vector_topk=vector_topk,
            max_per_file=2,
        )
        base_mode = "hybrid"
        retrieval_runtime.update(
            {
            "retrieval_mode": "hybrid",
            "query_embedded": True,
            "index_vectors_loaded": True,
            "index_vectors_used": bool(hybrid.embeddings_used),
            "chunks_with_vectors": len(vectors),
            "evidence_reason": str(hybrid.reason or "n/a"),
            "vector_topk_used": int(hybrid.vector_topk),
            }
        )
        base_candidates = hybrid.candidates
    else:
        if cmd == "ask":
            base_candidates = retrieve_topk(question, scoped_chunks, topk=topk)
        else:
            base_candidates = retrieve_topk_pro(
                question,
                scoped_chunks,
                topk=topk,
                task_type=cmd,
                max_per_file=2,
            )
        retrieval_runtime.update(
            {
            "retrieval_mode": "lexical",
            "query_embedded": bool(query_vector),
            "index_vectors_loaded": bool(vectors),
            "index_vectors_used": False,
            "chunks_with_vectors": len(vectors),
            "evidence_reason": "query_vector_missing" if not query_vector else "index_vectors_not_loaded",
            "vector_topk_used": 0,
            }
        )

    rerank = rerank_candidates(
        base_candidates,
        query_context={
            "question": question,
            "command": cmd,
            "changed_files": list((github_context or {}).get("changed_files", []) or []),
        },
    )
    filtered = filter_candidate_evidence(
        rerank.candidates,
        command=cmd,
        query=question,
        max_items=max(1, int(topk)),
    )
    segment_hints: dict[str, Any] | None = None
    file_map_raw = (github_context or {}).get("pr_segmentation_file_map", {})
    if isinstance(file_map_raw, dict) and file_map_raw:
        segment_hints = {
            "file_segment_class_map": {
                str(path).strip(): str(segment_class).strip()
                for path, segment_class in file_map_raw.items()
                if str(path).strip()
            }
        }
    budget_plan = plan_evidence_budget(
        filtered.candidates,
        command=cmd,
        github_context=github_context,
        limit_hint=max(1, int(topk)),
        incremental_scope_mode=str(retrieval_runtime.get("incremental_scope_mode", "fallback_full")),
        segment_hints=segment_hints,
    )
    retrieval_runtime["hybrid_rerank_used"] = bool(rerank.hybrid_rerank_used)
    mode_suffix = rerank.retrieval_ranking_mode
    retrieval_runtime["retrieval_ranking_mode"] = (
        f"{base_mode}+{mode_suffix}"
        if mode_suffix not in {"fallback_lexical", "passthrough"}
        else f"{base_mode}" if mode_suffix == "passthrough" else mode_suffix
    )
    retrieval_runtime["evidence_filtered_count"] = int(filtered.filtered_count)
    retrieval_runtime["evidence_filter_reason_codes"] = sorted(filtered.reason_codes) or ["none"]
    retrieval_runtime["evidence_budget_used"] = int(budget_plan.evidence_budget_used)
    retrieval_runtime["evidence_budget_limit"] = int(budget_plan.evidence_budget_limit)
    retrieval_runtime["evidence_budget_mode"] = str(budget_plan.evidence_budget_mode or "not_applied")
    retrieval_runtime["evidence_budget_bucket_counts"] = ",".join(
        f"{bucket}:{int(count)}"
        for bucket, count in budget_plan.evidence_budget_bucket_counts.items()
    ) or "changed_primary:0,changed_secondary:0,support_context:0,tests:0,docs:0,workflow_config:0"
    retrieval_runtime["evidence_budget_cutoffs"] = list(budget_plan.evidence_budget_cutoffs or ["no_cutoff"])
    retrieval_runtime["evidence_budget_overflow"] = int(budget_plan.evidence_budget_overflow)
    retrieval_runtime["evidence_budget_primary_selected"] = int(budget_plan.evidence_budget_primary_selected)
    retrieval_runtime["evidence_budget_support_selected"] = int(budget_plan.evidence_budget_support_selected)
    return budget_plan.candidates, retrieval_runtime


def _retrieve_candidates(
    question: str,
    chunks: list[CandidateChunk],
    *,
    topk: int,
    cmd: str,
    chunk_vectors_by_id: dict[str, list[float]] | None = None,
    query_vector: list[float] | None = None,
) -> list[CandidateChunk]:
    candidates, _ = _retrieve_candidates_with_runtime(
        question,
        chunks,
        topk=topk,
        cmd=cmd,
        chunk_vectors_by_id=chunk_vectors_by_id,
        query_vector=query_vector,
        github_context=None,
        repo_root=None,
    )
    return candidates


def retrieve_topk(
    question: str,
    chunks: list[CandidateChunk],
    topk: int,
) -> list[CandidateChunk]:
    """Compatibility wrapper used by existing tests and default ask retrieval."""
    return retrieve_topk_pro(question, chunks, topk=topk, task_type="ask", max_per_file=2)


def _qa_limits(
    *,
    cmd: str,
    max_sources: int,
    min_score_keep: float,
    keep_ratio: float,
    max_per_file: int,
    max_files: int,
    route_hint: str,
    topk_current: int,
    topk_fast: int,
    topk_deep: int,
    time_budget_s: int,
    perf_max_candidates: int,
    perf_max_series: int,
    perf_max_vectors: int,
    perf_max_edges: int,
    perf_max_paths: int,
    github_context: dict[str, Any] | None = None,
    verification_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    env_cfg = _runtime_env_cfg()
    policy: dict[str, Any] = {
        "no_raw_text": True,
        "privacy_mode": "signatures_only",
        "github_context": dict(github_context or {}),
        "verification_context": dict(verification_context or {}),
        "runtime": {
            "mode": "ci" if env_cfg.workflow.github_actions else "local",
            "network_allowed": bool(env_cfg.tkya.allow_remote),
        },
    }
    return {
        "max_sources": max_sources,
        "min_score_keep": min_score_keep,
        "keep_ratio": keep_ratio,
        "max_per_file": max_per_file,
        "max_files": max_files,
        "top_k": topk_current,
        "topk_fast": topk_fast,
        "topk_deep": topk_deep,
        "time_budget_s": time_budget_s,
        "tky_perf_max_candidates": perf_max_candidates,
        "tky_perf_max_series": perf_max_series,
        "tky_perf_max_vectors": perf_max_vectors,
        "tky_perf_max_edges": perf_max_edges,
        "tky_perf_max_paths": perf_max_paths,
        "route_hint": route_hint,
        "task_type": cmd,
        "privacy_mode": "signatures_only",
        "policy": policy,
        "repo_ctx": {
            "repo": extract_repo_from_env(),
            "sha": extract_sha_from_env(),
        },
    }


def _answer_with_remote_fallback(
    *,
    question: str,
    candidates: list[CandidateChunk],
    limits: dict[str, Any],
    provider: Any,
    tky_mode_requested: str,
    remote_fail_open: bool,
) -> tuple[Any, Any, dict[str, Any]]:
    """Run `answer_question`, falling back to baseline if remote provider fails."""
    engine_name = _provider_engine_name(provider)
    meta: dict[str, Any] = {
        "tky_mode_requested": tky_mode_requested,
        "tky_mode_used": tky_mode_requested,
        "remote_used": tky_mode_requested == "remote",
        "tky_engine": engine_name,
        "tky_fallback_reason": "n/a",
        "fallback_reason_code": "n/a",
        "tky_remote_status": None,
        "remote_latency_ms": None,
        "remote_retry_count": 0,
        "remote_rate_limited": False,
        "remote_error_class": "n/a",
    }
    active_provider = provider

    try:
        result = answer_question(
            question=question,
            candidates=candidates,
            provider=active_provider,
            limits=limits,
        )
        if isinstance(active_provider, RemoteTKYProvider):
            meta["tky_remote_status"] = active_provider.last_status_code
            diagnostics = active_provider.last_diagnostics
            if diagnostics is not None:
                meta["remote_latency_ms"] = diagnostics.latency_ms
                meta["remote_retry_count"] = diagnostics.retry_count
                meta["remote_rate_limited"] = diagnostics.rate_limited
                meta["remote_error_class"] = diagnostics.error_class or "n/a"
                meta["fallback_reason_code"] = diagnostics.fallback_reason_code or "n/a"
            meta["remote_used"] = True
            meta["tky_engine"] = "remote"
        elif isinstance(active_provider, LocalTKYProvider):
            meta["tky_engine"] = _local_engine_name_from_result(result) or "topocore_lite"
            meta["remote_used"] = False
        else:
            meta["tky_engine"] = "baseline"
            meta["remote_used"] = False
        return result, active_provider, meta
    except RemoteTKYError as exc:
        if tky_mode_requested != "remote":
            raise
        diagnostics = exc.diagnostics
        if diagnostics is not None:
            meta["remote_latency_ms"] = diagnostics.latency_ms
            meta["remote_retry_count"] = diagnostics.retry_count
            meta["remote_rate_limited"] = diagnostics.rate_limited
            meta["remote_error_class"] = diagnostics.error_class or "n/a"
        fallback_provider = make_provider("baseline")
        meta["tky_remote_status"] = exc.status_code
        meta["fallback_reason_code"] = exc.fallback_reason_code or "REMOTE_NETWORK"
        meta["remote_error_class"] = exc.error_class or "unknown"
        if not remote_fail_open:
            refuse = _build_refuse_answer_result(
                question,
                "Remote TKY unavailable and fail-open disabled by policy.",
            )
            meta["tky_mode_used"] = "remote"
            meta["remote_used"] = True
            meta["tky_engine"] = "remote"
            meta["tky_fallback_reason"] = "remote_refuse"
            return refuse, active_provider, meta
        result = answer_question(
            question=question,
            candidates=candidates,
            provider=fallback_provider,
            limits=limits,
        )
        meta["tky_mode_used"] = "fallback_baseline"
        meta["remote_used"] = False
        meta["tky_fallback_reason"] = "remote_error"
        meta["tky_engine"] = "baseline"
        return result, fallback_provider, meta


def run_qa_two_pass(
    *,
    question: str,
    cmd: str,
    chunks: list[CandidateChunk],
    chunk_vectors_by_id: dict[str, list[float]] | None = None,
    query_vector: list[float] | None = None,
    provider: Any,
    cfg: Any,
    tky_mode_requested: str = "baseline",
    remote_fail_open: bool = True,
    timings_ms: dict[str, float] | None = None,
    github_context: dict[str, Any] | None = None,
    verification_context: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Run at most two retrieval+TKY passes using the TKY route from pass 1."""
    topk_fast = int(getattr(cfg, "topk_fast", getattr(cfg, "topk", 30)))
    topk_deep = int(getattr(cfg, "topk_deep", 80))
    min_score_fast = float(getattr(cfg, "min_score_fast", 0.05))
    time_budget_s = int(getattr(cfg, "time_budget_s", 30))
    perf_max_candidates = int(getattr(cfg, "tky_perf_max_candidates", 800))
    perf_max_series = int(getattr(cfg, "tky_perf_max_series", 4096))
    perf_max_vectors = int(getattr(cfg, "tky_perf_max_vectors", 2048))
    perf_max_edges = int(getattr(cfg, "tky_perf_max_edges", 4096))
    perf_max_paths = int(getattr(cfg, "tky_perf_max_paths", 4096))
    active_provider = provider
    t0 = time.perf_counter()
    pass1_candidates, pass1_retrieval_runtime = _retrieve_candidates_with_runtime(
        question,
        chunks,
        topk=topk_fast,
        cmd=cmd,
        chunk_vectors_by_id=chunk_vectors_by_id,
        query_vector=query_vector,
        github_context=github_context,
        repo_root=repo_root,
    )
    if timings_ms is not None:
        timings_ms["retrieve_pass1"] = round((time.perf_counter() - t0) * 1000.0, 3)
    pass1_top_score = _top_score(pass1_candidates)
    pass1_policy = _selection_policy_for_candidates(
        cmd=cmd,
        candidates=pass1_candidates,
        cfg=cfg,
        phase="fast",
    )
    pass1_limits = _qa_limits(
        cmd=cmd,
        max_sources=int(pass1_policy["max_sources"]),
        min_score_keep=float(pass1_policy["min_score_keep"]),
        keep_ratio=float(pass1_policy["keep_ratio"]),
        max_per_file=int(pass1_policy["max_per_file"]),
        max_files=int(pass1_policy["max_files"]),
        route_hint=_route_hint_for_candidates(pass1_candidates, min_score_fast),
        topk_current=topk_fast,
        topk_fast=topk_fast,
        topk_deep=topk_deep,
        time_budget_s=time_budget_s,
        perf_max_candidates=perf_max_candidates,
        perf_max_series=perf_max_series,
        perf_max_vectors=perf_max_vectors,
        perf_max_edges=perf_max_edges,
        perf_max_paths=perf_max_paths,
        github_context=github_context,
        verification_context=verification_context,
    )
    t0 = time.perf_counter()
    result1, active_provider, pass1_meta = _answer_with_remote_fallback(
        question=question,
        candidates=pass1_candidates,
        limits=pass1_limits,
        provider=active_provider,
        tky_mode_requested=tky_mode_requested,
        remote_fail_open=remote_fail_open,
    )
    if timings_ms is not None:
        timings_ms["tky_pass1"] = round((time.perf_counter() - t0) * 1000.0, 3)

    final_result = result1
    final_meta = dict(pass1_meta)
    final_retrieval_runtime = dict(pass1_retrieval_runtime)
    pass_count = 1
    pass2_top_score: float | None = None

    route1 = _canonical_route(result1.tky.route)
    if route1 in {"REFUSE", "BLOCK"}:
        final_result = _build_refuse_answer_result(
            question,
            result1.tky.rationale or "Request blocked by TKY route.",
        )
    elif route1 == "WAIT":
        final_result = _build_wait_answer_result(
            question,
            result1.tky.rationale or "Verification is pending.",
        )

    should_second_pass = (
        cmd in {"ask", "explain"}
        and route1 == "DEEP"
        and final_result.tky.route not in {"REFUSE", "WAIT"}
    )
    if should_second_pass:
        t0 = time.perf_counter()
        pass2_candidates, pass2_retrieval_runtime = _retrieve_candidates_with_runtime(
            question,
            chunks,
            topk=topk_deep,
            cmd=cmd,
            chunk_vectors_by_id=chunk_vectors_by_id,
            query_vector=query_vector,
            github_context=github_context,
            repo_root=repo_root,
        )
        if timings_ms is not None:
            timings_ms["retrieve_pass2"] = round((time.perf_counter() - t0) * 1000.0, 3)
        pass2_top_score = _top_score(pass2_candidates)
        pass2_policy = _selection_policy_for_candidates(
            cmd=cmd,
            candidates=pass2_candidates,
            cfg=cfg,
            phase="deep",
        )
        pass2_limits = _qa_limits(
            cmd=cmd,
            max_sources=int(pass2_policy["max_sources"]),
            min_score_keep=float(pass2_policy["min_score_keep"]),
            keep_ratio=float(pass2_policy["keep_ratio"]),
            max_per_file=int(pass2_policy["max_per_file"]),
            max_files=int(pass2_policy["max_files"]),
            route_hint="DEEP",
            topk_current=topk_deep,
            topk_fast=topk_fast,
            topk_deep=topk_deep,
            time_budget_s=time_budget_s,
            perf_max_candidates=perf_max_candidates,
            perf_max_series=perf_max_series,
            perf_max_vectors=perf_max_vectors,
            perf_max_edges=perf_max_edges,
            perf_max_paths=perf_max_paths,
            github_context=github_context,
            verification_context=verification_context,
        )
        t0 = time.perf_counter()
        final_result, active_provider, pass2_meta = _answer_with_remote_fallback(
            question=question,
            candidates=pass2_candidates,
            limits=pass2_limits,
            provider=active_provider,
            tky_mode_requested=tky_mode_requested,
            remote_fail_open=remote_fail_open,
        )
        if timings_ms is not None:
            timings_ms["tky_pass2"] = round((time.perf_counter() - t0) * 1000.0, 3)
        final_meta.update(pass2_meta)
        final_retrieval_runtime = dict(pass2_retrieval_runtime)
        pass_count = 2

    final_route = _canonical_route(final_result.tky.route)
    if final_route in {"REFUSE", "BLOCK"} and final_result.tky.route != "REFUSE":
        final_result = _build_refuse_answer_result(
            question,
            final_result.tky.rationale or "Request blocked by TKY route.",
        )
        final_route = "REFUSE"
    elif final_route == "WAIT" and final_result.tky.route != "WAIT":
        final_result = _build_wait_answer_result(
            question,
            final_result.tky.rationale or "Verification is pending.",
        )
        final_route = "WAIT"

    audit_extra: dict[str, Any] = {
        "pass_count": pass_count,
        "pass1.top_score": round(pass1_top_score, 6),
        "route_final": final_route,
        "top_score": round(pass2_top_score if pass2_top_score is not None else pass1_top_score, 6),
    }
    audit_extra.update(_execution_from_tky_result(final_result.tky))
    if pass2_top_score is not None:
        audit_extra["pass2.top_score"] = round(pass2_top_score, 6)
        audit_extra["top_score_pass2"] = round(pass2_top_score, 6)
    audit_extra["hybrid_rerank_used"] = bool(final_retrieval_runtime.get("hybrid_rerank_used", False))
    audit_extra["retrieval_ranking_mode"] = str(
        final_retrieval_runtime.get("retrieval_ranking_mode", final_retrieval_runtime.get("retrieval_mode", "lexical"))
        or "lexical"
    )
    audit_extra["evidence_filtered_count"] = int(final_retrieval_runtime.get("evidence_filtered_count", 0) or 0)
    filter_codes = final_retrieval_runtime.get("evidence_filter_reason_codes", ["none"])
    if not isinstance(filter_codes, list):
        filter_codes = [str(filter_codes)]
    audit_extra["evidence_filter_reason_codes"] = ",".join(
        str(item).strip() for item in filter_codes if str(item).strip()
    ) or "none"
    audit_extra["incremental_retrieval_used"] = bool(
        final_retrieval_runtime.get("incremental_retrieval_used", False)
    )
    audit_extra["incremental_scope_mode"] = str(
        final_retrieval_runtime.get("incremental_scope_mode", "fallback_full") or "fallback_full"
    )
    audit_extra["changed_files_considered"] = int(
        final_retrieval_runtime.get("changed_files_considered", 0) or 0
    )
    audit_extra["changed_regions_considered"] = int(
        final_retrieval_runtime.get("changed_regions_considered", 0) or 0
    )
    audit_extra["unchanged_files_skipped"] = int(
        final_retrieval_runtime.get("unchanged_files_skipped", 0) or 0
    )
    audit_extra["unchanged_chunks_skipped"] = int(
        final_retrieval_runtime.get("unchanged_chunks_skipped", 0) or 0
    )
    audit_extra["retrieval_cache_hits"] = int(
        final_retrieval_runtime.get("retrieval_cache_hits", 0) or 0
    )
    audit_extra["retrieval_cache_misses"] = int(
        final_retrieval_runtime.get("retrieval_cache_misses", 0) or 0
    )
    audit_extra["incremental_fallback_reason"] = str(
        final_retrieval_runtime.get("incremental_fallback_reason", "none") or "none"
    )
    audit_extra["evidence_budget_used"] = int(final_retrieval_runtime.get("evidence_budget_used", 0) or 0)
    audit_extra["evidence_budget_limit"] = int(final_retrieval_runtime.get("evidence_budget_limit", 0) or 0)
    audit_extra["evidence_budget_mode"] = str(
        final_retrieval_runtime.get("evidence_budget_mode", "not_applied") or "not_applied"
    )
    bucket_counts_value = final_retrieval_runtime.get(
        "evidence_budget_bucket_counts",
        "changed_primary:0,changed_secondary:0,support_context:0,tests:0,docs:0,workflow_config:0",
    )
    audit_extra["evidence_budget_bucket_counts"] = (
        bucket_counts_value
        if isinstance(bucket_counts_value, str)
        else str(bucket_counts_value)
    )
    cutoffs_raw = final_retrieval_runtime.get("evidence_budget_cutoffs", ["no_cutoff"])
    cutoffs_list = (
        [str(item).strip() for item in cutoffs_raw if str(item).strip()]
        if isinstance(cutoffs_raw, list)
        else [str(cutoffs_raw).strip()]
    )
    audit_extra["evidence_budget_cutoffs"] = ",".join(cutoffs_list) if cutoffs_list else "no_cutoff"
    audit_extra["evidence_budget_overflow"] = int(final_retrieval_runtime.get("evidence_budget_overflow", 0) or 0)
    audit_extra["evidence_budget_primary_selected"] = int(
        final_retrieval_runtime.get("evidence_budget_primary_selected", 0) or 0
    )
    audit_extra["evidence_budget_support_selected"] = int(
        final_retrieval_runtime.get("evidence_budget_support_selected", 0) or 0
    )
    query_embedded = bool(query_vector)
    vectors_loaded = bool(chunk_vectors_by_id)
    chunks_with_vectors = len(chunk_vectors_by_id or {})
    runtime_reason = str(final_retrieval_runtime.get("evidence_reason", "n/a") or "n/a")
    index_vectors_used = bool(final_retrieval_runtime.get("index_vectors_used", False))
    if query_embedded and vectors_loaded and index_vectors_used:
        runtime_reason = "index_vectors_used_for_hybrid_scoring"
    elif query_embedded and not vectors_loaded:
        runtime_reason = "query_embedded_but_no_index_vectors"
    elif query_embedded and vectors_loaded and not index_vectors_used:
        runtime_reason = "query_embedded_but_index_vectors_not_used"
    embeddings_runtime = {
        "query_embedded": query_embedded,
        "index_vectors_loaded": bool(final_retrieval_runtime.get("index_vectors_loaded", vectors_loaded)),
        "index_vectors_used": index_vectors_used,
        "chunks_with_vectors": int(final_retrieval_runtime.get("chunks_with_vectors", chunks_with_vectors) or 0),
        "embedding_model": "n/a",
        "evidence_reason": runtime_reason,
    }
    audit_extra["embeddings_runtime"] = embeddings_runtime
    audit_extra["index_vectors_used"] = bool(embeddings_runtime["index_vectors_used"])
    audit_extra["rd"] = _extract_rd_summary_from_result(final_result)

    if tky_mode_requested == "remote":
        audit_extra["tky_mode_requested"] = "remote"
        audit_extra["tky_mode_used"] = final_meta.get("tky_mode_used", "remote")
        audit_extra["remote_used"] = bool(final_meta.get("remote_used", False))
        audit_extra["tky_engine"] = str(final_meta.get("tky_engine", "remote"))
        remote_status = final_meta.get("tky_remote_status", None)
        if remote_status is not None:
            audit_extra["tky_remote_status"] = remote_status
        fallback_reason = str(final_meta.get("tky_fallback_reason", "") or "")
        if fallback_reason:
            audit_extra["tky_fallback_reason"] = fallback_reason
        audit_extra["fallback_reason_code"] = str(
            final_meta.get("fallback_reason_code", "n/a") or "n/a"
        )
        audit_extra["remote_error_class"] = str(
            final_meta.get("remote_error_class", "n/a") or "n/a"
        )
        audit_extra["remote_retry_count"] = int(final_meta.get("remote_retry_count", 0) or 0)
        audit_extra["remote_rate_limited"] = bool(final_meta.get("remote_rate_limited", False))
        audit_extra["remote_latency_ms"] = final_meta.get("remote_latency_ms")
    else:
        audit_extra["tky_mode_requested"] = tky_mode_requested
        audit_extra["tky_mode_used"] = tky_mode_requested
        audit_extra["tky_engine"] = str(
            final_meta.get("tky_engine", _provider_engine_name(active_provider))
        )
        audit_extra["remote_used"] = False
        audit_extra["fallback_reason_code"] = "n/a"
        audit_extra["remote_error_class"] = "n/a"
        audit_extra["remote_retry_count"] = 0
        audit_extra["remote_rate_limited"] = False
        audit_extra["remote_latency_ms"] = None

    return final_result, audit_extra


def _dedupe_evidence_by_file(evidence: list[EvidenceItem], max_files: int = 5) -> list[EvidenceItem]:
    result: list[EvidenceItem] = []
    seen: set[str] = set()
    for item in evidence:
        if item.file_path in seen:
            continue
        seen.add(item.file_path)
        result.append(item)
        if len(result) >= max_files:
            break
    return result


def _module_reason(file_path: str) -> str:
    lower = file_path.lower()
    if lower.endswith("tky_provider.py"):
        return "provider interface and TKY result contract"
    if lower.endswith("github_flow.py"):
        return "command orchestration and runtime flow"
    if lower.endswith("retrieve.py") or lower.endswith("retrieve_pro.py"):
        return "retrieval ranking and candidate filtering"
    if lower.endswith("review.py"):
        return "PR review heuristics and risk scoring"
    if lower.endswith("formatting.py"):
        return "final markdown formatting for responses"
    if lower.endswith("config.py"):
        return "runtime thresholds and limits"
    if lower.startswith("scripts/"):
        return "CLI and workflow entrypoint behavior"
    return "relevant to the requested behavior based on retrieval signals"


def _build_explain_answer(evidence: list[EvidenceItem], question: str) -> str:
    if not evidence:
        return (
            f"Question: {question}\n"
            "Key modules likely involved:\n"
            "- No strong module matches found."
        )

    modules = [item.file_path for item in evidence[:7]]
    lines = [f"Question: {question}", "Key modules likely involved:"]
    for path in modules:
        lines.append(f"- `{path}`")
    lines.append("")
    lines.append("Why:")
    for path in modules:
        lines.append(f"- `{path}` — {_module_reason(path)}")
    return "\n".join(lines)


def _collect_pr_changed_files_from_context(github_context: dict[str, Any] | None) -> list[str]:
    if not isinstance(github_context, dict):
        return []
    raw = github_context.get("changed_files", [])
    if not isinstance(raw, list):
        return []
    files = [str(item).strip() for item in raw if str(item).strip()]
    return sorted(set(files))


def _enrich_github_context_with_pr_metadata(
    *,
    github_context_seed: dict[str, Any] | None,
) -> dict[str, Any]:
    context = dict(github_context_seed or {})
    changed_files = _collect_pr_changed_files_from_context(context)
    pr_number = _parse_optional_int(context.get("pr_number"))
    is_pr = bool(context.get("is_pr", False) or pr_number is not None)
    context["is_pr"] = is_pr

    needs_files = is_pr and not changed_files
    needs_head_base = is_pr and (
        not str(context.get("head_sha", "") or "").strip()
        or not str(context.get("base_sha", "") or "").strip()
    )
    if not (needs_files or needs_head_base):
        return context

    repo = extract_repo_from_env()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not repo or not token or pr_number is None:
        return context

    client = GitHubClient(repo=repo, token=token)
    if needs_files:
        files_payload = client.get_pull_files(pr_number)
        files: list[str] = []
        diff_hunks: list[str] = []
        for item in files_payload:
            if not isinstance(item, dict):
                continue
            filename = str(item.get("filename", "") or "").strip()
            if filename:
                files.append(filename)
            patch = item.get("patch")
            if isinstance(patch, str):
                patch_clean = patch.strip()
                if patch_clean:
                    diff_hunks.append(patch_clean)
        if files:
            context["changed_files"] = sorted(set(files))
        existing_hunks = context.get("diff_hunks")
        has_hunks = isinstance(existing_hunks, list) and any(str(item).strip() for item in existing_hunks)
        if diff_hunks and not has_hunks:
            context["diff_hunks"] = diff_hunks

    if needs_head_base:
        pull_payload = client.get_pull(pr_number)
        head_raw = pull_payload.get("head", {}) if isinstance(pull_payload, dict) else {}
        base_raw = pull_payload.get("base", {}) if isinstance(pull_payload, dict) else {}
        head = head_raw if isinstance(head_raw, dict) else {}
        base = base_raw if isinstance(base_raw, dict) else {}
        if not str(context.get("head_sha", "") or "").strip():
            context["head_sha"] = str(head.get("sha", "") or "")
        if not str(context.get("base_sha", "") or "").strip():
            context["base_sha"] = str(base.get("sha", "") or "")
        if not str(context.get("head_ref", "") or "").strip():
            context["head_ref"] = str(head.get("ref", "") or "")
        if not str(context.get("base_ref", "") or "").strip():
            context["base_ref"] = str(base.get("ref", "") or "")

    return context


def _should_use_pr_metadata_grounding(
    *,
    cmd: str,
    question: str,
    github_context: dict[str, Any] | None,
    execution_mode: str,
    llm_intent: str,
) -> bool:
    if cmd not in {"ask", "explain"}:
        return False
    changed_files = _collect_pr_changed_files_from_context(github_context)
    if not changed_files:
        return False
    if not isinstance(github_context, dict) or not bool(github_context.get("is_pr", False)):
        return False

    intent_norm = str(llm_intent or "").strip().lower()
    mode_norm = str(execution_mode or "").strip().lower()
    if intent_norm in {"summarize", "review", "explain"}:
        return True
    if mode_norm == "retrieval_plus_llm":
        return True

    question_norm = str(question or "").strip().lower()
    semantic_markers = (
        "pr",
        "pull request",
        "diff",
        "change",
        "changed",
        "file",
        "files",
        "измен",
        "файл",
        "пул",
    )
    return any(marker in question_norm for marker in semantic_markers)


def _prepend_pr_metadata_to_answer(
    *,
    answer_text: str,
    changed_files: list[str],
    primary_segments: str = "none",
    segment_summary: str = "none",
) -> str:
    if not changed_files:
        return answer_text
    lines = ["PR metadata (changed files):"]
    if str(primary_segments or "none") != "none":
        lines.append(f"- Primary segments: {primary_segments}")
    if str(segment_summary or "none") != "none":
        lines.append(f"- Segment summary: {segment_summary}")
    for path in changed_files[:12]:
        lines.append(f"- `{path}`")
    if len(changed_files) > 12:
        lines.append(f"- +{len(changed_files) - 12} more")
    prefix = "\n".join(lines)
    clean_answer = answer_text.strip()
    if not clean_answer:
        return prefix
    return f"{prefix}\n\n{clean_answer}"


def _resolve_answer_grounding_mode(*, pr_metadata_used: bool, evidence_count: int) -> str:
    if not pr_metadata_used:
        return "retrieval"
    return "hybrid" if int(evidence_count) > 0 else "pr_metadata"


def _build_qa_markdown(
    *,
    repo_root: Path,
    cmd: str,
    query: str,
    tky_mode: str,
    remote_url: str,
    api_key: str,
    hmac_secret: str,
    enable_hmac: bool,
    github_context_seed: dict[str, Any] | None = None,
    verification_context_seed: dict[str, Any] | None = None,
    audit: dict[str, Any] | None = None,
    governor: AIBudgetGovernor | None = None,
) -> str:
    resolved_repo_root = resolve_repo_root(repo_root)
    cfg = load_config(resolved_repo_root)
    repo_name = extract_repo_from_env()
    branch_name = extract_branch_from_env()
    effective_tky_mode, remote_skip, effective_remote_url = resolve_tky_mode(
        requested_mode=tky_mode,
        cfg=cfg,
        cmd=cmd,
        repo_name=repo_name,
        branch_name=branch_name,
        remote_url_input=remote_url,
    )
    remote_skipped_reason = str(remote_skip or "n/a")
    remote_fail_open = bool(getattr(cfg, "tky_remote_fail_open", True))
    index_path = resolved_repo_root / "artifacts" / "index-package.zip"
    question = question_from_command(cmd, query)
    qa_github_context = _enrich_github_context_with_pr_metadata(
        github_context_seed=github_context_seed,
    )
    changed_files_seed = _collect_pr_changed_files_from_context(qa_github_context)
    pr_segmentation_seed = build_pr_segmentation(
        changed_files=changed_files_seed,
        candidate_paths=[],
    )
    qa_github_context["pr_segmentation_file_map"] = dict(pr_segmentation_seed.file_segment_class_map)
    chunks, index_source, index_elapsed_ms, chunk_vectors_by_id, vectors_meta = _normalize_chunks_meta(
        load_or_build_chunks_with_meta(resolved_repo_root, index_path, governor=governor)
    )
    chunks_embedded_count = len(chunk_vectors_by_id)
    query_vector, embeddings_meta = _maybe_embed_query(
        question=question,
        chunks_embedded_count=chunks_embedded_count,
        governor=governor,
    )
    if not query_vector:
        embeddings_meta["embed_chunks_embedded"] = chunks_embedded_count
        embeddings_meta["embed_query_embedded"] = False
    index_embeddings_model = str(vectors_meta.get("model", "") or "")
    index_embeddings_dim = int(vectors_meta.get("dim", 0) or 0)
    is_dispatch_e2e = _is_dispatch_e2e_simulation()
    if audit is not None:
        audit["index_source"] = index_source
        add_timing(audit, "index_load_build", index_elapsed_ms)
        audit["repobrain_version"] = REPOBRAIN_VERSION
        audit["tkya_backend"] = str(cfg.tkya.backend or "lite")
        audit["remote_skipped_reason"] = remote_skipped_reason or "n/a"
        audit["config_loaded"] = bool(getattr(cfg, "config_loaded", False))
        audit["config_path"] = str(getattr(cfg, "config_path", "<missing>") or "<missing>")
        audit["config_remote_enabled"] = bool(getattr(cfg, "tky_remote_enabled", False))
        audit["config_allow_commands_count"] = len(getattr(cfg, "tky_remote_allow_commands", []))
        audit["config_allow_branches_count"] = len(getattr(cfg, "tky_remote_allow_branches", []))
        audit["config_allow_repos_count"] = len(getattr(cfg, "tky_remote_allow_repos", []))
        audit["tky_mode_requested"] = tky_mode
        audit["tky_mode_used"] = effective_tky_mode
        audit["embed_index_model"] = index_embeddings_model or "n/a"
        audit["embed_index_dim"] = index_embeddings_dim
    print(
        "CONFIG: "
        f"loaded={bool(getattr(cfg, 'config_loaded', False))} "
        f"path={str(getattr(cfg, 'config_path', '<missing>') or '<missing>')} "
        f"remote_enabled={bool(getattr(cfg, 'tky_remote_enabled', False))}"
    )

    provider = make_provider(
        effective_tky_mode,
        remote_url=effective_remote_url or None,
        api_key=api_key or None,
        hmac_secret=hmac_secret or None,
        enable_hmac=enable_hmac,
    )
    result, loop_audit = run_qa_two_pass(
        question=question,
        cmd=cmd,
        chunks=chunks,
        chunk_vectors_by_id=chunk_vectors_by_id,
        query_vector=query_vector,
        provider=provider,
        cfg=cfg,
        tky_mode_requested=effective_tky_mode,
        remote_fail_open=remote_fail_open,
        timings_ms=(audit.get("timings_ms") if isinstance(audit, dict) else None),
        github_context=qa_github_context,
        verification_context=verification_context_seed,
        repo_root=resolved_repo_root,
    )
    audit_summary = dict(result.audit_summary)
    audit_summary.update(loop_audit)
    audit_summary.setdefault("hybrid_rerank_used", False)
    audit_summary.setdefault("retrieval_ranking_mode", "lexical")
    audit_summary.setdefault("evidence_filtered_count", 0)
    audit_summary.setdefault("evidence_filter_reason_codes", "none")
    audit_summary.setdefault("signal_calibration_used", False)
    audit_summary.setdefault("patch_guard_triggered", False)
    audit_summary.setdefault("tldr_compressed", False)
    audit_summary.setdefault("incremental_retrieval_used", False)
    audit_summary.setdefault("incremental_scope_mode", "fallback_full")
    audit_summary.setdefault("changed_files_considered", 0)
    audit_summary.setdefault("changed_regions_considered", 0)
    audit_summary.setdefault("unchanged_files_skipped", 0)
    audit_summary.setdefault("unchanged_chunks_skipped", 0)
    audit_summary.setdefault("retrieval_cache_hits", 0)
    audit_summary.setdefault("retrieval_cache_misses", 0)
    audit_summary.setdefault("incremental_fallback_reason", "none")
    audit_summary.setdefault("evidence_budget_used", 0)
    audit_summary.setdefault("evidence_budget_limit", 0)
    audit_summary.setdefault("evidence_budget_mode", "not_applied")
    audit_summary.setdefault(
        "evidence_budget_bucket_counts",
        "changed_primary:0,changed_secondary:0,support_context:0,tests:0,docs:0,workflow_config:0",
    )
    audit_summary.setdefault("evidence_budget_cutoffs", "no_cutoff")
    audit_summary.setdefault("evidence_budget_overflow", 0)
    audit_summary.setdefault("evidence_budget_primary_selected", 0)
    audit_summary.setdefault("evidence_budget_support_selected", 0)
    for key, value in segmentation_defaults(fallback_reason="missing_changed_files").items():
        audit_summary.setdefault(key, value)
    audit_summary["remote_skipped_reason"] = remote_skipped_reason or "n/a"
    audit_summary["config_loaded"] = bool(getattr(cfg, "config_loaded", False))
    audit_summary["config_path"] = str(getattr(cfg, "config_path", "<missing>") or "<missing>")
    audit_summary["config_remote_enabled"] = bool(getattr(cfg, "tky_remote_enabled", False))
    audit_summary["config_allow_commands_count"] = len(getattr(cfg, "tky_remote_allow_commands", []))
    audit_summary["config_allow_branches_count"] = len(getattr(cfg, "tky_remote_allow_branches", []))
    audit_summary["config_allow_repos_count"] = len(getattr(cfg, "tky_remote_allow_repos", []))
    audit_summary["repobrain_version"] = REPOBRAIN_VERSION
    audit_summary["tkya_backend"] = str(cfg.tkya.backend or "lite")
    audit_summary["tky_mode_requested"] = tky_mode
    audit_summary["tky_mode_used"] = str(
        audit_summary.get("tky_mode_used", effective_tky_mode or "baseline")
    )
    compression_stats = result.tky.compression_stats if isinstance(result.tky.compression_stats, dict) else {}
    audit_summary.update(_extract_verification_audit_fields(compression_stats))
    if isinstance(audit, dict):
        audit_summary["security_scope"] = str(audit.get("security_scope", "n/a") or "n/a")
        audit_summary["security_outcome"] = str(audit.get("security_outcome", "n/a") or "n/a")
        audit_summary["security_reason_code"] = str(
            audit.get("security_reason_code", "n/a") or "n/a"
        )
        audit_summary["security_reason_short"] = str(
            audit.get("security_reason_short", "n/a") or "n/a"
        )
    else:
        audit_summary["security_scope"] = "n/a"
        audit_summary["security_outcome"] = "n/a"
        audit_summary["security_reason_code"] = "n/a"
        audit_summary["security_reason_short"] = "n/a"
    execution_fields = _execution_from_tky_result(result.tky)
    audit_summary.update(execution_fields)
    audit_summary["rd"] = _extract_rd_summary_from_audit_summary(audit_summary)
    if "tky_engine" not in audit_summary:
        audit_summary["tky_engine"] = _provider_engine_name(provider)
    audit_summary.update(embeddings_meta)
    retrieval_runtime = loop_audit.get("embeddings_runtime", {})
    if not isinstance(retrieval_runtime, dict):
        retrieval_runtime = {}
    retrieval_runtime = dict(retrieval_runtime)
    retrieval_runtime.setdefault("embedding_model", str(embeddings_meta.get("embed_model_id", "") or "n/a"))
    embeddings_runtime = _build_embeddings_runtime_truth(
        embeddings_enabled=bool(_embeddings_enabled()),
        vectors_meta=vectors_meta,
        embeddings_meta=embeddings_meta,
        retrieval_runtime=retrieval_runtime,
    )
    index_vectors_used = bool(embeddings_runtime.get("index_vectors_used", False))
    index_embeddings_status = str(embeddings_runtime.get("status", "UNKNOWN") or "UNKNOWN").upper()
    index_embeddings_reason = str(embeddings_runtime.get("evidence_reason", "n/a") or "n/a")

    audit_summary["embed_index_model"] = index_embeddings_model or "n/a"
    audit_summary["embed_index_dim"] = index_embeddings_dim
    audit_summary["embed_index_status"] = index_embeddings_status
    audit_summary["embed_index_reason"] = index_embeddings_reason
    audit_summary["index_vectors_used"] = index_vectors_used
    audit_summary["embeddings_index_status"] = index_embeddings_status
    audit_summary["embeddings_index_reason"] = index_embeddings_reason
    audit_summary["embeddings_runtime"] = dict(embeddings_runtime)
    if is_dispatch_e2e and _embeddings_enabled():
        evidence_payload = _build_index_embeddings_evidence_payload(
            index_path=index_path,
            vectors_meta=vectors_meta,
            embeddings_meta=embeddings_meta,
            index_vectors_used=index_vectors_used,
            embeddings_runtime=embeddings_runtime,
        )
        evidence_path = _write_index_embeddings_evidence(resolved_repo_root, evidence_payload)
        audit_summary["index_embeddings_evidence_artifact"] = "artifacts/index_embeddings_evidence.json"
        audit_summary["index_embeddings_evidence"] = dict(evidence_payload)
        if audit is not None:
            audit["index_embeddings_evidence_artifact"] = evidence_path.as_posix()
            audit["index_embeddings_evidence"] = dict(evidence_payload)
    if not audit_summary.get("embed_model_id"):
        audit_summary["embed_model_id"] = _embeddings_model()
    if "embed_used" not in audit_summary:
        audit_summary["embed_used"] = False
    if "embed_reason" not in audit_summary:
        audit_summary["embed_reason"] = "n/a"
    changed_files_from_pr = _collect_pr_changed_files_from_context(qa_github_context)
    if changed_files_from_pr:
        audit_summary["touched_files"] = changed_files_from_pr
        audit_summary["pr_changed_files_count"] = len(changed_files_from_pr)
    else:
        audit_summary["pr_changed_files_count"] = 0

    semantic_llm_intent = str(audit_summary.get("llm_intent", "none") or "none")
    semantic_execution_mode = str(audit_summary.get("execution_mode", "retrieval_only") or "retrieval_only")
    pr_metadata_used = _should_use_pr_metadata_grounding(
        cmd=cmd,
        question=question,
        github_context=qa_github_context,
        execution_mode=semantic_execution_mode,
        llm_intent=semantic_llm_intent,
    )
    audit_summary["pr_metadata_used"] = pr_metadata_used
    audit_summary["answer_grounding_mode"] = _resolve_answer_grounding_mode(
        pr_metadata_used=pr_metadata_used,
        evidence_count=len(result.evidence),
    )

    evidence_out = result.evidence
    answer_text_out = result.answer_text
    if cmd == "locate":
        evidence_out = _dedupe_evidence_by_file(result.evidence, max_files=5)
    elif cmd == "explain":
        evidence_out = _dedupe_evidence_by_file(result.evidence, max_files=7)
        answer_text_out = _build_explain_answer(evidence_out, question)
    evidence_filter_result = filter_evidence_items(
        evidence_out,
        command=cmd,
        query=question,
    )
    evidence_out = evidence_filter_result.evidence_items
    audit_summary["evidence_filtered_count"] = int(audit_summary.get("evidence_filtered_count", 0) or 0) + int(
        evidence_filter_result.filtered_count
    )
    existing_filter_codes = str(audit_summary.get("evidence_filter_reason_codes", "none") or "none")
    merged_filter_codes = sorted(
        {
            code.strip()
            for code in [*existing_filter_codes.split(","), *evidence_filter_result.reason_codes]
            if code and code.strip() and code.strip().lower() != "none"
        }
    )
    audit_summary["evidence_filter_reason_codes"] = ",".join(merged_filter_codes) if merged_filter_codes else "none"
    pr_segmentation = build_pr_segmentation(
        changed_files=changed_files_from_pr,
        candidate_paths=[str(item.file_path or "").strip() for item in evidence_out if str(item.file_path or "").strip()],
    )
    audit_summary.update(pr_segmentation.as_audit_fields())
    if isinstance(qa_github_context, dict):
        qa_github_context["pr_segmentation_file_map"] = dict(pr_segmentation.file_segment_class_map)

    llm_text, llm_meta = _maybe_generate_llm_text(
        cmd=cmd,
        intent="analysis",
        query=question,
        route=str(audit_summary.get("route_final", result.tky.route)),
        execution_mode=str(audit_summary.get("execution_mode", "retrieval_only")),
        llm_intent_decision=str(audit_summary.get("llm_intent", "none")),
        llm_decision_reason_short=str(
            audit_summary.get(
                "llm_decision_reason_short",
                "LLM not used: direct answer available from retrieved evidence.",
            )
        ),
        llm_decision_reason_code=str(
            audit_summary.get("llm_decision_reason_code", "DEFAULT_RETRIEVAL_ONLY")
        ),
        github_context=dict(qa_github_context or {}),
        locators=evidence_out,
        candidates_count=int(audit_summary.get("retrieved", len(evidence_out)) or 0),
        governor=governor,
    )
    if llm_text and cmd in {"ask", "explain"}:
        answer_text_out = llm_text
    if pr_metadata_used and cmd in {"ask", "explain"} and changed_files_from_pr:
        answer_text_out = _prepend_pr_metadata_to_answer(
            answer_text=answer_text_out,
            changed_files=changed_files_from_pr,
            primary_segments=str(audit_summary.get("pr_primary_segments", "none") or "none"),
            segment_summary=str(audit_summary.get("pr_segment_summary", "none") or "none"),
        )
    llm_meta["pr_changed_files_count"] = int(audit_summary.get("pr_changed_files_count", 0) or 0)
    llm_meta["pr_metadata_used"] = bool(audit_summary.get("pr_metadata_used", False))
    llm_meta["answer_grounding_mode"] = str(
        audit_summary.get("answer_grounding_mode", "retrieval") or "retrieval"
    )
    _merge_llm_meta(audit_summary, llm_meta)
    audit_summary["command"] = cmd
    desired_llm = str(audit_summary.get("execution_mode", "retrieval_only")) == "retrieval_plus_llm"
    if desired_llm and not bool(llm_meta.get("llm_used", False)):
        override_reason = _runtime_override_reason_from_skip(str(llm_meta.get("llm_skip_reason", "n/a")))
    else:
        override_reason = "n/a"
    audit_summary["llm_runtime_override_reason"] = override_reason
    llm_meta["llm_runtime_override_reason"] = override_reason

    if audit is not None:
        audit["route_final"] = str(audit_summary.get("route_final", result.tky.route))
        audit["repobrain_version"] = REPOBRAIN_VERSION
        audit["tkya_backend"] = str(cfg.tkya.backend or "lite")
        audit["pass_count"] = int(audit_summary.get("pass_count", 1) or 1)
        audit["retrieved"] = int(audit_summary.get("retrieved", 0) or 0)
        audit["selected"] = len(evidence_out)
        audit["check_answer_summary"] = " ".join(str(answer_text_out or "").strip().split())
        audit["top_score_pass1"] = audit_summary.get("pass1.top_score")
        audit["top_score_pass2"] = audit_summary.get("pass2.top_score")
        audit["tky_mode_requested"] = str(audit_summary.get("tky_mode_requested", tky_mode or "n/a"))
        audit["tky_mode_used"] = str(audit_summary.get("tky_mode_used", effective_tky_mode or "n/a"))
        audit["tky_engine"] = str(audit_summary.get("tky_engine", _provider_engine_name(provider)))
        audit["remote_used"] = bool(audit_summary.get("remote_used", False))
        audit["remote_latency_ms"] = audit_summary.get("remote_latency_ms", None)
        audit["remote_retry_count"] = int(audit_summary.get("remote_retry_count", 0) or 0)
        audit["remote_rate_limited"] = bool(audit_summary.get("remote_rate_limited", False))
        audit["remote_error_class"] = str(audit_summary.get("remote_error_class", "n/a") or "n/a")
        audit["fallback_reason_code"] = str(audit_summary.get("fallback_reason_code", "n/a") or "n/a")
        audit["remote_skipped_reason"] = str(
            audit_summary.get("remote_skipped_reason", remote_skipped_reason or "n/a") or "n/a"
        )
        audit["pr_changed_files_count"] = int(audit_summary.get("pr_changed_files_count", 0) or 0)
        audit["pr_metadata_used"] = bool(audit_summary.get("pr_metadata_used", False))
        audit["answer_grounding_mode"] = str(
            audit_summary.get("answer_grounding_mode", "retrieval") or "retrieval"
        )
        audit["hybrid_rerank_used"] = bool(audit_summary.get("hybrid_rerank_used", False))
        audit["retrieval_ranking_mode"] = str(audit_summary.get("retrieval_ranking_mode", "lexical") or "lexical")
        audit["evidence_filtered_count"] = int(audit_summary.get("evidence_filtered_count", 0) or 0)
        audit["evidence_filter_reason_codes"] = str(
            audit_summary.get("evidence_filter_reason_codes", "none") or "none"
        )
        audit["incremental_retrieval_used"] = bool(
            audit_summary.get("incremental_retrieval_used", False)
        )
        audit["incremental_scope_mode"] = str(
            audit_summary.get("incremental_scope_mode", "fallback_full") or "fallback_full"
        )
        audit["changed_files_considered"] = int(
            audit_summary.get("changed_files_considered", 0) or 0
        )
        audit["changed_regions_considered"] = int(
            audit_summary.get("changed_regions_considered", 0) or 0
        )
        audit["unchanged_files_skipped"] = int(
            audit_summary.get("unchanged_files_skipped", 0) or 0
        )
        audit["unchanged_chunks_skipped"] = int(
            audit_summary.get("unchanged_chunks_skipped", 0) or 0
        )
        audit["retrieval_cache_hits"] = int(audit_summary.get("retrieval_cache_hits", 0) or 0)
        audit["retrieval_cache_misses"] = int(
            audit_summary.get("retrieval_cache_misses", 0) or 0
        )
        audit["incremental_fallback_reason"] = str(
            audit_summary.get("incremental_fallback_reason", "none") or "none"
        )
        audit["evidence_budget_used"] = int(audit_summary.get("evidence_budget_used", 0) or 0)
        audit["evidence_budget_limit"] = int(audit_summary.get("evidence_budget_limit", 0) or 0)
        audit["evidence_budget_mode"] = str(
            audit_summary.get("evidence_budget_mode", "not_applied") or "not_applied"
        )
        audit["evidence_budget_bucket_counts"] = str(
            audit_summary.get(
                "evidence_budget_bucket_counts",
                "changed_primary:0,changed_secondary:0,support_context:0,tests:0,docs:0,workflow_config:0",
            )
            or "changed_primary:0,changed_secondary:0,support_context:0,tests:0,docs:0,workflow_config:0"
        )
        audit["evidence_budget_cutoffs"] = str(
            audit_summary.get("evidence_budget_cutoffs", "no_cutoff") or "no_cutoff"
        )
        audit["evidence_budget_overflow"] = int(audit_summary.get("evidence_budget_overflow", 0) or 0)
        audit["evidence_budget_primary_selected"] = int(
            audit_summary.get("evidence_budget_primary_selected", 0) or 0
        )
        audit["evidence_budget_support_selected"] = int(
            audit_summary.get("evidence_budget_support_selected", 0) or 0
        )
        audit["pr_segmentation_used"] = bool(audit_summary.get("pr_segmentation_used", False))
        audit["pr_segment_count"] = int(audit_summary.get("pr_segment_count", 0) or 0)
        audit["pr_primary_segments"] = str(audit_summary.get("pr_primary_segments", "none") or "none")
        audit["pr_support_segments"] = str(audit_summary.get("pr_support_segments", "none") or "none")
        audit["pr_cross_segment"] = bool(audit_summary.get("pr_cross_segment", False))
        audit["pr_segment_summary"] = str(audit_summary.get("pr_segment_summary", "none") or "none")
        audit["pr_segment_file_counts"] = str(audit_summary.get("pr_segment_file_counts", "none") or "none")
        audit["pr_segment_candidate_counts"] = str(
            audit_summary.get("pr_segment_candidate_counts", "none") or "none"
        )
        audit["pr_segmentation_fallback_reason"] = str(
            audit_summary.get("pr_segmentation_fallback_reason", "none") or "none"
        )
        audit["signal_calibration_used"] = bool(audit_summary.get("signal_calibration_used", False))
        audit["patch_guard_triggered"] = bool(audit_summary.get("patch_guard_triggered", False))
        audit["tldr_compressed"] = bool(audit_summary.get("tldr_compressed", False))
        audit["tky_remote_status"] = audit_summary.get("tky_remote_status", None)
        audit["tky_fallback_reason"] = str(audit_summary.get("tky_fallback_reason", "n/a") or "n/a")
        audit["rd"] = _extract_rd_summary_from_audit_summary(audit_summary)
        audit["comment_truncated"] = False
        audit["ask_result_artifact"] = "n/a"
        audit["check_intent"] = "analysis"
        audit["check_annotations_raw"] = _build_check_annotations_from_evidence(
            evidence_out,
            route=str(audit_summary.get("route_final", result.tky.route)),
        )
        audit["verification_report"] = {
            "checks": [],
            "summary": "Verification not executed for ask flow.",
            "overall": "NOT_RUN",
            "trusted_context": _env_true("RB_TRUSTED_CONTEXT", default=False),
            "dynamic_allowed": _env_true("RB_ALLOW_DYNAMIC_VERIFY", default=False),
        }
        _merge_llm_meta(audit, llm_meta)
        audit["llm_usage_payload"] = _build_llm_usage_payload(llm_meta)
        _merge_embeddings_meta(audit, embeddings_meta)
        audit["embed_index_model"] = index_embeddings_model or "n/a"
        audit["embed_index_dim"] = index_embeddings_dim
        audit["embed_index_status"] = index_embeddings_status
        audit["embed_index_reason"] = index_embeddings_reason
        audit["index_vectors_used"] = index_vectors_used
        audit["embeddings_index_status"] = index_embeddings_status
        audit["embeddings_index_reason"] = index_embeddings_reason
        audit["embeddings_runtime"] = dict(embeddings_runtime)
        audit["embeddings_usage_payload"] = _build_embeddings_usage_payload(embeddings_meta)

    diagnostic_markdown = render_diagnostic_summary_markdown(audit_summary)
    diagnostic_path = _write_diagnostic_summary_markdown(resolved_repo_root, diagnostic_markdown)
    audit_summary["diagnostic_summary_artifact"] = "artifacts/diagnostic_summary.md"
    if audit is not None:
        audit["diagnostic_summary_artifact"] = diagnostic_path.as_posix()

    t0 = time.perf_counter()
    final_route = str(audit_summary.get("route_final", result.tky.route) or result.tky.route).strip().upper()
    if final_route == "WAIT":
        full_body = render_wait_markdown(
            reason=result.tky.rationale or "Verification is pending.",
            audit_summary=audit_summary,
        )
    elif final_route in {"REFUSE", "BLOCK"}:
        full_body = render_refuse_markdown(
            reason=result.tky.rationale or "Request was refused by TKY route.",
            audit_summary=audit_summary,
            blocked=final_route == "BLOCK",
        )
    else:
        full_body = render_answer_markdown(
            answer_text=answer_text_out,
            evidence=evidence_out,
            audit_summary=audit_summary,
            next_steps=result.next_steps,
            command=cmd,
            repo=extract_repo_from_env() or None,
            sha=extract_sha_from_env() or None,
        )
    body, was_truncated = enforce_comment_limit(full_body)
    if was_truncated:
        artifact_path = _write_ask_result_markdown(resolved_repo_root, full_body)
        if audit is not None:
            audit["comment_truncated"] = True
            audit["ask_result_artifact"] = artifact_path.as_posix()
    elif audit is not None:
        audit["comment_truncated"] = False
    if audit is not None:
        add_timing(audit, "format", (time.perf_counter() - t0) * 1000.0)
    return body


def _review_candidates_from_files(files: list[dict[str, Any]]) -> list[CandidateChunk]:
    candidates: list[CandidateChunk] = []
    for idx, item in enumerate(files):
        path = str(item.get("filename", "") or "").strip()
        if not path:
            continue
        changes = int(item.get("changes", 0) or 0)
        additions = int(item.get("additions", 0) or 0)
        deletions = int(item.get("deletions", 0) or 0)
        score = max(0.01, min(1.0, 0.2 + (changes / 1000.0) + (0.04 / (idx + 1))))
        line_end = max(1, additions + deletions)
        candidates.append(
            CandidateChunk(
                chunk_id=f"pr:{path}:1-{line_end}",
                file_path=path,
                line_start=1,
                line_end=line_end,
                score=score,
                text=None,
            )
        )
    if candidates:
        return candidates
    return [
        CandidateChunk(
            chunk_id="pr:empty:1-1",
            file_path="README.md",
            line_start=1,
            line_end=1,
            score=0.01,
            text=None,
        )
    ]


def _count_confirmed_localized_findings(
    *,
    review: dict[str, Any],
    selected_files: list[str],
) -> int:
    selected_set = {str(path).strip() for path in selected_files if str(path).strip()}
    confirmed_items_raw = review.get("confirmed_risk_items", [])
    if not isinstance(confirmed_items_raw, list):
        return 0

    count = 0
    for item in confirmed_items_raw:
        if not isinstance(item, dict):
            continue
        evidence_paths_raw = item.get("evidence_paths", [])
        evidence_paths = (
            [str(path).strip() for path in evidence_paths_raw if str(path).strip()]
            if isinstance(evidence_paths_raw, list)
            else []
        )
        if not evidence_paths:
            continue
        if selected_set:
            if any(path in selected_set for path in evidence_paths):
                count += 1
        else:
            count += 1
    return count


def _should_block_fix_patch_without_localized_evidence(
    *,
    require_localized_evidence: bool,
    selected_files: list[str],
    confirmed_localized_findings: int,
) -> bool:
    if not bool(require_localized_evidence):
        return False
    if len([path for path in selected_files if str(path).strip()]) == 0:
        return True
    return int(confirmed_localized_findings) <= 0


def _build_review_markdown(
    *,
    repo_root: Path,
    cmd: str,
    query: str,
    is_pull_request: bool,
    issue_number: int | None,
    dry_run: bool,
    client: GitHubClient | None,
    tky_mode: str,
    remote_url: str,
    api_key: str,
    hmac_secret: str,
    enable_hmac: bool,
    github_context_seed: dict[str, Any] | None = None,
    verification_context_seed: dict[str, Any] | None = None,
    audit: dict[str, Any] | None = None,
    governor: AIBudgetGovernor | None = None,
) -> str:
    if not is_pull_request:
        if audit is not None:
            audit["route_final"] = "REVIEW"
            audit["pass_count"] = 1
            audit["index_source"] = "n/a"
        return "Review/fix is available in Pull Requests. Run `/repobrain review` in a PR discussion."

    if issue_number is None:
        if audit is not None:
            audit["route_final"] = "REVIEW"
            audit["pass_count"] = 1
            audit["index_source"] = "n/a"
        return "Review/fix is available in Pull Requests. Pull request number was not detected."

    files: list[dict[str, Any]]
    head_sha = ""
    pull: dict[str, Any] = {}
    repo_name = extract_repo_from_env() or (client.repo if client is not None else "")
    if dry_run:
        files = []
    else:
        if client is None:
            raise ValueError("GitHub client is required for PR review/fix in post mode")
        pull = client.get_pull(pull_number=issue_number)
        pr_state = str(pull.get("state", "") or "").strip().lower()
        pr_merged = bool(pull.get("merged", False))
        if pr_state == "closed" or pr_merged:
            status_label = "closed/merged" if pr_merged else "closed"
            if cmd == "fix":
                reason_short = (
                    "Skipped: `/repobrain fix` runs only on open PRs with an active diff context. "
                    f"This PR is already {status_label}. Run the command on an open PR."
                )
                reason_code = "pr_closed_or_merged_fix"
            else:
                reason_short = (
                    "Skipped: `/repobrain review` runs only on open PRs. "
                    f"This PR is already {status_label}. Run the command on an open PR."
                )
                reason_code = "pr_closed_or_merged_review"
            if audit is not None:
                audit["route_final"] = "WAIT"
                audit["pass_count"] = 1
                audit["index_source"] = "n/a"
                audit["skip_reason_code"] = reason_code
                audit["skip_reason_short"] = reason_short
                audit["skip_visible_to_user"] = True
                audit["pr_state"] = pr_state or "unknown"
                audit["pr_merged"] = pr_merged
            return reason_short
        head = pull.get("head", {})
        if isinstance(head, dict):
            head_sha = str(head.get("sha", "") or "")
        files = client.get_pull_files(pull_number=issue_number)

    if not head_sha:
        head_sha = extract_sha_from_env()

    review = build_pr_review(files, head_sha=head_sha or None, repo=repo_name or None)
    review = validate_review_findings(review)
    review_validation_payload = {
        "validated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "risk_level": str(review.get("risk_level", "low") or "low"),
        "confirmed_findings": list(review.get("confirmed_findings", []))
        if isinstance(review.get("confirmed_findings", []), list)
        else [],
        "possible_signals": list(review.get("possible_signals", []))
        if isinstance(review.get("possible_signals", []), list)
        else [],
        "validation": dict(review.get("validation", {}))
        if isinstance(review.get("validation", {}), dict)
        else {},
    }
    review_validation_path = _write_review_validation(repo_root, review_validation_payload)
    verification_report = _run_review_verification(repo_root=repo_root, cmd=cmd)
    _write_verification_report(repo_root, verification_report)

    if audit is not None:
        audit["index_source"] = "n/a"
        audit["retrieved"] = len(files)
        audit["selected"] = len(files)
        audit["verification_overall"] = str(verification_report.get("overall", "NOT_RUN"))

    cfg = load_config(repo_root)
    branch_name = extract_branch_from_env()
    effective_tky_mode, remote_skip, effective_remote_url = resolve_tky_mode(
        requested_mode=tky_mode,
        cfg=cfg,
        cmd="review",
        repo_name=repo_name,
        branch_name=branch_name,
        remote_url_input=remote_url,
    )
    provider = make_provider(
        effective_tky_mode,
        remote_url=effective_remote_url or None,
        api_key=api_key or None,
        hmac_secret=hmac_secret or None,
        enable_hmac=enable_hmac,
    )
    all_pr_changed_files = list(
        dict.fromkeys(str(item.get("filename", "")).strip() for item in files if item.get("filename"))
    )
    all_pr_changed_hunks = [
        str(item.get("patch", "")).strip()
        for item in files
        if isinstance(item, dict) and str(item.get("patch", "")).strip()
    ]
    review_segmentation_seed = build_pr_segmentation(
        changed_files=all_pr_changed_files,
        candidate_paths=[],
    )
    review_candidates = _review_candidates_from_files(files)
    planner_context = dict(github_context_seed or {})
    if all_pr_changed_files:
        planner_context["changed_files"] = list(all_pr_changed_files)
    planner_context["pr_segmentation_file_map"] = dict(review_segmentation_seed.file_segment_class_map)
    review_budget_plan = plan_evidence_budget(
        review_candidates,
        command=cmd,
        github_context=planner_context,
        limit_hint=min(80, max(10, len(review_candidates))),
        incremental_scope_mode="review_pr_files",
        segment_hints={"file_segment_class_map": review_segmentation_seed.file_segment_class_map},
    )
    review_candidates = review_budget_plan.candidates
    verification_context = dict(verification_context_seed or {})
    verification_context.update(_verification_context_from_report(verification_report))
    policy = {
        "corelocked": True,
        "intent": "patch" if cmd == "fix" else "review",
        "github_context": dict(github_context_seed or {}),
        "verification_context": verification_context,
        "runtime": {
            "mode": "ci" if _runtime_env_cfg().workflow.github_actions else "local",
            "network_allowed": bool(_runtime_env_cfg().tkya.allow_remote),
            "trusted_context": bool(_runtime_env_cfg().workflow.trusted_context),
        },
    }
    limits = _qa_limits(
        cmd="review",
        max_sources=min(8, max(1, len(review_candidates))),
        min_score_keep=0.01,
        keep_ratio=0.2,
        max_per_file=2,
        max_files=12,
        route_hint="REVIEW",
        topk_current=min(80, max(10, len(review_candidates))),
        topk_fast=30,
        topk_deep=80,
        time_budget_s=int(_runtime_env_cfg().workflow.verify_time_budget_s),
        perf_max_candidates=int(getattr(cfg, "tky_perf_max_candidates", 800)),
        perf_max_series=int(getattr(cfg, "tky_perf_max_series", 4096)),
        perf_max_vectors=int(getattr(cfg, "tky_perf_max_vectors", 2048)),
        perf_max_edges=int(getattr(cfg, "tky_perf_max_edges", 4096)),
        perf_max_paths=int(getattr(cfg, "tky_perf_max_paths", 4096)),
        github_context=policy["github_context"],
        verification_context=policy["verification_context"],
    )
    limits["policy"] = policy
    question = (
        f"Generate safe patch guidance: {query.strip()}"
        if cmd == "fix" and query.strip()
        else ("Generate safe patch guidance for PR changes." if cmd == "fix" else "Review PR changes.")
    )
    tky_result, _, tky_meta = _answer_with_remote_fallback(
        question=question,
        candidates=review_candidates,
        limits=limits,
        provider=provider,
        tky_mode_requested=effective_tky_mode,
        remote_fail_open=bool(getattr(cfg, "tky_remote_fail_open", True)),
    )
    compression_stats = (
        tky_result.tky.compression_stats
        if isinstance(tky_result.tky.compression_stats, dict)
        else {}
    )

    verification_checks = verification_report.get("checks", [])
    if not isinstance(verification_checks, list):
        verification_checks = []
    pass_count = sum(1 for item in verification_checks if isinstance(item, dict) and item.get("status") == "PASS")
    fail_count = sum(1 for item in verification_checks if isinstance(item, dict) and item.get("status") == "FAIL")
    not_run_count = sum(
        1 for item in verification_checks if isinstance(item, dict) and item.get("status") == "NOT_RUN"
    )
    audit_summary: dict[str, Any] = {
        "route_final": str(tky_result.tky.route or "REVIEW").upper(),
        "pass_count": 1,
        "retrieved": len(files),
        "selected": len(review.get("files_changed", [])),
        "repobrain_version": REPOBRAIN_VERSION,
        "tkya_backend": str(cfg.tkya.backend or "lite"),
        "tky_mode_used": str(tky_meta.get("tky_mode_used", effective_tky_mode)),
        "tky_engine": str(tky_meta.get("tky_engine", _provider_engine_name(provider))),
        "remote_skipped_reason": str(remote_skip or "n/a"),
        "verification_pass_count": pass_count,
        "verification_fail_count": fail_count,
        "verification_not_run_count": not_run_count,
        "verification_pending_count": 0,
        "verification_overall": str(verification_report.get("overall", "NOT_RUN")),
        "security_scope": str(audit.get("security_scope", "n/a") if isinstance(audit, dict) else "n/a"),
        "security_outcome": str(
            audit.get("security_outcome", "n/a") if isinstance(audit, dict) else "n/a"
        ),
        "security_reason_code": str(
            audit.get("security_reason_code", "n/a") if isinstance(audit, dict) else "n/a"
        ),
        "security_reason_short": str(
            audit.get("security_reason_short", "n/a") if isinstance(audit, dict) else "n/a"
        ),
        "hybrid_rerank_used": False,
        "retrieval_ranking_mode": "lexical",
        "evidence_filtered_count": 0,
        "evidence_filter_reason_codes": "none",
        "signal_calibration_used": False,
        "patch_guard_triggered": False,
        "tldr_compressed": False,
        "incremental_retrieval_used": False,
        "incremental_scope_mode": "fallback_full",
        "changed_files_considered": 0,
        "changed_regions_considered": 0,
        "unchanged_files_skipped": 0,
        "unchanged_chunks_skipped": 0,
        "retrieval_cache_hits": 0,
        "retrieval_cache_misses": 0,
        "incremental_fallback_reason": "not_applicable",
        "evidence_budget_used": int(review_budget_plan.evidence_budget_used),
        "evidence_budget_limit": int(review_budget_plan.evidence_budget_limit),
        "evidence_budget_mode": str(review_budget_plan.evidence_budget_mode or "not_applied"),
        "evidence_budget_bucket_counts": ",".join(
            f"{bucket}:{int(count)}"
            for bucket, count in review_budget_plan.evidence_budget_bucket_counts.items()
        )
        or "changed_primary:0,changed_secondary:0,support_context:0,tests:0,docs:0,workflow_config:0",
        "evidence_budget_cutoffs": ",".join(review_budget_plan.evidence_budget_cutoffs)
        if review_budget_plan.evidence_budget_cutoffs
        else "no_cutoff",
        "evidence_budget_overflow": int(review_budget_plan.evidence_budget_overflow),
        "evidence_budget_primary_selected": int(review_budget_plan.evidence_budget_primary_selected),
        "evidence_budget_support_selected": int(review_budget_plan.evidence_budget_support_selected),
    }
    audit_summary.update(review_segmentation_seed.as_audit_fields())
    audit_summary.update(_execution_from_tky_result(tky_result.tky))
    audit_summary.update(_extract_verification_audit_fields(compression_stats))
    validation_raw = review.get("validation", {})
    validation = dict(validation_raw) if isinstance(validation_raw, dict) else {}
    signal_calibration_used = bool(
        review.get("signal_calibration_used", validation.get("signal_calibration_used", False))
    )
    signal_calibration_codes_raw = review.get(
        "signal_calibration_reason_codes",
        validation.get("signal_calibration_reason_codes", ["none"]),
    )
    signal_calibration_codes = (
        [str(item).strip() for item in signal_calibration_codes_raw if str(item).strip()]
        if isinstance(signal_calibration_codes_raw, list)
        else [str(signal_calibration_codes_raw).strip()]
    )
    audit_summary["signal_calibration_used"] = signal_calibration_used
    audit_summary["signal_calibration_reason_codes"] = (
        ",".join(sorted(set(signal_calibration_codes))) if signal_calibration_codes else "none"
    )
    audit_summary["review_confirmed_findings_count"] = int(
        validation.get("confirmed_findings_count", 0) or 0
    )
    audit_summary["review_possible_signals_count"] = int(
        validation.get("possible_signals_count", 0) or 0
    )
    risk_drivers_raw = review.get("risk_drivers", [])
    risk_drivers = (
        [str(item).strip() for item in risk_drivers_raw if str(item).strip()]
        if isinstance(risk_drivers_raw, list)
        else []
    )
    audit_summary["review_risk_drivers_count"] = len(risk_drivers)
    audit_summary["review_informational_notes_count"] = int(
        validation.get("informational_notes_count", 0) or 0
    )
    audit_summary["review_validation_artifact"] = "artifacts/review_validation.json"
    audit_summary["patch_validation_result"] = "n/a"
    changed_files = list(all_pr_changed_files)
    changed_file_hunks = list(all_pr_changed_hunks)
    pr_metadata_available = bool(all_pr_changed_files)
    patch_targeting: dict[str, Any] = {
        "patch_target_files_total": len(all_pr_changed_files),
        "patch_target_files_selected": len(all_pr_changed_files),
        "patch_target_hunks_selected": len(all_pr_changed_hunks),
        "patch_targeting_mode": "full_pr_context",
        "patch_targeting_reason": "not_applicable",
        "localized_patch_evidence_count": 0,
        "selected_files": list(all_pr_changed_files),
        "selected_hunks": list(all_pr_changed_hunks),
    }
    confirmed_localized_findings = 0
    if cmd == "fix":
        patch_targeting = select_patch_targets(
            files=files,
            review=review,
            query=query or question,
            max_target_files=int(cfg.llm.patch_max_target_files),
            max_target_hunks=int(cfg.llm.patch_max_target_hunks),
            require_localized_evidence=bool(cfg.llm.patch_require_localized_evidence),
        )
        selected_files_raw = patch_targeting.get("selected_files", [])
        selected_hunks_raw = patch_targeting.get("selected_hunks", [])
        selected_files = (
            [str(item).strip() for item in selected_files_raw if str(item).strip()]
            if isinstance(selected_files_raw, list)
            else []
        )
        selected_hunks = (
            [str(item).strip() for item in selected_hunks_raw if str(item).strip()]
            if isinstance(selected_hunks_raw, list)
            else []
        )
        changed_files = list(dict.fromkeys(selected_files))
        changed_file_hunks = list(dict.fromkeys(selected_hunks))
    if changed_files:
        audit_summary["touched_files"] = changed_files
    audit_summary["pr_changed_files_count"] = len(all_pr_changed_files)
    audit_summary["pr_metadata_used"] = pr_metadata_available
    if pr_metadata_available:
        audit_summary["answer_grounding_mode"] = "hybrid" if changed_files else "pr_metadata"
    else:
        audit_summary["answer_grounding_mode"] = "retrieval"
    if cmd == "fix":
        audit_summary["patch_target_files_total"] = int(
            patch_targeting.get("patch_target_files_total", len(files)) or 0
        )
        audit_summary["patch_target_files_selected"] = int(
            patch_targeting.get("patch_target_files_selected", len(changed_files)) or 0
        )
        audit_summary["patch_target_hunks_selected"] = int(
            patch_targeting.get("patch_target_hunks_selected", len(changed_file_hunks)) or 0
        )
        audit_summary["patch_targeting_mode"] = str(
            patch_targeting.get("patch_targeting_mode", "n/a") or "n/a"
        )
        audit_summary["patch_targeting_reason"] = str(
            patch_targeting.get("patch_targeting_reason", "n/a") or "n/a"
        )
        audit_summary["localized_patch_evidence_count"] = int(
            patch_targeting.get("localized_patch_evidence_count", 0) or 0
        )
        audit_summary["patch_grounding_mode"] = "pr_metadata" if pr_metadata_available else "retrieval"
        confirmed_localized_findings = _count_confirmed_localized_findings(
            review=review,
            selected_files=changed_files,
        )
        audit_summary["patch_confirmed_localized_findings_count"] = int(confirmed_localized_findings)
        if _should_block_fix_patch_without_localized_evidence(
            require_localized_evidence=bool(cfg.llm.patch_require_localized_evidence),
            selected_files=changed_files,
            confirmed_localized_findings=confirmed_localized_findings,
        ):
            changed_files = []
            changed_file_hunks = []
            audit_summary["patch_target_files_selected"] = 0
            audit_summary["patch_target_hunks_selected"] = 0
            audit_summary["patch_targeting_mode"] = "none"
            audit_summary["patch_targeting_reason"] = "no_confirmed_localized_evidence"
            audit_summary["localized_patch_evidence_count"] = 0
    filtered_review_candidates = filter_candidate_evidence(
        review_candidates,
        command=cmd,
        query=query or question,
        max_items=len(review_candidates),
    )
    review_candidates = filtered_review_candidates.candidates
    audit_summary["evidence_filtered_count"] = int(filtered_review_candidates.filtered_count)
    audit_summary["evidence_filter_reason_codes"] = ",".join(filtered_review_candidates.reason_codes) or "none"
    review_segmentation = build_pr_segmentation(
        changed_files=all_pr_changed_files,
        candidate_paths=[str(item.file_path or "").strip() for item in review_candidates if str(item.file_path or "").strip()],
    )
    audit_summary.update(review_segmentation.as_audit_fields())
    review_locators = [
        EvidenceItem(
            file_path=item.file_path,
            line_start=item.line_start,
            line_end=item.line_end,
            score=item.score,
        )
        for item in review_candidates
    ]
    llm_intent = "patch" if cmd == "fix" else "review"
    llm_route = str(audit_summary.get("route_final", "REVIEW"))
    execution_mode = str(audit_summary.get("execution_mode", "retrieval_only"))
    llm_decision_intent = str(audit_summary.get("llm_intent", llm_intent) or llm_intent)
    llm_decision_reason_short = str(
        audit_summary.get(
            "llm_decision_reason_short",
            "LLM not used: direct answer available from retrieved evidence.",
        )
        or "LLM not used: direct answer available from retrieved evidence."
    )
    llm_decision_reason_code = str(
        audit_summary.get("llm_decision_reason_code", "DEFAULT_RETRIEVAL_ONLY")
        or "DEFAULT_RETRIEVAL_ONLY"
    )
    if cmd == "fix":
        (
            llm_decision_intent,
            llm_decision_reason_code,
            llm_decision_reason_short,
        ) = _normalize_fix_semantics(
            execution_mode=execution_mode,
            llm_intent=llm_decision_intent,
            reason_code=llm_decision_reason_code,
            reason_short=llm_decision_reason_short,
        )
        audit_summary["llm_intent"] = llm_decision_intent
        audit_summary["llm_decision_reason_code"] = llm_decision_reason_code
        audit_summary["llm_decision_reason_short"] = llm_decision_reason_short
    llm_context = dict(github_context_seed or {})
    if changed_files:
        llm_context["changed_files"] = list(changed_files)
    if changed_file_hunks:
        llm_context["diff_hunks"] = list(changed_file_hunks)
    llm_complexity = score_complexity(
        task_type=cmd,
        intent=llm_intent,
        route=llm_route,
        github_context=llm_context,
        candidates=[None] * max(0, len(review_candidates)),
        limits={"query_length": len(query or question)},
    )
    patch_budget_stats: dict[str, Any] = {}
    review_budget_stats: dict[str, Any] = {}
    review_estimated_input_tokens = 0
    patch_estimated_input_tokens = 0
    diff_hunks_raw = llm_context.get("diff_hunks", [])
    diff_hunks = [str(item) for item in diff_hunks_raw if str(item).strip()] if isinstance(diff_hunks_raw, list) else []
    if cmd == "review":
        review_snippets = [
            str(item.chunk_id)
            for item in review_candidates[:120]
            if str(getattr(item, "chunk_id", "")).strip()
        ]
        _, review_budget_stats = build_messages_for_review(
            query=query or question,
            changed_files=changed_files,
            diff_hunks=diff_hunks,
            max_input_tokens=int(cfg.llm.max_input_tokens_review_final),
            selected_snippets=review_snippets,
            max_files_context=int(cfg.llm.max_files_review_context),
            max_findings_context=int(cfg.llm.max_findings_review_context),
            max_hunks_context=int(cfg.llm.max_hunks_review_context),
        )
        review_estimated_input_tokens = int(
            review_budget_stats.get("input_budget_used_est", 0) or 0
        )
    if cmd == "fix":
        patch_snippets = [
            str(item.chunk_id)
            for item in review_candidates[:80]
            if str(getattr(item, "chunk_id", "")).strip()
        ]
        _, patch_budget_stats = build_messages_for_fix(
            query=query or question,
            changed_files=changed_files,
            diff_hunks=diff_hunks,
            max_input_tokens=int(cfg.llm.max_input_tokens_patch),
            selected_snippets=patch_snippets,
            max_hunks=int(cfg.batch.patch_max_hunks_per_call),
        )
        patch_estimated_input_tokens = int(patch_budget_stats.get("input_budget_used_est", 0) or 0)
    use_batch_mode = _should_use_batch_mode_for_review(
        cmd=cmd,
        route=llm_route,
        complexity_score=llm_complexity,
        changed_files_count=len(changed_files),
        diff_hunks_count=len(diff_hunks),
        estimated_patch_input_tokens=patch_estimated_input_tokens,
    )
    if cmd == "review" and _review_context_needs_batch(
        cfg=cfg,
        changed_files_count=len(changed_files),
        diff_hunks_count=len(diff_hunks),
        estimated_input_tokens=review_estimated_input_tokens,
    ):
        use_batch_mode = True
    batch_result: dict[str, Any] = {
        "batch_used": False,
        "planned_batches": 0,
        "executed_batches": 0,
        "summaries": [],
        "findings": [],
        "summary_text": "",
        "patch_parts": [],
        "no_patch_batches_count": 0,
        "no_patch_returned": False,
    }
    review_compaction_attempted = False
    review_batching_attempted = False
    review_generation_result = "single_call"
    no_localized_patch_target = (
        cmd == "fix"
        and _should_block_fix_patch_without_localized_evidence(
            require_localized_evidence=bool(cfg.llm.patch_require_localized_evidence),
            selected_files=changed_files,
            confirmed_localized_findings=confirmed_localized_findings,
        )
    )
    llm_text_for_patch = ""
    if no_localized_patch_target:
        llm_meta = _llm_default_meta(
            "no_localized_patch_target",
            execution_mode=execution_mode,
            llm_intent=llm_decision_intent,
            llm_decision_reason_short=(
                "LLM not used: no sufficiently localized, evidence-backed patch target."
            ),
            llm_decision_reason_code="FIX_CONTEXT_INSUFFICIENT",
        )
        llm_meta["llm_request_mode"] = "patch"
        llm_meta["llm_compacted"] = True
        llm_meta["llm_attempted_compaction"] = False
        llm_meta["llm_patch_batch_mode"] = False
        llm_meta["llm_patch_batch_count"] = 0
        llm_meta["llm_attempted_patch_batch"] = False
        llm_meta["llm_model_used"] = "not used"
        llm_meta["llm_final_synthesis_model_id"] = "not used"
        llm_meta["llm_effective_model_id"] = "not used"
        llm_meta["llm_retained_preferred_model_reason"] = "n/a"
        llm_meta["llm_downgrade_threshold_used"] = str(
            _llm_downgrade_threshold_for_command(cfg, cmd, llm_intent)
        )
    elif use_batch_mode:
        review_batching_attempted = cmd == "review"
        if cmd == "review":
            review_generation_result = "batch_mode"
        batch_result, llm_meta = _run_batch_llm_review_fix(
            repo_root=repo_root,
            cmd=cmd,
            intent=llm_intent,
            query=query or question,
            route=llm_route,
            execution_mode=execution_mode,
            llm_intent_decision=llm_decision_intent,
            llm_decision_reason_short=llm_decision_reason_short,
            llm_decision_reason_code=llm_decision_reason_code,
            github_context=llm_context,
            selected_chunks=review_candidates,
            locators=review_locators,
            governor=governor,
            force_patch_batch=False,
        )
        if str(batch_result.get("summary_text", "")).strip():
            review["summary_text"] = str(batch_result.get("summary_text", "")).strip()
        batch_findings = batch_result.get("findings", [])
        if isinstance(batch_findings, list) and batch_findings:
            notes_raw = review.get("notes", [])
            notes = [str(item) for item in notes_raw if str(item).strip()] if isinstance(notes_raw, list) else []
            notes.extend(str(item) for item in batch_findings[:8] if str(item).strip())
            review["notes"] = list(dict.fromkeys(notes))
    else:
        llm_text, llm_meta = _maybe_generate_llm_text(
            cmd=cmd,
            intent=llm_intent,
            query=query or question,
            route=llm_route,
            execution_mode=execution_mode,
            llm_intent_decision=llm_decision_intent,
            llm_decision_reason_short=llm_decision_reason_short,
            llm_decision_reason_code=llm_decision_reason_code,
            github_context=llm_context,
            locators=review_locators,
            candidates_count=len(review_candidates),
            governor=governor,
        )
        llm_text_for_patch = llm_text or ""
        if llm_text:
            review["summary_text"] = llm_text
        if cmd == "review" and _int_or_zero(llm_meta.get("llm_provider_http_status", 0)) == 413:
            review_compaction_attempted = True
            compact_messages, compact_stats = build_messages_for_review(
                query=query or question,
                changed_files=changed_files,
                diff_hunks=diff_hunks,
                max_input_tokens=max(256, int(cfg.llm.max_input_tokens_review_final // 2)),
                selected_snippets=[
                    str(item.chunk_id)
                    for item in review_candidates[:80]
                    if str(getattr(item, "chunk_id", "")).strip()
                ],
                max_files_context=max(8, int(cfg.llm.max_files_review_context // 2)),
                max_findings_context=max(8, int(cfg.llm.max_findings_review_context // 2)),
                max_hunks_context=max(6, int(cfg.llm.max_hunks_review_context // 2)),
            )
            compact_text, compact_meta = _maybe_generate_llm_text(
                cmd=cmd,
                intent=llm_intent,
                query=query or question,
                route=llm_route,
                execution_mode=execution_mode,
                llm_intent_decision=llm_decision_intent,
                llm_decision_reason_short=llm_decision_reason_short,
                llm_decision_reason_code=llm_decision_reason_code,
                github_context=llm_context,
                locators=review_locators,
                candidates_count=len(review_candidates),
                prebuilt_messages=compact_messages,
                prebuilt_budget_stats=compact_stats,
                governor=governor,
            )
            if compact_text:
                llm_meta = compact_meta
                review["summary_text"] = compact_text
                review_generation_result = "compacted_retry_ok"
            else:
                review_batching_attempted = True
                batch_result, retried_meta = _run_batch_llm_review_fix(
                    repo_root=repo_root,
                    cmd=cmd,
                    intent=llm_intent,
                    query=query or question,
                    route=llm_route,
                    execution_mode=execution_mode,
                    llm_intent_decision=llm_decision_intent,
                    llm_decision_reason_short=llm_decision_reason_short,
                    llm_decision_reason_code=llm_decision_reason_code,
                    github_context=llm_context,
                    selected_chunks=review_candidates,
                    locators=review_locators,
                    governor=governor,
                    force_patch_batch=False,
                )
                use_batch_mode = True
                llm_meta = retried_meta
                if str(batch_result.get("summary_text", "")).strip():
                    review["summary_text"] = str(batch_result.get("summary_text", "")).strip()
                batch_findings = batch_result.get("findings", [])
                if isinstance(batch_findings, list) and batch_findings:
                    notes_raw = review.get("notes", [])
                    notes = [str(item) for item in notes_raw if str(item).strip()] if isinstance(notes_raw, list) else []
                    notes.extend(str(item) for item in batch_findings[:8] if str(item).strip())
                    review["notes"] = list(dict.fromkeys(notes))
                review_generation_result = "batch_retry_after_413"
        should_retry_patch_batch = _should_retry_patch_batch_after_single_call(
            cmd=cmd,
            llm_meta=llm_meta,
        )
        if should_retry_patch_batch:
            llm_meta["llm_attempted_compaction"] = True
            llm_meta["llm_attempted_patch_batch"] = True
            batch_result, retried_meta = _run_batch_llm_review_fix(
                repo_root=repo_root,
                cmd=cmd,
                intent=llm_intent,
                query=query or question,
                route=llm_route,
                execution_mode=execution_mode,
                llm_intent_decision=llm_decision_intent,
                llm_decision_reason_short=llm_decision_reason_short,
                llm_decision_reason_code=llm_decision_reason_code,
                github_context=llm_context,
                selected_chunks=review_candidates,
                locators=review_locators,
                governor=governor,
                force_patch_batch=True,
            )
            use_batch_mode = True
            llm_meta = retried_meta
            if str(batch_result.get("summary_text", "")).strip():
                review["summary_text"] = str(batch_result.get("summary_text", "")).strip()
            batch_findings = batch_result.get("findings", [])
            if isinstance(batch_findings, list) and batch_findings:
                notes_raw = review.get("notes", [])
                notes = [str(item) for item in notes_raw if str(item).strip()] if isinstance(notes_raw, list) else []
                notes.extend(str(item) for item in batch_findings[:8] if str(item).strip())
                review["notes"] = list(dict.fromkeys(notes))
    if cmd == "fix":
        llm_meta.setdefault("llm_request_mode", "patch")
        llm_meta["llm_compacted"] = True
        llm_meta["llm_attempted_compaction"] = bool(
            llm_meta.get("llm_attempted_compaction", False)
            or (not no_localized_patch_target)
        )
        llm_meta["llm_patch_batch_mode"] = bool(batch_result.get("batch_used", False))
        llm_meta["llm_patch_batch_count"] = int(batch_result.get("executed_batches", 0) or 0)
        llm_meta["llm_attempted_patch_batch"] = bool(
            batch_result.get("batch_used", False)
            or _int_or_zero(llm_meta.get("llm_provider_http_status", 0)) == 413
        )
        if not _int_or_zero(llm_meta.get("llm_input_budget_used_est", 0)):
            llm_meta["llm_input_budget_used_est"] = int(
                patch_budget_stats.get("input_budget_used_est", 0) or 0
            )
        if not _int_or_zero(llm_meta.get("llm_input_budget_limit", 0)):
            llm_meta["llm_input_budget_limit"] = int(
                patch_budget_stats.get("input_budget_limit", cfg.llm.max_input_tokens_patch) or 0
            )
        llm_meta["llm_dropped_locators_count"] = int(
            llm_meta.get(
                "llm_dropped_locators_count",
                patch_budget_stats.get("dropped_locators_count", 0),
            )
            or 0
        )
        llm_meta["llm_dropped_hunks_count"] = int(
            llm_meta.get(
                "llm_dropped_hunks_count",
                patch_budget_stats.get("dropped_hunks_count", 0),
            )
            or 0
        )
        llm_meta["llm_dropped_snippets_count"] = int(
            llm_meta.get(
                "llm_dropped_snippets_count",
                patch_budget_stats.get("dropped_snippets_count", 0),
            )
            or 0
        )
    _merge_llm_meta(audit_summary, llm_meta)
    audit_summary["command"] = cmd
    if cmd == "review":
        if review_generation_result == "single_call" and use_batch_mode:
            review_generation_result = "batch_mode"
        if (
            review_generation_result == "single_call"
            and not bool(llm_meta.get("llm_used", False))
            and _int_or_zero(llm_meta.get("llm_provider_http_status", 0)) > 0
        ):
            review_generation_result = "provider_failed"
        review_risk_drivers = review.get("risk_drivers", [])
        if not isinstance(review_risk_drivers, list):
            review_risk_drivers = []
        audit_summary["review_batch_mode"] = bool(batch_result.get("batch_used", False) or use_batch_mode)
        audit_summary["review_batch_count"] = int(batch_result.get("executed_batches", 0) or 0)
        audit_summary["review_compacted"] = bool(
            review_compaction_attempted
            or review_budget_stats.get("review_compacted", False)
            or llm_meta.get("llm_compacted", False)
        )
        audit_summary["review_generation_result"] = review_generation_result
        audit_summary["review_risk_drivers"] = list(
            dict.fromkeys(str(item).strip() for item in review_risk_drivers if str(item).strip())
        )[:3]
        summary_text_probe = str(review.get("summary_text", "") or "")
        normalized_summary_probe = " ".join(summary_text_probe.strip().split())
        audit_summary["tldr_compressed"] = bool(
            review_compaction_attempted
            or ("\n" in summary_text_probe.strip())
            or (len(normalized_summary_probe) < len(summary_text_probe.strip()))
        )
    if cmd == "fix":
        audit_summary["patch_target_files_count"] = len(changed_files)
        audit_summary["patch_grounding_mode"] = "pr_metadata" if pr_metadata_available else "retrieval"
        audit_summary["patch_generation_result"] = str(
            audit_summary.get("patch_generation_result", "pending") or "pending"
        )
    desired_llm = str(audit_summary.get("execution_mode", "retrieval_only")) == "retrieval_plus_llm"
    if desired_llm and not bool(llm_meta.get("llm_used", False)):
        override_reason = _runtime_override_reason_from_skip(str(llm_meta.get("llm_skip_reason", "n/a")))
    else:
        override_reason = "n/a"
    audit_summary["llm_runtime_override_reason"] = override_reason
    llm_meta["llm_runtime_override_reason"] = override_reason
    llm_http_debug_payload: dict[str, Any] | None = None
    provider_http_status = llm_meta.get("llm_provider_http_status")
    provider_error_type = str(llm_meta.get("llm_provider_error_type", "n/a") or "n/a")
    provider_error_present = provider_http_status is not None or provider_error_type not in {"n/a", ""}
    if (
        cmd == "fix"
        and not bool(llm_meta.get("llm_used", False))
        and provider_error_present
        and os.environ.get("GITHUB_EVENT_NAME", "").strip() == "workflow_dispatch"
    ):
        llm_http_debug_payload = _build_llm_http_debug_payload(
            llm_meta=llm_meta,
            decision_route=str(audit_summary.get("route_final", "n/a") or "n/a"),
        )
        llm_http_debug_path = _write_llm_http_debug(repo_root, llm_http_debug_payload)
        audit_summary["llm_http_debug_artifact"] = llm_http_debug_path.as_posix()
    model_counts = llm_meta.get("llm_model_counts", {})
    if isinstance(model_counts, dict):
        model_counts_str = ", ".join(
            f"{model} ({count} calls)"
            for model, count in sorted(model_counts.items(), key=lambda kv: kv[0])
        )
        audit_summary["llm_models_used"] = model_counts_str or "n/a"
    llm_used_flag = bool(llm_meta.get("llm_used", False))
    preferred_model_id = str(llm_meta.get("llm_preferred_model_id", "n/a") or "n/a")
    final_synthesis_model_id = str(
        llm_meta.get("llm_final_synthesis_model_id", llm_meta.get("llm_model_used", "not used"))
        or "not used"
    )
    final_synthesis_retained_preferred = (
        llm_used_flag
        and preferred_model_id not in {"", "n/a", "not used"}
        and final_synthesis_model_id == preferred_model_id
    )
    has_mini_calls = isinstance(model_counts, dict) and any(
        "mini" in str(model).lower() and _int_or_zero(count) > 0
        for model, count in model_counts.items()
    )
    intermediate_downgrade_occurred = bool(final_synthesis_retained_preferred and has_mini_calls)
    intermediate_downgrade_reason = "n/a"
    if intermediate_downgrade_occurred:
        intermediate_downgrade_reason = str(
            llm_meta.get("llm_model_downgrade_reason", "n/a") or "n/a"
        )
        if intermediate_downgrade_reason == "n/a":
            intermediate_downgrade_reason = str(llm_meta.get("llm_budget_action", "n/a") or "n/a")
    llm_meta["llm_final_synthesis_retained_preferred_model"] = final_synthesis_retained_preferred
    llm_meta["llm_intermediate_downgrade_occurred"] = intermediate_downgrade_occurred
    llm_meta["llm_intermediate_downgrade_reason"] = intermediate_downgrade_reason
    audit_summary["llm_final_synthesis_retained_preferred_model"] = final_synthesis_retained_preferred
    audit_summary["llm_intermediate_downgrade_occurred"] = intermediate_downgrade_occurred
    audit_summary["llm_intermediate_downgrade_reason"] = intermediate_downgrade_reason
    if not bool(llm_meta.get("llm_used", False)):
        audit_summary["llm_model_used"] = "not used"
        audit_summary["llm_final_synthesis_model_id"] = "not used"
    elif not str(audit_summary.get("llm_final_synthesis_model_id", "")).strip():
        audit_summary["llm_final_synthesis_model_id"] = str(
            audit_summary.get("llm_model_used", "not used") or "not used"
        )
    audit_summary["llm_batch_used"] = bool(batch_result.get("batch_used", False))
    audit_summary["llm_batch_calls"] = int(llm_meta.get("llm_calls_this_run", 0) or 0)
    audit_summary["llm_batch_planned"] = int(batch_result.get("planned_batches", 0) or 0)
    audit_summary["llm_batch_executed"] = int(batch_result.get("executed_batches", 0) or 0)

    batch_summaries_raw = batch_result.get("summaries", [])
    if isinstance(batch_summaries_raw, list) and batch_summaries_raw:
        payload = {
            "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "task": cmd,
            "intent": llm_intent,
            "summaries": batch_summaries_raw,
        }
        path = _write_batch_summaries(repo_root, payload)
        audit_summary["batch_summaries_artifact"] = path.as_posix()
    if cmd == "review":
        review_debug_payload = {
            "attempted_compaction": bool(review_compaction_attempted),
            "attempted_review_batching": bool(review_batching_attempted or batch_result.get("batch_used", False)),
            "estimated_input_tokens": int(review_estimated_input_tokens),
            "final_summary_count": len(
                [
                    str(item).strip()
                    for item in str(review.get("summary_text", "") or "").splitlines()
                    if str(item).strip()
                ]
            ),
            "provider_http_status": llm_meta.get("llm_provider_http_status"),
            "provider_error_type": str(llm_meta.get("llm_provider_error_type", "n/a") or "n/a"),
            "review_generation_result": str(audit_summary.get("review_generation_result", "n/a") or "n/a"),
            "review_batch_mode": bool(audit_summary.get("review_batch_mode", False)),
            "review_batch_count": int(audit_summary.get("review_batch_count", 0) or 0),
            "review_compacted": bool(audit_summary.get("review_compacted", False)),
            "dropped_files_count": int(review_budget_stats.get("dropped_files_count", 0) or 0),
            "dropped_findings_count": int(review_budget_stats.get("dropped_findings_count", 0) or 0),
            "dropped_hunks_count": int(review_budget_stats.get("dropped_hunks_count", 0) or 0),
        }
        review_debug_path = _write_review_generation_debug(repo_root, review_debug_payload)
        audit_summary["review_generation_debug_artifact"] = review_debug_path.as_posix()

    diagnostic_markdown = render_diagnostic_summary_markdown(audit_summary)
    diagnostic_path = _write_diagnostic_summary_markdown(repo_root, diagnostic_markdown)
    audit_summary["diagnostic_summary_artifact"] = "artifacts/diagnostic_summary.md"

    check_annotations = _build_check_annotations_from_candidates(
        review_candidates,
        route=str(audit_summary.get("route_final", "REVIEW")),
        verification_report=verification_report,
    )
    check_intent = "patch" if cmd == "fix" else "review"

    if cmd != "fix":
        body = render_review_markdown(
            review=review,
            verification_report=verification_report,
            audit_summary=audit_summary,
        )
        body, truncated = enforce_comment_limit(body)
        if truncated:
            artifact_path = _write_ask_result_markdown(repo_root, body)
            if audit is not None:
                audit["comment_truncated"] = True
                audit["ask_result_artifact"] = artifact_path.as_posix()
        if audit is not None:
            audit["route_final"] = str(audit_summary.get("route_final", "REVIEW"))
            audit["pass_count"] = 1
            audit["retrieved"] = len(files)
            audit["selected"] = len(review.get("files_changed", []))
            audit["review_tldr"] = " ".join(str(review.get("summary_text", "") or "").strip().split())
            audit["review_risk_level"] = str(review.get("risk_level", "low") or "low").upper()
            audit["repobrain_version"] = REPOBRAIN_VERSION
            audit["tkya_backend"] = str(cfg.tkya.backend or "lite")
            audit["verification_pass_count"] = pass_count
            audit["verification_fail_count"] = fail_count
            audit["verification_not_run_count"] = not_run_count
            audit["tky_mode_used"] = str(audit_summary.get("tky_mode_used", "n/a"))
            audit["tky_engine"] = str(audit_summary.get("tky_engine", "n/a"))
            audit["pr_head_sha"] = head_sha
            audit["check_annotations_raw"] = check_annotations
            audit["check_intent"] = check_intent
            audit["verification_report"] = verification_report
            audit["llm_batch_used"] = bool(batch_result.get("batch_used", False))
            audit["llm_batch_planned"] = int(batch_result.get("planned_batches", 0) or 0)
            audit["llm_batch_executed"] = int(batch_result.get("executed_batches", 0) or 0)
            audit["batch_summaries_artifact"] = str(
                audit_summary.get("batch_summaries_artifact", "n/a") or "n/a"
            )
            audit["diagnostic_summary_artifact"] = diagnostic_path.as_posix()
            audit["review_validation_artifact"] = review_validation_path.as_posix()
            audit["review_generation_debug_artifact"] = str(
                audit_summary.get("review_generation_debug_artifact", "n/a") or "n/a"
            )
            audit["review_confirmed_findings_count"] = int(
                audit_summary.get("review_confirmed_findings_count", 0) or 0
            )
            audit["review_possible_signals_count"] = int(
                audit_summary.get("review_possible_signals_count", 0) or 0
            )
            audit["review_risk_drivers_count"] = int(
                audit_summary.get("review_risk_drivers_count", 0) or 0
            )
            audit["review_informational_notes_count"] = int(
                audit_summary.get("review_informational_notes_count", 0) or 0
            )
            audit["review_batch_mode"] = bool(audit_summary.get("review_batch_mode", False))
            audit["review_batch_count"] = int(audit_summary.get("review_batch_count", 0) or 0)
            audit["review_compacted"] = bool(audit_summary.get("review_compacted", False))
            audit["review_generation_result"] = str(
                audit_summary.get("review_generation_result", "n/a") or "n/a"
            )
            audit["hybrid_rerank_used"] = bool(audit_summary.get("hybrid_rerank_used", False))
            audit["retrieval_ranking_mode"] = str(
                audit_summary.get("retrieval_ranking_mode", "lexical") or "lexical"
            )
            audit["evidence_filtered_count"] = int(audit_summary.get("evidence_filtered_count", 0) or 0)
            audit["evidence_filter_reason_codes"] = str(
                audit_summary.get("evidence_filter_reason_codes", "none") or "none"
            )
            audit["incremental_retrieval_used"] = bool(
                audit_summary.get("incremental_retrieval_used", False)
            )
            audit["incremental_scope_mode"] = str(
                audit_summary.get("incremental_scope_mode", "fallback_full") or "fallback_full"
            )
            audit["changed_files_considered"] = int(
                audit_summary.get("changed_files_considered", 0) or 0
            )
            audit["changed_regions_considered"] = int(
                audit_summary.get("changed_regions_considered", 0) or 0
            )
            audit["unchanged_files_skipped"] = int(
                audit_summary.get("unchanged_files_skipped", 0) or 0
            )
            audit["unchanged_chunks_skipped"] = int(
                audit_summary.get("unchanged_chunks_skipped", 0) or 0
            )
            audit["retrieval_cache_hits"] = int(audit_summary.get("retrieval_cache_hits", 0) or 0)
            audit["retrieval_cache_misses"] = int(
                audit_summary.get("retrieval_cache_misses", 0) or 0
            )
            audit["incremental_fallback_reason"] = str(
                audit_summary.get("incremental_fallback_reason", "none") or "none"
            )
            audit["evidence_budget_used"] = int(audit_summary.get("evidence_budget_used", 0) or 0)
            audit["evidence_budget_limit"] = int(audit_summary.get("evidence_budget_limit", 0) or 0)
            audit["evidence_budget_mode"] = str(
                audit_summary.get("evidence_budget_mode", "not_applied") or "not_applied"
            )
            audit["evidence_budget_bucket_counts"] = str(
                audit_summary.get(
                    "evidence_budget_bucket_counts",
                    "changed_primary:0,changed_secondary:0,support_context:0,tests:0,docs:0,workflow_config:0",
                )
                or "changed_primary:0,changed_secondary:0,support_context:0,tests:0,docs:0,workflow_config:0"
            )
            audit["evidence_budget_cutoffs"] = str(
                audit_summary.get("evidence_budget_cutoffs", "no_cutoff") or "no_cutoff"
            )
            audit["evidence_budget_overflow"] = int(audit_summary.get("evidence_budget_overflow", 0) or 0)
            audit["evidence_budget_primary_selected"] = int(
                audit_summary.get("evidence_budget_primary_selected", 0) or 0
            )
            audit["evidence_budget_support_selected"] = int(
                audit_summary.get("evidence_budget_support_selected", 0) or 0
            )
            audit["pr_segmentation_used"] = bool(audit_summary.get("pr_segmentation_used", False))
            audit["pr_segment_count"] = int(audit_summary.get("pr_segment_count", 0) or 0)
            audit["pr_primary_segments"] = str(audit_summary.get("pr_primary_segments", "none") or "none")
            audit["pr_support_segments"] = str(audit_summary.get("pr_support_segments", "none") or "none")
            audit["pr_cross_segment"] = bool(audit_summary.get("pr_cross_segment", False))
            audit["pr_segment_summary"] = str(audit_summary.get("pr_segment_summary", "none") or "none")
            audit["pr_segment_file_counts"] = str(audit_summary.get("pr_segment_file_counts", "none") or "none")
            audit["pr_segment_candidate_counts"] = str(
                audit_summary.get("pr_segment_candidate_counts", "none") or "none"
            )
            audit["pr_segmentation_fallback_reason"] = str(
                audit_summary.get("pr_segmentation_fallback_reason", "none") or "none"
            )
            audit["signal_calibration_used"] = bool(audit_summary.get("signal_calibration_used", False))
            audit["patch_guard_triggered"] = bool(audit_summary.get("patch_guard_triggered", False))
            audit["tldr_compressed"] = bool(audit_summary.get("tldr_compressed", False))
            _merge_llm_meta(audit, llm_meta)
            audit["llm_usage_payload"] = _build_llm_usage_payload(llm_meta)
        return body

    patch_text = _apply_fix_localization_gate(
        patch_text=_extract_patch_from_stats(compression_stats),
        no_localized_patch_target=no_localized_patch_target,
    )
    patch_parts_raw = batch_result.get("patch_parts", [])
    patch_parts = patch_parts_raw if isinstance(patch_parts_raw, list) else []
    if no_localized_patch_target:
        patch_parts = []
    merged_batch_patch = ""
    batch_patch_conflicts = False
    batch_patch_conflict_details: list[str] = []
    if patch_parts:
        merged_batch_patch, batch_patch_conflicts, batch_patch_conflict_details = _merge_patch_parts(
            [item for item in patch_parts if isinstance(item, dict)]
        )
        if merged_batch_patch.strip():
            patch_text = merged_batch_patch
    found_fenced_diff = False
    found_raw_diff = False
    found_json_envelope = False
    no_patch_response = False
    patch_guard_triggered = False
    patch_guard_reason_code = "n/a"
    patch_guard_reason_short = "n/a"
    extraction_path_used = "none"
    response_chars = 0
    if no_localized_patch_target:
        no_patch_response = True
        extraction_path_used = "patch_targeting_no_patch"
    if not patch_text and llm_text_for_patch:
        patch_guard_decision = evaluate_patch_payload(llm_text_for_patch)
        if patch_guard_decision.triggered:
            patch_guard_triggered = True
            patch_guard_reason_code = patch_guard_decision.reason_code
            patch_guard_reason_short = patch_guard_decision.reason_short
            no_patch_response = True
            extraction_path_used = "patch_guard"
            response_chars = len(str(llm_text_for_patch or "").strip())
    if not patch_text and llm_text_for_patch and not patch_guard_triggered:
        (
            patch_text,
            found_fenced_diff,
            found_raw_diff,
            found_json_envelope,
            no_patch_response,
            extraction_path_used,
            response_chars,
        ) = _extract_patch_candidate(llm_text_for_patch)
    audit_summary["patch_guard_triggered"] = bool(patch_guard_triggered)
    if patch_guard_triggered:
        audit_summary["patch_guard_reason_code"] = patch_guard_reason_code
    if not patch_text and not no_patch_response and bool(batch_result.get("no_patch_returned", False)):
        no_patch_response = True
        extraction_path_used = "batch_no_patch"

    patch_validation_failed = False
    patch_validation_payload: dict[str, Any] = {
        "status": "no_patch",
        "reason_code": "NO_PATCH",
        "reason_short": "No patch returned by model/engine.",
        "valid": False,
        "touched_files": [],
        "placeholder_detected": False,
        "grounded": False,
    }
    if patch_text:
        patch_validation_payload = validate_patch_grounding(
            patch_text=patch_text,
            pr_changed_files=changed_files,
            command_type=cmd,
        )
        if not bool(patch_validation_payload.get("valid", False)):
            patch_validation_failed = True
            patch_text = ""

    patch_written = False
    patch_apply_message = "safe no_patch outcome: no sufficiently localized, evidence-backed patch target."
    patch_apply_result: dict[str, Any] = {
        "applied": False,
        "pushed": False,
        "branch": "",
        "message": patch_apply_message,
    }
    patch_pr_message = "auto-pr skipped"
    patch_debug_payload: dict[str, Any] | None = None
    snippet = ""
    if patch_validation_failed:
        patch_apply_message = str(
            patch_validation_payload.get(
                "reason_short",
                "patch validation failed",
            )
            or "patch validation failed"
        )
        patch_pr_message = "auto-pr skipped (validation failed)"
    if patch_text:
        patch_path = _write_patch_artifact(repo_root, patch_text)
        patch_written = True
        snippet = _patch_snippet(patch_text, max_lines=300)
        if batch_patch_conflicts:
            patch_apply_message = "conflicting patch parts detected; auto-apply skipped"
            patch_pr_message = "auto-pr skipped (conflicting patch parts)"
            audit_summary["route_final"] = "WAIT"
            review_summary = str(review.get("summary_text", "") or "").strip()
            review["summary_text"] = (
                f"{review_summary}\n\nConflicting patch parts were detected across batches. "
                "Review partial diffs in artifacts and resolve manually."
            ).strip()
        else:
            patch_apply_result = _maybe_apply_patch(repo_root=repo_root, patch_path=patch_path)
            patch_apply_message = str(patch_apply_result.get("message", patch_apply_message))
            patch_branch = str(patch_apply_result.get("branch", "") or "")
            if client is not None and patch_branch and bool(patch_apply_result.get("pushed", False)):
                base_branch = ""
                if isinstance(github_context_seed, dict):
                    base_branch = str(github_context_seed.get("base_ref", "") or "").strip()
                if not base_branch:
                    base_branch = extract_branch_from_env()
                patch_pr_message = _maybe_create_patch_pr(
                    repo_name=repo_name,
                    token=client.token,
                    patch_branch=patch_branch,
                    base_branch=base_branch or "main",
                    body_markdown=(
                        "RepoBrain generated and applied a suggested patch.\n\n"
                        f"Verification: {verification_report.get('summary', 'n/a')}"
                    ),
                )
            else:
                patch_pr_message = "auto-pr skipped (patch not pushed)"
    else:
        provider_http_status = llm_meta.get("llm_provider_http_status")
        provider_error_type = str(llm_meta.get("llm_provider_error_type", "n/a") or "n/a")
        if _int_or_zero(provider_http_status) == 413:
            provider_error_type = "payload_too_large"
        if patch_validation_failed:
            patch_validation_payload["status"] = "patch_validation_failed"
            patch_validation_payload["reason_code"] = str(
                patch_validation_payload.get("reason_code", "PATCH_VALIDATION_FAILED")
                or "PATCH_VALIDATION_FAILED"
            )
        elif no_patch_response:
            patch_validation_payload["status"] = "no_patch"
            if patch_guard_triggered:
                patch_validation_payload["reason_code"] = patch_guard_reason_code
                patch_validation_payload["reason_short"] = patch_guard_reason_short
                patch_apply_message = "safe no_patch outcome: placeholder/generic patch output rejected early."
                patch_pr_message = "auto-pr skipped (patch_guard)"
            else:
                patch_validation_payload["reason_code"] = "NO_PATCH"
                patch_validation_payload["reason_short"] = (
                    "No patch generated: no sufficiently localized, evidence-backed patch target was found."
                )
                patch_apply_message = (
                    "safe no_patch outcome: no sufficiently localized, evidence-backed patch target."
                )
                patch_pr_message = "auto-pr skipped (no_patch)"
        elif provider_http_status is not None or provider_error_type not in {"n/a", ""}:
            patch_validation_payload["status"] = "provider_failed"
            patch_validation_payload["reason_code"] = "PROVIDER_FAILED"
            patch_validation_payload["reason_short"] = "Patch generation failed due to LLM provider error."
            patch_apply_message = "patch generation failed due to LLM provider error"
            patch_pr_message = "auto-pr skipped (provider_failed)"
        else:
            patch_validation_payload["status"] = "patch_validation_failed"
            patch_validation_payload["reason_code"] = "PATCH_MISSING"
            patch_validation_payload["reason_short"] = (
                "Patch validation failed: no grounded unified diff could be extracted."
            )
            patch_apply_message = "patch extraction failed: no grounded unified diff"
            patch_pr_message = "auto-pr skipped (patch_missing)"
        patch_debug_payload = {
            "reason": (
                "patch_validation_failed"
                if patch_validation_failed
                else (
                    "patch_placeholder_detected"
                    if patch_guard_triggered
                    else ("no_patch_returned" if no_patch_response else "patch_missing")
                )
            ),
            "reason_code": str(patch_validation_payload.get("reason_code", "n/a") or "n/a"),
            "request_mode": "patch",
            "llm_used": bool(llm_meta.get("llm_used", False)),
            "model": str(llm_meta.get("llm_model_used", "n/a") or "n/a"),
            "effective_model_id": str(llm_meta.get("llm_effective_model_id", "n/a") or "n/a"),
            "fallback_used": bool(llm_meta.get("llm_fallback_used", False)),
            "llm_skip_reason": str(llm_meta.get("llm_skip_reason", "n/a") or "n/a"),
            "decision_route": str(audit_summary.get("route_final", "n/a") or "n/a"),
            "governor_reason": str(llm_meta.get("llm_governor_reason", "n/a") or "n/a"),
            "provider_http_status": provider_http_status,
            "provider_error_type": provider_error_type,
            "patch_guard_triggered": bool(patch_guard_triggered),
            "patch_guard_reason_code": patch_guard_reason_code,
            "patch_guard_reason_short": patch_guard_reason_short,
            "extracted_len": len(str(patch_text or "").strip()),
            "found_fenced_diff": bool(found_fenced_diff),
            "found_raw_diff": bool(found_raw_diff),
            "has_json_envelope": bool(found_json_envelope),
            "has_no_patch": bool(no_patch_response),
            "extraction_path_used": str(extraction_path_used or "none"),
            "response_chars": int(response_chars),
            "raw_output_shape": {
                "has_diff_fence": bool(found_fenced_diff),
                "has_raw_diff": bool(found_raw_diff),
                "has_json_envelope": bool(found_json_envelope),
                "has_no_patch": bool(no_patch_response),
            },
            "estimated_input_tokens": int(llm_meta.get("llm_input_budget_used_est", 0) or 0),
            "max_output_tokens_used": int(llm_meta.get("llm_max_output_tokens_used", 0) or 0),
            "patch_batch_mode": bool(llm_meta.get("llm_patch_batch_mode", False)),
            "patch_batch_count": int(llm_meta.get("llm_patch_batch_count", 0) or 0),
            "compacted": bool(llm_meta.get("llm_compacted", False)),
            "dropped_locators_count": int(llm_meta.get("llm_dropped_locators_count", 0) or 0),
            "dropped_hunks_count": int(llm_meta.get("llm_dropped_hunks_count", 0) or 0),
            "dropped_snippets_count": int(llm_meta.get("llm_dropped_snippets_count", 0) or 0),
            "attempted_compaction": bool(llm_meta.get("llm_attempted_compaction", False)),
            "attempted_patch_batch": bool(llm_meta.get("llm_attempted_patch_batch", False)),
            "output_truncated": False,
            "patch_validation_status": str(
                patch_validation_payload.get("status", "patch_validation_failed")
                or "patch_validation_failed"
            ),
            "patch_validation_reason_code": str(
                patch_validation_payload.get("reason_code", "n/a") or "n/a"
            ),
            "patch_validation_reason_short": str(
                patch_validation_payload.get("reason_short", "n/a") or "n/a"
            ),
            "patch_target_files_total": int(audit_summary.get("patch_target_files_total", 0) or 0),
            "patch_target_files_selected": int(
                audit_summary.get("patch_target_files_selected", 0) or 0
            ),
            "patch_targeting_mode": str(
                audit_summary.get("patch_targeting_mode", "n/a") or "n/a"
            ),
            "patch_targeting_reason": str(
                audit_summary.get("patch_targeting_reason", "n/a") or "n/a"
            ),
            "localized_patch_evidence_count": int(
                audit_summary.get("localized_patch_evidence_count", 0) or 0
            ),
        }
        debug_path = _write_patch_generation_debug(repo_root, patch_debug_payload)
        audit_summary["patch_generation_debug_artifact"] = debug_path.as_posix()
    patch_validation_path = _write_patch_validation(repo_root, patch_validation_payload)
    audit_summary["patch_validation_result"] = str(
        patch_validation_payload.get("status", "no_patch") or "no_patch"
    )
    audit_summary["patch_generation_result"] = str(
        patch_validation_payload.get("status", "no_patch") or "no_patch"
    )
    audit_summary["patch_validation_reason"] = str(
        patch_validation_payload.get("reason_short", "n/a") or "n/a"
    )
    audit_summary["patch_generation_reason_code"] = str(
        patch_validation_payload.get("reason_code", "n/a") or "n/a"
    )
    audit_summary["patch_validation_artifact"] = "artifacts/patch_validation.json"
    combined_patch_message = f"{patch_apply_message}; {patch_pr_message}"

    body = render_patch_markdown(
        review=review,
        verification_report=verification_report,
        patch_snippet=snippet,
        patch_written=patch_written,
        patch_apply_message=combined_patch_message,
        audit_summary=audit_summary,
    )
    body, truncated = enforce_comment_limit(body)
    if truncated:
        artifact_path = _write_ask_result_markdown(repo_root, body)
        if audit is not None:
            audit["comment_truncated"] = True
            audit["ask_result_artifact"] = artifact_path.as_posix()

    if audit is not None:
        audit["route_final"] = str(audit_summary.get("route_final", "REVIEW"))
        audit["pass_count"] = 1
        audit["retrieved"] = len(files)
        audit["selected"] = len(review.get("files_changed", []))
        audit["review_tldr"] = " ".join(str(review.get("summary_text", "") or "").strip().split())
        audit["review_risk_level"] = str(review.get("risk_level", "low") or "low").upper()
        audit["repobrain_version"] = REPOBRAIN_VERSION
        audit["tkya_backend"] = str(cfg.tkya.backend or "lite")
        audit["verification_pass_count"] = pass_count
        audit["verification_fail_count"] = fail_count
        audit["verification_not_run_count"] = not_run_count
        audit["patch_generated"] = patch_written
        audit["patch_apply_message"] = patch_apply_message
        audit["patch_pr_message"] = patch_pr_message
        audit["patch_branch"] = str(patch_apply_result.get("branch", "") or "")
        audit["tky_mode_used"] = str(audit_summary.get("tky_mode_used", "n/a"))
        audit["tky_engine"] = str(audit_summary.get("tky_engine", "n/a"))
        audit["pr_head_sha"] = head_sha
        audit["check_annotations_raw"] = check_annotations
        audit["check_intent"] = check_intent
        audit["verification_report"] = verification_report
        audit["llm_batch_used"] = bool(batch_result.get("batch_used", False))
        audit["llm_batch_planned"] = int(batch_result.get("planned_batches", 0) or 0)
        audit["llm_batch_executed"] = int(batch_result.get("executed_batches", 0) or 0)
        audit["batch_summaries_artifact"] = str(
            audit_summary.get("batch_summaries_artifact", "n/a") or "n/a"
        )
        audit["diagnostic_summary_artifact"] = diagnostic_path.as_posix()
        audit["review_validation_artifact"] = review_validation_path.as_posix()
        audit["review_confirmed_findings_count"] = int(
            audit_summary.get("review_confirmed_findings_count", 0) or 0
        )
        audit["review_possible_signals_count"] = int(
            audit_summary.get("review_possible_signals_count", 0) or 0
        )
        audit["patch_parts_count"] = len(patch_parts)
        audit["patch_conflicts_detected"] = batch_patch_conflicts
        audit["patch_conflict_details"] = batch_patch_conflict_details[:20]
        audit["patch_validation_result"] = str(
            audit_summary.get("patch_validation_result", "n/a") or "n/a"
        )
        audit["patch_generation_result"] = str(
            audit_summary.get("patch_generation_result", "n/a") or "n/a"
        )
        audit["patch_validation_reason"] = str(
            audit_summary.get("patch_validation_reason", "n/a") or "n/a"
        )
        audit["patch_target_files_count"] = int(
            audit_summary.get("patch_target_files_count", 0) or 0
        )
        audit["patch_target_files_selected"] = int(
            audit_summary.get("patch_target_files_selected", 0) or 0
        )
        audit["patch_target_files_total"] = int(
            audit_summary.get("patch_target_files_total", 0) or 0
        )
        audit["patch_targeting_mode"] = str(
            audit_summary.get("patch_targeting_mode", "n/a") or "n/a"
        )
        audit["patch_grounding_mode"] = str(
            audit_summary.get("patch_grounding_mode", "n/a") or "n/a"
        )
        audit["fix_outcome_line"] = str(
            audit_summary.get("patch_validation_reason", patch_apply_message) or patch_apply_message
        )
        audit["hybrid_rerank_used"] = bool(audit_summary.get("hybrid_rerank_used", False))
        audit["retrieval_ranking_mode"] = str(
            audit_summary.get("retrieval_ranking_mode", "lexical") or "lexical"
        )
        audit["evidence_filtered_count"] = int(audit_summary.get("evidence_filtered_count", 0) or 0)
        audit["evidence_filter_reason_codes"] = str(
            audit_summary.get("evidence_filter_reason_codes", "none") or "none"
        )
        audit["incremental_retrieval_used"] = bool(audit_summary.get("incremental_retrieval_used", False))
        audit["incremental_scope_mode"] = str(
            audit_summary.get("incremental_scope_mode", "fallback_full") or "fallback_full"
        )
        audit["changed_files_considered"] = int(
            audit_summary.get("changed_files_considered", 0) or 0
        )
        audit["changed_regions_considered"] = int(
            audit_summary.get("changed_regions_considered", 0) or 0
        )
        audit["unchanged_files_skipped"] = int(
            audit_summary.get("unchanged_files_skipped", 0) or 0
        )
        audit["unchanged_chunks_skipped"] = int(
            audit_summary.get("unchanged_chunks_skipped", 0) or 0
        )
        audit["retrieval_cache_hits"] = int(audit_summary.get("retrieval_cache_hits", 0) or 0)
        audit["retrieval_cache_misses"] = int(
            audit_summary.get("retrieval_cache_misses", 0) or 0
        )
        audit["incremental_fallback_reason"] = str(
            audit_summary.get("incremental_fallback_reason", "none") or "none"
        )
        audit["evidence_budget_used"] = int(audit_summary.get("evidence_budget_used", 0) or 0)
        audit["evidence_budget_limit"] = int(audit_summary.get("evidence_budget_limit", 0) or 0)
        audit["evidence_budget_mode"] = str(
            audit_summary.get("evidence_budget_mode", "not_applied") or "not_applied"
        )
        audit["evidence_budget_bucket_counts"] = str(
            audit_summary.get(
                "evidence_budget_bucket_counts",
                "changed_primary:0,changed_secondary:0,support_context:0,tests:0,docs:0,workflow_config:0",
            )
            or "changed_primary:0,changed_secondary:0,support_context:0,tests:0,docs:0,workflow_config:0"
        )
        audit["evidence_budget_cutoffs"] = str(
            audit_summary.get("evidence_budget_cutoffs", "no_cutoff") or "no_cutoff"
        )
        audit["evidence_budget_overflow"] = int(audit_summary.get("evidence_budget_overflow", 0) or 0)
        audit["evidence_budget_primary_selected"] = int(
            audit_summary.get("evidence_budget_primary_selected", 0) or 0
        )
        audit["evidence_budget_support_selected"] = int(
            audit_summary.get("evidence_budget_support_selected", 0) or 0
        )
        audit["pr_segmentation_used"] = bool(audit_summary.get("pr_segmentation_used", False))
        audit["pr_segment_count"] = int(audit_summary.get("pr_segment_count", 0) or 0)
        audit["pr_primary_segments"] = str(audit_summary.get("pr_primary_segments", "none") or "none")
        audit["pr_support_segments"] = str(audit_summary.get("pr_support_segments", "none") or "none")
        audit["pr_cross_segment"] = bool(audit_summary.get("pr_cross_segment", False))
        audit["pr_segment_summary"] = str(audit_summary.get("pr_segment_summary", "none") or "none")
        audit["pr_segment_file_counts"] = str(audit_summary.get("pr_segment_file_counts", "none") or "none")
        audit["pr_segment_candidate_counts"] = str(
            audit_summary.get("pr_segment_candidate_counts", "none") or "none"
        )
        audit["pr_segmentation_fallback_reason"] = str(
            audit_summary.get("pr_segmentation_fallback_reason", "none") or "none"
        )
        audit["signal_calibration_used"] = bool(audit_summary.get("signal_calibration_used", False))
        audit["patch_guard_triggered"] = bool(audit_summary.get("patch_guard_triggered", False))
        audit["tldr_compressed"] = bool(audit_summary.get("tldr_compressed", False))
        audit["patch_validation_artifact"] = patch_validation_path.as_posix()
        if patch_debug_payload is not None:
            audit["patch_generation_debug"] = dict(patch_debug_payload)
            audit["patch_generation_debug_artifact"] = "artifacts/patch_generation_debug.json"
        if llm_http_debug_payload is not None:
            audit["llm_http_debug"] = dict(llm_http_debug_payload)
            audit["llm_http_debug_artifact"] = "artifacts/llm_http_debug.json"
        _merge_llm_meta(audit, llm_meta)
        audit["llm_usage_payload"] = _build_llm_usage_payload(llm_meta)
    return body


def _build_verify_markdown(
    *,
    is_pull_request: bool,
    issue_number: int | None,
    dry_run: bool,
    client: GitHubClient | None,
    audit: dict[str, Any] | None = None,
) -> str:
    if not is_pull_request:
        if audit is not None:
            audit["route_final"] = "VERIFY"
            audit["pass_count"] = 1
            audit["verify_source"] = "none"
        return (
            "Verify works in PRs (checks/CI). Create a PR and run `/repobrain verify` "
            "in PR discussion."
        )
    if issue_number is None:
        if audit is not None:
            audit["route_final"] = "VERIFY"
            audit["pass_count"] = 1
            audit["verify_source"] = "none"
        return "Verify is available in Pull Requests. Pull request number was not detected."

    if dry_run:
        report = build_verify_report({}, None, {})
        if audit is not None:
            audit["route_final"] = "VERIFY"
            audit["pass_count"] = 1
        t0 = time.perf_counter()
        body = format_verify_comment(report)
        if audit is not None:
            audit["retrieved"] = 0
            audit["selected"] = 0
            audit["checks_total"] = int(report.get("total", 0) or 0)
            audit["checks_failure"] = int(report.get("failure", 0) or 0)
            audit["checks_pending"] = int(report.get("pending", 0) or 0)
            audit["verify_source"] = str(report.get("verify_source", "none") or "none")
            add_timing(audit, "format", (time.perf_counter() - t0) * 1000.0)
        return body

    if client is None:
        raise ValueError("GitHub client is required for verify in post mode")

    pull = client.get_pull(issue_number)
    head = pull.get("head", {})
    sha = str(head.get("sha", "")) if isinstance(head, dict) else ""
    if not sha:
        fallback_sha = extract_sha_from_env()
        sha = fallback_sha or ""

    check_runs = client.get_check_runs(sha) if sha else {"total_count": 0, "check_runs": []}
    status = client.get_combined_status(sha) if sha else {"state": "unknown", "statuses": []}
    workflow_runs = client.get_workflow_runs(head_sha=sha or None)
    report = build_verify_report(check_runs, status, workflow_runs, head_sha=sha or None)
    if audit is not None:
        audit["route_final"] = "VERIFY"
        audit["pass_count"] = 1
        audit["retrieved"] = int(report.get("total", 0) or 0)
        audit["selected"] = int(report.get("failure", 0) or 0)
        audit["checks_total"] = int(report.get("total", 0) or 0)
        audit["checks_failure"] = int(report.get("failure", 0) or 0)
        audit["checks_pending"] = int(report.get("pending", 0) or 0)
        audit["verify_source"] = str(report.get("verify_source", "none") or "none")
    t0 = time.perf_counter()
    body = format_verify_comment(report)
    if audit is not None:
        add_timing(audit, "format", (time.perf_counter() - t0) * 1000.0)
    return body


def _resolve_pr_head_sha(
    *,
    client: GitHubClient | None,
    issue_number: int | None,
    audit: dict[str, Any],
    github_context_seed: dict[str, Any],
) -> str:
    sha = str(audit.get("pr_head_sha", "") or "").strip()
    if sha:
        return sha
    sha = str(github_context_seed.get("head_sha", "") or "").strip()
    if sha:
        return sha
    if client is not None and issue_number is not None:
        pull = client.get_pull(issue_number)
        head = pull.get("head", {})
        if isinstance(head, dict):
            sha = str(head.get("sha", "") or "").strip()
            if sha:
                return sha
    return extract_sha_from_env()


def _classify_check_run_failure(
    *,
    attempted: bool,
    status_code: Any,
    skip_reason: str,
) -> str:
    if not attempted:
        if skip_reason == "deferred_workflow_publisher":
            return "deferred"
        if skip_reason in {"client_missing", "head_sha_missing", "unsupported_command"}:
            return skip_reason
        return "not_attempted"
    status = _int_or_zero(status_code)
    if status in {401, 403}:
        return "permissions"
    if status in {404, 422}:
        return "missing_sha"
    if status == 0:
        return "transport"
    if status >= 500:
        return "transport"
    if status >= 200 and status < 300:
        return "none"
    return "other"


def _publish_pr_check_run(
    *,
    repo_root: Path,
    client: GitHubClient | None,
    cmd: str,
    issue_number: int | None,
    body_markdown: str,
    audit: dict[str, Any],
    github_context_seed: dict[str, Any],
) -> None:
    event_name = os.environ.get("GITHUB_EVENT_NAME", "").strip() or "unknown"
    publish_mode = os.environ.get("RB_CHECK_RUN_PUBLISH_MODE", "").strip().lower()
    if publish_mode not in {"direct", "deferred"}:
        publish_mode = "deferred" if event_name == "issue_comment" else "direct"
    check_name = check_name_for_command(cmd)
    audit["check_run_name"] = check_name
    audit.setdefault("check_run_attempted", False)
    audit.setdefault("check_run_base_conclusion", "n/a")
    audit.setdefault("check_run_conclusion", "n/a")
    audit.setdefault("check_run_published", False)
    audit.setdefault("check_run_status_code", "skipped")
    audit.setdefault("check_run_skip_reason", "n/a")
    audit.setdefault("check_run_token_source", "github_token")
    audit.setdefault("check_run_event_name", event_name)
    audit.setdefault("check_run_required_permissions_header", "n/a")
    audit.setdefault("check_run_failure_class", "not_attempted")

    token_source = (
        "workflow_run_github_token"
        if publish_mode == "deferred"
        else str(os.environ.get("RB_CHECK_RUN_TOKEN_SOURCE", "github_token") or "github_token")
    )
    audit["check_run_token_source"] = token_source
    audit["check_run_event_name"] = event_name

    if client is None:
        audit["check_run_skip_reason"] = "client_missing"
        audit["check_run_failure_class"] = _classify_check_run_failure(
            attempted=False,
            status_code=audit.get("check_run_status_code"),
            skip_reason="client_missing",
        )
        return
    if cmd not in {"ask", "locate", "explain", "review", "fix"}:
        audit["check_run_skip_reason"] = "unsupported_command"
        audit["check_run_failure_class"] = _classify_check_run_failure(
            attempted=False,
            status_code=audit.get("check_run_status_code"),
            skip_reason="unsupported_command",
        )
        return

    head_sha = _resolve_pr_head_sha(
        client=client,
        issue_number=issue_number,
        audit=audit,
        github_context_seed=github_context_seed,
    )
    if not head_sha:
        audit["check_run_skip_reason"] = "head_sha_missing"
        audit["check_run_failure_class"] = _classify_check_run_failure(
            attempted=False,
            status_code=audit.get("check_run_status_code"),
            skip_reason="head_sha_missing",
        )
        return

    verification_report_raw = audit.get("verification_report", {})
    verification_report = (
        dict(verification_report_raw) if isinstance(verification_report_raw, dict) else {}
    )
    route = str(audit.get("route_final", "FAST") or "FAST")
    intent = str(audit.get("check_intent", "analysis") or "analysis")
    base_conclusion, _headline, _details = compute_conclusion(route, verification_report, intent)
    conclusion = map_check_conclusion(
        cmd=cmd,
        audit=audit,
        base_conclusion=base_conclusion,
    )
    audit["check_run_skip_reason"] = "n/a"
    annotations_raw = audit.get("check_annotations_raw", [])
    annotations = annotations_raw if isinstance(annotations_raw, list) else []
    summary_md, text_md = build_check_summary_markdown(
        cmd=cmd,
        audit=audit,
        conclusion=conclusion,
    )
    if not str(text_md or "").strip():
        text_md = str(body_markdown or summary_md)
    payload = build_check_run_payload(
        name=check_name,
        head_sha=head_sha,
        conclusion=conclusion,
        summary_md=summary_md,
        text_md=text_md,
        annotations=annotations,
    )
    _write_check_run_payload(repo_root, payload)
    if publish_mode == "deferred":
        audit["check_run_attempted"] = False
        audit["check_run_status_code"] = "deferred"
        audit["check_run_skip_reason"] = "deferred_workflow_publisher"
        audit["check_run_required_permissions_header"] = "n/a"
        audit["check_run_failure_class"] = _classify_check_run_failure(
            attempted=False,
            status_code="deferred",
            skip_reason="deferred_workflow_publisher",
        )
        return

    audit["check_run_attempted"] = True
    result = publish_check_run(
        repo=client.repo,
        token=client.token,
        name=check_name,
        head_sha=head_sha,
        conclusion=conclusion,
        summary_md=summary_md,
        text_md=text_md,
        annotations=annotations,
    )
    audit["check_run_name"] = check_name
    audit["check_run_base_conclusion"] = base_conclusion
    audit["check_run_conclusion"] = conclusion
    audit["check_run_published"] = bool(result.get("ok", False))
    audit["check_run_status_code"] = result.get("status_code")
    audit["check_run_required_permissions_header"] = str(
        result.get("required_permissions_header", "n/a") or "n/a"
    )
    audit["check_run_failure_class"] = _classify_check_run_failure(
        attempted=True,
        status_code=audit.get("check_run_status_code"),
        skip_reason=str(audit.get("check_run_skip_reason", "n/a") or "n/a"),
    )
    if not bool(result.get("ok", False)):
        print("Check-run publish unavailable, using comment fallback only.")


def run_github_flow(
    *,
    repo_root: Path,
    dry_run: bool,
    comment_text: str,
    issue_number: int | None,
    tky_mode: str = "auto",
    remote_url: str = "",
    api_key: str = "",
    hmac_secret: str = "",
    enable_hmac: bool = False,
    event_path: Path | None = None,
) -> str:
    """Run RepoBrain GitHub flow in dry-run or post mode."""
    env_cfg = RepoBrainConfig.from_env()
    _set_runtime_env_cfg(env_cfg)
    repo_name = extract_repo_from_env()
    sha_value = extract_sha_from_env()
    run_id = os.environ.get("GITHUB_RUN_ID", "").strip()
    event_ctx = extract_event_context_from_event(event_path)
    event_payload = _load_event_payload(event_path)
    source_text = (comment_text or "").strip() or event_ctx.comment_text.strip()
    resolved_issue_number = issue_number if issue_number is not None else event_ctx.issue_number
    source_text, resolved_issue_number, event_ctx, event_payload = _resolve_workflow_dispatch_simulation(
        repo=repo_name,
        source_text=source_text,
        resolved_issue_number=resolved_issue_number,
        event_ctx=event_ctx,
        event_payload=event_payload,
    )
    github_context_seed = _build_github_context_seed(
        payload=event_payload,
        event_ctx=event_ctx,
        resolved_issue_number=resolved_issue_number,
    )
    verification_context_seed = _build_verification_context_seed(time_budget_s=30, env_cfg=env_cfg)
    mode_label = "DRY_RUN" if dry_run else "POST_MODE"
    audit = build_audit_base(
        {
            "repo": repo_name,
            "sha": sha_value,
            "run_id": run_id,
            "issue_number": resolved_issue_number,
            "pr_number": resolved_issue_number if event_ctx.is_pull_request else None,
            "comment_id": event_ctx.comment_id,
            "dry_run": dry_run,
            "posted": False,
            "mode": mode_label,
            "tky_mode_requested": tky_mode,
            "repobrain_version": REPOBRAIN_VERSION,
            "tkya_backend": str(env_cfg.tkya.backend or "lite"),
        }
    )
    governor = build_governor_from_env(cfg=env_cfg)
    audit["ai_governor_policy"] = governor.summary().get("policy", {})

    if not source_text:
        print(f"Mode={mode_label}")
        print("Cmd=help")
        print("Query=")
        print(HELP_TEXT.strip())
        audit["command"] = "help"
        audit["task_type"] = "help"
        audit["route_final"] = "HELP"
        audit["pass_count"] = 1
        t0 = time.perf_counter()
        _ = HELP_TEXT.strip()
        add_timing(audit, "format", (time.perf_counter() - t0) * 1000.0)
        _finalize_run(repo_root=repo_root, audit=audit, governor=governor)
        return "IGNORED"

    if _is_bot_login(event_ctx.comment_user_login):
        print(f"Mode={mode_label}")
        print("Cmd=ignored_bot")
        print("Query=")
        print(f"Ignored bot comment from {event_ctx.comment_user_login}")
        audit["command"] = "ignored_bot"
        audit["task_type"] = "ignored_bot"
        audit["route_final"] = "IGNORED_BOT"
        audit["pass_count"] = 1
        _finalize_run(repo_root=repo_root, audit=audit, governor=governor)
        return "IGNORED_BOT"

    if not source_text.startswith("/repobrain"):
        print(f"Mode={mode_label}")
        print("Cmd=ignored")
        print("Query=")
        print("Ignored: comment does not start with /repobrain")
        audit["command"] = "ignored"
        audit["task_type"] = "ignored"
        audit["route_final"] = "IGNORED"
        audit["pass_count"] = 1
        _finalize_run(repo_root=repo_root, audit=audit, governor=governor)
        return "IGNORED"

    t0 = time.perf_counter()
    parsed = parse_command(source_text)
    add_timing(audit, "parse", (time.perf_counter() - t0) * 1000.0)
    cmd = parsed["cmd"]
    query = parsed["query"]
    audit["command"] = cmd
    audit["task_type"] = cmd
    print(f"Mode={mode_label}")
    print(f"Cmd={cmd}")
    print(f"Query={query}")

    target_paths_raw = github_context_seed.get("changed_files", [])
    target_paths = (
        [str(item).strip() for item in target_paths_raw if str(item).strip()]
        if isinstance(target_paths_raw, list)
        else []
    )
    t0 = time.perf_counter()
    sec = classify_security_scope(
        source_text,
        github_context=github_context_seed,
        target_paths=target_paths,
        command_type=cmd,
    )
    add_timing(audit, "security_check", (time.perf_counter() - t0) * 1000.0)
    audit["security"] = sec.as_audit_dict()
    audit["security_scope"] = sec.security_scope
    audit["security_outcome"] = sec.security_outcome
    audit["security_reason_code"] = sec.security_reason_code
    audit["security_reason_short"] = sec.security_reason_short
    if sec.blocked:
        t0 = time.perf_counter()
        body_markdown = format_refusal_comment(
            reason=sec.security_reason_short,
            audit_summary={
                "route": "REFUSE",
                "security": {
                    "blocked": sec.blocked,
                    "risk": sec.risk,
                    "signals": list(sec.signals),
                    "scope": sec.security_scope,
                    "outcome": sec.security_outcome,
                    "reason_code": sec.security_reason_code,
                },
            },
        )
        add_timing(audit, "format", (time.perf_counter() - t0) * 1000.0)
        audit["route_final"] = "REFUSE"
        audit["pass_count"] = 1
        audit["index_source"] = "n/a"

        if dry_run:
            print(body_markdown)
            _finalize_run(repo_root=repo_root, audit=audit, governor=governor)
            return "DRY_RUN_OK"

        if resolved_issue_number is None:
            _finalize_run(repo_root=repo_root, audit=audit, governor=governor)
            raise ValueError("issue_number is required when dry_run=False")

        client = _build_post_client()
        if _internal_reactions_enabled() and event_ctx.comment_id is not None:
            client.add_reaction_to_issue_comment(comment_id=event_ctx.comment_id, content="eyes")
        t0 = time.perf_counter()
        client.create_issue_comment(issue_number=resolved_issue_number, body_markdown=body_markdown)
        add_timing(audit, "post", (time.perf_counter() - t0) * 1000.0)
        audit["posted"] = True
        print(f"Posted comment to issue #{resolved_issue_number}")
        _finalize_run(repo_root=repo_root, audit=audit, governor=governor)
        return "POSTED_OK"

    client: GitHubClient | None = None
    if not dry_run:
        if resolved_issue_number is None:
            _finalize_run(repo_root=repo_root, audit=audit, governor=governor)
            raise ValueError("issue_number is required when dry_run=False")
        client = _build_post_client()
        if _internal_reactions_enabled() and event_ctx.comment_id is not None:
            client.add_reaction_to_issue_comment(comment_id=event_ctx.comment_id, content="eyes")

    if cmd == "help":
        t0 = time.perf_counter()
        body_markdown = HELP_TEXT.strip()
        add_timing(audit, "format", (time.perf_counter() - t0) * 1000.0)
        audit["route_final"] = "HELP"
        audit["pass_count"] = 1
        audit["index_source"] = "n/a"
    elif cmd in {"review", "fix"}:
        body_markdown = _build_review_markdown(
            repo_root=repo_root,
            cmd=cmd,
            query=query,
            is_pull_request=event_ctx.is_pull_request,
            issue_number=resolved_issue_number,
            dry_run=dry_run,
            client=client,
            tky_mode=tky_mode,
            remote_url=remote_url,
            api_key=api_key,
            hmac_secret=hmac_secret,
            enable_hmac=enable_hmac,
            github_context_seed=github_context_seed,
            verification_context_seed=verification_context_seed,
            audit=audit,
            governor=governor,
        )
        audit["index_source"] = "n/a"
    elif cmd == "verify":
        body_markdown = _build_verify_markdown(
            is_pull_request=event_ctx.is_pull_request,
            issue_number=resolved_issue_number,
            dry_run=dry_run,
            client=client,
            audit=audit,
        )
        audit["index_source"] = "n/a"
    else:
        try:
            body_markdown = _build_qa_markdown(
                repo_root=repo_root,
                cmd=cmd,
                query=query,
                tky_mode=tky_mode,
                remote_url=remote_url,
                api_key=api_key,
                hmac_secret=hmac_secret,
                enable_hmac=enable_hmac,
                github_context_seed=github_context_seed,
                verification_context_seed=verification_context_seed,
                audit=audit,
                governor=governor,
            )
        except Exception:
            audit["route_final"] = "ERROR"
            audit["pass_count"] = 1
            body_markdown = render_error_markdown(
                message="Unexpected processing error. Try a narrower query or run again.",
                audit_summary={
                    "route_final": "ERROR",
                    "retrieved": 0,
                    "selected": 0,
                },
            )

    if event_ctx.is_pull_request and cmd in {"ask", "locate", "explain", "review", "fix"}:
        if dry_run:
            dry_head_sha = _resolve_pr_head_sha(
                client=None,
                issue_number=resolved_issue_number,
                audit=audit,
                github_context_seed=github_context_seed,
            )
            if dry_head_sha:
                verification_report_raw = audit.get("verification_report", {})
                verification_report = (
                    dict(verification_report_raw) if isinstance(verification_report_raw, dict) else {}
                )
                route = str(audit.get("route_final", "FAST") or "FAST")
                intent = str(audit.get("check_intent", "analysis") or "analysis")
                base_conclusion, _headline, _details = compute_conclusion(route, verification_report, intent)
                conclusion = map_check_conclusion(
                    cmd=cmd,
                    audit=audit,
                    base_conclusion=base_conclusion,
                )
                check_name = check_name_for_command(cmd)
                annotations_raw = audit.get("check_annotations_raw", [])
                annotations = annotations_raw if isinstance(annotations_raw, list) else []
                summary_md, text_md = build_check_summary_markdown(
                    cmd=cmd,
                    audit=audit,
                    conclusion=conclusion,
                )
                payload = build_check_run_payload(
                    name=check_name,
                    head_sha=dry_head_sha,
                    conclusion=conclusion,
                    summary_md=summary_md,
                    text_md=text_md,
                    annotations=annotations,
                )
                _write_check_run_payload(repo_root, payload)
                audit["check_run_name"] = check_name
                audit["check_run_attempted"] = False
                audit["check_run_base_conclusion"] = base_conclusion
                audit["check_run_conclusion"] = conclusion
                audit["check_run_published"] = False
                audit["check_run_status_code"] = "dry_run"
                audit["check_run_skip_reason"] = "dry_run"
                audit["check_run_token_source"] = "github_token"
                audit["check_run_event_name"] = os.environ.get("GITHUB_EVENT_NAME", "").strip() or "unknown"
                audit["check_run_required_permissions_header"] = "n/a"
                audit["check_run_failure_class"] = "not_attempted"
        else:
            _publish_pr_check_run(
                repo_root=repo_root,
                client=client,
                cmd=cmd,
                issue_number=resolved_issue_number,
                body_markdown=body_markdown,
                audit=audit,
                github_context_seed=github_context_seed,
            )

    if dry_run:
        print(body_markdown)
        _finalize_run(repo_root=repo_root, audit=audit, governor=governor)
        return "DRY_RUN_OK"

    if client is None:
        _finalize_run(repo_root=repo_root, audit=audit, governor=governor)
        raise ValueError("GitHub client was not initialized")

    t0 = time.perf_counter()
    client.create_issue_comment(issue_number=resolved_issue_number, body_markdown=body_markdown)
    add_timing(audit, "post", (time.perf_counter() - t0) * 1000.0)
    audit["posted"] = True
    print(f"Posted comment to issue #{resolved_issue_number}")
    _finalize_run(repo_root=repo_root, audit=audit, governor=governor)
    return "POSTED_OK"
