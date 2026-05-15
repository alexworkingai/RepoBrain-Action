from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any

from .execution_mode import coerce_execution_decision
from .signatures import build_query_signature
from .topocore_backend import (
    BACKEND_V6,
    TopoCoreBackendError,
    resolve_backend,
    run_v6_backend,
    should_fallback_to_v5,
)
from .tkya.engine import describe_engine_instance, get_engine
from .tky_engine import EngineCandidate, EngineQuery, EngineRequest
from .tky_provider import CandidateChunk, TKYProvider, TKYResult


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return default


def _load_event_payload() -> dict[str, Any]:
    event_path = os.getenv("GITHUB_EVENT_PATH", "").strip()
    if not event_path:
        return {}
    path = Path(event_path)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _build_github_context(limits: dict[str, Any], policy_seed: dict[str, Any]) -> dict[str, Any]:
    payload = _load_event_payload()
    seed_ctx = policy_seed.get("github_context", {})
    if not isinstance(seed_ctx, dict):
        seed_ctx = {}
    issue = payload.get("issue", {})
    pull_request = payload.get("pull_request", {})

    issue_number: int | None = None
    pr_number: int | None = None
    is_pr = False
    if isinstance(issue, dict):
        value = issue.get("number")
        if isinstance(value, int):
            issue_number = value
        issue_pr = issue.get("pull_request")
        if isinstance(issue_pr, dict):
            is_pr = True
            pr_number = issue_number
    if issue_number is None:
        seed_issue = seed_ctx.get("issue_number")
        if isinstance(seed_issue, int):
            issue_number = seed_issue
    if pr_number is None:
        seed_pr = seed_ctx.get("pr_number")
        if isinstance(seed_pr, int):
            pr_number = seed_pr
            is_pr = True

    base_sha = ""
    head_sha = ""
    base_ref = ""
    if isinstance(pull_request, dict):
        base = pull_request.get("base", {})
        head = pull_request.get("head", {})
        if isinstance(base, dict):
            base_sha = str(base.get("sha", "") or "")
            base_ref = str(base.get("ref", "") or "")
        if isinstance(head, dict):
            head_sha = str(head.get("sha", "") or "")

    if not base_sha:
        base_sha = str(seed_ctx.get("base_sha", "") or "")
    if not head_sha:
        head_sha = str(seed_ctx.get("head_sha", "") or "")
    if not base_ref:
        base_ref = str(seed_ctx.get("base_ref", "") or "")

    changed_files = limits.get("changed_files", [])
    if not isinstance(changed_files, list):
        changed_files = seed_ctx.get("changed_files", [])
        if not isinstance(changed_files, list):
            changed_files = []
    changed_files = [str(item) for item in changed_files if str(item).strip()]

    diff_hunks = limits.get("diff_hunks", [])
    if not isinstance(diff_hunks, list):
        diff_hunks = seed_ctx.get("diff_hunks", [])
        if not isinstance(diff_hunks, list):
            diff_hunks = []
    diff_hunks = [str(item) for item in diff_hunks if isinstance(item, str)]

    return {
        "event_name": os.getenv("GITHUB_EVENT_NAME", "").strip(),
        "repository": os.getenv("GITHUB_REPOSITORY", "").strip(),
        "sha": os.getenv("GITHUB_SHA", "").strip(),
        "ref": os.getenv("GITHUB_REF", "").strip(),
        "run_id": os.getenv("GITHUB_RUN_ID", "").strip(),
        "actor": os.getenv("GITHUB_ACTOR", "").strip(),
        "issue_number": issue_number,
        "pr_number": pr_number,
        "is_pr": bool(is_pr),
        "base_sha": base_sha,
        "head_sha": head_sha,
        "base_ref": base_ref,
        "changed_files": changed_files,
        "diff_hunks": diff_hunks,
    }


def _build_verification_context(limits: dict[str, Any]) -> dict[str, Any]:
    repo_root = Path.cwd()
    tests_present = (repo_root / "tests").exists()
    can_run_pytest = tests_present and shutil.which("pytest") is not None
    can_run_ruff = (repo_root / "pyproject.toml").exists() and shutil.which("ruff") is not None
    return {
        "can_run_pytest": bool(can_run_pytest),
        "can_run_ruff": bool(can_run_ruff),
        "time_budget_s": int(limits.get("time_budget_s", 30) or 30),
        "mode": "ci" if os.getenv("GITHUB_ACTIONS", "").strip().lower() == "true" else "local",
        "allow_patch_apply": _to_bool(os.getenv("RB_APPLY_PATCH", "")) or _to_bool(
            limits.get("allow_patch_apply", False)
        ),
        "network_allowed": _to_bool(os.getenv("RB_TKYA_ALLOW_REMOTE", "0")),
    }


