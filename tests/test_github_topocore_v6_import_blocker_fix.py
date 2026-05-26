from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


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


def _run_runtime_import_script(*, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    script_path = _ROOT / "scripts" / "check_topocore_v6_runtime_import.py"
    return subprocess.run(
        [sys.executable, str(script_path)],
        cwd=_ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def _write_fake_topocore_package(
    parent: Path,
    *,
    missing_engine_candidate: bool = False,
    missing_factory: bool = False,
) -> Path:
    package_dir = parent / "topocore_v6"
    package_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "__version__ = '0.0.test'",
        "",
        "class EngineQuery:",
        "    def __init__(self, *, text, signature=None):",
        "        self.text = text",
        "        self.signature = signature",
        "",
    ]
    if not missing_engine_candidate:
        lines.extend(
            [
                "class EngineCandidate:",
                "    def __init__(self, *, chunk_id, score_local, signature=None, file_path=None, line_start=None, line_end=None):",
                "        self.chunk_id = chunk_id",
                "        self.score_local = score_local",
                "        self.signature = signature",
                "        self.file_path = file_path",
                "        self.line_start = line_start",
                "        self.line_end = line_end",
                "",
            ]
        )
    lines.extend(
        [
            "class EngineRequest:",
            "    def __init__(self, *, task_type, query, candidates, limits, policy):",
            "        self.task_type = task_type",
            "        self.query = query",
            "        self.candidates = candidates",
            "        self.limits = limits",
            "        self.policy = policy",
            "",
            "class ExternalDecisionView:",
            "    pass",
            "",
            "class _Facade:",
            "    def health(self):",
            "        return {'release_stage': 'test', 'api_stability': 'foundation'}",
            "    @property",
            "    def decide_raw(self):",
            "        raise AssertionError('decide_raw should never be accessed')",
            "",
        ]
    )
    if not missing_factory:
        lines.extend(
            [
                "def create_topocore():",
                "    return _Facade()",
                "",
            ]
        )
    (package_dir / "__init__.py").write_text("\n".join(lines), encoding="utf-8")
    return parent


@pytest.fixture(autouse=True)
def _clean_lab_artifacts(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "RB_TOPOCORE_BACKEND",
        "RB_TKYA_BACKEND",
        "RB_TOPOCORE_V6_REQUIRE_LOCAL",
        "RB_TOPOCORE_V6_LOCAL_PATH",
        "RB_REPOBRAIN_LAB_COMMAND",
        "RB_REPOBRAIN_LAB_QUERY",
        "RB_REPOBRAIN_LAB_FIXTURE",
        "GITHUB_EVENT_NAME",
    ):
        monkeypatch.delenv(name, raising=False)
    evidence_dir = _ROOT / "artifacts" / "lab_backend_evidence"
    if evidence_dir.exists():
        for path in evidence_dir.glob("*"):
            path.unlink()
        evidence_dir.rmdir()
    yield
    if evidence_dir.exists():
        for path in evidence_dir.glob("*"):
            path.unlink()
        evidence_dir.rmdir()


def test_runtime_import_diagnostic_script_exists() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert (_ROOT / "scripts" / "check_topocore_v6_runtime_import.py").exists()
    assert "check_topocore_v6_runtime_import.py" in workflow_text


def test_manual_diagnostic_step_remains_strict_for_workflow_dispatch() -> None:
    workflow = _load_workflow_yaml()
    steps = workflow["jobs"]["repobrain"]["steps"]
    diagnostic_step = next(step for step in steps if step.get("name") == "Check TopoCore v6 runtime import for manual lab run")
    condition = diagnostic_step["if"]

    assert "github.event_name == 'workflow_dispatch'" in condition
    assert "inputs.topocore_v6_dependency_mode == 'private_checkout'" in condition
    assert "inputs.topocore_backend == 'v6' || inputs.topocore_backend == 'auto'" in condition


def test_workflow_sets_local_path_for_private_checkout() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "RB_TOPOCORE_V6_LOCAL_PATH" in workflow_text
    assert "$GITHUB_ENV" in workflow_text
    assert "TopoCore v6 runtime path prepared" in workflow_text


def test_workflow_sets_pythonpath_for_private_checkout() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "PYTHONPATH=" in workflow_text
    assert ".topocore-v6/src:${PYTHONPATH}" in workflow_text or ".topocore-v6:${PYTHONPATH}" in workflow_text


def test_diagnostic_script_passes_with_fake_module_via_local_path(tmp_path: Path) -> None:
    fake_parent = _write_fake_topocore_package(tmp_path)
    env = dict(os.environ)
    env["RB_TOPOCORE_V6_LOCAL_PATH"] = str(fake_parent)
    env["RB_TOPOCORE_V6_RUNTIME_MODE"] = "local_path"

    result = _run_runtime_import_script(env=env)

    assert result.returncode == 0
    assert "TOPOCORE_V6_RUNTIME_IMPORT=ok" in result.stdout
    assert "TOPOCORE_V6_PUBLIC_API=ok" in result.stdout
    assert "TOPOCORE_V6_HEALTH=ok" in result.stdout
    assert "sys.path" not in result.stdout


def test_diagnostic_script_fails_safely_when_module_missing(tmp_path: Path) -> None:
    isolated = tmp_path / "empty"
    isolated.mkdir()
    env = dict(os.environ)
    env["RB_TOPOCORE_V6_LOCAL_PATH"] = str(isolated)
    env["RB_TOPOCORE_V6_RUNTIME_MODE"] = "local_path"

    result = _run_runtime_import_script(env=env)

    assert result.returncode != 0
    assert "TOPOCORE_V6_RUNTIME_IMPORT=failed" in result.stdout
    assert "TOPOCORE_V6_FAILURE_CATEGORY=" in result.stdout
    assert "ghp_" not in result.stdout
    assert "github_pat_" not in result.stdout
    assert "Traceback" not in result.stdout


def test_diagnostic_script_reports_missing_symbols_safely(tmp_path: Path) -> None:
    fake_parent = _write_fake_topocore_package(tmp_path, missing_engine_candidate=True)
    env = dict(os.environ)
    env["RB_TOPOCORE_V6_LOCAL_PATH"] = str(fake_parent)
    env["RB_TOPOCORE_V6_RUNTIME_MODE"] = "local_path"

    result = _run_runtime_import_script(env=env)

    assert result.returncode != 0
    assert "TOPOCORE_V6_FAILURE_CATEGORY=topocore_v6_missing_symbol" in result.stdout
    assert "Traceback" not in result.stdout


def test_diagnostic_script_never_calls_decide_raw(tmp_path: Path) -> None:
    fake_parent = _write_fake_topocore_package(tmp_path)
    env = dict(os.environ)
    env["RB_TOPOCORE_V6_LOCAL_PATH"] = str(fake_parent)
    env["RB_TOPOCORE_V6_RUNTIME_MODE"] = "local_path"

    result = _run_runtime_import_script(env=env)

    assert result.returncode == 0
    assert "decide_raw" not in result.stdout.lower()


def test_evidence_failure_category_is_more_precise(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_run_github_module()
    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("RB_REPOBRAIN_LAB_COMMAND", "ask")
    monkeypatch.setenv("RB_REPOBRAIN_LAB_FIXTURE", "minimal")
    monkeypatch.setenv("RB_TOPOCORE_BACKEND", "v6")
    monkeypatch.setenv("RB_TOPOCORE_V6_REQUIRE_LOCAL", "1")

    with pytest.raises(ValueError):
        module.run_workflow_dispatch_lab_command(repo_root=_ROOT)

    evidence_path = _ROOT / "artifacts" / "lab_backend_evidence" / "repobrain_lab_backend_evidence.json"
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))

    assert payload["failure_category"] in {
        "topocore_v6_import_failed",
        "topocore_v6_missing_symbol",
        "topocore_v6_wrong_python_context",
        "topocore_v6_health_failed",
        "topocore_v6_adapter_contract_failed",
        "topocore_v6_runtime_unknown",
    }
    assert "ghp_" not in json.dumps(payload)
    assert ".topocore-v6" not in json.dumps(payload)


def test_issue_comment_behavior_is_controlled_by_lab_gate() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "issue_comment:" in workflow_text
    assert "Check TopoCore v6 runtime import for manual lab run" in workflow_text
    assert "Check TopoCore v6 runtime import for issue_comment lab run" in workflow_text
    assert "vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1'" in workflow_text


def test_no_patch_or_autofix_workflow_steps_introduced() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8").lower()
    action_text = (_ROOT / "action.yml").read_text(encoding="utf-8").lower()

    assert "git commit" not in workflow_text
    assert "git push" not in workflow_text
    assert "gh pr create" not in workflow_text
    assert "run: git commit" not in workflow_text
    assert "run: gh pr create" not in workflow_text
    assert "autofix" not in workflow_text
    assert "git commit" not in action_text
    assert "gh pr create" not in action_text
