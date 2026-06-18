from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_sprint94e_validation_evidence.py"
TEMPLATE = ROOT / "docs" / "release" / "SPRINT_94E_TRUSTED_PARTNER_BETA_VALIDATION_EVIDENCE.md"


def _run_checker(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--path", str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "evidence.md"
    path.write_text(text, encoding="utf-8")
    return path


def _trusted_ready_text() -> str:
    text = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "Sprint status: `SPRINT_94E_VALIDATION_PACKAGE_READY_OPERATOR_SETUP_PENDING`": "Sprint status: `TRUSTED_PARTNER_BETA_READY`",
        '"sprint_status": "SPRINT_94E_VALIDATION_PACKAGE_READY_OPERATOR_SETUP_PENDING"': '"sprint_status": "TRUSTED_PARTNER_BETA_READY"',
        '"decision": "NOT_READY_OPERATOR_SETUP_PENDING"': '"decision": "TRUSTED_PARTNER_BETA_READY"',
        '"repobrain_action_ref": "TBD_VALIDATED_REF"': '"repobrain_action_ref": "18e0c32"',
        '"validation_datetime": "TBD"': '"validation_datetime": "2026-06-18T12:00:00Z"',
        '"operator": "TBD"': '"operator": "codex-operator"',
        '"github_app_installed_on_mcp": "pending"': '"github_app_installed_on_mcp": "yes"',
        '"github_app_installed_on_community": "pending"': '"github_app_installed_on_community": "yes"',
        '"private_control_repo_configured": "pending"': '"private_control_repo_configured": "yes"',
        '"topocore_mode": "none"': '"topocore_mode": "real_private_entrypoint"',
        "| /repobrain score | TBD | TBD | TBD | TBD | TBD | none | pending | pending | not_run |": "| /repobrain score | https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/1 | https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/1#issuecomment-1 | rbq_mcp_score | run-1 | https://github.com/alexworkingai/Elen-MCP-v.2.2.0/issues/1#issuecomment-2 | real_private_entrypoint | yes | yes | pass |",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    for repo in ("alexworkingai/Elen-MCP-v.2.2.0", "alexworkingai/repobrain-community"):
        for command, suffix in (
            ("/repobrain score", "score"),
            ("/repobrain audit", "audit"),
            ("/repobrain audit --profile premium", "premium"),
        ):
            text = text.replace(
                f'"repository": "{repo}",\n      "command": "{command}",\n      "validation_url": "TBD",\n      "queue_comment_url": "TBD",\n      "request_id": "TBD",\n      "control_worker_run_ref": "TBD",\n      "final_result_url": "TBD",\n      "topocore_mode": "none",\n      "idempotency_pass": "pending",\n      "leakage_scan_pass": "pending",\n      "status": "not_run"',
                f'"repository": "{repo}",\n      "command": "{command}",\n      "validation_url": "https://github.com/{repo}/issues/1",\n      "queue_comment_url": "https://github.com/{repo}/issues/1#issuecomment-{suffix}-queue",\n      "request_id": "rbq_{repo.split("/")[1].replace(".", "").replace("-", "")}_{suffix}",\n      "control_worker_run_ref": "run-{repo.split("/")[1]}-{suffix}",\n      "final_result_url": "https://github.com/{repo}/issues/1#issuecomment-{suffix}-final",\n      "topocore_mode": "real_private_entrypoint",\n      "idempotency_pass": "yes",\n      "leakage_scan_pass": "yes",\n      "status": "pass"',
            )
    for key in (
        "no_github_app_private_key",
        "no_installation_token",
        "no_raw_jwt",
        "no_authorization_or_bearer",
        "no_pat",
        "no_topocore_token",
        "no_topocore_private_path",
        "no_dot_topocore_v6",
        "no_hosted_api_default_path",
        "no_repobrain_hosted_api_url_blocker",
        "no_decide_raw",
        "no_raw_internal_trace",
    ):
        text = text.replace(f'"{key}": "pending"', f'"{key}": "yes"')
    return text


def test_package_only_pending_evidence_passes(tmp_path: Path) -> None:
    result = _run_checker(_write(tmp_path, TEMPLATE.read_text(encoding="utf-8")))
    assert result.returncode == 0
    assert "SPRINT94E_EVIDENCE_CHECK=PASS" in result.stdout


def test_stub_only_status_passes(tmp_path: Path) -> None:
    text = TEMPLATE.read_text(encoding="utf-8").replace(
        "Sprint status: `SPRINT_94E_VALIDATION_PACKAGE_READY_OPERATOR_SETUP_PENDING`",
        "Sprint status: `SPRINT_94E_PLUMBING_VALIDATED_REAL_TOPOCORE_PENDING`",
    ).replace(
        '"sprint_status": "SPRINT_94E_VALIDATION_PACKAGE_READY_OPERATOR_SETUP_PENDING"',
        '"sprint_status": "SPRINT_94E_PLUMBING_VALIDATED_REAL_TOPOCORE_PENDING"',
    ).replace(
        '"topocore_mode": "none"',
        '"topocore_mode": "stub"',
    )
    result = _run_checker(_write(tmp_path, text))
    assert result.returncode == 0


def test_trusted_ready_with_placeholders_fails(tmp_path: Path) -> None:
    text = TEMPLATE.read_text(encoding="utf-8").replace(
        "Sprint status: `SPRINT_94E_VALIDATION_PACKAGE_READY_OPERATOR_SETUP_PENDING`",
        "Sprint status: `TRUSTED_PARTNER_BETA_READY`",
    ).replace(
        '"sprint_status": "SPRINT_94E_VALIDATION_PACKAGE_READY_OPERATOR_SETUP_PENDING"',
        '"sprint_status": "TRUSTED_PARTNER_BETA_READY"',
    )
    result = _run_checker(_write(tmp_path, text))
    assert result.returncode != 0
    assert "trusted_ready_contains_placeholders" in result.stdout


def test_trusted_ready_with_stub_mode_fails(tmp_path: Path) -> None:
    text = _trusted_ready_text().replace('"topocore_mode": "real_private_entrypoint"', '"topocore_mode": "stub"', 1)
    result = _run_checker(_write(tmp_path, text))
    assert result.returncode != 0
    assert "trusted_ready_requires_real_private_entrypoint" in result.stdout or "trusted_ready_stub_or_missing_topocore_mode" in result.stdout


def test_trusted_ready_without_both_repos_fails(tmp_path: Path) -> None:
    text = _trusted_ready_text().replace("alexworkingai/repobrain-community", "missing/repo")
    result = _run_checker(_write(tmp_path, text))
    assert result.returncode != 0
    assert "secondary_repo_missing" in result.stdout or "trusted_ready_repository_mismatch" in result.stdout


def test_trusted_ready_missing_one_command_fails(tmp_path: Path) -> None:
    text = _trusted_ready_text().replace('/repobrain audit --profile premium', '/repobrain audit --profile removed', 1)
    result = _run_checker(_write(tmp_path, text))
    assert result.returncode != 0
    assert "required_command_missing:/repobrain audit --profile premium" in result.stdout or "trusted_ready_missing_row" in result.stdout


def test_trusted_ready_missing_queue_reference_fails(tmp_path: Path) -> None:
    text = _trusted_ready_text().replace('#issuecomment-score-queue', '#issuecomment-TBD-queue', 1)
    result = _run_checker(_write(tmp_path, text))
    assert result.returncode != 0
    assert "trusted_ready_missing_field" in result.stdout


def test_trusted_ready_missing_final_result_reference_fails(tmp_path: Path) -> None:
    text = _trusted_ready_text().replace('#issuecomment-score-final', '#issuecomment-TBD-final', 1)
    result = _run_checker(_write(tmp_path, text))
    assert result.returncode != 0
    assert "trusted_ready_missing_field" in result.stdout


def test_trusted_ready_missing_request_id_fails(tmp_path: Path) -> None:
    text = _trusted_ready_text().replace('"request_id": "rbq_', '"request_id": "TBD_', 1)
    result = _run_checker(_write(tmp_path, text))
    assert result.returncode != 0
    assert "trusted_ready_missing_field" in result.stdout


def test_trusted_ready_with_hosted_api_used_yes_fails(tmp_path: Path) -> None:
    text = _trusted_ready_text().replace('"hosted_api_used": "no"', '"hosted_api_used": "yes"')
    result = _run_checker(_write(tmp_path, text))
    assert result.returncode != 0
    assert "trusted_ready_requires_hosted_api_no" in result.stdout


def test_trusted_ready_with_leakage_scan_not_pass_fails(tmp_path: Path) -> None:
    text = _trusted_ready_text().replace('"no_github_app_private_key": "yes"', '"no_github_app_private_key": "pending"', 1)
    result = _run_checker(_write(tmp_path, text))
    assert result.returncode != 0
    assert "trusted_ready_requires_leakage_scan_yes" in result.stdout


def test_trusted_ready_with_idempotency_not_pass_fails(tmp_path: Path) -> None:
    text = _trusted_ready_text().replace('"idempotency_pass": "yes"', '"idempotency_pass": "pending"', 1)
    result = _run_checker(_write(tmp_path, text))
    assert result.returncode != 0
    assert "trusted_ready_idempotency_missing" in result.stdout


def test_forbidden_statuses_fail(tmp_path: Path) -> None:
    for forbidden in ("PUBLIC_DEVELOPER_BETA_READY", "MARKETPLACE_READY", "PRODUCTION_APPROVED", "SECURITY_CERTIFIED"):
        result = _run_checker(_write(tmp_path, TEMPLATE.read_text(encoding="utf-8") + f"\n{forbidden}\n"))
        assert result.returncode != 0
        assert f"forbidden_status_present:{forbidden}" in result.stdout
