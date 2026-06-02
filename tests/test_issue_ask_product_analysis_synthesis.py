from __future__ import annotations

from pathlib import Path

import pytest

from repobrain.github_flow import _maybe_refine_operational_ask_answer


def test_issue_ask_product_analysis_has_deterministic_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workflow = tmp_path / ".github" / "workflows" / "repobrain.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(
        "name: RepoBrain\npermissions:\n  contents: read\n  issues: write\n",
        encoding="utf-8",
    )
    for rel in (
        "repobrain/commands.py",
        "repobrain/github_flow.py",
        "repobrain/output_md.py",
        "repobrain/doctor_status.py",
        "repobrain/audit_scoring.py",
        "repobrain/topocore_v6_adapter.py",
    ):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# stub\n", encoding="utf-8")

    control_plane_root = tmp_path / "repobrain-control"
    control_plane_root.mkdir(parents=True, exist_ok=True)
    (control_plane_root / "pyproject.toml").write_text("[project]\nname = 'repobrain-control'\n", encoding="utf-8")
    release_dir = control_plane_root / "docs" / "release"
    security_dir = control_plane_root / "docs" / "security"
    release_dir.mkdir(parents=True, exist_ok=True)
    security_dir.mkdir(parents=True, exist_ok=True)
    (release_dir / "PUBLIC_READINESS_ASSESSMENT.md").write_text(
        "- current public readiness decision: `PARTNER_PILOT_READY_AFTER_DIAGNOSTICS_AND_PERMISSION_CLASSIFICATION`\n",
        encoding="utf-8",
    )
    (release_dir / "INSTALLED_PACKAGE_LIVE_PROOF.md").write_text(
        "- `INSTALLED_PACKAGE_LIVE_PROOF_PASSED`\n",
        encoding="utf-8",
    )
    (security_dir / "REPO_GOVERNANCE_MODEL.md").write_text(
        "- `PROTECTED_MAIN_BASELINE_ENABLED`\n- `GOVERNANCE_PARTIAL_REQUIRED_CHECKS_DEFERRED`\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GITHUB_ACTION_PATH", str(control_plane_root))
    monkeypatch.setenv("RB_TOPOCORE_V6_RUNTIME_MODE", "installed_package")

    answer_text, next_steps, audit_summary = _maybe_refine_operational_ask_answer(
        repo_root=tmp_path,
        cmd="ask",
        question=(
            "Analyze this repository as an MCP product. Summarize functions/modules, runtime, "
            "external integrations, readiness, quality signals, risks, and next 5 steps."
        ),
        answer_text="Question: test\nRoute: REVIEW",
        next_steps="placeholder",
        audit_summary={
            "route_final": "REVIEW",
            "requested_backend": "auto",
            "resolved_backend": "not_applicable",
            "fallback_used": "not_applicable",
            "fallback_reason": "status_report_only",
        },
        github_context={"repository": "alexworkingai/RepoBrain-Action"},
    )

    assert "Core functions and modules:" in answer_text
    assert "External integrations:" in answer_text
    assert "Readiness and quality signals:" in answer_text
    assert "Next 5 steps:" in answer_text
    assert "Route: REVIEW" not in answer_text
    assert audit_summary["route_final"] == "ASK"
    assert next_steps
