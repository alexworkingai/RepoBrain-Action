from __future__ import annotations

from dataclasses import dataclass
import importlib
import json
import os
import re
import shlex
import subprocess
from typing import Any, Callable, Mapping


TOPOCORE_ENTRYPOINT_ADAPTER_VERSION = "repobrain.topocore_entrypoint_adapter.v1"


class TopoCoreEntrypointError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


@dataclass(frozen=True)
class TopoCoreEntrypointConfig:
    mode: str = ""
    command: str = ""
    module: str = ""
    timeout_s: float = 20.0

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "TopoCoreEntrypointConfig":
        env = environ or os.environ
        return cls(
            mode=str(env.get("REPOBRAIN_TOPOCORE_ENTRYPOINT_MODE", "") or "").strip().lower(),
            command=str(env.get("REPOBRAIN_TOPOCORE_ENTRYPOINT_CMD", "") or "").strip(),
            module=str(env.get("REPOBRAIN_TOPOCORE_ENTRYPOINT_MODULE", "") or "").strip(),
            timeout_s=float(str(env.get("REPOBRAIN_TOPOCORE_ENTRYPOINT_TIMEOUT_S", "20") or "20").strip() or "20"),
        )


_UNSAFE_SUBSTRINGS = (
    "authorization",
    "bearer ",
    "ghp_",
    "github_pat_",
    "-----begin private key-----",
    ".topocore-v6",
    "private_checkout",
    "topocore token",
    "repobrain_github_installation_token",
)
_UNSAFE_PATTERNS = (
    re.compile(r"\b[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"(?i)(?:[a-z]:\\|/)[^\n\"]*topocore"),
)


@dataclass(frozen=True)
class TopoCoreEntrypointResponse:
    backend: str
    fallback: str
    score: int | None
    verdict: str | None
    blockers_summary: list[str]
    warnings_summary: list[str]
    evidence_summary: list[str]
    public_notes: list[str]
    capability_markers: list[str]


class TopoCoreEntrypointAdapter:
    def __init__(
        self,
        config: TopoCoreEntrypointConfig,
        *,
        subprocess_run: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    ) -> None:
        self._config = config
        self._subprocess_run = subprocess_run or subprocess.run

    @classmethod
    def from_env(
        cls,
        *,
        environ: Mapping[str, str] | None = None,
        subprocess_run: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    ) -> "TopoCoreEntrypointAdapter":
        return cls(TopoCoreEntrypointConfig.from_env(environ), subprocess_run=subprocess_run)

    def invoke(self, request_payload: Mapping[str, Any]) -> TopoCoreEntrypointResponse:
        mode = self._resolve_mode()
        if mode == "stub":
            return self._invoke_stub(request_payload)
        if mode == "command":
            return self._invoke_command(request_payload)
        if mode == "module":
            return self._invoke_module(request_payload)
        raise TopoCoreEntrypointError(
            "TOPOCORE_ENTRYPOINT_NOT_CONFIGURED",
            "RepoBrain private control worker TopoCore entrypoint is not configured.",
            retryable=False,
        )

    def _resolve_mode(self) -> str:
        if self._config.mode:
            return self._config.mode
        if self._config.command:
            return "command"
        if self._config.module:
            return "module"
        return ""

    def _invoke_stub(self, request_payload: Mapping[str, Any]) -> TopoCoreEntrypointResponse:
        command = str(request_payload.get("command", "audit") or "audit").strip().lower()
        profile = str(request_payload.get("profile", "standard") or "standard").strip().lower()
        score = 84 if command == "audit" else 82
        if profile == "premium":
            score += 2
        return self._normalize_response(
            {
                "backend": "private_topocore_stub",
                "fallback": "not_applicable",
                "score": score,
                "verdict": "GOOD",
                "blockers_summary": ["No blocking issues were reported by the stub entrypoint."],
                "warnings_summary": ["Stub mode is for control-plane validation only."],
                "evidence_summary": ["Bounded GitHub queue context was passed to the stub entrypoint."],
                "public_notes": ["Stub TopoCore mode completed safely for private control worker testing."],
                "capability_markers": ["topocore.stub.v1"],
            }
        )

    def _invoke_command(self, request_payload: Mapping[str, Any]) -> TopoCoreEntrypointResponse:
        if not self._config.command:
            raise TopoCoreEntrypointError(
                "TOPOCORE_ENTRYPOINT_NOT_CONFIGURED",
                "RepoBrain private control worker command entrypoint is not configured.",
                retryable=False,
            )
        args = shlex.split(self._config.command, posix=os.name != "nt")
        try:
            completed = self._subprocess_run(
                args,
                input=json.dumps(dict(request_payload), ensure_ascii=False),
                text=True,
                capture_output=True,
                timeout=float(self._config.timeout_s),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TopoCoreEntrypointError(
                "TOPOCORE_ENTRYPOINT_TIMEOUT",
                "RepoBrain private control worker TopoCore entrypoint timed out.",
                retryable=True,
            ) from exc
        except OSError as exc:
            raise TopoCoreEntrypointError(
                "TOPOCORE_ENTRYPOINT_FAILED",
                "RepoBrain private control worker could not start the configured TopoCore entrypoint command.",
                retryable=False,
            ) from exc

        stdout = str(completed.stdout or "")
        stderr = str(completed.stderr or "")
        if completed.returncode != 0:
            if self._contains_unsafe_text(stderr) or self._contains_unsafe_text(stdout):
                raise TopoCoreEntrypointError(
                    "TOPOCORE_ENTRYPOINT_FAILED",
                    "RepoBrain private control worker TopoCore entrypoint failed safely without exposing private output.",
                    retryable=False,
                )
            raise TopoCoreEntrypointError(
                "TOPOCORE_ENTRYPOINT_FAILED",
                "RepoBrain private control worker TopoCore entrypoint returned a non-zero status.",
                retryable=False,
            )
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise TopoCoreEntrypointError(
                "TOPOCORE_RESPONSE_INVALID",
                "RepoBrain private control worker TopoCore entrypoint returned invalid JSON.",
                retryable=False,
            ) from exc
        return self._normalize_response(payload)

    def _invoke_module(self, request_payload: Mapping[str, Any]) -> TopoCoreEntrypointResponse:
        if not self._config.module:
            raise TopoCoreEntrypointError(
                "TOPOCORE_ENTRYPOINT_NOT_CONFIGURED",
                "RepoBrain private control worker module entrypoint is not configured.",
                retryable=False,
            )
        try:
            module = importlib.import_module(self._config.module)
        except Exception as exc:
            raise TopoCoreEntrypointError(
                "TOPOCORE_ENTRYPOINT_FAILED",
                "RepoBrain private control worker could not import the configured TopoCore module entrypoint.",
                retryable=False,
            ) from exc
        handler = getattr(module, "run", None)
        if not callable(handler):
            raise TopoCoreEntrypointError(
                "TOPOCORE_ENTRYPOINT_FAILED",
                "Configured TopoCore module entrypoint does not expose a callable `run` handler.",
                retryable=False,
            )
        try:
            payload = handler(dict(request_payload))
        except Exception as exc:
            raise TopoCoreEntrypointError(
                "TOPOCORE_ENTRYPOINT_FAILED",
                "RepoBrain private control worker module entrypoint failed safely.",
                retryable=False,
            ) from exc
        return self._normalize_response(payload)

    def _normalize_response(self, payload: Any) -> TopoCoreEntrypointResponse:
        if not isinstance(payload, Mapping):
            raise TopoCoreEntrypointError(
                "TOPOCORE_RESPONSE_INVALID",
                "RepoBrain private control worker TopoCore response must be a JSON object.",
                retryable=False,
            )
        if self._payload_contains_unsafe(payload):
            raise TopoCoreEntrypointError(
                "TOPOCORE_RESPONSE_UNSAFE",
                "RepoBrain private control worker TopoCore response contained unsafe private data.",
                retryable=False,
            )
        return TopoCoreEntrypointResponse(
            backend=str(payload.get("backend", "private_topocore_entrypoint") or "private_topocore_entrypoint").strip(),
            fallback=str(payload.get("fallback", "not_applicable") or "not_applicable").strip(),
            score=payload.get("score") if isinstance(payload.get("score"), int) else None,
            verdict=str(payload.get("verdict", "") or "").strip() or None,
            blockers_summary=self._string_list(payload.get("blockers_summary"), fallback="No blocking issues were reported."),
            warnings_summary=self._string_list(payload.get("warnings_summary"), fallback="No warning conditions were reported."),
            evidence_summary=self._string_list(payload.get("evidence_summary"), fallback="Bounded GitHub control-plane context was processed."),
            public_notes=self._string_list(payload.get("public_notes"), fallback="Private control worker processing completed safely."),
            capability_markers=self._string_list(payload.get("capability_markers"), fallback="topocore.entrypoint.adapter.v1"),
        )

    def _contains_unsafe_text(self, text: str) -> bool:
        lowered = str(text or "").lower()
        if any(snippet in lowered for snippet in _UNSAFE_SUBSTRINGS):
            return True
        if any(pattern.search(str(text or "")) for pattern in _UNSAFE_PATTERNS):
            return True
        return False

    def _payload_contains_unsafe(self, value: Any) -> bool:
        if isinstance(value, Mapping):
            return any(self._payload_contains_unsafe(item) for item in value.values())
        if isinstance(value, list):
            return any(self._payload_contains_unsafe(item) for item in value)
        if isinstance(value, str):
            return self._contains_unsafe_text(value)
        return False

    def _string_list(self, value: Any, *, fallback: str) -> list[str]:
        if isinstance(value, list):
            items = [str(item or "").strip() for item in value if str(item or "").strip()]
            if items and not any(self._contains_unsafe_text(item) for item in items):
                return items
        return [fallback]
