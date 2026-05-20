from pathlib import Path
import sys
import types

from repobrain.external_flow import ExternalFlowInput, run_external_flow


def _build_fake_topocore_v6_module() -> types.ModuleType:
    class EngineQuery:
        def __init__(self, *, text: str, signature=None) -> None:  # noqa: ANN001
            self.text = text
            self.signature = signature

    class EngineCandidate:
        def __init__(
            self,
            *,
            chunk_id: str,
            score_local: float,
            signature=None,  # noqa: ANN001
            file_path: str | None = None,
            line_start: int | None = None,
            line_end: int | None = None,
        ) -> None:
            self.chunk_id = chunk_id
            self.score_local = score_local
            self.signature = signature
            self.file_path = file_path
            self.line_start = line_start
            self.line_end = line_end

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


def test_external_flow_ask_returns_answer(monkeypatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "auto")
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module()
    result = run_external_flow(
        ExternalFlowInput(
            repo_root=Path.cwd(),
            query="what does external_flow do?",
            command="ask",
        )
    )

    assert result.status == "success"
    assert result.decision == "ANSWER"
    assert "Question:" in result.content
    sys.modules.pop("topocore_v6", None)


def test_external_flow_rejects_unsupported_command() -> None:
    result = run_external_flow(
        ExternalFlowInput(
            repo_root=Path.cwd(),
            query="test",
            command="review",
        )
    )

    assert result.status == "blocked"
    assert result.decision == "UNSUPPORTED_COMMAND"
