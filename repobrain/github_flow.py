from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import time
from typing import Any

import requests

from repobrain.audit import add_timing, build_audit_base, finalize_audit
from repobrain.ask import AnswerResult, answer_question, make_provider
from repobrain.commands import parse_command
from repobrain.config import RepoBrainConfig, load_config
from repobrain.evidence import EvidenceItem
from repobrain.formatting import (
    format_github_comment,
    format_pr_review_comment,
    format_refusal_comment,
    format_verify_comment,
)
from repobrain.index_store import build_index, load_index
from repobrain.retrieve_pro import retrieve_topk_pro
from repobrain.review import build_pr_review
from repobrain.security import detect_injection_or_exfiltration
from repobrain.tky_local import LocalTKYProvider
from repobrain.tky_provider import CandidateChunk, TKYResult
from repobrain.tky_remote import RemoteTKYError, RemoteTKYProvider
from repobrain.verify import build_verify_report

HELP_TEXT = """RepoBrain command examples:
- /repobrain help
- /repobrain ask How does provider selection work?
- /repobrain locate TKYProvider
- /repobrain explain retrieve_topk
- /repobrain review
- /repobrain verify (PR checks-based verification ladder v0)
"""

BOT_MARKER = "[bot]"
_LAST_AUDIT: dict[str, Any] | None = None


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
        response = requests.post(
            build_issue_comment_url(self.repo, issue_number),
            json={"body": body_markdown},
            headers=self._headers(),
            timeout=15,
        )
        response.raise_for_status()

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


def _is_bot_login(login: str) -> bool:
    normalized = (login or "").strip().lower()
    return bool(normalized) and BOT_MARKER in normalized


def _build_post_client() -> GitHubClient:
    repo = extract_repo_from_env()
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not repo:
        raise ValueError("GITHUB_REPOSITORY is required when dry_run=False")
    if not token:
        raise ValueError("GITHUB_TOKEN is required when dry_run=False")
    return GitHubClient(repo=repo, token=token)


def _internal_reactions_enabled() -> bool:
    return os.environ.get("RB_DISABLE_INTERNAL_REACTIONS", "").strip() != "1"


def _provider_engine_name(provider: Any) -> str:
    if isinstance(provider, RemoteTKYProvider):
        return "remote"
    if isinstance(provider, LocalTKYProvider):
        return "topocore_lite"
    return "baseline"


def _allow_match(value: str, allowed: tuple[str, ...]) -> bool:
    if not allowed:
        return True
    normalized = value.strip().lower()
    return normalized in {item.strip().lower() for item in allowed}


def _resolve_tky_mode_for_command(
    *,
    requested_mode: str,
    cmd: str,
    cfg: RepoBrainConfig,
    repo_name: str,
    branch_name: str,
) -> tuple[str, str]:
    mode = (requested_mode or "baseline").strip().lower()
    if mode != "remote":
        return mode, "n/a"

    if not bool(getattr(cfg, "tky_remote_enabled", False)):
        return "baseline", "remote_disabled"

    allowed_commands = tuple(
        str(item).strip().lower()
        for item in getattr(cfg, "tky_remote_allow_commands", ("ask", "explain"))
        if str(item).strip()
    )
    if allowed_commands and cmd.strip().lower() not in allowed_commands:
        return "baseline", "command_not_allowed"

    allowed_branches = tuple(
        str(item).strip().lower()
        for item in getattr(cfg, "tky_remote_allow_branches", ("main",))
        if str(item).strip()
    )
    if allowed_branches and branch_name.strip().lower() not in allowed_branches:
        return "baseline", "branch_not_allowed"

    allowed_repos = tuple(
        str(item).strip().lower()
        for item in getattr(cfg, "tky_remote_allow_repos", ())
        if str(item).strip()
    )
    if allowed_repos and repo_name.strip().lower() not in allowed_repos:
        return "baseline", "repo_not_allowed"

    return "remote", "n/a"


def _build_refuse_answer_result(question: str, reason: str) -> AnswerResult:
    tky = TKYResult(
        selected_chunk_ids=[],
        route="REFUSE",
        compression_stats={"retrieved": 0, "selected": 0},
        rationale=reason,
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
        audit_summary={"retrieved": 0, "selected": 0, "route": "REFUSE"},
        next_steps="Open evidence links and verify logic",
    )


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
    chunks, _, _ = load_or_build_chunks_with_meta(repo_root, index_path)
    return chunks


