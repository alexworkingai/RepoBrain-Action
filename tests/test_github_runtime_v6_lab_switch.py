from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest
import yaml

import repobrain.tky_local as tky_local
from repobrain.topocore_backend import BACKEND_V5, resolve_backend
from repobrain.tky_engine import EngineDecision, EngineSecurity
from repobrain.tky_provider import CandidateChunk


_ROOT = Path(__file__).resolve().parents[1]


class _CaptureV5Engine:
    def __init__(self) -> None:
        self.calls = 0

    def decide(self, req):  # noqa: ANN001
        self.calls += 1
        return EngineDecision(
            route="FAST",
            selected_chunk_ids=[req.candidates[0].chunk_id] if req.candidates else [],
            compression_stats={"retrieved": len(req.candidates), "selected": 1},
            security=EngineSecurity(
                blocked=False,
                injection_risk="low",
                exfiltration_risk="low",
                signals=[],
            ),
            rationale="v5 ok",
            stable_tokens=["s1"],
        )


def _sample_candidates() -> list[CandidateChunk]:
    return [
        CandidateChunk(
            chunk_id="c1",
            file_path="repobrain/tky_provider.py",
            line_start=1,
            line_end=20,
            score=0.91,
            signature=[1, 2, 3],
        ),
        CandidateChunk(
            chunk_id="c2",
            file_path="repobrain/review.py",
            line_start=5,
            line_end=16,
            score=0.27,
            signature=[4, 5, 6],
        ),
    ]


