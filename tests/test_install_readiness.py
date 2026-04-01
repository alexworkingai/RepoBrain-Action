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
    assert payload["readiness_contract_version"] == "install_readiness_v2"
    assert payload["status_reason_code"] == "ready_all_prereqs_satisfied"
    assert payload["ready_for_ask_review_fix"] is True
    assert payload["repository_selection_mode"] == "selected"
    assert payload["inputs_seen"]["selected_repositories_count"] == 2
    assert payload["inputs_seen"]["app_id_source"] == "env"
    assert payload["inputs_seen"]["installation_id_source"] == "env"
    assert payload["readiness_provenance"]["generation_ref_kind"] in {
        "unknown",
        "branch_ref",
        "pull_ref",
        "workflow_branch_ref",
        "workflow_other_ref",
    }


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
    assert payload["status_reason_code"] in {
        "github_app_id_missing",
        "github_app_installation_id_missing",
        "github_app_private_key_missing",
        "selected_repositories_missing",
    }
    check_codes = {item["code"] for item in payload["checks"]}
    assert "github_app_id_missing" in check_codes
    assert "github_app_installation_id_missing" in check_codes
    assert "github_app_private_key_missing" in check_codes
    assert "selected_repositories_missing" in check_codes
    assert payload["inputs_seen"]["app_id_present"] is False
    assert payload["inputs_seen"]["installation_id_present"] is False
    assert payload["inputs_seen"]["app_id_source"] == "missing"
    assert payload["inputs_seen"]["installation_id_source"] == "missing"


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
    assert payload["status_reason_code"] == "workflow_permissions_missing"
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
    assert payload["status_reason_code"] in {
        "unsupported_runtime_event",
        "unsupported_repository_selection_mode",
        "issue_comment_trigger_missing",
    }
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
    assert "Contract version" in markdown
    assert "Status reason" in markdown
    assert "Overall status" in markdown
    assert "Next Safe Steps" in markdown
    assert "[FAIL]" in markdown


def test_install_readiness_reports_selected_repo_binding_mismatch(tmp_path: Path) -> None:
    module = _load_module()
    workflow = tmp_path / "repobrain.yml"
    _write_workflow(workflow)
    payload = module.evaluate_install_readiness(
        workflow_path=workflow,
        env={
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "GITHUB_REPOSITORY": "owner/repo-c",
            "RB_GH_APP_ID": "123456",
            "RB_GH_APP_INSTALLATION_ID": "99999",
            "RB_GH_APP_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----...",
            "RB_GH_APP_REPOSITORY_SELECTION": "selected",
            "RB_GH_APP_SELECTED_REPOS": "owner/repo-a,owner/repo-b",
        },
    )

    assert payload["overall_status"] == "UNSUPPORTED_SETUP"
    assert payload["status_reason_code"] == "selected_repo_binding_mismatch"
    check_codes = {item["code"] for item in payload["checks"]}
    assert "selected_repositories_repo_not_allowed" in check_codes


def test_install_readiness_reports_invalid_app_and_installation_ids(tmp_path: Path) -> None:
    module = _load_module()
    workflow = tmp_path / "repobrain.yml"
    _write_workflow(workflow)
    payload = module.evaluate_install_readiness(
        workflow_path=workflow,
        env={
            "GITHUB_EVENT_NAME": "workflow_dispatch",
            "RB_GH_APP_ID": "abc",
            "RB_GH_APP_INSTALLATION_ID": "xyz",
            "RB_GH_APP_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----...",
            "RB_GH_APP_REPOSITORY_SELECTION": "all",
        },
    )
    check_codes = {item["code"] for item in payload["checks"]}
    assert "github_app_id_invalid" in check_codes
    assert "github_app_installation_id_invalid" in check_codes
    assert payload["overall_status"] == "MISSING_CONFIG"
    assert payload["inputs_seen"]["app_id_present"] is True
    assert payload["inputs_seen"]["installation_id_present"] is True
    assert payload["inputs_seen"]["app_id_source"] == "env"
    assert payload["inputs_seen"]["installation_id_source"] == "env"


def test_install_readiness_tracks_source_hints_and_generation_provenance(tmp_path: Path) -> None:
    module = _load_module()
    workflow = tmp_path / "repobrain.yml"
    _write_workflow(workflow)
    payload = module.evaluate_install_readiness(
        workflow_path=workflow,
        env={
            "GITHUB_EVENT_NAME": "issue_comment",
            "GITHUB_REF": "refs/heads/main",
            "GITHUB_SHA": "abc123",
            "RB_GH_APP_ID": "abc",
            "RB_GH_APP_ID_SOURCE": "vars",
            "RB_GH_APP_INSTALLATION_ID": "789",
            "RB_GH_APP_INSTALLATION_ID_SOURCE": "secret",
            "RB_GH_APP_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----...",
            "RB_GH_APP_REPOSITORY_SELECTION": "all",
            "RB_READINESS_GENERATION_WORKFLOW_REF": "owner/repo/.github/workflows/repobrain.yml@refs/heads/main",
            "RB_READINESS_GENERATION_WORKFLOW_SHA": "def456",
            "RB_READINESS_GENERATION_RUN_ID": "1001",
            "RB_READINESS_GENERATION_RUN_ATTEMPT": "3",
            "RB_READINESS_GENERATION_JOB_NAME": "repobrain",
        },
    )

    assert payload["status_reason_code"] == "github_app_id_invalid"
    assert payload["inputs_seen"]["app_id_present"] is True
    assert payload["inputs_seen"]["app_id_source"] == "vars"
    assert payload["inputs_seen"]["installation_id_source"] == "secret"
    assert payload["readiness_provenance"]["generation_event_name"] == "issue_comment"
    assert payload["readiness_provenance"]["generation_ref"] == "refs/heads/main"
    assert payload["readiness_provenance"]["generation_sha"] == "abc123"
    assert payload["readiness_provenance"]["generation_workflow_sha"] == "def456"
    assert payload["readiness_provenance"]["generation_run_id"] == "1001"
    assert payload["readiness_provenance"]["generation_run_attempt"] == "3"


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
