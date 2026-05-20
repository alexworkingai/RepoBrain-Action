import sys
import types

from repobrain.tky_stub_server import build_response_from_payload


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


def test_stub_server_builds_engine_based_response_shape() -> None:
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module()
    payload = {
        "task_type": "ask",
        "query": {"text": "Where is TKYProvider?", "signature": [1, 2, 3]},
        "candidates": [
            {
                "chunk_id": "c1",
                "file_path": "repobrain/tky_provider.py",
                "line_start": 1,
                "line_end": 20,
                "score_local": 0.12,
                "signature": [10, 20],
            },
            {
                "chunk_id": "c2",
                "file_path": "README.md",
                "line_start": 1,
                "line_end": 20,
                "score_local": 0.01,
                "signature": [30],
            },
        ],
        "limits": {"max_sources": 4, "min_score_keep": 0.02},
        "privacy": {"mode": "signatures_only"},
    }

    response = build_response_from_payload(payload)

    assert "decision" in response
    assert "selection" in response
    assert "security" in response
    assert isinstance(response["selection"]["selected_chunk_ids"], list)
    assert response["decision"]["route"] in {"FAST", "DEEP", "REFUSE", "REVIEW"}
    sys.modules.pop("topocore_v6", None)
