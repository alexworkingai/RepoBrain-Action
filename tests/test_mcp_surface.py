from __future__ import annotations

from pathlib import Path

from repobrain.mcp_surface import (
    MCP_SUPPORTED_CAPABILITIES,
    MCPSurfaceRequest,
    handle_mcp_request,
    request_from_payload,
)


def test_request_from_payload_normalizes_fields() -> None:
    request = request_from_payload(
        {
            "capability": "ask",
            "repo_root": ".",
            "query": "What is this repo?",
            "dry_run": "yes",
            "tky_mode": "auto",
            "request_id": "req-1",
        }
    )

    assert request.capability == "ask"
    assert request.repo_root == Path(".").resolve()
    assert request.query == "What is this repo?"
    assert request.dry_run is True
    assert request.tky_mode == "auto"
    assert request.request_id == "req-1"


def test_handle_mcp_request_blocks_unsupported_capability() -> None:
    response = handle_mcp_request(
        MCPSurfaceRequest(
            capability="review",
            repo_root=Path(".").resolve(),
            query="test",
        )
    )

    assert response["status"] == "blocked"
    assert response["decision"] == "UNSUPPORTED_CAPABILITY"
    assert response["capability_used"] == "none"
    assert response["supported_capabilities"] == list(MCP_SUPPORTED_CAPABILITIES)
    assert response["kernel_disclosure"] == "protected_internal_kernel"


def test_handle_mcp_request_blocks_missing_query() -> None:
    response = handle_mcp_request(
        MCPSurfaceRequest(
            capability="ask",
            repo_root=Path(".").resolve(),
            query="",
        )
    )

    assert response["status"] == "blocked"
    assert response["decision"] == "INVALID_REQUEST"
    assert response["reason_code"] == "query_missing"


def test_handle_mcp_request_executes_external_ask() -> None:
    response = handle_mcp_request(
        MCPSurfaceRequest(
            capability="ask",
            repo_root=Path(".").resolve(),
            query="what does external flow do?",
        )
    )

    assert response["status"] == "success"
    assert response["decision"] == "ANSWER"
    assert response["capability_used"] == "ask"
    assert response["public_safe"] is True
    answer_text = response.get("output", {}).get("answer_text")
    assert isinstance(answer_text, str)
    assert "Rationale:" not in answer_text
