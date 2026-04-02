from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from repobrain.external_flow import ExternalFlowInput, run_external_flow

MCP_SURFACE_VERSION = "repobrain_mcp_surface_v1"
MCP_SUPPORTED_CAPABILITIES = ("ask",)


@dataclass(frozen=True)
class MCPSurfaceRequest:
    capability: str
    repo_root: Path
    query: str
    dry_run: bool = True
    tky_mode: str = "auto"
    request_id: str = ""


def _as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _sanitize_answer_text(text: str) -> str:
    lines = []
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        # Keep bounded public-safe summary lines; drop deeper rationale internals.
        if line.lower().startswith("rationale:"):
            continue
        lines.append(raw)
    return "\n".join(lines).strip()


def _base_response(*, request: MCPSurfaceRequest) -> dict[str, Any]:
    return {
        "surface_version": MCP_SURFACE_VERSION,
        "public_safe": True,
        "kernel_disclosure": "protected_internal_kernel",
        "capability_requested": request.capability,
        "supported_capabilities": list(MCP_SUPPORTED_CAPABILITIES),
        "request_id": request.request_id or "n/a",
    }


def handle_mcp_request(request: MCPSurfaceRequest) -> dict[str, Any]:
    capability = _as_str(request.capability).lower()
    payload = _base_response(request=request)

    if capability not in MCP_SUPPORTED_CAPABILITIES:
        payload.update(
            {
                "status": "blocked",
                "decision": "UNSUPPORTED_CAPABILITY",
                "capability_used": "none",
                "reason_code": "unsupported_capability",
                "reason_short": (
                    f"Supported capabilities: {', '.join(MCP_SUPPORTED_CAPABILITIES)}; "
                    f"got: {request.capability or 'empty'}."
                ),
            }
        )
        return payload

    if not _as_str(request.query):
        payload.update(
            {
                "status": "blocked",
                "decision": "INVALID_REQUEST",
                "capability_used": "none",
                "reason_code": "query_missing",
                "reason_short": "`query` is required for ask capability.",
            }
        )
        return payload

    try:
        result = run_external_flow(
            ExternalFlowInput(
                repo_root=request.repo_root,
                query=request.query,
                command="ask",
                dry_run=bool(request.dry_run),
                tky_mode=request.tky_mode,
            )
        )
    except Exception:
        payload.update(
            {
                "status": "error",
                "decision": "EXECUTION_ERROR",
                "capability_used": "ask",
                "reason_code": "execution_error",
                "reason_short": "External ask execution failed.",
            }
        )
        return payload

    payload.update(
        {
            "status": result.status,
            "decision": result.decision,
            "capability_used": "ask",
            "reason_code": "ok" if result.status == "success" else "execution_blocked",
            "reason_short": "Capability executed." if result.status == "success" else "Capability blocked.",
            "output": {"answer_text": _sanitize_answer_text(result.content)},
        }
    )
    return payload


def request_from_payload(payload: dict[str, Any]) -> MCPSurfaceRequest:
    capability = _as_str(payload.get("capability", ""))
    repo_root = Path(_as_str(payload.get("repo_root", ".")) or ".").resolve()
    query = _as_str(payload.get("query", ""))
    dry_run = str(payload.get("dry_run", "true")).strip().lower() in {"1", "true", "yes", "y", "on"}
    tky_mode = _as_str(payload.get("tky_mode", "auto"), "auto")
    request_id = _as_str(payload.get("request_id", ""))
    return MCPSurfaceRequest(
        capability=capability,
        repo_root=repo_root,
        query=query,
        dry_run=dry_run,
        tky_mode=tky_mode,
        request_id=request_id,
    )
