from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Literal

from repobrain.topocore_lite import TopoCoreLite
from repobrain.tky_engine import EngineDecision, EngineRequest, EngineSecurity, TKYEngine

BACKEND_LITE = "lite"
BACKEND_V5 = "v5"
BACKEND_ORIGINAL = "original"
TKYABackend = Literal["lite", "v5", "original"]

_V5_FILENAME = "TopoCore_TCX_v5-Advance_CAS+Git.py"
_ORIGINAL_FILENAME = "TopoCore_TCX_v2-CAS.py"
_REMOTE_METHOD_GUARDS = (
    "remote_call",
    "call_remote",
    "request_remote",
    "send_remote",
    "_remote_call",
    "http_call",
)
_WARNED_MESSAGES: set[str] = set()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False


def _get_backend(value: str | None) -> TKYABackend:
    normalized = (value or "").strip().lower()
    if normalized in {BACKEND_V5, "advance", "final"}:
        return BACKEND_V5
    if normalized in {BACKEND_ORIGINAL, "v2"}:
        return BACKEND_ORIGINAL
    return BACKEND_LITE


def _vendor_path_v5() -> Path:
    override = os.getenv("RB_TKYA_V5_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (Path(__file__).resolve().parent / "vendor" / _V5_FILENAME).resolve()


def _vendor_path_original() -> Path:
    override = os.getenv("RB_TKYA_ORIGINAL_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return (Path(__file__).resolve().parent / "vendor" / _ORIGINAL_FILENAME).resolve()


def _load_module_from_path(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("repobrain_tkya_vendor_topocore", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to build import spec for: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _warn_once(message: str) -> None:
    if message in _WARNED_MESSAGES:
        return
    _WARNED_MESSAGES.add(message)
    print(message)


def _stable_percent_bucket(value: str) -> int:
    digest = hashlib.blake2s(value.encode("utf-8"), digest_size=8).digest()
    number = int.from_bytes(digest, "little", signed=False)
    return number % 100


def _canary_allows_v5() -> bool:
    raw_percent = os.getenv("RB_TKYA_V5_CANARY_PERCENT", "").strip()
    if not raw_percent:
        return True
    try:
        percent = int(raw_percent)
    except ValueError:
        return True
    percent = max(0, min(100, percent))
    if percent >= 100:
        return True
    if percent <= 0:
        return False
    key = (
        os.getenv("RB_TKYA_CANARY_KEY", "").strip()
        or os.getenv("GITHUB_REPOSITORY", "").strip()
        or os.getenv("GITHUB_RUN_ID", "").strip()
        or "local"
    )
    return _stable_percent_bucket(key) < percent


class OriginalEngineAdapter(TKYEngine):
    """Adapter for original TopoCore module with a RepoBrain-compatible decide() API."""

    def __init__(self, core: Any, *, allow_remote: bool) -> None:
        self._core = core
        self._allow_remote = allow_remote
        self._lite = TopoCoreLite()
        if not allow_remote:
            install_remote_guards(self._core)

    @staticmethod
    def _blocked_remote_call(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError("Remote operations are disabled (RB_TKYA_ALLOW_REMOTE=0).")

    @staticmethod
    def _response_text(response: Any) -> str:
        parts = [
            str(getattr(response, "summary", "") or ""),
            str(getattr(response, "answer", "") or ""),
            str(getattr(response, "topo_rationale", "") or ""),
        ]
        return " ".join(part for part in parts if part).lower()

    def _is_blocked(self, response: Any) -> bool:
        text = self._response_text(response)
        blocked_markers = ("corelocked", "blocked", "инъек", "эксфил", "prompt")
        return any(marker in text for marker in blocked_markers)

    def _map_route(self, req: EngineRequest, lite_route: str, response: Any) -> str:
        if req.task_type == "review":
            return "REVIEW"
        text = self._response_text(response)
        if "expand" in text or "расшир" in text or "deep" in text:
            return "DEEP"
        if "narrow" in text or "суз" in text or "fast" in text:
            return "FAST"
        return lite_route

    def decide(self, req: EngineRequest) -> EngineDecision:
        lite_decision = self._lite.decide(req)
        handle_request = getattr(self._core, "handle_request", None)
        if not callable(handle_request):
            return lite_decision

        try:
            response = handle_request(req.query.text, data=None)
        except Exception:
            return lite_decision

        if self._is_blocked(response):
            return EngineDecision(
                route="REFUSE",
                selected_chunk_ids=[],
                compression_stats={
                    "retrieved": len(req.candidates),
                    "selected": 0,
                    "top_score": float(req.candidates[0].score_local) if req.candidates else 0.0,
                    "route": "REFUSE",
                },
                security=EngineSecurity(
                    blocked=True,
                    injection_risk="high",
                    exfiltration_risk="high",
                    signals=["corelocked_policy"],
                ),
                rationale="CoreLocked: blocked by original security policy.",
                stable_tokens=[],
            )

        compression_stats = dict(lite_decision.compression_stats)
        compression_stats["backend"] = "original"
        return EngineDecision(
            route=self._map_route(req, lite_decision.route, response),
            selected_chunk_ids=list(lite_decision.selected_chunk_ids),
            compression_stats=compression_stats,
            security=lite_decision.security,
            rationale="CoreLocked: original TKYA adapter active.",
            stable_tokens=list(lite_decision.stable_tokens),
        )


def install_remote_guards(core: Any) -> None:
    """Fail-closed remote hooks for vendor backends unless explicitly enabled."""
    for method_name in _REMOTE_METHOD_GUARDS:
        if not hasattr(core, method_name):
            continue
        try:
            setattr(core, method_name, OriginalEngineAdapter._blocked_remote_call)
        except Exception:
            continue


def describe_engine_instance(engine: Any) -> str:
    """Return stable local engine label for audit/formatting."""
    name = type(engine).__name__.lower()
    if "v5" in name or "advance" in name:
        return "topocore_v5"
    if "lite" in name:
        return "topocore_lite"
    if "originalengineadapter" in name or "v2" in name:
        return "topocore_original"
    return "topocore_local"


def _build_v5_engine(path: Path, *, allow_remote: bool) -> TKYEngine:
    module = _load_module_from_path(path)
    core_cls = (
        getattr(module, "TopoCoreTCXv5AdvanceCASGit", None)
        or getattr(module, "TopoCoreTCXv5AdvanceCAS", None)
        or getattr(module, "TopoCoreTCXv2CAS", None)
    )
    if core_cls is None:
        raise RuntimeError(
            "TopoCore v5 module is missing TopoCoreTCXv5AdvanceCASGit/TopoCoreTCXv5AdvanceCAS."
        )
    core = core_cls()
    if not callable(getattr(core, "decide", None)):
        raise RuntimeError("TopoCore v5 backend must expose decide(req).")
    if not allow_remote:
        install_remote_guards(core)
    return core


def _build_original_engine(path: Path, *, allow_remote: bool) -> TKYEngine:
    module = _load_module_from_path(path)
    core_cls = getattr(module, "TopoCoreTCXv2CAS", None)
    if core_cls is None:
        raise RuntimeError("Original TKYA module is missing TopoCoreTCXv2CAS.")
    core = core_cls()
    return OriginalEngineAdapter(core, allow_remote=allow_remote)


def get_engine() -> TKYEngine:
    """Return the selected TKYA engine with safe defaults."""
    backend = _get_backend(os.getenv("RB_TKYA_BACKEND", BACKEND_LITE))
    allow_remote = _to_bool(os.getenv("RB_TKYA_ALLOW_REMOTE", "0"))
    strict_original = _to_bool(os.getenv("RB_TKYA_STRICT_ORIGINAL", "0"))
    strict_v5 = _to_bool(os.getenv("RB_TKYA_STRICT_V5", "0"))

    if backend == BACKEND_LITE:
        return TopoCoreLite()

    if backend == BACKEND_V5:
        if not _canary_allows_v5():
            _warn_once("WARN: TopoCore v5 skipped by canary rollout policy, fallback to lite backend.")
            return TopoCoreLite()
        v5_path = _vendor_path_v5()
        if not v5_path.exists():
            message = (
                f"TopoCore v5 backend requested but vendor file is missing: {v5_path}. "
                "Place TopoCore_TCX_v5-Advance_CAS+Git.py under repobrain/tkya/vendor/."
            )
            if strict_v5:
                raise RuntimeError(message)
            _warn_once("WARN: TopoCore v5 file not found, fallback to lite backend.")
            return TopoCoreLite()

        try:
            return _build_v5_engine(v5_path, allow_remote=allow_remote)
        except Exception as exc:
            if strict_v5:
                raise RuntimeError("Failed to initialize TopoCore v5 backend.") from exc
            _warn_once("WARN: TopoCore v5 initialization failed, fallback to lite backend.")
            return TopoCoreLite()

    original_path = _vendor_path_original()
    if not original_path.exists():
        message = (
            f"Original TKYA backend requested but vendor file is missing: {original_path}. "
            "Place TopoCore_TCX_v2-CAS.py under repobrain/tkya/vendor/."
        )
        if strict_original:
            raise RuntimeError(message)
        _warn_once("WARN: Original TKYA file not found, fallback to lite backend.")
        return TopoCoreLite()

    try:
        return _build_original_engine(original_path, allow_remote=allow_remote)
    except Exception as exc:
        if strict_original:
            raise RuntimeError("Failed to initialize original TKYA backend.") from exc
        _warn_once("WARN: Original TKYA initialization failed, fallback to lite backend.")
        return TopoCoreLite()
