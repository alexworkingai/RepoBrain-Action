from __future__ import annotations

from pathlib import Path

import yaml


_ROOT = Path(__file__).resolve().parents[1]


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


def test_workflow_dispatch_has_dependency_mode_input() -> None:
    workflow = _load_workflow_yaml()
    inputs = _workflow_on_section(workflow)["workflow_dispatch"]["inputs"]
    dependency_mode = inputs["topocore_v6_dependency_mode"]

    assert dependency_mode["default"] == "none"
    assert dependency_mode["type"] == "choice"
    assert dependency_mode["options"] == ["none", "private_checkout"]


def test_workflow_dispatch_has_v6_ref_input() -> None:
    workflow = _load_workflow_yaml()
    inputs = _workflow_on_section(workflow)["workflow_dispatch"]["inputs"]

    assert "topocore_v6_ref" in inputs
    assert inputs["topocore_v6_ref"]["default"] == "main"
    rendered = str(inputs["topocore_v6_ref"])
    assert "TOPOCORE_V6_REPO_TOKEN" not in rendered
    assert "ghp_" not in rendered


def test_private_checkout_is_manual_only() -> None:
    workflow = _load_workflow_yaml()
    steps = workflow["jobs"]["repobrain"]["steps"]
    checkout_step = next(step for step in steps if step.get("name") == "Checkout private TopoCore v6 for manual lab run")
    condition = checkout_step["if"]

    assert "github.event_name == 'workflow_dispatch'" in condition
    assert "inputs.topocore_v6_dependency_mode == 'private_checkout'" in condition
    assert "inputs.topocore_backend == 'v6' || inputs.topocore_backend == 'auto'" in condition


def test_issue_comment_private_checkout_is_gate_controlled() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "issue_comment:" in workflow_text
    assert "Checkout private TopoCore v6 for issue_comment lab run" in workflow_text
    assert "github.event_name == 'issue_comment'" in workflow_text
    assert "vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1'" in workflow_text
    assert "startsWith(github.event.comment.body, '/repobrain')" in workflow_text


def test_private_install_is_conditional() -> None:
    workflow = _load_workflow_yaml()
    steps = workflow["jobs"]["repobrain"]["steps"]
    checkout_step = next(step for step in steps if step.get("name") == "Checkout private TopoCore v6 for manual lab run")
    install_step = next(step for step in steps if step.get("name") == "Install private TopoCore v6 for manual lab run")
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert install_step["if"] == checkout_step["if"]
    assert "python -m pip install -e ./.topocore-v6" in workflow_text
    assert "RB_TOPOCORE_V6_RUNTIME_MODE=private_checkout" in workflow_text
    assert "pip install topocore_v6" not in workflow_text
    assert "pip install git+" not in workflow_text


def test_no_private_dependency_in_default_ci() -> None:
    workflow = _load_workflow_yaml()
    inputs = _workflow_on_section(workflow)["workflow_dispatch"]["inputs"]

    assert inputs["topocore_backend"]["default"] == "auto"
    assert inputs["topocore_v6_dependency_mode"]["default"] == "none"


def test_token_handling_is_secret_only() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "${{ secrets.TOPOCORE_V6_REPO_TOKEN }}" in workflow_text
    assert "ghp_" not in workflow_text
    assert "github_pat_" not in workflow_text
    assert "x-access-token:" not in workflow_text


def test_strict_local_mode_only_for_private_checkout_lab_run() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "RB_TOPOCORE_V6_REQUIRE_LOCAL" in workflow_text
    assert "topocore_v6_dependency_mode == 'private_checkout'" in workflow_text
    assert "inputs.topocore_backend == 'v6' || inputs.topocore_backend == 'auto'" in workflow_text
    assert "|| '0'" in workflow_text


def test_action_and_workflow_defaults_now_use_auto() -> None:
    action = _load_action_yaml()
    workflow = _load_workflow_yaml()
    inputs = _workflow_on_section(workflow)["workflow_dispatch"]["inputs"]

    assert action["inputs"]["topocore_backend"]["default"] == "auto"
    assert inputs["topocore_backend"]["default"] == "auto"


def test_no_patch_or_autofix_steps_introduced() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8").lower()
    action_text = (_ROOT / "action.yml").read_text(encoding="utf-8").lower()

    assert "git commit" not in workflow_text
    assert "git push" not in workflow_text
    assert "gh pr create" not in workflow_text
    assert "autofix" not in workflow_text
    assert "run: git commit" not in workflow_text
    assert "run: gh pr create" not in workflow_text
    assert "git commit" not in action_text
    assert "gh pr create" not in action_text
