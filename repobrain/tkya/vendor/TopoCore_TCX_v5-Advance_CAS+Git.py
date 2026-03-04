"""TopoCore TCX v5 Advance CAS+Git.

Phase coverage in this file:
- Phase 0: contract-compatible deterministic core.
- Phase 1: codebook/symbolizer/HUK/action routing primitives.
- Phase 2: diff-aware ranking and hash-only trace packing.
- Phase 4: expanded MorseFlow confidence signals, verification ladder
  PASS/FAIL/PENDING/NOT_RUN states, and DS graph/vector/path kernels.
- Phase 5: optional v2 compatibility shim and branch-protection verification profiles.
- Phase 6: explicit shim adapter registry and versioned trace schema.
"""

from __future__ import annotations

from dataclasses import dataclass
import enum
import hashlib
import importlib.util
import math
import os
from pathlib import Path
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
    ".env",
    "private key",
    "exfiltrate",
    "dump",
    "reveal",
)
TRACE_SCHEMA_VERSION = "1.1"


def _to_bool(v: Any, default: bool = False) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, str):
        return v.strip().lower() in {"1", "true", "yes", "y", "on"}
    return default


def _to_float(v: Any, default: float) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _to_int(v: Any, default: int) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def _clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"\w+", (text or "").lower(), flags=re.UNICODE) if t]


def _h(value: str, size: int = 10) -> str:
    return hashlib.blake2s(value.encode("utf-8"), digest_size=size).hexdigest()


def _path_tokens(path: str) -> list[str]:
    normalized = str(path or "").replace("\\", "/").lower()
    return [token for token in re.split(r"[\/._\-]+", normalized) if token]


def _to_int_tuple(value: Any) -> tuple[int, int] | None:
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        a = _to_int(value[0], -1)
        b = _to_int(value[1], -1)
        if a >= 0 and b >= 0:
            return min(a, b), max(a, b)
    return None


@dataclass(frozen=True)
class TopoCoreResponse:
    summary: str
    answer: str
    next_steps: list[str]
    risks: list[str]
    topo_rationale: str | None = None
    trace_hashes: dict[str, Any] | None = None


@dataclass(frozen=True)
class GitHubContext:
    is_pr: bool
    changed_files: tuple[str, ...]
    changed_ranges: dict[str, tuple[tuple[int, int], ...]]
    diff_hunks_hash: str


