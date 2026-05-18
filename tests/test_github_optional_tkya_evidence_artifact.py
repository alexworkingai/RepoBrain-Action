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


def test_tkya_evidence_artifact_upload_is_nonfatal_when_files_are_absent() -> None:
    workflow = _load_workflow_yaml()
    steps = workflow["jobs"]["repobrain"]["steps"]
    tkya_upload = next(step for step in steps if step.get("name") == "Upload RepoBrain TKYA evidence pack artifact")

    assert tkya_upload["uses"] == "actions/upload-artifact@v4"
    assert tkya_upload["with"]["if-no-files-found"] == "warn"


def test_lab_backend_evidence_artifact_remains_visible() -> None:
    workflow = _load_workflow_yaml()
    steps = workflow["jobs"]["repobrain"]["steps"]
    lab_upload = next(step for step in steps if step.get("name") == "Upload RepoBrain lab backend evidence artifact")

    assert lab_upload["uses"] == "actions/upload-artifact@v4"
    assert lab_upload["with"]["name"] == "repobrain-lab-backend-evidence"
    assert "artifacts/lab_backend_evidence/repobrain_lab_backend_evidence.json" in lab_upload["with"]["path"]


def test_private_checkout_and_install_behavior_is_unchanged() -> None:
    workflow = _load_workflow_yaml()
    steps = workflow["jobs"]["repobrain"]["steps"]
    checkout_step = next(step for step in steps if step.get("name") == "Checkout private TopoCore v6 for manual lab run")
    install_step = next(step for step in steps if step.get("name") == "Install private TopoCore v6 for manual lab run")

    expected_condition = (
        "github.event_name == 'workflow_dispatch' && "
        "inputs.topocore_v6_dependency_mode == 'private_checkout' && "
        "(inputs.topocore_backend == 'v6' || inputs.topocore_backend == 'auto')"
    )
    assert checkout_step["if"] == expected_condition
    assert install_step["if"] == expected_condition


def test_runtime_import_diagnostic_behavior_is_unchanged() -> None:
    workflow = _load_workflow_yaml()
    steps = workflow["jobs"]["repobrain"]["steps"]
    diagnostic_step = next(step for step in steps if step.get("name") == "Check TopoCore v6 runtime import for manual lab run")

    assert diagnostic_step["if"] == (
        "github.event_name == 'workflow_dispatch' && "
        "inputs.topocore_v6_dependency_mode == 'private_checkout' && "
        "(inputs.topocore_backend == 'v6' || inputs.topocore_backend == 'auto')"
    )
    assert "check_topocore_v6_runtime_import.py" in diagnostic_step["run"]


def test_issue_comment_behavior_is_unchanged() -> None:
    workflow = _load_workflow_yaml()
    on_section = _workflow_on_section(workflow)
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "issue_comment" in on_section
    assert "github.event_name == 'issue_comment' && inputs.topocore_v6_dependency_mode == 'private_checkout'" not in workflow_text
    assert "github.event_name == 'workflow_dispatch'" in workflow_text
    assert "inputs.topocore_backend" in workflow_text


def test_workflow_dispatch_defaults_are_unchanged() -> None:
    workflow = _load_workflow_yaml()
    dispatch_inputs = _workflow_on_section(workflow)["workflow_dispatch"]["inputs"]

    assert dispatch_inputs["topocore_backend"]["default"] == "v5"
    assert dispatch_inputs["topocore_v6_dependency_mode"]["default"] == "none"
    assert dispatch_inputs["repobrain_lab_command"]["default"] == "help"


def test_no_patch_or_autofix_steps_are_introduced() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "git commit" not in workflow_text
    assert "git push" not in workflow_text
    assert "gh pr create" not in workflow_text
    assert "git apply" not in workflow_text
    assert "autofix publishing step" not in workflow_text.lower()


def test_fix_is_narrow_to_tkya_evidence_upload() -> None:
    workflow_text = (_ROOT / ".github" / "workflows" / "repobrain.yml").read_text(encoding="utf-8")

    assert "Upload RepoBrain TKYA evidence pack artifact" in workflow_text
    assert "if-no-files-found: warn" in workflow_text
    assert workflow_text.count("if-no-files-found: warn") == 1
