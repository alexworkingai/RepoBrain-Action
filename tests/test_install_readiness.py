from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "check_install_readiness.py"
    spec = spec_from_file_location("repobrain_check_install_readiness", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_workflow(path: Path, *, checks_permission: str = "write", include_issue_comment: bool = True) -> None:
    issue_comment_block = "  issue_comment:\n    types: [created]\n" if include_issue_comment else ""
    path.write_text(
        "\n".join(
            [
                "name: RepoBrain",
                "on:",
                issue_comment_block.rstrip(),
                "  workflow_dispatch:",
                "permissions:",
                "  contents: read",
                "  issues: write",
                "  pull-requests: write",
                f"  checks: {checks_permission}",
                "  statuses: read",
                "  actions: read",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_install_readiness_reports_ready_for_app_first_selected_rollout(tmp_path: Path) -> None:
    module = _load_module()
    workflow = tmp_path / "repobrain.yml"
    _write_workflow(workflow)
    payload = module.evaluate_install_readiness(
        workflow_path=workflow,
        env={
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "RB_GH_APP_ID": "123456",
            "RB_GH_APP_INSTALLATION_ID": "99999",
            "RB_GH_APP_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----...",
            "RB_GH_APP_WEBHOOK_SECRET": "secret",
            "RB_GH_APP_REPOSITORY_SELECTION": "selected",
            "RB_GH_APP_SELECTED_REPOS": "owner/repo-a,owner/repo-b",
        },
    )

    assert payload["overall_status"] == "READY"
    assert payload["ready_for_ask_review_fix"] is True
    assert payload["repository_selection_mode"] == "selected"
    assert payload["inputs_seen"]["selected_repositories_count"] == 2


def test_install_readiness_reports_missing_config_when_app_inputs_absent(tmp_path: Path) -> None:
    module = _load_module()
    workflow = tmp_path / "repobrain.yml"
    _write_workflow(workflow)
    payload = module.evaluate_install_readiness(
        workflow_path=workflow,
        env={
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "RB_GH_APP_REPOSITORY_SELECTION": "selected",
            "RB_GH_APP_SELECTED_REPOS": "",
        },
    )

    assert payload["overall_status"] == "MISSING_CONFIG"
    check_codes = {item["code"] for item in payload["checks"]}
    assert "github_app_id_missing" in check_codes
    assert "github_app_installation_id_missing" in check_codes
    assert "github_app_private_key_missing" in check_codes
    assert "selected_repositories_missing" in check_codes


def test_install_readiness_reports_missing_permission_when_workflow_permissions_are_weak(
    tmp_path: Path,
) -> None:
    module = _load_module()
    workflow = tmp_path / "repobrain.yml"
    _write_workflow(workflow, checks_permission="read")
    payload = module.evaluate_install_readiness(
        workflow_path=workflow,
        env={
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "RB_GH_APP_ID": "123",
            "RB_GH_APP_INSTALLATION_ID": "456",
            "RB_GH_APP_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----...",
            "RB_GH_APP_REPOSITORY_SELECTION": "all",
        },
    )

    assert payload["overall_status"] == "MISSING_PERMISSION"
    assert "checks:write" in payload["workflow_probe"]["missing_permissions"]


def test_install_readiness_reports_unsupported_setup_for_invalid_selection_mode(tmp_path: Path) -> None:
    module = _load_module()
    workflow = tmp_path / "repobrain.yml"
    _write_workflow(workflow, include_issue_comment=False)
    payload = module.evaluate_install_readiness(
        workflow_path=workflow,
        env={
            "GITHUB_EVENT_NAME": "push",
            "RB_GH_APP_REPOSITORY_SELECTION": "subset",
        },
    )

    assert payload["overall_status"] == "UNSUPPORTED_SETUP"
    check_codes = {item["code"] for item in payload["checks"]}
    assert "runtime_event_unsupported" in check_codes
    assert "repository_selection_mode_invalid" in check_codes
    assert "workflow_issue_comment_missing" in check_codes


def test_install_readiness_markdown_includes_actionable_summary(tmp_path: Path) -> None:
    module = _load_module()
    workflow = tmp_path / "repobrain.yml"
    _write_workflow(workflow)
    payload = module.evaluate_install_readiness(
        workflow_path=workflow,
        env={
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "RB_GH_APP_REPOSITORY_SELECTION": "selected",
        },
    )
    markdown = module.render_install_readiness_markdown(payload)
    assert "RepoBrain GitHub App Install Readiness" in markdown
    assert "Overall status" in markdown
    assert "Next Safe Steps" in markdown
    assert "[FAIL]" in markdown


def test_install_readiness_main_writes_json_and_markdown(tmp_path: Path, monkeypatch) -> None:
    module = _load_module()
    workflow = tmp_path / "repobrain.yml"
    _write_workflow(workflow)
    output_json = tmp_path / "artifacts" / "onboarding" / "repobrain_install_readiness.json"
    output_md = tmp_path / "artifacts" / "onboarding" / "repobrain_install_readiness.md"

    monkeypatch.setenv("GITHUB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("RB_GH_APP_ID", "123")
    monkeypatch.setenv("RB_GH_APP_INSTALLATION_ID", "456")
    monkeypatch.setenv("RB_GH_APP_PRIVATE_KEY", "-----BEGIN PRIVATE KEY-----...")
    monkeypatch.setenv("RB_GH_APP_REPOSITORY_SELECTION", "all")

    exit_code = module.main(
        [
            "--workflow",
            str(workflow),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ]
    )
    assert exit_code == 0
    assert output_json.exists()
    assert output_md.exists()
