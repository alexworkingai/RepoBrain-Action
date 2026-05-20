from __future__ import annotations

from pathlib import Path
import sys
import types

from repobrain.mcp_surface import (
    MCP_SUPPORTED_CAPABILITIES,
    MCPSurfaceRequest,
    handle_mcp_request,
    request_from_payload,
)


def _build_fake_topocore_v6_module() -> types.ModuleType:
    class EngineQuery:
        def __init__(self, *, text: str, signature=None) -> None:  # noqa: ANN001
            self.text = text
            self.signature = signature

    class EngineCandidate:
        def __init__(self, **kwargs) -> None:  # noqa: ANN003
            self.chunk_id = kwargs["chunk_id"]
            self.score_local = kwargs["score_local"]
            self.signature = kwargs.get("signature")
            self.file_path = kwargs.get("file_path")
            self.line_start = kwargs.get("line_start")
            self.line_end = kwargs.get("line_end")

    class EngineRequest:
        def __init__(self, **kwargs) -> None:  # noqa: ANN003
            self.task_type = kwargs["task_type"]
            self.query = kwargs["query"]
            self.candidates = kwargs["candidates"]
            self.limits = kwargs["limits"]
            self.policy = kwargs["policy"]

    class ExternalDecisionView:
        def __init__(self) -> None:
            self.status = "ready"
            self.action = "proceed"
            self.reference_hash = "safe-ref"
            self.selected_count = 1
            self.blocked = False
            self.confidence_band = "high"
            self.message_code = "DECISION_READY"

    class FakeFacade:
        def health(self) -> dict[str, object]:
            return {"status": "ok"}

        def decide_external(self, request: EngineRequest) -> ExternalDecisionView:
            assert request.task_type in {"ask", "locate", "explain", "review"}
            return ExternalDecisionView()

    fake_module = types.ModuleType("topocore_v6")
    fake_module.create_topocore = lambda: FakeFacade()
    fake_module.EngineRequest = EngineRequest
    fake_module.EngineQuery = EngineQuery
    fake_module.EngineCandidate = EngineCandidate
    fake_module.ExternalDecisionView = ExternalDecisionView
    return fake_module


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


def test_handle_mcp_request_executes_external_ask(monkeypatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "auto")
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module()
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
    sys.modules.pop("topocore_v6", None)
