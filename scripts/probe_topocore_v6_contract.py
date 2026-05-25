from __future__ import annotations

import importlib
import os
import re
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, TextIO


_SKIP_MESSAGE = "TopoCore v6 contract probe skipped: set RB_TOPOCORE_V6_CONTRACT_PROBE=1 to run."
_MISSING_DEP_MESSAGE = (
    "TopoCore v6 contract probe skipped: local/private TopoCore v6 dependency is not available."
)
_STRICT_MISSING_DEP_MESSAGE = (
    "TopoCore v6 contract probe failed: private dependency import unavailable."
)
_MISSING_SYMBOLS_MESSAGE = "TopoCore v6 contract probe failed: required public symbols missing."
_CONFIG_ERROR_MESSAGE = "TopoCore v6 contract probe configuration error."

_REQUIRED_MODULE_SYMBOLS = (
    "create_topocore",
    "EngineRequest",
    "EngineQuery",
    "EngineCandidate",
)
_REQUIRED_FACADE_METHODS = (
    "decide",
    "decide_external",
    "health",
)

_PATH_TOKEN_RE = re.compile(
    r"([A-Za-z]:\\[^\\\s]+(?:\\[^\\\s]+)*)|(/[^/\s]+(?:/[^/\s]+)*)"
)


def _env_flag(name: str, default: str = "0", env: Mapping[str, str] | None = None) -> str:
    source = env if env is not None else os.environ
    return str(source.get(name, default) or default).strip()


def _probe_enabled(env: Mapping[str, str] | None = None) -> bool:
    return _env_flag("RB_TOPOCORE_V6_CONTRACT_PROBE", env=env) == "1"


def _require_local(env: Mapping[str, str] | None = None) -> bool:
    return _env_flag("RB_TOPOCORE_V6_REQUIRE_LOCAL", env=env) == "1"


def _local_path(env: Mapping[str, str] | None = None) -> str:
    return _env_flag("RB_TOPOCORE_V6_LOCAL_PATH", default="", env=env)


def _print_line(message: str, stdout: TextIO | None = None) -> None:
    stream = stdout if stdout is not None else sys.stdout
    stream.write(f"{message}\n")


def _sanitize_output(text: str) -> str:
    normalized = " ".join(str(text or "").split())
    normalized = _PATH_TOKEN_RE.sub("[redacted-path]", normalized)
    return normalized


def _classify_import_error(exc: Exception) -> str:
    name = exc.__class__.__name__.lower()
    message = str(exc).lower()
    if "module" in name or "import" in name or "module" in message or "import" in message:
        return "private_dependency_import_unavailable"
    return "private_dependency_import_failed"


@contextmanager
def _temporary_sys_path(local_path: str) -> Iterator[None]:
    inserted = False
    try:
        if local_path:
            path_obj = Path(local_path)
            candidate = str(path_obj)
            if candidate and candidate not in sys.path:
                sys.path.insert(0, candidate)
                inserted = True
        yield
    finally:
        if inserted:
            try:
                sys.path.remove(candidate)
            except ValueError:
                pass


def _load_topocore_v6(local_path: str) -> tuple[Any | None, Exception | None]:
    with _temporary_sys_path(local_path):
        try:
            return importlib.import_module("topocore_v6"), None
        except Exception as exc:  # pragma: no cover - exercised via tests
            return None, exc


def _module_symbol_status(module: Any) -> dict[str, bool]:
    return {name: hasattr(module, name) for name in _REQUIRED_MODULE_SYMBOLS + ("ExternalDecisionView", "__version__")}


def _build_minimal_request(module: Any) -> Any:
    query = module.EngineQuery(text="safe contract probe request")
    candidate = module.EngineCandidate(
        chunk_id="chunk-1",
        score_local=0.8,
        file_path="sanitized/path.py",
        line_start=1,
        line_end=2,
    )
    return module.EngineRequest(
        task_type="ask",
        query=query,
        candidates=[candidate],
        limits={},
        policy={},
    )