def load_or_build_chunks_with_meta(
    repo_root: Path,
    index_path: Path,
) -> tuple[list[CandidateChunk], str, float]:
    """Load/build index and return (chunks, source, elapsed_ms)."""
    started = time.perf_counter()
    existed_before = index_path.exists()
    cache_restored = os.environ.get("RB_INDEX_CACHE_RESTORED", "").strip() == "1"

    if existed_before:
        chunks = load_index(index_path)
        source = "cache_hit" if cache_restored else "artifact_present"
        return chunks, source, (time.perf_counter() - started) * 1000.0

    index_path.parent.mkdir(parents=True, exist_ok=True)
    build_index(root=repo_root, out_zip=index_path, store_text=False)
    chunks = load_index(index_path)
    return chunks, "rebuilt", (time.perf_counter() - started) * 1000.0


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


def _retrieve_candidates(
    question: str,
    chunks: list[CandidateChunk],
    *,
    topk: int,
    cmd: str,
) -> list[CandidateChunk]:
    if cmd == "ask":
        return retrieve_topk(question, chunks, topk=topk)
    return retrieve_topk_pro(question, chunks, topk=topk, task_type=cmd, max_per_file=2)


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
) -> dict[str, Any]:
    return {
        "max_sources": max_sources,
        "min_score_keep": min_score_keep,
        "keep_ratio": keep_ratio,
        "max_per_file": max_per_file,
        "max_files": max_files,
        "route_hint": route_hint,
        "task_type": cmd,
        "privacy_mode": "signatures_only",
        "policy": {"no_raw_text": True, "privacy_mode": "signatures_only"},
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
            meta["tky_engine"] = "topocore_lite"
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
    provider: Any,
    cfg: Any,
    tky_mode_requested: str = "baseline",
    remote_fail_open: bool = True,
    timings_ms: dict[str, float] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Run at most two retrieval+TKY passes using the TKY route from pass 1."""
    topk_fast = int(getattr(cfg, "topk_fast", getattr(cfg, "topk", 30)))
    topk_deep = int(getattr(cfg, "topk_deep", 80))
    min_score_fast = float(getattr(cfg, "min_score_fast", 0.05))
    active_provider = provider
    t0 = time.perf_counter()
    pass1_candidates = _retrieve_candidates(question, chunks, topk=topk_fast, cmd=cmd)
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
    pass_count = 1
    pass2_top_score: float | None = None

    should_second_pass = cmd in {"ask", "explain"} and result1.tky.route == "DEEP"
    if should_second_pass:
        t0 = time.perf_counter()
        pass2_candidates = _retrieve_candidates(question, chunks, topk=topk_deep, cmd=cmd)
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
        pass_count = 2

    audit_extra: dict[str, Any] = {
        "pass_count": pass_count,
        "pass1.top_score": round(pass1_top_score, 6),
        "route_final": final_result.tky.route,
        "top_score": round(pass2_top_score if pass2_top_score is not None else pass1_top_score, 6),
    }
    if pass2_top_score is not None:
        audit_extra["pass2.top_score"] = round(pass2_top_score, 6)
        audit_extra["top_score_pass2"] = round(pass2_top_score, 6)

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
        audit_extra["tky_engine"] = _provider_engine_name(active_provider)
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
    audit: dict[str, Any] | None = None,
) -> str:
    cfg = load_config(repo_root)
    repo_name = extract_repo_from_env()
    branch_name = extract_branch_from_env()
    effective_tky_mode, remote_skipped_reason = _resolve_tky_mode_for_command(
        requested_mode=tky_mode,
        cmd=cmd,
        cfg=cfg,
        repo_name=repo_name,
        branch_name=branch_name,
    )
    if effective_tky_mode == "remote" and not (remote_url or "").strip():
        effective_tky_mode = "baseline"
        remote_skipped_reason = "remote_url_missing"
    remote_fail_open = bool(getattr(cfg, "tky_remote_fail_open", True))
    index_path = repo_root / "artifacts" / "index-package.zip"
    question = question_from_command(cmd, query)
    chunks, index_source, index_elapsed_ms = load_or_build_chunks_with_meta(repo_root, index_path)
    if audit is not None:
        audit["index_source"] = index_source
        add_timing(audit, "index_load_build", index_elapsed_ms)
        audit["remote_skipped_reason"] = remote_skipped_reason or "n/a"
        audit["tky_mode_requested"] = tky_mode
        audit["tky_mode_used"] = effective_tky_mode

    provider = make_provider(
        effective_tky_mode,
        remote_url=remote_url or None,
        api_key=api_key or None,
        hmac_secret=hmac_secret or None,
        enable_hmac=enable_hmac,
    )
    result, loop_audit = run_qa_two_pass(
        question=question,
        cmd=cmd,
        chunks=chunks,
        provider=provider,
        cfg=cfg,
        tky_mode_requested=effective_tky_mode,
        remote_fail_open=remote_fail_open,
        timings_ms=(audit.get("timings_ms") if isinstance(audit, dict) else None),
    )
    audit_summary = dict(result.audit_summary)
    audit_summary.update(loop_audit)
    audit_summary["remote_skipped_reason"] = remote_skipped_reason or "n/a"
    audit_summary["tky_mode_requested"] = tky_mode
    audit_summary["tky_mode_used"] = str(
        audit_summary.get("tky_mode_used", effective_tky_mode or "baseline")
    )
    if "tky_engine" not in audit_summary:
        audit_summary["tky_engine"] = _provider_engine_name(provider)
    evidence_out = result.evidence
    answer_text_out = result.answer_text
    if cmd == "locate":
        evidence_out = _dedupe_evidence_by_file(result.evidence, max_files=5)
        audit_summary["route_final"] = "LOCATE"
    elif cmd == "explain":
        evidence_out = _dedupe_evidence_by_file(result.evidence, max_files=7)
        answer_text_out = _build_explain_answer(evidence_out, question)

    if audit is not None:
        audit["route_final"] = str(audit_summary.get("route_final", result.tky.route))
        audit["pass_count"] = int(audit_summary.get("pass_count", 1) or 1)
        audit["retrieved"] = int(audit_summary.get("retrieved", 0) or 0)
        audit["selected"] = len(evidence_out)
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
        audit["tky_remote_status"] = audit_summary.get("tky_remote_status", None)
        audit["tky_fallback_reason"] = str(audit_summary.get("tky_fallback_reason", "n/a") or "n/a")

    t0 = time.perf_counter()
    body = format_github_comment(
        answer_text_out,
        evidence_out,
        audit_summary,
        result.next_steps,
        command=cmd,
        repo=extract_repo_from_env() or None,
        sha=extract_sha_from_env() or None,
    )
    if audit is not None:
        add_timing(audit, "format", (time.perf_counter() - t0) * 1000.0)
    return body


def _build_review_markdown(
    *,
    is_pull_request: bool,
    issue_number: int | None,
    dry_run: bool,
    client: GitHubClient | None,
    audit: dict[str, Any] | None = None,
) -> str:
    if not is_pull_request:
        if audit is not None:
            audit["route_final"] = "REVIEW"
            audit["pass_count"] = 1
        return "Review is available in Pull Requests. Run /repobrain review in a PR discussion."

    if issue_number is None:
        if audit is not None:
            audit["route_final"] = "REVIEW"
            audit["pass_count"] = 1
        return "Review is available in Pull Requests. Pull request number was not detected."

    files: list[dict[str, Any]]
    head_sha = ""
    repo_name = extract_repo_from_env() or (client.repo if client is not None else "")
    if dry_run:
        files = []
    else:
        if client is None:
            raise ValueError("GitHub client is required for PR review in post mode")
        pull = client.get_pull(pull_number=issue_number)
        head = pull.get("head", {})
        if isinstance(head, dict):
            head_sha = str(head.get("sha", "") or "")
        files = client.get_pull_files(pull_number=issue_number)

    if not head_sha:
        head_sha = extract_sha_from_env()
    review = build_pr_review(files, head_sha=head_sha or None, repo=repo_name or None)
    if audit is not None:
        audit["route_final"] = "REVIEW"
        audit["pass_count"] = 1
        audit["retrieved"] = len(files)
        audit["selected"] = len(files)
    t0 = time.perf_counter()
    body = format_pr_review_comment(review)
    if audit is not None:
        add_timing(audit, "format", (time.perf_counter() - t0) * 1000.0)
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


def run_github_flow(
    *,
    repo_root: Path,
    dry_run: bool,
    comment_text: str,
    issue_number: int | None,
    tky_mode: str = "baseline",
    remote_url: str = "",
    api_key: str = "",
    hmac_secret: str = "",
    enable_hmac: bool = False,
    event_path: Path | None = None,
) -> str:
    """Run RepoBrain GitHub flow in dry-run or post mode."""
    event_ctx = extract_event_context_from_event(event_path)
    source_text = (comment_text or "").strip() or event_ctx.comment_text.strip()
    resolved_issue_number = issue_number if issue_number is not None else event_ctx.issue_number
    mode_label = "DRY_RUN" if dry_run else "POST_MODE"
    repo_name = extract_repo_from_env()
    sha_value = extract_sha_from_env()
    run_id = os.environ.get("GITHUB_RUN_ID", "").strip()
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
        }
    )

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
        _set_last_audit(audit)
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
        _set_last_audit(audit)
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
        _set_last_audit(audit)
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

    t0 = time.perf_counter()
    sec = detect_injection_or_exfiltration(source_text)
    add_timing(audit, "security_check", (time.perf_counter() - t0) * 1000.0)
    audit["security"] = {
        "blocked": bool(sec["blocked"]),
        "risk": sec["risk"],
        "signals": list(sec["signals"]),
    }
    if sec["blocked"]:
        t0 = time.perf_counter()
        body_markdown = format_refusal_comment(
            reason="Possible prompt-injection / exfiltration attempt was blocked.",
            audit_summary={
                "route": "REFUSE",
                "security": {
                    "blocked": sec["blocked"],
                    "risk": sec["risk"],
                    "signals": sec["signals"],
                },
            },
        )
        add_timing(audit, "format", (time.perf_counter() - t0) * 1000.0)
        audit["route_final"] = "REFUSE"
        audit["pass_count"] = 1
        audit["index_source"] = "n/a"

        if dry_run:
            print(body_markdown)
            _set_last_audit(audit)
            return "DRY_RUN_OK"

        if resolved_issue_number is None:
            _set_last_audit(audit)
            raise ValueError("issue_number is required when dry_run=False")

        client = _build_post_client()
        if _internal_reactions_enabled() and event_ctx.comment_id is not None:
            client.add_reaction_to_issue_comment(comment_id=event_ctx.comment_id, content="eyes")
        t0 = time.perf_counter()
        client.create_issue_comment(issue_number=resolved_issue_number, body_markdown=body_markdown)
        add_timing(audit, "post", (time.perf_counter() - t0) * 1000.0)
        audit["posted"] = True
        print(f"Posted comment to issue #{resolved_issue_number}")
        _set_last_audit(audit)
        return "POSTED_OK"

    client: GitHubClient | None = None
    if not dry_run:
        if resolved_issue_number is None:
            _set_last_audit(audit)
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
    elif cmd == "review":
        body_markdown = _build_review_markdown(
            is_pull_request=event_ctx.is_pull_request,
            issue_number=resolved_issue_number,
            dry_run=dry_run,
            client=client,
            audit=audit,
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
        body_markdown = _build_qa_markdown(
            repo_root=repo_root,
            cmd=cmd,
            query=query,
            tky_mode=tky_mode,
            remote_url=remote_url,
            api_key=api_key,
            hmac_secret=hmac_secret,
            enable_hmac=enable_hmac,
            audit=audit,
        )

    if dry_run:
        print(body_markdown)
        _set_last_audit(audit)
        return "DRY_RUN_OK"

    if client is None:
        _set_last_audit(audit)
        raise ValueError("GitHub client was not initialized")

    t0 = time.perf_counter()
    client.create_issue_comment(issue_number=resolved_issue_number, body_markdown=body_markdown)
    add_timing(audit, "post", (time.perf_counter() - t0) * 1000.0)
    audit["posted"] = True
    print(f"Posted comment to issue #{resolved_issue_number}")
    _set_last_audit(audit)
    return "POSTED_OK"