def _build_fake_topocore_v6_module(*, decide_raw_raises: bool = False) -> types.ModuleType:
    class EngineQuery:
        def __init__(self, *, text: str, signature: list[int] | None = None) -> None:
            self.text = text
            self.signature = signature

    class EngineCandidate:
        def __init__(
            self,
            *,
            chunk_id: str,
            score_local: float,
            signature: list[int] | None = None,
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
        def __init__(
            self,
            *,
            task_type: str,
            query: EngineQuery,
            candidates: list[EngineCandidate],
            limits: dict[str, object],
            policy: dict[str, object],
        ) -> None:
            self.task_type = task_type
            self.query = query
            self.candidates = candidates
            self.limits = limits
            self.policy = policy

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
            assert request.task_type in {"ask", "review", "explain", "locate"}
            return ExternalDecisionView()

        if decide_raw_raises:

            @property
            def decide_raw(self) -> object:
                raise AssertionError("decide_raw should never be accessed")

    fake_module = types.ModuleType("topocore_v6")
    fake_module.create_topocore = lambda: FakeFacade()
    fake_module.EngineRequest = EngineRequest
    fake_module.EngineQuery = EngineQuery
    fake_module.EngineCandidate = EngineCandidate
    fake_module.ExternalDecisionView = ExternalDecisionView
    return fake_module


@pytest.fixture(autouse=True)
def _clear_env_and_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RB_TOPOCORE_BACKEND", raising=False)
    monkeypatch.delenv("RB_TKYA_BACKEND", raising=False)
    monkeypatch.delenv("RB_TOPOCORE_V6_REQUIRE_LOCAL", raising=False)
    monkeypatch.delenv("RB_TOPOCORE_V6_LOCAL_PATH", raising=False)
    sys.modules.pop("topocore_v6", None)
    yield
    sys.modules.pop("topocore_v6", None)


def _load_action_yaml() -> dict[str, object]:
    return yaml.safe_load((_ROOT / "action.yml").read_text(encoding="utf-8"))


def _load_workflow_yaml() -> dict[str, object]:
    return yaml.safe_load((_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8"))


def _workflow_on_section(workflow: dict[str, object]) -> dict[str, object]:
    on_section = workflow.get("on")
    if isinstance(on_section, dict):
        return on_section
    on_section = workflow.get(True)
    if isinstance(on_section, dict):
        return on_section
    raise AssertionError("Workflow is missing an `on` section.")


def test_action_yml_exposes_topocore_backend_input() -> None:
    action = _load_action_yaml()
    inputs = action["inputs"]
    assert "topocore_backend" in inputs
    assert inputs["topocore_backend"]["default"] == "v5"
    assert "v5" in inputs["topocore_backend"]["description"]


def test_action_yml_default_remains_v5() -> None:
    action = _load_action_yaml()

    assert action["inputs"]["topocore_backend"]["default"] == "v5"
    assert action["runs"]["steps"][-1]["env"]["RB_TKYA_BACKEND"] == "v5"
    assert action["inputs"]["topocore_backend"]["default"] != "auto"
    assert action["inputs"]["topocore_backend"]["default"] != "v6"


def test_action_yml_passes_rb_topocore_backend() -> None:
    action_text = (_ROOT / "action.yml").read_text(encoding="utf-8")

    assert "RB_TOPOCORE_BACKEND" in action_text
    assert "${{ env.RB_TOPOCORE_BACKEND || inputs.topocore_backend }}" in action_text
    assert 'RB_TOPOCORE_BACKEND: ${{ env.RB_TOPOCORE_BACKEND || inputs.topocore_backend }}' in action_text
    assert 'RB_TOPOCORE_BACKEND: "v6"' not in action_text


def test_workflow_dispatch_exposes_lab_backend_choice() -> None:
    workflow = _load_workflow_yaml()
    dispatch_inputs = _workflow_on_section(workflow)["workflow_dispatch"]["inputs"]
    backend = dispatch_inputs["topocore_backend"]

    assert backend["default"] == "v5"
    assert backend["type"] == "choice"
    assert backend["options"] == ["v5", "v6", "auto"]


def test_issue_comment_path_has_controlled_v6_lab_gate_with_safe_default() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "issue_comment:" in workflow_text
    assert "workflow_dispatch:" in workflow_text
    assert "topocore_backend:" in workflow_text
    assert "vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1'" in workflow_text
    assert "&& 'auto' || 'v5'" in workflow_text
    assert "startsWith(github.event.comment.body, '/repobrain')" in workflow_text


def test_workflow_default_path_does_not_install_private_topocore_v6() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8").lower()
    workflow = _load_workflow_yaml()
    dispatch_inputs = _workflow_on_section(workflow)["workflow_dispatch"]["inputs"]

    assert dispatch_inputs["topocore_backend"]["default"] == "v5"
    assert dispatch_inputs["topocore_v6_dependency_mode"]["default"] == "none"
    assert "workflow_dispatch" in workflow_text
    assert "issue_comment" in workflow_text
    assert "github packages" not in workflow_text
    assert "package registry" not in workflow_text


def test_action_workflow_do_not_enable_strict_v6_by_default() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")
    workflow = _load_workflow_yaml()
    dispatch_inputs = _workflow_on_section(workflow)["workflow_dispatch"]["inputs"]

    assert dispatch_inputs["topocore_v6_dependency_mode"]["default"] == "none"
    assert "RB_TOPOCORE_V6_REQUIRE_LOCAL" in workflow_text
    assert "topocore_v6_dependency_mode == 'private_checkout'" in workflow_text
    assert "|| '0'" in workflow_text


def test_no_decide_raw_exposure() -> None:
    action_text = (_ROOT / "action.yml").read_text(encoding="utf-8")
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "decide_raw" not in action_text
    assert "decide_raw" not in workflow_text


def test_default_github_pin_simulation_remains_v5() -> None:
    resolution = resolve_backend(env={"RB_TKYA_BACKEND": "v5"})
    assert resolution.requested_backend == BACKEND_V5
    assert resolution.selected_backend == BACKEND_V5


def test_workflow_dispatch_v6_lab_simulation_is_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(decide_raw_raises=True)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Review runtime lab path.",
        candidates=_sample_candidates(),
        limits={"task_type": "review"},
    )

    assert result.compression_stats["resolved_backend"] == "v6"
    assert result.compression_stats["topocore_backend"] == "v6"
    assert result.compression_stats["external_action"] == "proceed"


def test_workflow_dispatch_v6_without_dependency_falls_back_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    capture = _CaptureV5Engine()
    monkeypatch.setattr(tky_local, "get_engine", lambda: capture)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Ask on missing v6 dependency.",
        candidates=_sample_candidates(),
        limits={"task_type": "ask"},
    )

    assert capture.calls == 1
    assert result.compression_stats["resolved_backend"] == "v5"
    assert result.compression_stats["fallback_used"] is True
    assert result.compression_stats["fallback_reason"] == "v6_unavailable"
    assert "C:\\" not in json.dumps(result.compression_stats, sort_keys=True)


def test_manual_workflow_dispatch_auto_simulation_is_valid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "auto")
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(decide_raw_raises=True)

    result = tky_local.LocalTKYProvider().compress_context(
        question="Explain runtime lab path.",
        candidates=_sample_candidates(),
        limits={"task_type": "explain"},
    )

    assert result.compression_stats["requested_backend"] == "auto"
    assert result.compression_stats["resolved_backend"] == "v6"


def test_no_patch_or_autofix_behavior_from_lab_switch() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8").lower()
    action_text = (_ROOT / "action.yml").read_text(encoding="utf-8").lower()

    assert "git commit" not in workflow_text
    assert "git checkout -b" not in workflow_text
    assert "gh pr create" not in workflow_text
    assert "autofix" not in workflow_text
    assert "safe_to_merge" not in workflow_text
    assert "git commit" not in action_text
    assert "gh pr create" not in action_text