def _run_probe(module: Any) -> tuple[int, list[str], str]:
    symbol_status = _module_symbol_status(module)
    missing_symbols = [name for name, present in symbol_status.items() if name in _REQUIRED_MODULE_SYMBOLS and not present]
    if missing_symbols:
        summary = [
            _MISSING_SYMBOLS_MESSAGE,
            f"missing_symbols={','.join(sorted(missing_symbols))}",
            "error_category=public_api_symbol_missing",
        ]
        return 1, summary, "blocked_by_api_mismatch"

    factory = module.create_topocore
    facade = factory()
    method_status = {name: hasattr(facade, name) for name in _REQUIRED_FACADE_METHODS + ("decide_raw",)}
    missing_methods = [name for name, present in method_status.items() if name in _REQUIRED_FACADE_METHODS and not present]
    if missing_methods:
        summary = [
            _MISSING_SYMBOLS_MESSAGE,
            f"missing_methods={','.join(sorted(missing_methods))}",
            "error_category=public_api_method_missing",
        ]
        return 1, summary, "blocked_by_api_mismatch"

    request = _build_minimal_request(module)
    health = facade.health()
    external = facade.decide_external(request)
    audit_score_capability = hasattr(facade, "run_audit_score_v1")
    audit_score_contract_version = _sanitize_output(
        str(getattr(facade, "audit_score_contract_version", ""))
    )

    health_version = _sanitize_output(str(health.get("version", "")))
    release_stage = _sanitize_output(str(health.get("release_stage", "")))
    api_stability = _sanitize_output(str(health.get("api_stability", "")))
    ext_status = _sanitize_output(str(getattr(external, "status", "")))
    ext_action = _sanitize_output(str(getattr(external, "action", "")))
    ext_confidence = _sanitize_output(str(getattr(external, "confidence_band", "")))
    ext_message = _sanitize_output(str(getattr(external, "message_code", "")))

    summary = [
        "TopoCore v6 contract probe passed.",
        f"module_symbols={','.join(name for name, present in symbol_status.items() if present)}",
        f"facade_methods={','.join(name for name, present in method_status.items() if present and name != 'decide_raw')}",
        f"decide_raw_present={'yes' if method_status.get('decide_raw') else 'no'}",
        "decide_raw_used=no",
        f"health_version={health_version or 'unknown'}",
        f"health_release_stage={release_stage or 'unknown'}",
        f"health_api_stability={api_stability or 'unknown'}",
        f"external_status={ext_status or 'unknown'}",
        f"external_action={ext_action or 'unknown'}",
        f"external_confidence={ext_confidence or 'unknown'}",
        f"external_message_code={ext_message or 'unknown'}",
        f"audit_score_v1_present={'yes' if audit_score_capability else 'no'}",
        f"audit_score_contract_version={audit_score_contract_version or 'unknown'}",
        "compatibility_status=compatible_with_adapter_changes",
    ]
    return 0, summary, "compatible_with_adapter_changes"


def main(
    *,
    env: Mapping[str, str] | None = None,
    stdout: TextIO | None = None,
) -> int:
    if not _probe_enabled(env):
        _print_line(_SKIP_MESSAGE, stdout)
        return 0

    local_path = _local_path(env)
    if local_path and not Path(local_path).exists():
        _print_line(_CONFIG_ERROR_MESSAGE, stdout)
        _print_line("error_category=invalid_local_path", stdout)
        return 2

    module, load_error = _load_topocore_v6(local_path)
    if load_error is not None:
        category = _classify_import_error(load_error)
        if _require_local(env):
            _print_line(_STRICT_MISSING_DEP_MESSAGE, stdout)
            _print_line(f"error_category={category}", stdout)
            return 1
        _print_line(_MISSING_DEP_MESSAGE, stdout)
        _print_line(f"error_category={category}", stdout)
        return 0

    try:
        exit_code, summary_lines, _compatibility = _run_probe(module)
    except Exception as exc:  # pragma: no cover - exercised through tests
        category = _sanitize_output(exc.__class__.__name__.lower() or "contract_probe_failure")
        _print_line("TopoCore v6 contract probe failed.", stdout)
        _print_line(f"error_category={category}", stdout)
        return 1

    for line in summary_lines:
        _print_line(_sanitize_output(line), stdout)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
