"""
TopoCore TCX v4-CAS+Git
-----------------------

Autonomous GitHub-ready core for complex tasks and topological analytics.

Properties:
- Fully standalone (no bridge/dependency on v2 runtime).
- RepoBrain engine contract compatible: `decide(req) -> EngineDecision`.
- Deterministic ranking/routing/selection.
- Diff-aware boosts for PR contexts.
- DataScience & BigAnalytics helper calculations (stdlib only).
- Security-first REFUSE path.
- Remote path fail-closed by default.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import os
import re
import statistics
from typing import Any, Iterable

try:
    from repobrain.security import detect_injection_or_exfiltration as _detect_security_external
except Exception:  # pragma: no cover
    _detect_security_external = None

try:
    from repobrain.tky_engine import (
        EngineCandidate,
        EngineDecision,
        EngineQuery,
        EngineRequest,
        EngineSecurity,
    )
except Exception:  # pragma: no cover
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


_SECURITY_MARKERS = (
    "system prompt",
    "скрытые правила",
    "инструкции",
    "api key",
    "token",
    "secret",
    "пароль",
    "private key",
    "credential",
    "exfiltrate",
    "dump",
    "reveal",
    ".env",
)

_ANALYTICS_HINTS = (
    "topology",
    "topological",
    "betti",
    "persistent",
    "homology",
    "graph",
    "cluster",
    "anomaly",
    "datascience",
    "biganalytics",
    "dataset",
    "vector",
    "feature",
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


def _clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"\w+", (text or "").lower(), flags=re.UNICODE) if token]


def _h(value: str, size: int = 8) -> str:
    return hashlib.blake2s(value.encode("utf-8"), digest_size=size).hexdigest()


@dataclass(frozen=True)
class TopoCoreResponse:
    summary: str
    answer: str
    next_steps: list[str]
    risks: list[str]
    topo_rationale: str | None = None
    trace_hashes: dict[str, Any] | None = None


@dataclass(frozen=True)
class _GitHubContext:
    is_pr: bool
    pull_number: int | None
    changed_files: set[str]
    line_ranges: dict[str, list[tuple[int, int]]]
    commitish: list[str]


@dataclass(frozen=True)
class _TopologySignals:
    mode: str
    complexity: str
    metric_count: int
    metrics: dict[str, float]
    signals: list[str]


@dataclass(frozen=True)
class _RankedCandidate:
    candidate: EngineCandidate
    score: float


class _DSU:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra = self.find(a)
        rb = self.find(b)
        if ra != rb:
            self.parent[rb] = ra


class DataScienceTopologyKernel:
    """Stdlib-only topology/data analytics utility layer."""

    @staticmethod
    def _normalize_series(values: Iterable[Any]) -> list[float]:
        out: list[float] = []
        for value in values:
            try:
                out.append(float(value))
            except (TypeError, ValueError):
                continue
        return out

    @staticmethod
    def _normalize_vectors(values: Iterable[Any], max_dim: int = 64) -> list[list[float]]:
        vectors: list[list[float]] = []
        for row in values:
            if not isinstance(row, (list, tuple)):
                continue
            parsed: list[float] = []
            for item in row:
                try:
                    parsed.append(float(item))
                except (TypeError, ValueError):
                    continue
            if parsed:
                vectors.append(parsed[:max_dim])
        return vectors

    def summarize_series(self, values: Iterable[Any]) -> dict[str, float]:
        numbers = self._normalize_series(values)
        if not numbers:
            return {"count": 0.0}
        q1, q3 = self._quartiles(numbers)
        stdev = statistics.pstdev(numbers) if len(numbers) > 1 else 0.0
        return {
            "count": float(len(numbers)),
            "mean": float(statistics.fmean(numbers)),
            "median": float(statistics.median(numbers)),
            "stdev": float(stdev),
            "min": float(min(numbers)),
            "max": float(max(numbers)),
            "span": float(max(numbers) - min(numbers)),
            "q1": float(q1),
            "q3": float(q3),
            "iqr": float(q3 - q1),
        }

    @staticmethod
    def _quartiles(values: list[float]) -> tuple[float, float]:
        ordered = sorted(values)
        n = len(ordered)
        if n == 0:
            return 0.0, 0.0
        mid = n // 2
        lower = ordered[:mid]
        upper = ordered[mid + (0 if n % 2 == 0 else 1) :]
        q1 = statistics.median(lower) if lower else ordered[0]
        q3 = statistics.median(upper) if upper else ordered[-1]
        return float(q1), float(q3)

    @staticmethod
    def _euclidean(a: list[float], b: list[float]) -> float:
        width = min(len(a), len(b))
        if width == 0:
            return 0.0
        total = 0.0
        for idx in range(width):
            diff = a[idx] - b[idx]
            total += diff * diff
        return math.sqrt(total)

    def graph_stats(self, vectors: list[list[float]], threshold: float = 1.0) -> dict[str, float]:
        nodes = len(vectors)
        if nodes == 0:
            return {"nodes": 0.0, "edges": 0.0, "components": 0.0, "betti1_est": 0.0}
        if nodes == 1:
            return {"nodes": 1.0, "edges": 0.0, "components": 1.0, "betti1_est": 0.0}

        dsu = _DSU(nodes)
        edges = 0
        for i in range(nodes):
            for j in range(i + 1, nodes):
                if self._euclidean(vectors[i], vectors[j]) <= threshold:
                    edges += 1
                    dsu.union(i, j)

        roots = {dsu.find(i) for i in range(nodes)}
        nodes_f = float(nodes)
        edges_f = float(edges)
        components = float(len(roots))
        betti1 = max(0.0, edges_f - nodes_f + components)
        max_edges = max(1.0, nodes_f * (nodes_f - 1.0) / 2.0)
        density = edges_f / max_edges
        avg_degree = (2.0 * edges_f / nodes_f) if nodes_f > 0 else 0.0
        return {
            "nodes": nodes_f,
            "edges": edges_f,
            "components": components,
            "density": density,
            "avg_degree": avg_degree,
            "betti1_est": betti1,
        }

    def anomaly_profile(self, values: Iterable[Any], z_threshold: float = 2.5) -> dict[str, float]:
        numbers = self._normalize_series(values)
        if len(numbers) < 2:
            return {"count": float(len(numbers)), "outliers": 0.0, "outlier_ratio": 0.0}
        mean = statistics.fmean(numbers)
        stdev = statistics.pstdev(numbers)
        if stdev <= 1e-12:
            return {"count": float(len(numbers)), "outliers": 0.0, "outlier_ratio": 0.0}
        outliers = 0
        for value in numbers:
            z = abs((value - mean) / stdev)
            if z >= z_threshold:
                outliers += 1
        count_f = float(len(numbers))
        return {
            "count": count_f,
            "outliers": float(outliers),
            "outlier_ratio": float(outliers) / count_f,
        }

    def persistent_signature(
        self,
        *,
        series: Iterable[Any],
        graph: dict[str, float],
        bins: int = 16,
    ) -> str:
        numbers = self._normalize_series(series)
        bucket = [0] * max(2, bins)
        if numbers:
            minimum = min(numbers)
            maximum = max(numbers)
            span = maximum - minimum or 1.0
            for value in numbers:
                idx = int(((value - minimum) / span) * (len(bucket) - 1))
                idx = max(0, min(len(bucket) - 1, idx))
                bucket[idx] += 1
        payload = [
            ",".join(str(v) for v in bucket),
            f"n={graph.get('nodes', 0.0):.4f}",
            f"e={graph.get('edges', 0.0):.4f}",
            f"c={graph.get('components', 0.0):.4f}",
            f"b1={graph.get('betti1_est', 0.0):.4f}",
        ]
        return _h("|".join(payload), size=12)

    def analyze(self, query: str, policy: dict[str, Any], limits: dict[str, Any]) -> _TopologySignals:
        ctx: dict[str, Any] = {}
        for key in ("analytics_context", "topology_context", "dataset_context"):
            value = policy.get(key)
            if isinstance(value, dict):
                ctx = dict(value)
                break
        if not ctx:
            for key in ("analytics_context", "topology_context", "dataset_context"):
                value = limits.get(key)
                if isinstance(value, dict):
                    ctx = dict(value)
                    break

        metrics: dict[str, float] = {}
        signals: list[str] = []

        series = ctx.get("series", [])
        if isinstance(series, (list, tuple)):
            series_stats = self.summarize_series(series)
            for key in ("count", "mean", "stdev", "span", "iqr"):
                if key in series_stats:
                    metrics[f"series_{key}"] = float(series_stats[key])
            if series_stats.get("count", 0.0) > 0:
                signals.append("series_present")

            anomaly = self.anomaly_profile(series)
            metrics["anomaly_outlier_ratio"] = float(anomaly.get("outlier_ratio", 0.0))
            if anomaly.get("outliers", 0.0) > 0:
                signals.append("series_outliers_detected")

        vectors = self._normalize_vectors(ctx.get("vectors", []) if isinstance(ctx.get("vectors"), list) else [])
        graph = self.graph_stats(vectors, threshold=_to_float(ctx.get("threshold"), 1.0))
        for key, value in graph.items():
            metrics[f"graph_{key}"] = float(value)
        if vectors:
            signals.append("vector_graph_built")

        signature = self.persistent_signature(
            series=series if isinstance(series, (list, tuple)) else [],
            graph=graph,
        )
        metrics["persistent_hash_seed"] = float(int(signature[:12], 16))

        hinted = any(h in set(_tokens(query)) for h in _ANALYTICS_HINTS)
        metric_count = len(metrics)
        if metric_count >= 10:
            complexity = "high"
        elif metric_count >= 4 or hinted:
            complexity = "medium"
        else:
            complexity = "low"
        mode = "analytics" if metric_count > 0 or hinted else "generic"
        return _TopologySignals(
            mode=mode,
            complexity=complexity,
            metric_count=metric_count,
            metrics=metrics,
            signals=sorted(set(signals)),
        )


class TopoCoreTCXv4CASGit:
    """Autonomous v4 core for complex tasks and topological calculations."""

    def __init__(self) -> None:
        self.default_min_fast_score = 0.05
        self.default_min_score_keep = 0.02
        self.default_max_sources = 8
        self.default_min_sources = 3
        self.default_locate_max_files = 5
        self.kernel = DataScienceTopologyKernel()

    def _normalize_task_type(self, task_type: str) -> str:
        task = (task_type or "ask").strip().lower()
        if task in {"ask", "locate", "explain", "review"}:
            return task
        return "ask"

    def _security_check(self, text: str, policy: dict[str, Any]) -> EngineSecurity:
        lowered = (text or "").lower()
        blocked = False
        signals: list[str] = []

        if _detect_security_external is not None:
            result = _detect_security_external(text)
            blocked = blocked or bool(result.get("blocked", False))
            for signal in result.get("signals", []):
                token = str(signal).strip()
                if token:
                    signals.append(token)

        for marker in _SECURITY_MARKERS:
            if marker in lowered:
                blocked = True
                signals.append(f"keyword:{marker}")

        disallowed = policy.get("disallowed_actions", [])
        if isinstance(disallowed, (list, tuple, set)):
            for item in disallowed:
                marker = str(item).strip().lower()
                if marker and marker in lowered:
                    blocked = True
                    signals.append(f"policy:{marker}")

        return EngineSecurity(
            blocked=blocked,
            injection_risk="high" if blocked else "low",
            exfiltration_risk="high" if blocked else "low",
            signals=sorted(set(signals)),
        )

    def _normalize_github_context(self, policy: dict[str, Any], limits: dict[str, Any]) -> _GitHubContext:
        raw: dict[str, Any] = {}
        for key in ("github_context", "github", "pr_context"):
            value = policy.get(key)
            if isinstance(value, dict):
                raw = dict(value)
                break
        if not raw:
            for key in ("github_context", "github", "pr_context"):
                value = limits.get(key)
                if isinstance(value, dict):
                    raw = dict(value)
                    break

        changed_files: set[str] = set()
        for item in raw.get("changed_files", []):
            if isinstance(item, str) and item.strip():
                changed_files.add(item.strip())

        line_ranges: dict[str, list[tuple[int, int]]] = {}
        hunks = raw.get("diff_hunks", {})
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
                    line_ranges[path] = parsed

        commitish: list[str] = []
        for key in ("head_sha", "base_sha", "head_ref", "base_ref", "commit"):
            value = raw.get(key)
            if isinstance(value, str) and value.strip():
                commitish.append(value.strip())

        return _GitHubContext(
            is_pr=bool(raw.get("is_pr")) or "pull_number" in raw,
            pull_number=_to_int(raw.get("pull_number"), 0) or None,
            changed_files=changed_files,
            line_ranges=line_ranges,
            commitish=commitish,
        )

    @staticmethod
    def _line_overlap(candidate: EngineCandidate, ranges: list[tuple[int, int]]) -> bool:
        if candidate.line_start is None or candidate.line_end is None:
            return False
        for start, end in ranges:
            if candidate.line_end >= start and candidate.line_start <= end:
                return True
        return False

    @staticmethod
    def _signature_overlap(query_sig: list[int] | None, chunk_sig: list[int] | None) -> float:
        if not query_sig or not chunk_sig:
            return 0.0
        q = set(int(x) for x in query_sig)
        c = set(int(x) for x in chunk_sig)
        if not q or not c:
            return 0.0
        return float(len(q & c)) / float(len(q | c))

    def _rank_candidates(
        self,
        *,
        req: EngineRequest,
        task_type: str,
        gh: _GitHubContext,
        topology: _TopologySignals,
    ) -> list[_RankedCandidate]:
        query_tokens = set(_tokens(req.query.text))
        ranked: list[_RankedCandidate] = []
        for candidate in list(req.candidates):
            score = float(candidate.score_local)
            path = str(candidate.file_path or "")
            lower_path = path.lower()
            cid = candidate.chunk_id.lower()

            if gh.is_pr and path and path in gh.changed_files:
                score += 0.08
                if self._line_overlap(candidate, gh.line_ranges.get(path, [])):
                    score += 0.06

            score += 0.08 * self._signature_overlap(req.query.signature, candidate.signature)

            for token in query_tokens:
                if token and (token in lower_path or token in cid):
                    score += 0.01

            if topology.mode == "analytics":
                if any(marker in lower_path for marker in ("graph", "topo", "model", "feature", "data")):
                    score += 0.02
                if topology.complexity == "high" and task_type in {"ask", "explain"}:
                    score += 0.01

            ranked.append(_RankedCandidate(candidate=candidate, score=_clip(score)))

        ranked.sort(
            key=lambda item: (
                -item.score,
                str(item.candidate.file_path or ""),
                int(item.candidate.line_start or 0),
                int(item.candidate.line_end or 0),
                item.candidate.chunk_id,
            )
        )
        return ranked

    def _route(self, task_type: str, top_score: float, topology: _TopologySignals, limits: dict[str, Any]) -> str:
        if task_type == "review":
            return "REVIEW"
        min_fast = _to_float(limits.get("min_score_fast"), self.default_min_fast_score)
        if topology.complexity == "high":
            return "DEEP"
        if top_score < min_fast:
            return "DEEP"
        return "FAST"

    def _select(self, *, task_type: str, ranked: list[_RankedCandidate], limits: dict[str, Any]) -> list[str]:
        if not ranked:
            return []

        max_sources = max(1, _to_int(limits.get("max_sources"), self.default_max_sources))
        min_keep = _to_float(limits.get("min_score_keep"), self.default_min_score_keep)
        top_score = ranked[0].score
        keep_ratio = {"ask": 0.35, "locate": 0.30, "explain": 0.25, "review": 0.20}[task_type]
        threshold = max(min_keep, top_score * keep_ratio)
        min_sources = 1 if task_type == "locate" else self.default_min_sources
        max_files = self.default_locate_max_files if task_type == "locate" else max_sources

        selected: list[str] = []
        selected_set: set[str] = set()
        files_seen: set[str] = set()
        for idx, item in enumerate(ranked):
            if len(selected) >= max_sources:
                break
            candidate = item.candidate
            if idx > 0 and item.score < threshold:
                continue
            path = str(candidate.file_path or "")
            if task_type == "locate" and path and path in files_seen:
                continue
            if path and path not in files_seen and len(files_seen) >= max_files:
                continue
            if candidate.chunk_id in selected_set:
                continue
            selected.append(candidate.chunk_id)
            selected_set.add(candidate.chunk_id)
            if path:
                files_seen.add(path)

        if len(selected) < min_sources:
            for item in ranked:
                if len(selected) >= min_sources:
                    break
                cid = item.candidate.chunk_id
                if cid in selected_set:
                    continue
                selected.append(cid)
                selected_set.add(cid)
        return selected

    def _review_verification(self, gh: _GitHubContext, topology: _TopologySignals) -> tuple[list[str], list[str]]:
        verified = ["deterministic_ranking", "selection_policy_applied"]
        if gh.is_pr:
            verified.append("github_diff_context_applied")
        if topology.mode == "analytics":
            verified.append("topology_metrics_computed")
        not_run = [
            "external_ci_checks",
            "external_security_scans",
            "runtime_integration_tests",
            "networked_topology_jobs",
        ]
        return verified, not_run

    def _stable_tokens(
        self,
        *,
        req: EngineRequest,
        selected_ids: list[str],
        gh: _GitHubContext,
        topology: _TopologySignals,
    ) -> list[str]:
        seeds: list[str] = []
        seeds.extend(_tokens(req.query.text)[:24])
        seeds.extend(gh.commitish[:10])
        seeds.extend(selected_ids[:20])
        seeds.extend(topology.signals[:12])
        seeds.append(topology.mode)
        seeds.append(topology.complexity)
        seeds.append(str(topology.metric_count))
        if req.query.signature:
            seeds.append(_h("|".join(str(int(x)) for x in req.query.signature[:64]), size=12))
        for key in sorted(topology.metrics.keys())[:20]:
            seeds.append(key)
            seeds.append(f"{topology.metrics[key]:.6f}")
        return sorted({_h(seed, size=12) for seed in seeds if seed})[:28]

    def decide(self, req: EngineRequest) -> EngineDecision:
        task_type = self._normalize_task_type(str(getattr(req, "task_type", "ask")))
        limits = dict(getattr(req, "limits", {}) or {})
        policy = dict(getattr(req, "policy", {}) or {})
        question = str(getattr(getattr(req, "query"), "text", "") or "")

        security = self._security_check(question, policy)
        if security.blocked:
            return EngineDecision(
                route="REFUSE",
                selected_chunk_ids=[],
                compression_stats={
                    "retrieved": len(req.candidates),
                    "selected": 0,
                    "route": "REFUSE",
                    "verified": [],
                    "not_run": ["all_actions_blocked_by_security_policy"],
                    "topology_mode": "n/a",
                    "topology_metric_count": 0,
                },
                security=security,
                rationale="CoreLocked v4: blocked by security policy.",
                stable_tokens=[],
            )

        gh = self._normalize_github_context(policy, limits)
        topology = self.kernel.analyze(question, policy, limits)
        ranked = self._rank_candidates(req=req, task_type=task_type, gh=gh, topology=topology)
        top_score = ranked[0].score if ranked else 0.0
        route = self._route(task_type, top_score, topology, limits)
        selected_ids = self._select(task_type=task_type, ranked=ranked, limits=limits)

        verified: list[str] = []
        not_run: list[str] = []
        if task_type == "review":
            verified, not_run = self._review_verification(gh, topology)

        stable_tokens = self._stable_tokens(req=req, selected_ids=selected_ids, gh=gh, topology=topology)
        rationale_map = {
            "FAST": "CoreLocked v4: high-confidence structural match.",
            "DEEP": "CoreLocked v4: expanded search due to complexity/low confidence.",
            "REVIEW": "CoreLocked v4: review mode with verification ladder semantics.",
        }
        return EngineDecision(
            route=route,
            selected_chunk_ids=selected_ids,
            compression_stats={
                "retrieved": len(req.candidates),
                "selected": len(selected_ids),
                "top_score": round(top_score, 6),
                "route": route,
                "verified": verified,
                "not_run": not_run,
                "topology_mode": topology.mode,
                "topology_complexity": topology.complexity,
                "topology_metric_count": topology.metric_count,
                "topology_signals": topology.signals,
            },
            security=security,
            rationale=rationale_map.get(route, "CoreLocked v4: decision complete."),
            stable_tokens=stable_tokens,
        )

    def run_topological_calculation(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = payload if isinstance(payload, dict) else {}
        series = data.get("series", [])
        vectors_raw = data.get("vectors", [])
        vectors = self.kernel._normalize_vectors(vectors_raw if isinstance(vectors_raw, list) else [])
        graph = self.kernel.graph_stats(vectors, threshold=1.0)
        series_stats = self.kernel.summarize_series(series if isinstance(series, (list, tuple)) else [])
        anomaly = self.kernel.anomaly_profile(series if isinstance(series, (list, tuple)) else [])
        signature = self.kernel.persistent_signature(
            series=series if isinstance(series, (list, tuple)) else [],
            graph=graph,
        )
        return {
            "series_summary": series_stats,
            "graph_stats": graph,
            "anomaly": anomaly,
            "signature": signature,
        }

    def handle_request(self, user_text: str, **_kwargs: Any) -> TopoCoreResponse:
        security = self._security_check(user_text, {})
        if security.blocked:
            return TopoCoreResponse(
                summary="Request blocked by security policy.",
                answer="CoreLocked v4: request refused.",
                next_steps=["Rephrase without secrets/internal-policy extraction attempts."],
                risks=["Potential prompt-injection / exfiltration attempt."],
                topo_rationale="security_refuse",
                trace_hashes={"signals": security.signals[:8]},
            )
        return TopoCoreResponse(
            summary="TopoCore v4 autonomous kernel active.",
            answer="Use decide(req) for deterministic routing and topology-aware selection.",
            next_steps=[
                "Pass github_context for diff-aware selection in PR tasks.",
                "Pass analytics_context/topology_context for advanced metrics.",
            ],
            risks=["External checks are NOT_RUN unless executed by outer orchestration."],
            topo_rationale="contract_compatible",
        )

    def remote_call(self, _payload: Any) -> dict[str, Any]:
        if not _to_bool(os.getenv("RB_TKYA_ALLOW_REMOTE", "0")):
            raise RuntimeError("Remote operations are disabled (RB_TKYA_ALLOW_REMOTE=0).")
        return {"status": "allowed_but_not_implemented"}


TopoCoreTCXv2CAS = TopoCoreTCXv4CASGit
TopoCoreTCXv4CAS = TopoCoreTCXv4CASGit


def _examples() -> Iterable[tuple[str, str]]:
    yield ("ask", "Where is retrieval orchestration logic?")
    yield ("review", "Review PR changes with topology-aware risk lens")


if __name__ == "__main__":  # pragma: no cover
    core = TopoCoreTCXv4CASGit()
    for task, question in _examples():
        req = EngineRequest(
            task_type=task,  # type: ignore[arg-type]
            query=EngineQuery(text=question, signature=[]),
            candidates=[],
            limits={},
            policy={},
        )
        decision = core.decide(req)
        print(task, decision.route, decision.compression_stats.get("topology_mode"))