class V2CompatibilityShim:
    """Optional compatibility shim for selected v2 adapters.

    The shim is disabled by default and only enabled with `RB_TKYA_ENABLE_V2_SHIM=1`.
    It never exposes raw outputs from v2 methods; all diagnostics are hash-only.
    """

    _ADAPTER_REGISTRY = {
        "topology_calc": "run_topological_calculation",
        "request_entry": "handle_request",
        "remote_entry": "remote_call",
    }

    def __init__(self) -> None:
        self.enabled = _to_bool(os.getenv("RB_TKYA_ENABLE_V2_SHIM", "0"))
        self.strict = _to_bool(os.getenv("RB_TKYA_V2_SHIM_STRICT", "0"))
        override = os.getenv("RB_TKYA_V2_SHIM_PATH", "").strip()
        if override:
            self.path = Path(override).expanduser().resolve()
        else:
            self.path = (Path(__file__).resolve().parent / "TopoCore_TCX_v2-CAS.py").resolve()

        self._core: Any | None = None
        self._state_reason = "disabled"
        self._caps: list[str] = []
        self._adapters: list[str] = []
        self._adapter_methods: dict[str, Any] = {}
        if self.enabled:
            self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._state_reason = "missing"
            if self.strict:
                raise RuntimeError(f"v2 compatibility shim enabled, but file is missing: {self.path}")
            return

        try:
            spec = importlib.util.spec_from_file_location("repobrain_tkya_v2_compat", self.path)
            if spec is None or spec.loader is None:
                raise RuntimeError(f"Failed to build import spec for: {self.path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            core_cls = getattr(module, "TopoCoreTCXv2CAS", None)
            if core_cls is None:
                raise RuntimeError("v2 module missing TopoCoreTCXv2CAS.")
            self._core = core_cls()
            self._adapter_methods = {}
            self._adapters = []
            self._caps = []
            for adapter_name, method_name in self._ADAPTER_REGISTRY.items():
                method = getattr(self._core, method_name, None)
                if callable(method):
                    self._adapter_methods[adapter_name] = method
                    self._adapters.append(adapter_name)
                    self._caps.append(method_name)
            self._adapters.sort()
            self._caps.sort()
            self._state_reason = "loaded"
        except Exception as exc:
            self._state_reason = "load_error"
            if self.strict:
                raise RuntimeError("Failed to initialize v2 compatibility shim.") from exc

    @staticmethod
    def _hash_keys(raw: Any) -> str:
        if isinstance(raw, dict):
            payload = "|".join(sorted(map(str, raw.keys())))
            return _h(payload, size=12)
        return _h(type(raw).__name__, size=12)

    def _run_topology_calc(
        self,
        method: Any,
        *,
        policy: dict[str, Any],
        limits: dict[str, Any],
    ) -> dict[str, Any]:
        analytics_context = policy.get("analytics_context") or limits.get("analytics_context")
        if not isinstance(analytics_context, dict):
            return {"state": "skipped", "reason": "no_analytics_context"}
        try:
            raw = method(analytics_context)
        except Exception:
            return {"state": "error", "reason": "call_failed"}
        return {
            "state": "ok",
            "result_hash": self._hash_keys(raw),
            "result_keys_count": len(raw.keys()) if isinstance(raw, dict) else 0,
        }

    def _run_request_entry(
        self,
        method: Any,
        *,
        policy: dict[str, Any],
        limits: dict[str, Any],
    ) -> dict[str, Any]:
        probe_text = str(
            policy.get("shim_probe_query")
            or limits.get("shim_probe_query")
            or "compat_probe"
        )
        try:
            raw = method(probe_text)
        except Exception:
            return {"state": "error", "reason": "call_failed"}
        summary = str(getattr(raw, "summary", "") or "")
        answer = str(getattr(raw, "answer", "") or "")
        payload = f"{type(raw).__name__}|{len(summary)}|{len(answer)}"
        return {"state": "ok", "result_hash": _h(payload, size=12)}

    def _run_remote_entry(
        self,
        method: Any,
        *,
        policy: dict[str, Any],
        limits: dict[str, Any],
    ) -> dict[str, Any]:
        del limits
        if not _to_bool(os.getenv("RB_TKYA_ALLOW_REMOTE", "0")):
            return {"state": "blocked", "reason": "remote_disabled"}
        if not _to_bool(policy.get("allow_remote_shim"), False):
            return {"state": "blocked", "reason": "policy_disallow_remote_shim"}
        try:
            raw = method({"probe": "compat"})
        except Exception:
            return {"state": "error", "reason": "call_failed"}
        return {"state": "ok", "result_hash": self._hash_keys(raw)}

    def _run_adapter(
        self,
        adapter_name: str,
        method: Any,
        *,
        policy: dict[str, Any],
        limits: dict[str, Any],
    ) -> dict[str, Any]:
        if adapter_name == "topology_calc":
            return self._run_topology_calc(method, policy=policy, limits=limits)
        if adapter_name == "request_entry":
            return self._run_request_entry(method, policy=policy, limits=limits)
        if adapter_name == "remote_entry":
            return self._run_remote_entry(method, policy=policy, limits=limits)
        return {"state": "skipped", "reason": "unknown_adapter"}

    def enrich(self, *, policy: dict[str, Any], limits: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            return {
                "used": False,
                "reason": "disabled",
                "caps": [],
                "adapters": [],
                "adapter_results": {},
            }
        if self._core is None:
            return {
                "used": False,
                "reason": self._state_reason,
                "caps": [],
                "adapters": [],
                "adapter_results": {},
            }

        result: dict[str, Any] = {
            "used": True,
            "reason": self._state_reason,
            "caps": list(self._caps),
            "adapters": list(self._adapters),
            "path_hash": _h(str(self.path), size=12),
            "adapter_results": {},
        }
        adapter_results: dict[str, dict[str, Any]] = {}
        for adapter_name in self._adapters:
            method = self._adapter_methods.get(adapter_name)
            if not callable(method):
                adapter_results[adapter_name] = {"state": "error", "reason": "missing_method"}
                continue
            adapter_results[adapter_name] = self._run_adapter(
                adapter_name,
                method,
                policy=policy,
                limits=limits,
            )
        result["adapter_results"] = adapter_results
        result["adapter_results_hash"] = _h(
            "|".join(
                f"{name}:{adapter_results.get(name, {}).get('state', 'unknown')}:"
                f"{adapter_results.get(name, {}).get('result_hash', '')}"
                for name in sorted(adapter_results)
            ),
            size=12,
        )

        topology_result = adapter_results.get("topology_calc", {})
        result["topology_call"] = str(topology_result.get("state", "n/a"))
        result["topology_hash"] = topology_result.get("result_hash")
        result["topology_keys_count"] = int(topology_result.get("result_keys_count", 0) or 0)
        return result


@dataclass
class Codebook:
    id: str
    bins_per_axis: int = 12
    hamming_gap: int = 2

    def quantize(self, value: float) -> int:
        return int(_clip(value) * (max(2, self.bins_per_axis) - 1))


class CodebookRegistry:
    def __init__(self) -> None:
        self._books: dict[str, Codebook] = {}

    def register(self, book: Codebook) -> None:
        self._books[book.id] = book

    def get(self, book_id: str) -> Codebook:
        return self._books.get(book_id) or Codebook(id=book_id)


class Symbolizer:
    def __init__(self, registry: CodebookRegistry) -> None:
        self.registry = registry

    @staticmethod
    def _hamming(a: list[int], b: list[int]) -> int:
        width = min(len(a), len(b))
        return sum(1 for i in range(width) if a[i] != b[i]) + abs(len(a) - len(b))

    def symbolize(self, values: list[float], book_id: str) -> list[int]:
        book = self.registry.get(book_id)
        return [book.quantize(v) for v in values]

    def enforce_gap(self, codes: list[list[int]], book_id: str) -> list[list[int]]:
        book = self.registry.get(book_id)
        out = [list(c) for c in codes]
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                if self._hamming(out[i], out[j]) < book.hamming_gap and out[i]:
                    out[i][-1] = (out[i][-1] + book.hamming_gap) % max(2, book.bins_per_axis)
        return out


class HUKCore:
    def __init__(self, symbolizer: Symbolizer) -> None:
        self.symbolizer = symbolizer

    @staticmethod
    def _entropy(text: str) -> float:
        if not text:
            return 0.0
        freq: dict[str, int] = {}
        for ch in text:
            freq[ch] = freq.get(ch, 0) + 1
        n = float(len(text))
        return -sum((c / n) * math.log2(max(c / n, 1e-12)) for c in freq.values())

    def fast_gate(self, text: str, *, book_id: str) -> dict[str, Any]:
        toks = _tokens(text)
        entropy = _clip(self._entropy(text) / 7.5)
        density = _clip(len(toks) / 40.0)
        smooth = _clip(1.0 - abs(len(set(toks)) - len(toks)) / max(1, len(toks)))
        bars = [entropy, density, smooth]
        codes = self.symbolizer.symbolize(bars, book_id)
        score = _clip(0.55 * entropy + 0.30 * density + 0.15 * smooth)
        return {"score": score, "bars": bars, "codes": codes, "bars_hash": _h(",".join(f"{x:.3f}" for x in bars))}


class Action(enum.Enum):
    NARROW_RETRIEVAL = "NARROW_RETRIEVAL"
    VERIFY = "VERIFY"
    REDUCE_BRANCHING = "REDUCE_BRANCHING"
    EXPAND = "EXPAND"


class TopoRoute:
    def decide(self, *, score: float, risk_high: bool, task_type: str) -> dict[str, Any]:
        if task_type == "review":
            return {"action": Action.VERIFY.value, "params": {"verification": "review"}}
        if score >= 0.64 and not risk_high:
            return {"action": Action.NARROW_RETRIEVAL.value, "params": {"k_multiplier": 0.75}}
        if risk_high:
            return {"action": Action.VERIFY.value, "params": {"verification": "safety"}}
        if score >= 0.42:
            return {"action": Action.REDUCE_BRANCHING.value, "params": {"branch_limit": 2}}
        return {"action": Action.EXPAND.value, "params": {"branch_limit": 4}}


class DataScienceTopologyKernel:
    @staticmethod
    def _series(values: Iterable[Any]) -> list[float]:
        out: list[float] = []
        for x in values:
            try:
                out.append(float(x))
            except (TypeError, ValueError):
                continue
        return out

    @staticmethod
    def _vectors(values: Any) -> list[list[float]]:
        if not isinstance(values, list):
            return []
        out: list[list[float]] = []
        for row in values:
            if not isinstance(row, (list, tuple)):
                continue
            vector: list[float] = []
            for item in row:
                try:
                    vector.append(float(item))
                except (TypeError, ValueError):
                    vector = []
                    break
            if vector:
                out.append(vector)
        return out

    @staticmethod
    def _extract_edges(values: Any) -> list[tuple[str, str]]:
        if not isinstance(values, list):
            return []
        out: list[tuple[str, str]] = []
        for item in values:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                a = str(item[0]).strip()
                b = str(item[1]).strip()
            elif isinstance(item, dict):
                a = str(item.get("from", item.get("src", ""))).strip()
                b = str(item.get("to", item.get("dst", ""))).strip()
            else:
                continue
            if not a or not b:
                continue
            out.append((a, b))
        return out

    @staticmethod
    def _graph_metrics(edges: list[tuple[str, str]]) -> dict[str, float]:
        if not edges:
            return {}
        nodes = {node for edge in edges for node in edge}
        n = len(nodes)
        m = len(edges)
        if n <= 0:
            return {}

        parent: dict[str, str] = {node: node for node in nodes}

        def find(x: str) -> str:
            root = x
            while parent[root] != root:
                root = parent[root]
            while parent[x] != x:
                nxt = parent[x]
                parent[x] = root
                x = nxt
            return root

        def union(a: str, b: str) -> None:
            ra = find(a)
            rb = find(b)
            if ra != rb:
                parent[rb] = ra

        for a, b in edges:
            union(a, b)

        components = len({find(node) for node in nodes})
        avg_degree = (2.0 * m) / float(n)
        density = 0.0 if n <= 1 else _clip((2.0 * m) / float(n * (n - 1)))
        return {
            "graph_nodes": float(n),
            "graph_edges": float(m),
            "graph_components": float(components),
            "graph_avg_degree": float(avg_degree),
            "graph_density": float(density),
        }

    @staticmethod
    def _vector_metrics(vectors: list[list[float]]) -> dict[str, float]:
        if not vectors:
            return {}
        dim = max((len(row) for row in vectors), default=0)
        if dim <= 0:
            return {}
        aligned: list[list[float]] = []
        for row in vectors:
            padded = list(row[:dim])
            if len(padded) < dim:
                padded.extend([0.0] * (dim - len(padded)))
            aligned.append(padded)
        centroid = [statistics.fmean(row[i] for row in aligned) for i in range(dim)]

        def norm(row: list[float]) -> float:
            return math.sqrt(sum(v * v for v in row))

        dists = []
        for row in aligned:
            delta = [row[i] - centroid[i] for i in range(dim)]
            dists.append(norm(delta))
        return {
            "vector_count": float(len(aligned)),
            "vector_dim": float(dim),
            "vector_dispersion": float(statistics.fmean(dists) if dists else 0.0),
            "vector_centroid_norm": float(norm(centroid)),
        }

    @staticmethod
    def _path_metrics(values: Any) -> dict[str, float]:
        if not isinstance(values, list):
            return {}
        lengths: list[float] = []
        for item in values:
            try:
                value = float(item)
            except (TypeError, ValueError):
                continue
            if value >= 0:
                lengths.append(value)
        if not lengths:
            return {}
        mean = statistics.fmean(lengths)
        stdev = statistics.pstdev(lengths) if len(lengths) > 1 else 0.0
        return {
            "path_count": float(len(lengths)),
            "path_mean": float(mean),
            "path_max": float(max(lengths)),
            "path_cv": float(stdev / mean if mean > 1e-12 else 0.0),
        }

    def analyze(self, query: str, policy: dict[str, Any], limits: dict[str, Any]) -> dict[str, Any]:
        ctx = policy.get("analytics_context") or limits.get("analytics_context") or {}
        if not isinstance(ctx, dict):
            ctx = {}
        series = self._series(ctx.get("series", []))
        vectors = self._vectors(ctx.get("vectors", []))
        edges = self._extract_edges(ctx.get("graph_edges", ctx.get("edges", [])))
        paths = ctx.get("path_lengths", [])
        outliers = 0.0
        if len(series) > 1:
            mean = statistics.fmean(series)
            stdev = statistics.pstdev(series)
            if stdev > 1e-12:
                outliers = sum(1 for v in series if abs((v - mean) / stdev) >= 2.5) / float(len(series))
        hinted = bool(
            set(_tokens(query))
            & {
                "topology",
                "graph",
                "cluster",
                "anomaly",
                "dataset",
                "path",
                "community",
            }
        )
        metrics: dict[str, float] = {}
        if series:
            metrics["series_count"] = float(len(series))
            metrics["series_mean"] = float(statistics.fmean(series))
            metrics["outlier_ratio"] = float(outliers)
        metrics.update(self._vector_metrics(vectors))
        metrics.update(self._graph_metrics(edges))
        metrics.update(self._path_metrics(paths))
        metric_count = len(metrics)
        has_graph = "graph_nodes" in metrics
        has_vectors = "vector_count" in metrics
        has_paths = "path_count" in metrics
        if metric_count >= 10 or metrics.get("graph_nodes", 0.0) >= 500:
            complexity = "high"
        elif metric_count >= 4 or hinted:
            complexity = "medium"
        else:
            complexity = "low"
        if has_graph and has_vectors:
            mode = "analytics_graph_vector"
        elif has_graph:
            mode = "analytics_graph"
        elif has_vectors or has_paths or series:
            mode = "analytics"
        else:
            mode = "generic"
        return {"mode": mode, "complexity": complexity, "metric_count": metric_count, "metrics": metrics}


class ZigZagAnalyzer:
    """Signal-shape analyzer used to tune route confidence without randomness."""

    @staticmethod
    def analyze(values: list[float]) -> dict[str, Any]:
        if len(values) < 2:
            return {"turning_points": 0, "volatility": 0.0, "trend": "flat"}

        deltas = [values[i + 1] - values[i] for i in range(len(values) - 1)]
        signs = [1 if d > 1e-12 else -1 if d < -1e-12 else 0 for d in deltas]

        turning_points = 0
        last_sign = 0
        for sign in signs:
            if sign == 0:
                continue
            if last_sign != 0 and sign != last_sign:
                turning_points += 1
            last_sign = sign

        slope = values[-1] - values[0]
        if abs(slope) < 1e-12:
            trend = "flat"
        elif slope > 0:
            trend = "up"
        else:
            trend = "down"

        volatility = statistics.fmean(abs(d) for d in deltas)
        return {
            "turning_points": int(turning_points),
            "volatility": round(float(volatility), 6),
            "trend": trend,
        }


class MorseFlowGate:
    """Diff-signal gate used to enforce safe verification routing in PR contexts."""

    _SECRET_PATTERNS = (
        r"-----BEGIN (?:RSA )?PRIVATE KEY-----",
        r"\bghp_[A-Za-z0-9]{20,}\b",
        r"\bAKIA[0-9A-Z]{16}\b",
        r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"]?.{8,}",
    )
    _WORKFLOW_RISK_PATTERNS = (
        r"(?i)\bpull_request_target\b",
        r"(?i)\bpermissions\s*:\s*write-all\b",
        r"(?i)\bcurl\s+[^|]+\|\s*(sh|bash)\b",
        r"(?i)\b--no-verify\b",
        r"(?i)\bset-output\b",
    )

    @classmethod
    def analyze(cls, github_context: GitHubContext, policy: dict[str, Any]) -> dict[str, Any]:
        payload = policy.get("github_context", {})
        hunks: list[str] = []
        if isinstance(payload, dict):
            raw_hunks = payload.get("diff_hunks", [])
            if isinstance(raw_hunks, list):
                hunks = [str(item) for item in raw_hunks if isinstance(item, str)]
        patch_blob = "\n".join(hunks)
        has_conflict_markers = any(token in patch_blob for token in ("<<<<<<<", "=======", ">>>>>>>"))
        todo_count = len(re.findall(r"(?i)\b(TODO|FIXME)\b", patch_blob))
        has_secret_signal = any(re.search(pattern, patch_blob) for pattern in cls._SECRET_PATTERNS)
        workflow_risky = any(re.search(pattern, patch_blob) for pattern in cls._WORKFLOW_RISK_PATTERNS)
        test_disable_signal = bool(
            re.search(r"(?i)\b(pytest\s+-k\s+not|\bskipif\b|xfail|pragma:\s*no cover)\b", patch_blob)
        )
        workflow_files_changed = any(
            path.startswith(".github/workflows/")
            for path in github_context.changed_files
        )

        policy_force_verify = _to_bool(policy.get("force_verify"), False)
        confidence = 0.0
        signals: list[str] = []
        if has_conflict_markers:
            confidence += 0.70
            signals.append("conflict_markers")
        if has_secret_signal:
            confidence += 0.55
            signals.append("secret_signal")
        if workflow_risky:
            confidence += 0.35
            signals.append("workflow_risky_pattern")
        if workflow_files_changed:
            confidence += 0.12
            signals.append("workflow_files_changed")
        if test_disable_signal:
            confidence += 0.20
            signals.append("test_disable_signal")
        if todo_count > 0:
            confidence += min(0.15, 0.03 * todo_count)
            signals.append("todo_fixme_present")
        confidence = _clip(confidence)
        verify_required = bool(policy_force_verify or confidence >= 0.35)
        if policy_force_verify:
            signals.append("policy_force_verify")

        if confidence >= 0.55:
            risk = "high"
        elif confidence >= 0.25 or (todo_count > 0 and github_context.is_pr):
            risk = "medium"
        else:
            risk = "low"
        return {
            "risk": risk,
            "verify_required": verify_required,
            "confidence": round(confidence, 6),
            "signals": sorted(set(signals)),
            "has_conflict_markers": has_conflict_markers,
            "has_secret_signal": has_secret_signal,
            "workflow_risky": bool(workflow_risky or workflow_files_changed),
            "test_disable_signal": test_disable_signal,
            "todo_count": int(todo_count),
        }


class VerificationPlanner:
    """Planner that marks what checks were truly observed vs NOT_RUN."""

    _DEFAULT_CHECKS = ("ruff check .", "pytest -q")
    _DEFAULT_BY_TASK = {
        "ask": ("ruff check .",),
        "locate": (),
        "explain": ("ruff check .",),
        "review": ("ruff check .", "pytest -q"),
    }

    @classmethod
    def _resolve_profile(
        cls,
        *,
        task: str,
        policy: dict[str, Any],
    ) -> tuple[str, str, list[str]]:
        github_context = policy.get("github_context", {})
        branch = "unknown"
        if isinstance(github_context, dict):
            branch = str(
                github_context.get("base_ref")
                or github_context.get("target_branch")
                or github_context.get("branch")
                or "unknown"
            ).strip()
        profile_name = "default"
        required_from_profile: list[str] = []

        profiles = policy.get("branch_protection_profiles", {})
        profile_data: dict[str, Any] = {}
        if isinstance(profiles, dict):
            if branch in profiles and isinstance(profiles[branch], dict):
                profile_name = branch
                profile_data = profiles[branch]
            elif "default" in profiles and isinstance(profiles["default"], dict):
                profile_name = "default"
                profile_data = profiles["default"]

        if not profile_data:
            branch_protection = policy.get("branch_protection", {})
            if isinstance(branch_protection, dict):
                profile_name = str(branch_protection.get("name", "policy") or "policy")
                profile_data = branch_protection

        required_checks = profile_data.get("required_checks", {})
        if isinstance(required_checks, dict):
            by_task = required_checks.get(task, [])
            if isinstance(by_task, list):
                required_from_profile.extend(str(item).strip() for item in by_task if str(item).strip())
            global_items = required_checks.get("all", [])
            if isinstance(global_items, list):
                required_from_profile.extend(
                    str(item).strip()
                    for item in global_items
                    if str(item).strip()
                )
        elif isinstance(required_checks, list):
            required_from_profile.extend(str(item).strip() for item in required_checks if str(item).strip())

        defaults = list(cls._DEFAULT_BY_TASK.get(task, cls._DEFAULT_CHECKS))
        required = sorted(set(defaults + required_from_profile))
        return profile_name, branch or "unknown", required

    @classmethod
    def plan(cls, *, task: str, policy: dict[str, Any], morse: dict[str, Any]) -> dict[str, Any]:
        if task != "review":
            return {
                "verified": [],
                "not_run": [],
                "failed": [],
                "pending": [],
                "ladder": [],
                "pass_count": 0,
                "fail_count": 0,
                "pending_count": 0,
                "not_run_count": 0,
                "completeness": 0.0,
                "strict_pass": False,
                "profile_name": "n/a",
                "branch": "n/a",
                "required_checks": [],
            }

        verified: list[str] = ["deterministic_ranking", "phase1_router_applied"]
        observed_pass: set[str] = set()
        observed_failed: set[str] = set()
        observed_pending: set[str] = set()
        profile_name, branch, required_checks = cls._resolve_profile(task=task, policy=policy)

        verification_context = policy.get("verification_context", {})
        if isinstance(verification_context, dict):
            checks = verification_context.get("checks", [])
            if isinstance(checks, list):
                for item in checks:
                    if not isinstance(item, dict):
                        continue
                    name = str(item.get("name", "")).strip()
                    state = str(item.get("status", "")).strip().lower()
                    if not name:
                        continue
                    if state in {"pass", "passed", "success"}:
                        observed_pass.add(name)
                    elif state in {"fail", "failed", "failure"}:
                        observed_failed.add(name)
                    elif state in {"pending", "queued", "running", "in_progress"}:
                        observed_pending.add(name)

        if isinstance(verification_context, dict):
            extra_required = verification_context.get("required_checks", [])
            if isinstance(extra_required, list):
                for item in extra_required:
                    name = str(item).strip()
                    if name:
                        required_checks.append(name)
        required_checks = sorted(set(required_checks))

        ladder_names = sorted(set(required_checks) | observed_pass | observed_failed | observed_pending)

        not_run: list[str] = []
        failed_checks: list[str] = []
        pending_checks: list[str] = []
        ladder: list[dict[str, str]] = []
        for check in ladder_names:
            if check in observed_failed:
                state = "FAIL"
                failed_checks.append(check)
                not_run.append(f"{check}:FAILED")
            elif check in observed_pending:
                state = "PENDING"
                pending_checks.append(check)
                not_run.append(f"{check}:PENDING")
            elif check not in observed_pass:
                state = "NOT_RUN"
                not_run.append(f"{check}:NOT_RUN")
            else:
                state = "PASS"
                verified.append(check)
            ladder.append({"check": check, "state": state})

        if morse.get("has_conflict_markers"):
            not_run.append("merge_conflicts_resolved:NOT_RUN")
        if morse.get("has_secret_signal"):
            not_run.append("manual_security_review:NOT_RUN")
        if morse.get("todo_count", 0):
            not_run.append("todo_cleanup_review:NOT_RUN")

        pass_count = sum(1 for item in ladder if item["state"] == "PASS")
        fail_count = sum(1 for item in ladder if item["state"] == "FAIL")
        pending_count = sum(1 for item in ladder if item["state"] == "PENDING")
        not_run_count = sum(1 for item in ladder if item["state"] == "NOT_RUN")
        total = max(1, len(ladder))
        completeness = pass_count / float(total)

        return {
            "verified": sorted(set(verified)),
            "not_run": sorted(set(not_run)),
            "failed": sorted(set(failed_checks)),
            "pending": sorted(set(pending_checks)),
            "ladder": ladder,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "pending_count": pending_count,
            "not_run_count": not_run_count,
            "completeness": round(completeness, 6),
            "strict_pass": bool(pass_count == len(ladder) and fail_count == 0 and pending_count == 0),
            "profile_name": profile_name,
            "branch": branch,
            "required_checks": required_checks,
        }


class TopoCoreTCXv5AdvanceCASGit:
    def __init__(self) -> None:
        self.book_id = "v5-default"
        self.registry = CodebookRegistry()
        self.registry.register(Codebook(id=self.book_id, bins_per_axis=12, hamming_gap=2))
        self.symbolizer = Symbolizer(self.registry)
        self.huk = HUKCore(self.symbolizer)
        self.router = TopoRoute()
        self.kernel = DataScienceTopologyKernel()
        self.zigzag = ZigZagAnalyzer()
        self.morse = MorseFlowGate()
        self.verifier = VerificationPlanner()
        self.v2_compat = V2CompatibilityShim()

    @staticmethod
    def _normalize_github_context(policy: dict[str, Any], limits: dict[str, Any]) -> GitHubContext:
        raw = policy.get("github_context") or limits.get("github_context") or {}
        if not isinstance(raw, dict):
            raw = {}

        is_pr = _to_bool(raw.get("is_pr"), False)

        changed_files_raw = raw.get("changed_files", [])
        changed_files: list[str] = []
        if isinstance(changed_files_raw, list):
            for item in changed_files_raw:
                path = str(item or "").replace("\\", "/").strip()
                if path:
                    changed_files.append(path)

        ranges_map: dict[str, list[tuple[int, int]]] = {}
        changed_ranges_raw = raw.get("changed_ranges", {})
        if isinstance(changed_ranges_raw, dict):
            for path_value, segments in changed_ranges_raw.items():
                path = str(path_value or "").replace("\\", "/").strip()
                if not path:
                    continue
                if not isinstance(segments, list):
                    continue
                for segment in segments:
                    pair = _to_int_tuple(segment)
                    if pair is None:
                        continue
                    ranges_map.setdefault(path, []).append(pair)

        changed_lines_raw = raw.get("changed_lines", [])
        if isinstance(changed_lines_raw, list):
            for item in changed_lines_raw:
                if not isinstance(item, dict):
                    continue
                path = str(item.get("file_path", "") or "").replace("\\", "/").strip()
                if not path:
                    continue
                start = _to_int(item.get("line_start"), -1)
                end = _to_int(item.get("line_end"), -1)
                if start >= 0 and end >= 0:
                    ranges_map.setdefault(path, []).append((min(start, end), max(start, end)))

        hunks = raw.get("diff_hunks", [])
        if not isinstance(hunks, list):
            hunks = []
        hunks_norm = [str(item) for item in hunks if isinstance(item, str)]
        diff_hunks_hash = _h("|".join(_h(item, size=8) for item in hunks_norm), size=12)

        normalized_ranges = {
            path: tuple(sorted(set(segments)))
            for path, segments in ranges_map.items()
        }
        return GitHubContext(
            is_pr=is_pr,
            changed_files=tuple(sorted(set(changed_files))),
            changed_ranges=normalized_ranges,
            diff_hunks_hash=diff_hunks_hash,
        )

    @staticmethod
    def _line_overlap_score(
        *,
        candidate_start: int | None,
        candidate_end: int | None,
        ranges: tuple[tuple[int, int], ...],
    ) -> float:
        if candidate_start is None or candidate_end is None or not ranges:
            return 0.0
        c0 = min(candidate_start, candidate_end)
        c1 = max(candidate_start, candidate_end)
        if c1 < c0:
            return 0.0
        c_len = max(1, c1 - c0 + 1)
        best = 0.0
        for r0, r1 in ranges:
            inter = max(0, min(c1, r1) - max(c0, r0) + 1)
            if inter <= 0:
                continue
            score = inter / float(c_len)
            if score > best:
                best = score
        return _clip(best)

    def _rank_candidates(
        self,
        candidates: list[EngineCandidate],
        github_context: GitHubContext,
    ) -> tuple[list[tuple[EngineCandidate, float]], dict[str, Any]]:
        changed_files = set(github_context.changed_files)
        ranked: list[tuple[EngineCandidate, float]] = []
        boosted_changed = 0
        for candidate in candidates:
            base = _clip(float(candidate.score_local))
            path = str(candidate.file_path or "").replace("\\", "/")
            path_lower = path.lower()
            file_boost = 0.08 if path in changed_files else 0.0
            line_boost = 0.0
            if path in github_context.changed_ranges:
                line_boost = 0.12 * self._line_overlap_score(
                    candidate_start=candidate.line_start,
                    candidate_end=candidate.line_end,
                    ranges=github_context.changed_ranges[path],
                )
            if file_boost > 0 or line_boost > 0:
                boosted_changed += 1
            pr_penalty = 0.01 if github_context.is_pr and changed_files and path not in changed_files else 0.0
            path_prior = 0.01 if path_lower.startswith("repobrain/") or path_lower.startswith("src/") else 0.0
            adjusted = _clip(base + file_boost + line_boost + path_prior - pr_penalty)
            ranked.append((candidate, adjusted))
        ranked.sort(key=lambda item: (-item[1], str(item[0].file_path or ""), item[0].chunk_id))
        return ranked, {"boosted_changed_candidates": boosted_changed}

    @staticmethod
    def _build_hash_only_trace(
        *,
        question: str,
        selected_ids: list[str],
        github_context: GitHubContext,
        zigzag: dict[str, Any],
        morse: dict[str, Any],
        ranked: list[tuple[EngineCandidate, float]],
    ) -> dict[str, Any]:
        selected_join = ",".join(selected_ids[:32])
        ranking_tokens = [f"{item[0].chunk_id}:{item[1]:.4f}" for item in ranked[:20]]
        return {
            "schema_version": TRACE_SCHEMA_VERSION,
            "query_hash": _h(question, size=12),
            "selected_hash": _h(selected_join, size=12),
            "ranking_hash": _h("|".join(ranking_tokens), size=12),
            "github_scope_hash": _h(
                ",".join(github_context.changed_files) + "|" + github_context.diff_hunks_hash,
                size=12,
            ),
            "zigzag_hash": _h(
                f"{zigzag.get('turning_points', 0)}|{zigzag.get('volatility', 0.0)}|{zigzag.get('trend', 'flat')}",
                size=12,
            ),
            "morse_hash": _h(
                (
                    f"{morse.get('risk', 'low')}|"
                    f"{float(morse.get('confidence', 0.0)):.3f}|"
                    f"{int(bool(morse.get('has_conflict_markers', False)))}|"
                    f"{int(bool(morse.get('has_secret_signal', False)))}|"
                    f"{int(bool(morse.get('workflow_risky', False)))}|"
                    f"{int(bool(morse.get('test_disable_signal', False)))}|"
                    f"{int(morse.get('todo_count', 0) or 0)}"
                ),
                size=12,
            ),
            "trace_inputs_hash": _h(
                "|".join(
                    [
                        _h(question, size=8),
                        _h(selected_join, size=8),
                        _h(",".join(github_context.changed_files), size=8),
                    ]
                ),
                size=12,
            ),
        }

    def _security(self, text: str, policy: dict[str, Any]) -> EngineSecurity:
        blocked = False
        signals: list[str] = []
        lowered = (text or "").lower()
        if _detect_security_external is not None:
            data = _detect_security_external(text)
            blocked = blocked or bool(data.get("blocked", False))
            for item in data.get("signals", []):
                token = str(item).strip()
                if token:
                    signals.append(token)
        for marker in _SECURITY_MARKERS:
            if marker in lowered:
                blocked = True
                signals.append(f"keyword:{marker}")
        disallowed = policy.get("disallowed_actions", [])
        if isinstance(disallowed, (list, tuple, set)):
            for marker in disallowed:
                token = str(marker).strip().lower()
                if token and token in lowered:
                    blocked = True
                    signals.append(f"policy:{token}")
        return EngineSecurity(
            blocked=blocked,
            injection_risk="high" if blocked else "low",
            exfiltration_risk="high" if blocked else "low",
            signals=sorted(set(signals)),
        )

    def decide(self, req: EngineRequest) -> EngineDecision:
        task = str(req.task_type or "ask").lower().strip()
        task = task if task in {"ask", "locate", "explain", "review"} else "ask"
        question = str(req.query.text or "")
        limits = dict(req.limits or {})
        policy = dict(req.policy or {})
        github_context = self._normalize_github_context(policy, limits)
        sec = self._security(question, policy)
        if sec.blocked:
            return EngineDecision(
                route="REFUSE",
                selected_chunk_ids=[],
                compression_stats={
                    "retrieved": len(req.candidates),
                    "selected": 0,
                    "phase1_action": "REFUSE",
                    "phase1_params": {"reason": "security_block"},
                    "github_is_pr": github_context.is_pr,
                },
                security=sec,
                rationale="CoreLocked v5: blocked by security policy.",
                stable_tokens=[],
            )

        topology = self.kernel.analyze(question, policy, limits)
        huk = self.huk.fast_gate(question, book_id=self.book_id)
        ranked, rank_meta = self._rank_candidates(list(req.candidates), github_context)
        ranked_scores = [score for _, score in ranked]
        top_score = float(ranked_scores[0]) if ranked_scores else 0.0
        zigzag = self.zigzag.analyze(ranked_scores[:12] if ranked_scores else [top_score])
        morse = self.morse.analyze(github_context, policy)

        risk_high = topology["complexity"] == "high" or morse.get("risk") == "high"
        phase1 = self.router.decide(score=float(huk["score"]), risk_high=risk_high, task_type=task)
        if morse.get("verify_required"):
            phase1 = {
                "action": Action.VERIFY.value,
                "params": {
                    "verification": "morse_gate",
                    "reason": "conflict_or_secret_signal",
                },
            }
        action = str(phase1["action"])

        min_fast = _to_float(limits.get("min_score_fast"), 0.05)

        if task == "review":
            route = "REVIEW"
        elif action == Action.VERIFY.value and morse.get("verify_required"):
            route = "DEEP"
        elif action == Action.VERIFY.value and risk_high:
            route = "DEEP"
        elif action == Action.NARROW_RETRIEVAL.value and top_score >= min_fast:
            route = "FAST"
        elif top_score < min_fast or topology["complexity"] == "high" or zigzag["turning_points"] >= 3:
            route = "DEEP"
        else:
            route = "FAST"

        max_sources = max(1, _to_int(limits.get("max_sources"), 8))
        selected_ids = [candidate.chunk_id for candidate, _ in ranked[:max_sources]]
        verification = self.verifier.plan(task=task, policy=policy, morse=morse)
        compat = self.v2_compat.enrich(policy=policy, limits=limits)
        trace = self._build_hash_only_trace(
            question=question,
            selected_ids=selected_ids,
            github_context=github_context,
            zigzag=zigzag,
            morse=morse,
            ranked=ranked,
        )
        stable = sorted(
            {
                _h(question, size=8),
                _h(",".join(selected_ids[:16]), size=8),
                str(huk["bars_hash"]),
                str(trace["ranking_hash"]),
                str(trace["github_scope_hash"]),
            }
        )[:12]
        return EngineDecision(
            route=route,
            selected_chunk_ids=selected_ids,
            compression_stats={
                "retrieved": len(req.candidates),
                "selected": len(selected_ids),
                "top_score": round(top_score, 6),
                "phase1_action": action,
                "phase1_params": dict(phase1.get("params", {})),
                "huk_score": round(float(huk["score"]), 6),
                "huk_bars_hash": str(huk["bars_hash"]),
                "codebook_id": self.book_id,
                "topology_mode": topology["mode"],
                "topology_complexity": topology["complexity"],
                "topology_metric_count": topology["metric_count"],
                "zigzag_turning_points": int(zigzag["turning_points"]),
                "zigzag_volatility": float(zigzag["volatility"]),
                "zigzag_trend": str(zigzag["trend"]),
                "morse_risk": str(morse["risk"]),
                "morse_verify_required": bool(morse["verify_required"]),
                "morse_confidence": float(morse.get("confidence", 0.0)),
                "morse_signals": list(morse.get("signals", [])),
                "morse_todo_count": int(morse["todo_count"]),
                "morse_conflict_markers": bool(morse["has_conflict_markers"]),
                "morse_secret_signal": bool(morse["has_secret_signal"]),
                "morse_workflow_risky": bool(morse.get("workflow_risky", False)),
                "morse_test_disable_signal": bool(morse.get("test_disable_signal", False)),
                "diff_boosted_candidates": int(rank_meta["boosted_changed_candidates"]),
                "github_is_pr": bool(github_context.is_pr),
                "github_changed_files": len(github_context.changed_files),
                "verified": list(verification["verified"]),
                "not_run": list(verification["not_run"]),
                "verification_failed": list(verification["failed"]),
                "verification_pending": list(verification["pending"]),
                "verification_ladder": list(verification["ladder"]),
                "verification_pass_count": int(verification["pass_count"]),
                "verification_fail_count": int(verification["fail_count"]),
                "verification_pending_count": int(verification["pending_count"]),
                "verification_not_run_count": int(verification["not_run_count"]),
                "verification_completeness": float(verification["completeness"]),
                "verification_strict_pass": bool(verification["strict_pass"]),
                "verification_profile": str(verification.get("profile_name", "n/a")),
                "verification_branch": str(verification.get("branch", "n/a")),
                "verification_required_checks": list(verification.get("required_checks", [])),
                "v2_compat_used": bool(compat.get("used", False)),
                "v2_compat_reason": str(compat.get("reason", "n/a")),
                "v2_compat_caps": list(compat.get("caps", [])),
                "v2_compat_adapters": list(compat.get("adapters", [])),
                "v2_compat_adapter_results": dict(compat.get("adapter_results", {})),
                "v2_compat_adapter_results_hash": compat.get("adapter_results_hash"),
                "v2_compat_path_hash": compat.get("path_hash"),
                "v2_compat_topology_call": str(compat.get("topology_call", "n/a")),
                "v2_compat_topology_hash": compat.get("topology_hash"),
                "v2_compat_topology_keys_count": int(compat.get("topology_keys_count", 0) or 0),
                "trace_schema_version": str(trace.get("schema_version", TRACE_SCHEMA_VERSION)),
                "trace": trace,
            },
            security=sec,
            rationale=f"CoreLocked v5: {route} via Phase1 action {action}.",
            stable_tokens=stable,
        )

    def run_topological_calculation(self, payload: dict[str, Any]) -> dict[str, Any]:
        policy = {"analytics_context": payload if isinstance(payload, dict) else {}}
        result = self.kernel.analyze("topology", policy, {})
        series = self.kernel._series((payload or {}).get("series", [])) if isinstance(payload, dict) else []
        zigzag = self.zigzag.analyze(series[:12] if series else [0.0])
        return {
            "mode": result["mode"],
            "complexity": result["complexity"],
            "metrics": result["metrics"],
            "zigzag": zigzag,
            "signature": _h(str(result["metrics"]), size=12),
        }

    def handle_request(self, user_text: str, **_kwargs: Any) -> TopoCoreResponse:
        sec = self._security(user_text, {})
        if sec.blocked:
            return TopoCoreResponse(
                summary="Request blocked by security policy.",
                answer="CoreLocked v5: request refused.",
                next_steps=["Rephrase without secrets/internal extraction attempts."],
                risks=["Potential prompt-injection / exfiltration attempt."],
                topo_rationale="security_refuse",
            )
        huk = self.huk.fast_gate(user_text, book_id=self.book_id)
        return TopoCoreResponse(
            summary="TopoCore v5 advanced kernel active.",
            answer="Use decide(req) for deterministic phase1 routing and selection.",
            next_steps=["Pass github_context and analytics_context for richer behavior."],
            risks=["External checks stay NOT_RUN unless executed externally."],
            topo_rationale=f"huk_score={huk['score']:.4f}",
            trace_hashes={"huk_bars_hash": str(huk["bars_hash"])},
        )

    def remote_call(self, _payload: Any) -> dict[str, Any]:
        if not _to_bool(os.getenv("RB_TKYA_ALLOW_REMOTE", "0")):
            raise RuntimeError("Remote operations are disabled (RB_TKYA_ALLOW_REMOTE=0).")
        return {"status": "allowed_but_not_implemented"}


TopoCoreTCXv2CAS = TopoCoreTCXv5AdvanceCASGit
TopoCoreTCXv5AdvanceCAS = TopoCoreTCXv5AdvanceCASGit
