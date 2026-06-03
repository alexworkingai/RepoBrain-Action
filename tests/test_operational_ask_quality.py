from __future__ import annotations

from pathlib import Path

import pytest

from repobrain.github_flow import (
    _classify_operational_ask_intent,
    _maybe_refine_operational_ask_answer,
)


def test_operational_ask_intent_is_recognized() -> None:
    kind = _classify_operational_ask_intent(
        "What is the current runtime mode, workflow location, and public-switch readiness status?"
    )

    assert kind in {"runtime_status", "public_readiness"}


def test_operational_ask_answer_includes_runtime_workflow_and_readiness(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workflow = tmp_path / ".github" / "workflows" / "repobrain.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(
        "name: RepoBrain\npermissions:\n  contents: read\n  issues: write\n",
        encoding="utf-8",
    )
    control_plane_root = tmp_path / "repobrain-control"
    control_plane_root.mkdir(parents=True, exist_ok=True)
    (control_plane_root / "pyproject.toml").write_text("[project]\nname = 'repobrain-control'\n", encoding="utf-8")
    release_dir = control_plane_root / "docs" / "release"
    release_dir.mkdir(parents=True, exist_ok=True)
    (release_dir / "PUBLIC_READINESS_ASSESSMENT.md").write_text(
        "# Public Readiness Assessment\n\n- current public readiness decision: `PUBLIC_BLOCKED_BY_RUNTIME_PROOF`\n",
        encoding="utf-8",
    )
    (release_dir / "INSTALLED_PACKAGE_LIVE_PROOF.md").write_text(
        "# Installed Package Live Proof\n\n- `INSTALLED_PACKAGE_LIVE_PROOF_BLOCKED`\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GITHUB_ACTION_PATH", str(control_plane_root))
    monkeypatch.setenv("RB_TOPOCORE_V6_RUNTIME_MODE", "installed_package")

    answer_text, next_steps, audit_summary = _maybe_refine_operational_ask_answer(
        repo_root=tmp_path,
        cmd="ask",
        question="What is the current runtime mode, workflow location, and public-switch readiness status?",
        answer_text="Question: test\nRoute: REVIEW",
        next_steps="placeholder",
        audit_summary={
            "route_final": "REVIEW",
            "requested_backend": "auto",
            "resolved_backend": "not_applicable",
            "fallback_used": "not_applicable",
            "fallback_reason": "status_report_only",
        },
        github_context={"repository": "alexworkingai/Elen-MCP-v.2.2.0"},
    )

    assert "Current RepoBrain operational status:" in answer_text
    assert "Workflow location: `.github/workflows/repobrain.yml`" in answer_text
    assert "Private runtime boundary is configured." in answer_text
    assert "Partner-preferred path: installed private package." in answer_text
    assert "Public-switch readiness: `PUBLIC_BLOCKED_BY_RUNTIME_PROOF`" in answer_text
    assert "Installed-package live proof: `INSTALLED_PACKAGE_LIVE_PROOF_BLOCKED`" in answer_text
    assert "no patch/autofix" in answer_text.lower()
    assert "Route: REVIEW" not in answer_text
    assert "review-style" not in answer_text.lower()
    assert "repo brain-action is public" not in answer_text.lower()
    assert "C:\\" not in answer_text
    assert next_steps.startswith("Complete external installed-package live proof")
    assert audit_summary["route_final"] == "ASK"
    assert audit_summary["operational_ask_intent"] is True


def test_non_operational_ask_is_left_unchanged(tmp_path: Path) -> None:
    workflow = tmp_path / ".github" / "workflows" / "repobrain.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text("name: RepoBrain\n", encoding="utf-8")

    answer_text, next_steps, audit_summary = _maybe_refine_operational_ask_answer(
        repo_root=tmp_path,
        cmd="ask",
        question="Where is TKYProvider defined?",
        answer_text="Question: test\nRoute: FAST",
        next_steps="Open evidence links and verify logic",
        audit_summary={"route_final": "FAST"},
        github_context={"repository": "alexworkingai/RepoBrain-Action"},
    )

    assert answer_text == "Question: test\nRoute: FAST"
    assert next_steps == "Open evidence links and verify logic"
    assert audit_summary["route_final"] == "FAST"
