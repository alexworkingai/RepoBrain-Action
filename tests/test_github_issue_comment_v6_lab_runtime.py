from __future__ import annotations

from pathlib import Path

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


def test_issue_comment_v6_lab_gate_exists() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "RB_ENABLE_ISSUE_COMMENT_V6_LAB" in workflow_text
    assert "vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1'" in workflow_text


def test_issue_comment_default_safe_behavior_is_defined() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1' && 'auto' || 'v5'" in workflow_text
    assert "topocore_backend: ${{ github.event_name == 'workflow_dispatch'" in workflow_text


def test_issue_comment_can_run_private_checkout_when_lab_gate_enabled() -> None:
    workflow = _load_workflow_yaml()
    steps = workflow["jobs"]["repobrain"]["steps"]
    checkout_step = next(step for step in steps if step.get("name") == "Checkout private TopoCore v6 for issue_comment lab run")

    assert "github.event_name == 'issue_comment'" in checkout_step["if"]
    assert "startsWith(github.event.comment.body, '/repobrain')" in checkout_step["if"]
    assert "vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1'" in checkout_step["if"]
    assert checkout_step["with"]["token"] == "${{ secrets.TOPOCORE_V6_REPO_TOKEN }}"


def test_issue_comment_can_install_private_topocore_v6_when_lab_gate_enabled() -> None:
    workflow = _load_workflow_yaml()
    steps = workflow["jobs"]["repobrain"]["steps"]
    install_step = next(step for step in steps if step.get("name") == "Install private TopoCore v6 for issue_comment lab run")

    assert "github.event_name == 'issue_comment'" in install_step["if"]
    assert "steps.issue_comment_topocore_checkout.outcome == 'success'" in install_step["if"]
    assert install_step["continue-on-error"] is True


def test_issue_comment_path_propagation_exists() -> None:
    workflow = _load_workflow_yaml()
    steps = workflow["jobs"]["repobrain"]["steps"]
    path_step = next(step for step in steps if step.get("name") == "Expose private TopoCore v6 path for issue_comment lab run")
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "github.event_name == 'issue_comment'" in path_step["if"]
    assert "steps.issue_comment_topocore_checkout.outcome == 'success'" in path_step["if"]
    assert "RB_TOPOCORE_V6_LOCAL_PATH" in workflow_text
    assert "PYTHONPATH=" in workflow_text


def test_issue_comment_diagnostic_behavior_is_safe() -> None:
    workflow = _load_workflow_yaml()
    steps = workflow["jobs"]["repobrain"]["steps"]
    strict_step = next(step for step in steps if step.get("name") == "Check TopoCore v6 runtime import for manual lab run")
    issue_step = next(step for step in steps if step.get("name") == "Check TopoCore v6 runtime import for issue_comment lab run")

    assert strict_step.get("continue-on-error") is None
    assert issue_step["continue-on-error"] is True
    assert "github.event_name == 'issue_comment'" in issue_step["if"]
    assert "vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1'" in issue_step["if"]


def test_issue_comment_backend_env_changes_correctly() -> None:
    workflow = _load_workflow_yaml()
    steps = workflow["jobs"]["repobrain"]["steps"]
    action_step = next(step for step in steps if step.get("uses") == "./.")
    topocore_backend_expr = action_step["with"]["topocore_backend"]

    assert "github.event_name == 'issue_comment'" in topocore_backend_expr
    assert "vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1'" in topocore_backend_expr
    assert "'auto'" in topocore_backend_expr
    assert "'v5'" in topocore_backend_expr


def test_workflow_dispatch_behavior_is_preserved() -> None:
    workflow = _load_workflow_yaml()
    dispatch_inputs = _workflow_on_section(workflow)["workflow_dispatch"]["inputs"]
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert dispatch_inputs["topocore_backend"]["default"] == "v5"
    assert dispatch_inputs["topocore_v6_dependency_mode"]["default"] == "none"
    assert dispatch_inputs["repobrain_lab_command"]["default"] == "help"
    assert "Checkout private TopoCore v6 for manual lab run" in workflow_text
    assert "Install private TopoCore v6 for manual lab run" in workflow_text


def test_no_strict_issue_comment_v6_by_default() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "RB_TOPOCORE_V6_REQUIRE_LOCAL" in workflow_text
    assert "topocore_v6_dependency_mode == 'private_checkout'" in workflow_text
    assert "github.event_name == 'issue_comment' && startsWith(github.event.comment.body, '/repobrain') && vars.RB_ENABLE_ISSUE_COMMENT_V6_LAB == '1' && '1'" not in workflow_text


def test_no_default_ci_private_dependency_drift() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "pip install topocore_v6" not in workflow_text
    assert "pip install git+" not in workflow_text
    assert "github.event_name == 'workflow_dispatch'" in workflow_text
    assert "github.event_name == 'issue_comment'" in workflow_text


def test_no_decide_raw_exposure() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")
    action_text = (_ROOT / "action.yml").read_text(encoding="utf-8")

    assert "decide_raw" not in workflow_text
    assert "decide_raw" not in action_text


def test_no_patch_or_autofix_workflow_steps_introduced() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8").lower()
    action_text = (_ROOT / "action.yml").read_text(encoding="utf-8").lower()

    assert "git commit" not in workflow_text
    assert "git push" not in workflow_text
    assert "gh pr create" not in workflow_text
    assert "git apply" not in workflow_text
    assert "autofix publishing step" not in workflow_text
    assert "git commit" not in action_text
    assert "gh pr create" not in action_text


def test_no_user_visible_unsafe_claims_are_added_by_default() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8").lower()
    action_text = (_ROOT / "action.yml").read_text(encoding="utf-8").lower()

    for forbidden in ("safe-to-merge", "security-approved", "patch applied", "branch created", "commit created", "pr created"):
        assert forbidden not in workflow_text
        assert forbidden not in action_text
