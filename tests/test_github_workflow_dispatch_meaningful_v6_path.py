from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest
import yaml

from repobrain.topocore_deprecation import (
    TOPOCORE_V5_ALLOW_DEPRECATED_ENV,
    TOPOCORE_V5_DEPRECATED_ALLOWED_REASON,
)


_ROOT = Path(__file__).resolve().parents[1]


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


def _load_run_github_module():
    path = _ROOT / "scripts" / "run_github.py"
    spec = importlib.util.spec_from_file_location("run_github_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_fake_topocore_v6_module(*, decide_raw_raises: bool = False) -> types.ModuleType:
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
            assert request.task_type in {"ask", "review"}
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
def _clear_env_and_artifacts(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "RB_TOPOCORE_BACKEND",
        "RB_TKYA_BACKEND",
        "RB_TOPOCORE_V6_REQUIRE_LOCAL",
        "RB_TOPOCORE_V6_LOCAL_PATH",
        "RB_REPOBRAIN_LAB_COMMAND",
        "RB_REPOBRAIN_LAB_QUERY",
        "RB_REPOBRAIN_LAB_FIXTURE",
        "RB_REPOBRAIN_LAB_EVIDENCE",
        "GITHUB_EVENT_NAME",
        TOPOCORE_V5_ALLOW_DEPRECATED_ENV,
    ):
        monkeypatch.delenv(name, raising=False)
    sys.modules.pop("topocore_v6", None)
    evidence_dir = _ROOT / "artifacts" / "lab_backend_evidence"
    if evidence_dir.exists():
        for path in evidence_dir.glob("*"):
            path.unlink()
        evidence_dir.rmdir()
    yield
    sys.modules.pop("topocore_v6", None)
    if evidence_dir.exists():
        for path in evidence_dir.glob("*"):
            path.unlink()
        evidence_dir.rmdir()


def test_workflow_dispatch_has_lab_command_input() -> None:
    workflow = _load_workflow_yaml()
    inputs = _workflow_on_section(workflow)["workflow_dispatch"]["inputs"]
    lab_command = inputs["repobrain_lab_command"]

    assert lab_command["default"] == "help"
    assert lab_command["type"] == "choice"
    assert lab_command["options"] == ["help", "ask", "review", "verify", "fix-lite"]


def test_workflow_dispatch_has_lab_query_input() -> None:
    workflow = _load_workflow_yaml()
    inputs = _workflow_on_section(workflow)["workflow_dispatch"]["inputs"]

    assert inputs["repobrain_lab_query"]["default"] == "Summarize current RepoBrain TopoCore backend status."
    assert "token" not in str(inputs["repobrain_lab_query"]).lower()


def test_workflow_dispatch_has_lab_fixture_input() -> None:
    workflow = _load_workflow_yaml()
    inputs = _workflow_on_section(workflow)["workflow_dispatch"]["inputs"]
    lab_fixture = inputs["repobrain_lab_fixture"]

    assert lab_fixture["default"] == "minimal"
    assert lab_fixture["type"] == "choice"
    assert lab_fixture["options"] == ["minimal", "review", "verify", "fix_lite"]


def test_issue_comment_is_not_affected() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "issue_comment:" in workflow_text
    assert "startsWith(github.event.comment.body, '/repobrain')" in workflow_text
    assert "github.event_name == 'issue_comment' && github.event.inputs.repobrain_lab_command" not in workflow_text
    assert "Checkout private TopoCore v6 for issue_comment lab run" in workflow_text
    assert "vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1'" in workflow_text


def test_workflow_dispatch_default_remains_safe() -> None:
    workflow = _load_workflow_yaml()
    inputs = _workflow_on_section(workflow)["workflow_dispatch"]["inputs"]

    assert inputs["topocore_backend"]["default"] == "auto"
    assert inputs["topocore_v6_dependency_mode"]["default"] == "none"
    assert inputs["repobrain_lab_command"]["default"] == "help"


def test_private_checkout_still_only_runs_for_v6_or_auto_private_checkout() -> None:
    workflow = _load_workflow_yaml()
    steps = workflow["jobs"]["repobrain"]["steps"]
    checkout_step = next(step for step in steps if step.get("name") == "Checkout private TopoCore v6 for manual lab run")
    condition = checkout_step["if"]

    assert "github.event_name == 'workflow_dispatch'" in condition
    assert "inputs.topocore_v6_dependency_mode == 'private_checkout'" in condition
    assert "inputs.topocore_backend == 'v6' || inputs.topocore_backend == 'auto'" in condition


def test_lab_command_env_is_passed_to_action_runtime() -> None:
    workflow = _load_workflow_yaml()
    steps = workflow["jobs"]["repobrain"]["steps"]
    action_step = next(step for step in steps if step.get("uses") == "./.")
    env = action_step["env"]

    assert "RB_REPOBRAIN_LAB_COMMAND" in env
    assert "RB_REPOBRAIN_LAB_QUERY" in env
    assert "RB_REPOBRAIN_LAB_FIXTURE" in env


def test_meaningful_ask_lab_path_produces_backend_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_run_github_module()
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("RB_REPOBRAIN_LAB_COMMAND", "ask")
    monkeypatch.setenv("RB_REPOBRAIN_LAB_QUERY", "Summarize current RepoBrain TopoCore backend status.")
    monkeypatch.setenv("RB_REPOBRAIN_LAB_FIXTURE", "minimal")
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(decide_raw_raises=True)

    evidence = module.run_workflow_dispatch_lab_command(repo_root=_ROOT)

    assert evidence["lab_command"] == "ask"
    assert evidence["requested_backend"] == "v6"
    assert evidence["resolved_backend"] == "v6"
    assert evidence["fallback_used"] is False
    assert evidence["status"] == "ready"
    assert evidence["action"] == "proceed"
    assert evidence["message_code"] == "DECISION_READY"
    assert evidence["confidence_band"] == "high"


def test_default_workflow_dispatch_v6_failure_is_safely_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_run_github_module()
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("RB_REPOBRAIN_LAB_COMMAND", "ask")
    monkeypatch.setenv("RB_REPOBRAIN_LAB_FIXTURE", "minimal")
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")

    with pytest.raises(ValueError) as exc_info:
        module.run_workflow_dispatch_lab_command(repo_root=_ROOT)

    assert "v6_unavailable_v5_disabled" in str(exc_info.value)


def test_emergency_allow_restores_deprecated_fallback_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_run_github_module()
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("RB_REPOBRAIN_LAB_COMMAND", "ask")
    monkeypatch.setenv("RB_REPOBRAIN_LAB_FIXTURE", "minimal")
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    monkeypatch.setenv(TOPOCORE_V5_ALLOW_DEPRECATED_ENV, "1")

    evidence = module.run_workflow_dispatch_lab_command(repo_root=_ROOT)

    assert evidence["requested_backend"] == "v6"
    assert evidence["resolved_backend"] == "v5"
    assert evidence["fallback_used"] is True
    assert evidence["fallback_reason"] == TOPOCORE_V5_DEPRECATED_ALLOWED_REASON


def test_strict_v6_failure_is_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_run_github_module()
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("RB_REPOBRAIN_LAB_COMMAND", "ask")
    monkeypatch.setenv("RB_REPOBRAIN_LAB_FIXTURE", "minimal")
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    monkeypatch.setenv("RB_TOPOCORE_V6_REQUIRE_LOCAL", "1")

    with pytest.raises(ValueError) as exc_info:
        module.run_workflow_dispatch_lab_command(repo_root=_ROOT)

    message = str(exc_info.value)
    assert "topocore v6" in message.lower()
    assert ".topocore-v6" not in message
    assert "ghp_" not in message


def test_decide_raw_is_never_called(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_run_github_module()
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("RB_REPOBRAIN_LAB_COMMAND", "ask")
    monkeypatch.setenv("RB_REPOBRAIN_LAB_FIXTURE", "minimal")
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(decide_raw_raises=True)

    evidence = module.run_workflow_dispatch_lab_command(repo_root=_ROOT)

    assert evidence["decide_raw_used"] is False


def test_fix_lite_evidence_remains_conservative(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_run_github_module()
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("RB_REPOBRAIN_LAB_COMMAND", "fix-lite")
    monkeypatch.setenv("RB_REPOBRAIN_LAB_FIXTURE", "fix_lite")
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    sys.modules["topocore_v6"] = _build_fake_topocore_v6_module(decide_raw_raises=True)

    evidence = module.run_workflow_dispatch_lab_command(repo_root=_ROOT)

    assert evidence["lab_command"] == "fix-lite"
    assert evidence["resolved_backend"] == "v6"
    assert evidence["patch_authorized"] is False
    assert evidence["patch_applied"] is False
    assert evidence["files_modified"] is False
    assert evidence["branch_created"] is False
    assert evidence["commit_created"] is False
    assert evidence["pr_created"] is False


def test_no_patch_or_autofix_workflow_steps_introduced() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8").lower()
    action_text = (_ROOT / "action.yml").read_text(encoding="utf-8").lower()

    assert "git commit" not in workflow_text
    assert "git push" not in workflow_text
    assert "gh pr create" not in workflow_text
    assert "autofix" not in workflow_text
    assert "git commit" not in action_text
    assert "gh pr create" not in action_text
