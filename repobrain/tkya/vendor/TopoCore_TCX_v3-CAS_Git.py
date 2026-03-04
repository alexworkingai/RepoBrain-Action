"""
TopoCore TCX v3-CAS Git (GitHub-ready, RepoBrain contract-preserving).

This file intentionally keeps a compact, deterministic engine focused on
RepoBrain/GitHub workflows:
- Engine contract: decide(req) -> EngineDecision
- Security-first behavior: REFUSE route for suspicious requests
- Diff-aware selection for PR-oriented tasks
- Stable, non-sensitive tokens for traceability

Compatibility notes:
- Keeps `TopoCoreTCXv2CAS` symbol as an alias for backward loader compatibility.
- Keeps `TopoCoreResponse` and `handle_request(...)` for legacy adapters.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
import re
from typing import Any, Iterable

try:
    from repobrain.security import detect_injection_or_exfiltration as _detect_security_external
except Exception:  # pragma: no cover - fallback for standalone execution
    _detect_security_external = None

try:
    from repobrain.tky_engine import (
        EngineCandidate,
        EngineDecision,
        EngineQuery,
        EngineRequest,
        EngineSecurity,
    )
except Exception:  # pragma: no cover - fallback for standalone execution
    @dataclass(frozen=True)
    class EngineCandidate:
        chunk_id: str
        score_local: float
        signature: list[int] | None = None
        file_path: str | None = None
        line_start: int | None = None
        line_end: int | None = None

    @dataclass(frozen=True)
    class EngineQuery:
        text: str
        signature: list[int] | None = None

    @dataclass(frozen=True)
    class EngineRequest:
        task_type: str
        query: EngineQuery
        candidates: list[EngineCandidate]
        limits: dict[str, Any]
        policy: dict[str, Any]

    @dataclass(frozen=True)
    class EngineSecurity:
        blocked: bool
        injection_risk: str
        exfiltration_risk: str
        signals: list[str]

    @dataclass(frozen=True)
    class EngineDecision:
        route: str
        selected_chunk_ids: list[str]
        compression_stats: dict[str, Any]
        security: EngineSecurity
        rationale: str
        stable_tokens: list[str]


_SECURITY_KEYWORDS = (
    "system prompt",
    "скрытые правила",
    "инструкции",
    "api key",
    "token",
    "secret",
    "пароль",
    ".env",
    "exfiltrate",
    "dump",
    "reveal",
)


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return default


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _norm_tokens(text: str) -> list[str]:
    return [tok for tok in re.findall(r"\w+", (text or "").lower(), flags=re.UNICODE) if tok]


def _deterministic_hash(value: str) -> str:
    return hashlib.blake2s(value.encode("utf-8"), digest_size=8).hexdigest()


@dataclass(frozen=True)
class TopoCoreResponse:
    summary: str
    answer: str
    next_steps: list[str]
    risks: list[str]
    topo_rationale: str | None = None
    trace_hashes: dict[str, Any] | None = None


@dataclass(frozen=True)
class _NormalizedGitHubContext:
    is_pr: bool
    pull_number: int | None
    base_ref: str | None
    head_ref: str | None
    changed_files: set[str]
    line_ranges_by_file: dict[str, list[tuple[int, int]]]
    commitish: list[str]


@dataclass(frozen=True)
class _ScoredCandidate:
    candidate: EngineCandidate
    adjusted_score: float


class TopoCoreTCXv3CASGit:
    """GitHub-ready v3 TKYA core preserving RepoBrain engine contract."""

    def __init__(self) -> None:
        # WHY: keep defaults stable for deterministic CI behavior.
        # WHAT: route threshold values are fixed and only overrideable via limits.
        # RISK: mis-tuned thresholds could over/under select; mitigated by explicit limits.
        self.default_min_fast_score = 0.05
        self.default_min_score_keep = 0.02
        self.default_max_sources = 8
        self.default_min_sources = 3

    def _normalize_task_type(self, task_type: str) -> str:
        task = (task_type or "ask").strip().lower()
        if task in {"ask", "locate", "explain", "review"}:
            return task
        return "ask"

    def _security_check(self, text: str, policy: dict[str, Any]) -> EngineSecurity:
        raw = (text or "").strip()
        lowered = raw.lower()
        signals: list[str] = []
        blocked = False

        if _detect_security_external is not None:
            external = _detect_security_external(raw)
            if bool(external.get("blocked", False)):
                blocked = True
            for item in external.get("signals", []):
                token = str(item).strip()
                if token:
                    signals.append(token)

        for marker in _SECURITY_KEYWORDS:
            if marker in lowered:
                blocked = True
                signals.append(f"keyword:{marker}")

        disallowed = policy.get("disallowed_actions", [])
        if isinstance(disallowed, (list, tuple, set)):
            for rule in disallowed:
                needle = str(rule).strip().lower()
                if needle and needle in lowered:
                    blocked = True
                    signals.append(f"policy:{needle}")

        return EngineSecurity(
            blocked=blocked,
            injection_risk="high" if blocked else "low",
            exfiltration_risk="high" if blocked else "low",
            signals=sorted(set(signals)),
        )

    def _normalize_github_context(
        self,
        policy: dict[str, Any],
        limits: dict[str, Any],
    ) -> _NormalizedGitHubContext:
        # WHY: PR-aware prioritization improves relevance for `/review` and targeted asks.
        # WHAT: normalize optional GitHub metadata from policy/limits without requiring it.
        # RISK: malformed payload may degrade ranking; mitigated with strict type checks.
        raw_ctx: dict[str, Any] = {}
        for key in ("github_context", "github", "pr_context"):
            value = policy.get(key)
            if isinstance(value, dict):
                raw_ctx = dict(value)
                break

        if not raw_ctx:
            for key in ("github_context", "github", "pr_context"):
                value = limits.get(key)
                if isinstance(value, dict):
                    raw_ctx = dict(value)
                    break

        changed_files: set[str] = set()
        line_ranges_by_file: dict[str, list[tuple[int, int]]] = {}

        files = raw_ctx.get("changed_files", [])
        if isinstance(files, list):
            for item in files:
                if isinstance(item, str) and item.strip():
                    changed_files.add(item.strip())

        hunks = raw_ctx.get("diff_hunks", {})
        if isinstance(hunks, dict):
            for file_path, ranges in hunks.items():
                if not isinstance(file_path, str):
                    continue
                path = file_path.strip()
                if not path:
                    continue
                changed_files.add(path)
                parsed: list[tuple[int, int]] = []
                if isinstance(ranges, list):
                    for pair in ranges:
                        if isinstance(pair, (list, tuple)) and len(pair) == 2:
                            start = _to_int(pair[0], 0)
                            end = _to_int(pair[1], 0)
                            if start > 0 and end >= start:
                                parsed.append((start, end))
                if parsed:
                    line_ranges_by_file[path] = parsed

        commitish: list[str] = []
        for key in ("head_sha", "base_sha", "head_ref", "base_ref", "commit"):
            value = raw_ctx.get(key)
            if isinstance(value, str) and value.strip():
                commitish.append(value.strip())

        is_pr = bool(raw_ctx.get("is_pr")) or "pull_number" in raw_ctx
        pull_number = _to_int(raw_ctx.get("pull_number"), 0) or None
        base_ref = str(raw_ctx.get("base_ref", "") or "").strip() or None
        head_ref = str(raw_ctx.get("head_ref", "") or "").strip() or None

        return _NormalizedGitHubContext(
            is_pr=is_pr,
            pull_number=pull_number,
            base_ref=base_ref,
            head_ref=head_ref,
            changed_files=changed_files,
            line_ranges_by_file=line_ranges_by_file,
            commitish=commitish,
        )

    def _line_overlap_boost(self, candidate: EngineCandidate, ranges: list[tuple[int, int]]) -> float:
        if candidate.line_start is None or candidate.line_end is None:
            return 0.0
        for start, end in ranges:
            if candidate.line_end >= start and candidate.line_start <= end:
                return 0.06
        return 0.0

    def _rank_candidates(
        self,
        candidates: list[EngineCandidate],
        gh_ctx: _NormalizedGitHubContext,
    ) -> list[_ScoredCandidate]:
        scored: list[_ScoredCandidate] = []
        for candidate in candidates:
            base = float(candidate.score_local)
            file_path = str(candidate.file_path or "")
            boost = 0.0
            if gh_ctx.is_pr and file_path and file_path in gh_ctx.changed_files:
                boost += 0.08
                boost += self._line_overlap_boost(candidate, gh_ctx.line_ranges_by_file.get(file_path, []))
            scored.append(_ScoredCandidate(candidate=candidate, adjusted_score=max(0.0, min(1.0, base + boost))))

        # WHY: deterministic ordering is required for reproducible CI comments and audits.
        # WHAT: stable sorting by adjusted score + explicit field tie-breakers.
        # RISK: tie-breakers may bias similarly scored chunks; mitigated by consistent policy.
        scored.sort(
            key=lambda item: (
                -item.adjusted_score,
                str(item.candidate.file_path or ""),
                int(item.candidate.line_start or 0),
                int(item.candidate.line_end or 0),
                item.candidate.chunk_id,
            )
        )
        return scored

    def _build_stable_tokens(
        self,
        *,
        query_text: str,
        selected: list[EngineCandidate],
        gh_ctx: _NormalizedGitHubContext,
    ) -> list[str]:
        # WHY: stable tokens are used for traceability without leaking sensitive inputs.
        # WHAT: hash only normalized query tokens + ids/paths + commit-ish metadata.
        # RISK: over-sharing raw content; mitigated by hashing and excluding env/secrets/diffs.
        seeds: list[str] = []
        seeds.extend(_norm_tokens(query_text)[:16])
        seeds.extend(gh_ctx.commitish[:6])
        for candidate in selected[:10]:
            seeds.append(candidate.chunk_id)
            if candidate.file_path:
                seeds.append(candidate.file_path)
        hashed = sorted({_deterministic_hash(seed) for seed in seeds if seed})
        return hashed[:12]

    def _review_verification_info(self, gh_ctx: _NormalizedGitHubContext) -> tuple[list[str], list[str]]:
        verified = ["selection_policy_applied", "deterministic_ranking"]
        if gh_ctx.is_pr:
            verified.append("github_context_normalized")
        not_run = [
            "external_ci_checks",
            "external_security_scans",
            "runtime_integration_tests",
        ]
        return verified, not_run

    def _select_ids(
        self,
        *,
        task_type: str,
        ranked: list[_ScoredCandidate],
        limits: dict[str, Any],
    ) -> list[str]:
        max_sources = max(1, _to_int(limits.get("max_sources"), self.default_max_sources))
        min_score_keep = _to_float(limits.get("min_score_keep"), self.default_min_score_keep)
        keep_ratio = {"ask": 0.35, "locate": 0.30, "explain": 0.25, "review": 0.20}.get(task_type, 0.30)

        if not ranked:
            return []
        top_score = ranked[0].adjusted_score
        keep_threshold = max(min_score_keep, top_score * keep_ratio)
        min_sources = 1 if task_type == "locate" else self.default_min_sources

        selected: list[EngineCandidate] = []
        selected_ids: set[str] = set()
        used_files: set[str] = set()
        max_files = 5 if task_type == "locate" else max_sources

        for idx, item in enumerate(ranked):
            candidate = item.candidate
            if len(selected) >= max_sources:
                break
            if idx > 0 and item.adjusted_score < keep_threshold:
                continue
            file_path = str(candidate.file_path or "")
            if task_type == "locate" and file_path and file_path in used_files:
                continue
            if file_path and file_path not in used_files and len(used_files) >= max_files:
                continue
            if candidate.chunk_id in selected_ids:
                continue
            selected.append(candidate)
            selected_ids.add(candidate.chunk_id)
            if file_path:
                used_files.add(file_path)

        if len(selected) < min_sources:
            for item in ranked:
                if len(selected) >= min_sources:
                    break
                candidate = item.candidate
                if candidate.chunk_id in selected_ids:
                    continue
                selected.append(candidate)
                selected_ids.add(candidate.chunk_id)

        return [candidate.chunk_id for candidate in selected]

    def decide(self, req: EngineRequest) -> EngineDecision:
        task_type = self._normalize_task_type(str(getattr(req, "task_type", "ask")))
        limits = dict(getattr(req, "limits", {}) or {})
        policy = dict(getattr(req, "policy", {}) or {})
        query = getattr(req, "query")
        question = str(getattr(query, "text", "") or "")
        candidates = list(getattr(req, "candidates", []) or [])

        security = self._security_check(question, policy)
        if security.blocked:
            return EngineDecision(
                route="REFUSE",
                selected_chunk_ids=[],
                compression_stats={
                    "retrieved": len(candidates),
                    "selected": 0,
                    "route": "REFUSE",
                    "verified": [],
                    "not_run": ["all_actions_blocked_by_security_policy"],
                },
                security=security,
                rationale="CoreLocked: blocked by security policy.",
                stable_tokens=[],
            )

        gh_ctx = self._normalize_github_context(policy, limits)
        ranked = self._rank_candidates(candidates, gh_ctx)
        top_score = ranked[0].adjusted_score if ranked else 0.0
        min_fast_score = _to_float(limits.get("min_score_fast"), self.default_min_fast_score)

        if task_type == "review":
            route = "REVIEW"
        elif top_score < min_fast_score:
            route = "DEEP"
        else:
            route = "FAST"

        selected_ids = self._select_ids(task_type=task_type, ranked=ranked, limits=limits)
        selected_candidates = [item.candidate for item in ranked if item.candidate.chunk_id in set(selected_ids)]
        stable_tokens = self._build_stable_tokens(
            query_text=question,
            selected=selected_candidates,
            gh_ctx=gh_ctx,
        )

        verified: list[str] = []
        not_run: list[str] = []
        if task_type == "review":
            verified, not_run = self._review_verification_info(gh_ctx)

        rationale_map = {
            "FAST": "CoreLocked v3: high-confidence structural match.",
            "DEEP": "CoreLocked v3: low-confidence match; expanded search recommended.",
            "REVIEW": "CoreLocked v3: review mode with verification ladder flags.",
        }

        return EngineDecision(
            route=route,
            selected_chunk_ids=selected_ids,
            compression_stats={
                "retrieved": len(candidates),
                "selected": len(selected_ids),
                "top_score": round(top_score, 6),
                "route": route,
                "verified": verified,
                "not_run": not_run,
            },
            security=security,
            rationale=rationale_map.get(route, "CoreLocked v3: decision completed."),
            stable_tokens=stable_tokens,
        )

    def handle_request(self, user_text: str, **_kwargs: Any) -> TopoCoreResponse:
        # WHY: current RepoBrain loader still calls handle_request on vendor objects.
        # WHAT: provide minimal backward-compatible response object.
        # RISK: legacy adapters may expect richer fields; mitigated by stable defaults.
        security = self._security_check(user_text, {})
        if security.blocked:
            return TopoCoreResponse(
                summary="Request blocked by security policy.",
                answer="CoreLocked: request refused.",
                next_steps=["Rephrase the request without secrets/internals."],
                risks=["Potential prompt-injection / exfiltration attempt."],
                topo_rationale="security_refuse",
            )
        return TopoCoreResponse(
            summary="TopoCore v3 GitHub-ready core active.",
            answer="Deterministic routing and selection are available via decide(req).",
            next_steps=["Use engine.decide(req) for RepoBrain workflow decisions."],
            risks=["No external verification tools were executed in this call."],
            topo_rationale="contract_compatible",
        )

    def remote_call(self, _payload: Any) -> dict[str, Any]:
        # WHY: remote is dangerous by default for CI and local safety.
        # WHAT: hard-guard remote path behind explicit env opt-in.
        # RISK: accidental outbound traffic; mitigated by fail-closed RuntimeError.
        if not _to_bool(os.getenv("RB_TKYA_ALLOW_REMOTE", "0")):
            raise RuntimeError("Remote operations are disabled (RB_TKYA_ALLOW_REMOTE=0).")
        return {"status": "allowed_but_not_implemented"}


# Backward-compatible export expected by existing loaders/adapters.
TopoCoreTCXv2CAS = TopoCoreTCXv3CASGit


def _iter_examples() -> Iterable[tuple[str, str]]:
    yield ("ask", "Where is TKY provider logic?")
    yield ("review", "Review this PR for risks")


if __name__ == "__main__":  # pragma: no cover
    core = TopoCoreTCXv3CASGit()
    for task, text in _iter_examples():
        req = EngineRequest(
            task_type=task,  # type: ignore[arg-type]
            query=EngineQuery(text=text, signature=[]),
            candidates=[],
            limits={},
            policy={},
        )
        decision = core.decide(req)
        print(task, decision.route, decision.selected_chunk_ids)
