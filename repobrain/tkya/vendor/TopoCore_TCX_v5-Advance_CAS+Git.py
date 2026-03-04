"""TopoCore TCX v5 Advance CAS+Git (Phase 0 + Phase 1, standalone)."""

from __future__ import annotations

from dataclasses import dataclass
import enum
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
    ".env",
    "private key",
    "exfiltrate",
    "dump",
    "reveal",
)


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


@dataclass(frozen=True)
class TopoCoreResponse:
    summary: str
    answer: str
    next_steps: list[str]
    risks: list[str]
    topo_rationale: str | None = None
    trace_hashes: dict[str, Any] | None = None


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

    def analyze(self, query: str, policy: dict[str, Any], limits: dict[str, Any]) -> dict[str, Any]:
        ctx = policy.get("analytics_context") or limits.get("analytics_context") or {}
        if not isinstance(ctx, dict):
            ctx = {}
        series = self._series(ctx.get("series", []))
        outliers = 0.0
        if len(series) > 1:
            mean = statistics.fmean(series)
            stdev = statistics.pstdev(series)
            if stdev > 1e-12:
                outliers = sum(1 for v in series if abs((v - mean) / stdev) >= 2.5) / float(len(series))
        hinted = bool(set(_tokens(query)) & {"topology", "graph", "cluster", "anomaly", "dataset"})
        metric_count = 0
        metrics: dict[str, float] = {}
        if series:
            metric_count += 3
            metrics["series_count"] = float(len(series))
            metrics["series_mean"] = float(statistics.fmean(series))
            metrics["outlier_ratio"] = float(outliers)
        complexity = "high" if metric_count >= 6 else "medium" if metric_count >= 3 or hinted else "low"
        mode = "analytics" if metric_count > 0 or hinted else "generic"
        return {"mode": mode, "complexity": complexity, "metric_count": metric_count, "metrics": metrics}


class TopoCoreTCXv5AdvanceCASGit:
    def __init__(self) -> None:
        self.book_id = "v5-default"
        self.registry = CodebookRegistry()
        self.registry.register(Codebook(id=self.book_id, bins_per_axis=12, hamming_gap=2))
        self.symbolizer = Symbolizer(self.registry)
        self.huk = HUKCore(self.symbolizer)
        self.router = TopoRoute()
        self.kernel = DataScienceTopologyKernel()

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
        sec = self._security(question, policy)
        if sec.blocked:
            return EngineDecision(
                route="REFUSE",
                selected_chunk_ids=[],
                compression_stats={"retrieved": len(req.candidates), "selected": 0, "phase1_action": "REFUSE"},
                security=sec,
                rationale="CoreLocked v5: blocked by security policy.",
                stable_tokens=[],
            )

        topology = self.kernel.analyze(question, policy, limits)
        huk = self.huk.fast_gate(question, book_id=self.book_id)
        risk_high = topology["complexity"] == "high"
        phase1 = self.router.decide(score=float(huk["score"]), risk_high=risk_high, task_type=task)
        action = str(phase1["action"])

        ranked = sorted(
            list(req.candidates),
            key=lambda c: (-float(c.score_local), str(c.file_path or ""), c.chunk_id),
        )
        top_score = float(ranked[0].score_local) if ranked else 0.0
        min_fast = _to_float(limits.get("min_score_fast"), 0.05)

        if task == "review":
            route = "REVIEW"
        elif action == Action.VERIFY.value:
            route = "DEEP"
        elif action == Action.NARROW_RETRIEVAL.value and top_score >= min_fast:
            route = "FAST"
        elif top_score < min_fast or topology["complexity"] == "high":
            route = "DEEP"
        else:
            route = "FAST"

        max_sources = max(1, _to_int(limits.get("max_sources"), 8))
        selected_ids = [c.chunk_id for c in ranked[:max_sources]]
        stable = sorted({_h(question), _h(",".join(selected_ids[:16])), str(huk["bars_hash"])})[:12]
        verified = ["deterministic_ranking", "phase1_router_applied"] if task == "review" else []
        not_run = ["external_ci_checks", "runtime_integration_tests"] if task == "review" else []
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
                "verified": verified,
                "not_run": not_run,
            },
            security=sec,
            rationale=f"CoreLocked v5: {route} via Phase1 action {action}.",
            stable_tokens=stable,
        )

    def run_topological_calculation(self, payload: dict[str, Any]) -> dict[str, Any]:
        policy = {"analytics_context": payload if isinstance(payload, dict) else {}}
        result = self.kernel.analyze("topology", policy, {})
        return {"mode": result["mode"], "complexity": result["complexity"], "metrics": result["metrics"]}

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