def _build_runtime_context() -> dict[str, Any]:
    return {
        "python_version": sys.version.split()[0],
        "platform": os.name,
        "github_actions": os.getenv("GITHUB_ACTIONS", "").strip().lower() == "true",
    }


def _normalize_requested_task_type(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"ask", "locate", "explain", "review", "verify"}:
        return normalized
    return "ask"


def _normalize_engine_task_type(requested_task_type: str) -> str:
    if requested_task_type == "verify":
        return "review"
    if requested_task_type in {"ask", "locate", "explain", "review"}:
        return requested_task_type
    return "ask"


def _build_policy(limits: dict[str, Any]) -> dict[str, Any]:
    seed = limits.get("policy", {})
    policy = dict(seed) if isinstance(seed, dict) else {}
    policy["corelocked"] = True
    policy["github_context"] = _build_github_context(limits, policy)
    policy["verification_context"] = _build_verification_context(limits)
    policy["runtime"] = _build_runtime_context()
    return policy


@dataclass
class LocalTKYProvider(TKYProvider):
    """Local TKY provider stub.

    Local provider backed by selectable TKYA engines.
    Safe default keeps the current v5/TKYA path. Explicit `RB_TOPOCORE_BACKEND=v6`
    can select the real TopoCore v6 adapter in local or lab paths without
    changing default GitHub runtime behavior.
    """

    def compress_context(
        self,
        *,
        question: str,
        candidates: list[CandidateChunk],
        limits: dict[str, Any],
    ) -> TKYResult:
        requested_task_type = _normalize_requested_task_type(limits.get("task_type", "ask"))
        task_type = _normalize_engine_task_type(requested_task_type)
        limits = dict(limits)
        limits["task_type"] = task_type
        limits["requested_task_type"] = requested_task_type
        limits["strict_local_v6"] = _to_bool(os.getenv("RB_TOPOCORE_V6_REQUIRE_LOCAL", "0"))
        policy = _build_policy(limits)
        backend = resolve_backend()

        if backend.selected_backend == BACKEND_V6:
            try:
                result = run_v6_backend(
                    question=question,
                    candidates=candidates,
                    limits=limits,
                    policy=policy,
                    local_path=backend.local_path,
                ).tky_result
                compression_stats = dict(result.compression_stats)
                compression_stats.setdefault("tky_engine_local", "topocore_v6")
                compression_stats.setdefault("topocore_backend", "v6")
                return TKYResult(
                    selected_chunk_ids=list(result.selected_chunk_ids),
                    route=result.route,
                    compression_stats=compression_stats,
                    rationale=result.rationale,
                    execution_mode=result.execution_mode,
                    llm_intent=result.llm_intent,
                    llm_decision_reason_short=result.llm_decision_reason_short,
                    llm_decision_reason_code=result.llm_decision_reason_code,
                )
            except TopoCoreBackendError as exc:
                if backend.strict_v6 or not should_fallback_to_v5(exc):
                    raise TopoCoreBackendError(str(exc)) from exc

        engine = get_engine()

        req = EngineRequest(
            task_type=task_type,  # type: ignore[arg-type]
            query=EngineQuery(text=question, signature=build_query_signature(question)),
            candidates=[
                EngineCandidate(
                    chunk_id=c.chunk_id,
                    score_local=float(c.score),
                    signature=c.signature,
                    file_path=c.file_path,
                    line_start=c.line_start,
                    line_end=c.line_end,
                )
                for c in candidates
            ],
            limits=limits,
            policy=policy,
        )
        decision = engine.decide(req)
        execution = coerce_execution_decision(
            route=decision.route,
            execution_mode=getattr(decision, "execution_mode", None),
            llm_intent=getattr(decision, "llm_intent", None),
            reason_short=getattr(decision, "llm_decision_reason_short", None),
            reason_code=getattr(decision, "llm_decision_reason_code", None),
        )
        compression_stats = dict(decision.compression_stats)
        compression_stats.setdefault("tky_engine_local", describe_engine_instance(engine))
        compression_stats.setdefault("topocore_backend", "v5")
        if backend.selected_backend == BACKEND_V6:
            compression_stats.setdefault("topocore_backend_requested", "v6")
            compression_stats.setdefault("topocore_backend_fallback", "v5")
        return TKYResult(
            selected_chunk_ids=decision.selected_chunk_ids,
            route=decision.route,
            compression_stats=compression_stats,
            rationale=decision.rationale,
            execution_mode=execution.execution_mode,
            llm_intent=execution.llm_intent,
            llm_decision_reason_short=execution.reason_short,
            llm_decision_reason_code=execution.reason_code,
        )
