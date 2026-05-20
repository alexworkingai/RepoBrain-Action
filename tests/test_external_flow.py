from pathlib import Path

from repobrain.external_flow import ExternalFlowInput, run_external_flow


def test_external_flow_ask_returns_answer(monkeypatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_ALLOW_DEPRECATED_V5", "1")
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
